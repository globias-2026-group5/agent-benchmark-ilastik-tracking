"""Same frames, every annotator: Session 4's simulated annotators next to the real 2014 one.

Needs a rerun of Session 4's scripts (sessions/session-4-blind-opus/scripts, run as described in
sessions/RUNBOOK_blind_sessions.md); point S4_RUN at that run's root folder (with projects/, out/probs/,
out/consensus/). Session 4's own consensus.load() is used, so the masks are exactly the ones it compared:
probability > 0.5, holes filled, objects of 20 px or less removed.

Row 1: what each annotator painted (its brush labels, on the frame where it painted most).
Rows 2-3: each annotator's resulting nucleus mask and three consensus rules, on the same crop of two frames.
The crops are where the six annotators disagree most.

usage: S4_RUN=/path/to/s4run python figures/annotators_panel.py
"""
import os
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.segmentation import find_boundaries

REPO = Path(__file__).resolve().parents[1]
S4 = Path(os.environ["S4_RUN"]).resolve()
sys.path.insert(0, str(S4 / "scripts"))
import consensus as s4  # noqa: E402  (Session 4's own script)

OUT = REPO / "img" / "annotators_same_frame.png"
BLUE, ORANGE, MAGENTA, INK, INK2, SURFACE = "#2a78d6", "#eb6834", "#e87ba4", "#0b0b0b", "#52514e", "#fcfcfb"
ANNOTATORS = [("A0_ilastik_human", "A0: the 2014 person\n(real brush strokes)"),
              ("A1_tight", "A1: tight edges"), ("A2_generous", "A2: 2-px halo"),
              ("A3_bright_only", "A3: dim nuclei =\nbackground"), ("A4_sparse", "A4: very few strokes"),
              ("A5_late_frames", "A5: late frames only")]
RULES = [("majority (>=4of6)", "majority (≥ 4 of 6)"), ("unanimity (6of6)", "unanimity (6 of 6)"),
         ("STAPLE", "STAPLE")]
CROP, ZOOM = 120, 3

raw = h5py.File(S4 / "data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
lo, hi = np.percentile(raw[::4, ::4, ::4, 0], [1, 99.8])
gray = lambda t: np.clip((raw[t, ..., 0].T - lo) / (hi - lo), 0, 1)  # (y, x)


def strokes(name):
    """{frame: label image (y, x)} of the brush labels stored in the annotator's project."""
    out = {}
    with h5py.File(S4 / "projects" / f"{name}.ilp", "r") as f:
        for block in f["PixelClassification/LabelSets/labels000"].values():
            t = int(block.attrs["blockSlice"].strip("[]").split(",")[0].split(":")[0])
            lab = block[0, ..., 0]
            out[t] = np.maximum(out.get(t, np.zeros_like(lab)), lab)
    return out


def best_crop(score, size):
    """Top-left (y, x) of the size x size window with the largest sum of `score`."""
    s = ndimage.uniform_filter(score.astype(np.float32), size=size, mode="constant")
    h = size // 2
    s[:h], s[-h:], s[:, :h], s[:, -h:] = 0, 0, 0, 0
    cy, cx = np.unravel_index(np.argmax(s), s.shape)
    return int(cy - h), int(cx - h)


def show(ax, rgb, title=None, sub=None):
    ax.imshow(np.kron(rgb, np.ones((ZOOM, ZOOM, 1))), interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#d0cfca")
    if title:
        ax.set_title(title, fontsize=8.5, color=INK)
    if sub:
        ax.set_xlabel(sub, fontsize=7.5, color=INK2)


def mask_tile(t, win, mask):
    g = gray(t)[win]
    rgb = np.repeat(g[..., None] * 0.85, 3, axis=2)
    m = mask[win]
    rgb[m] = rgb[m] * 0.55 + np.array(matplotlib.colors.to_rgb(ORANGE)) * 0.45
    rgb[find_boundaries(m, mode="inner")] = matplotlib.colors.to_rgb(ORANGE)
    return rgb


def main():
    names = [n for n, _ in ANNOTATORS]
    _, M = s4.load(names)                      # masks as (t, x, y)
    M = {k: np.transpose(v, (0, 2, 1)) for k, v in M.items()}  # -> (t, y, x)
    votes = np.stack([M[k] for k in names]).sum(0)
    with h5py.File(S4 / "out/consensus/consensus_A0_A1_A2_A3_A4_A5.h5", "r") as f:
        R = {k: np.transpose(f[k][...].astype(bool), (0, 2, 1)) for k, _ in RULES}
    disputed = (votes > 0) & (votes < len(names))
    frames = [26, 45]
    wins = []
    for t in frames:
        y0, x0 = best_crop(disputed[t], CROP)
        wins.append((slice(y0, y0 + CROP), slice(x0, x0 + CROP)))

    cols = len(ANNOTATORS) + len(RULES)
    fig, axes = plt.subplots(3, cols, figsize=(1.75 * cols, 6.3))
    for c, (name, label) in enumerate(ANNOTATORS):
        st = strokes(name)
        t = max(st, key=lambda k: int((st[k] > 0).sum()))
        lab = st[t]
        y0, x0 = best_crop(lab > 0, CROP)
        win = (slice(y0, y0 + CROP), slice(x0, x0 + CROP))
        rgb = np.repeat(gray(t)[win][..., None], 3, axis=2)
        rgb[lab[win] == 1] = matplotlib.colors.to_rgb(BLUE)
        rgb[lab[win] == 2] = matplotlib.colors.to_rgb(ORANGE)
        n_px = int((lab > 0).sum())
        show(axes[0, c], rgb, label, f"painted: frame {t}, {n_px:,} px")
    for c, (_, label) in enumerate(RULES, start=len(ANNOTATORS)):
        axes[0, c].axis("off")
        axes[0, c].text(0.5, 0.5, f"consensus\n{label}", ha="center", va="center", fontsize=9, color=INK)
    for r, (t, win) in enumerate(zip(frames, wins), start=1):
        for c, (name, _) in enumerate(ANNOTATORS):
            n_obj = ndimage.label(M[name][t][win])[1]
            show(axes[r, c], mask_tile(t, win, M[name][t]), sub=f"{n_obj} objects")
        for c, (key, _) in enumerate(RULES, start=len(ANNOTATORS)):
            n_obj = ndimage.label(R[key][t][win])[1]
            show(axes[r, c], mask_tile(t, win, R[key][t]), sub=f"{n_obj} objects")
        axes[r, 0].set_ylabel(f"frame {t}\nx {win[1].start}–{win[1].stop}\ny {win[0].start}–{win[0].stop}",
                              fontsize=8, color=INK2)
    fig.suptitle("Same frames, every annotator (Session 4, rerun): row 1 what each one painted "
                 "(blue = background, orange = nucleus); rows 2–3 the nucleus mask its ilastik classifier "
                 "produced (orange)", x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.text(0.01, 0.005, "Crops in rows 2–3 are where the six annotators disagree most. A1–A5 are simulated "
             "by Session 4's program; only A0 was drawn by a person.", fontsize=8, color=INK2)
    fig.patch.set_facecolor(SURFACE)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(OUT, dpi=110, facecolor=SURFACE)
    print(OUT)


if __name__ == "__main__":
    main()
