"""6 x 6 panel: the 2014 object segmentation vs Session 0's rerun (ilastik 1.3.3post3).

"2014 original": the object label image stored in data/mitocheck_2d+t/conservationTracking.ilp
(TrackingFeatureExtraction/LabelImage), i.e. what ilastik segmented in 2014.
"Session 0": results/ilastik-1.3.3post3/03_tracking/*_Object-Identities.h5 from this repository.

36 frames are drawn at random (fixed seed, without replacement); in each, a 96 x 96 px crop is centred on
a random labelled pixel. Outlines: white where both runs draw the same object boundary, blue where only
the 2014 original has a boundary, orange where only Session 0 has one.

usage: python figures/annotation_panel.py   (see the README for ILASTIK_RUN)
"""
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy import ndimage
from skimage.segmentation import find_boundaries

import sys
import os
REPO = Path(__file__).resolve().parents[1]
START = Path.cwd()
# data/, results/ and scripts/ come from a checkout of globias-2026-group5/ilastik-mitocheck-run.
ORIGINAL = Path(os.environ.get("ILASTIK_RUN", REPO.parent / "ilastik-mitocheck-run")).resolve()
os.chdir(ORIGINAL)
sys.path.insert(0, str(ORIGINAL / "scripts"))
from overlay import contrast_limits  # noqa: E402

OUT = REPO / "img" / "annotations_vs_2014.png"
BLUE, ORANGE, INK, INK2, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
SEED, GRID, CROP, ZOOM = 2026, 6, 96, 3

raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
orig = h5py.File("data/mitocheck_2d+t/conservationTracking.ilp", "r")["TrackingFeatureExtraction/LabelImage/0"]
mine = h5py.File("results/ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_Object-Identities.h5",
                 "r")["exported_data"]
lo, hi = contrast_limits(raw)


def frame_labels(t):
    """(2014, Session 0) object labels of frame t, as (y, x)."""
    o = orig[f"[[{t}, 0, 0, 0, 0], [{t + 1}, 1344, 1024, 1, 1]]"][0, :, :, 0, 0].T
    return o, mine[t, ..., 0].T


def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)


def tile(t, rng):
    a, b = frame_labels(t)
    ys, xs = np.nonzero((a > 0) | (b > 0))
    i = rng.integers(len(ys))
    h, w = a.shape
    y0 = int(np.clip(ys[i] - CROP // 2, 0, h - CROP))
    x0 = int(np.clip(xs[i] - CROP // 2, 0, w - CROP))
    win = (slice(y0, y0 + CROP), slice(x0, x0 + CROP))
    # Upscale first so outlines are thin relative to the cells.
    up = lambda img: np.kron(img, np.ones((ZOOM, ZOOM), dtype=img.dtype))
    gray = up(np.clip((raw[t, ..., 0].T[win] - lo) / (hi - lo), 0, 1))
    la, lb = up(a[win]), up(b[win])
    ea, eb = find_boundaries(la, mode="inner"), find_boundaries(lb, mode="inner")
    ea, eb = ndimage.binary_dilation(ea), ndimage.binary_dilation(eb)
    rgb = np.repeat(gray[..., None] * 0.9, 3, axis=2)
    rgb[ea & ~eb] = matplotlib.colors.to_rgb(BLUE)
    rgb[eb & ~ea] = matplotlib.colors.to_rgb(ORANGE)
    rgb[ea & eb] = 1.0
    return rgb, (t, x0, y0, iou(a[win] > 0, b[win] > 0))


def whole_movie():
    I = U = 0
    counts = []
    for t in range(raw.shape[0]):
        a, b = frame_labels(t)
        I += int(((a > 0) & (b > 0)).sum())
        U += int(((a > 0) | (b > 0)).sum())
        counts.append((len(np.unique(a)) - 1, len(np.unique(b)) - 1))
    return I / U, counts


def main():
    rng = np.random.default_rng(SEED)
    frames = sorted(rng.choice(raw.shape[0], size=GRID * GRID, replace=False).tolist())
    total_iou, counts = whole_movie()
    fig, axes = plt.subplots(GRID, GRID, figsize=(13, 14.2))
    for ax, t in zip(axes.ravel(), frames):
        img, (t, x0, y0, tile_iou) = tile(t, rng)
        ax.imshow(img, interpolation="nearest")
        ax.set_title(f"frame {t} · x {x0} y {y0} · IoU {tile_iou:.3f}", fontsize=7.5, color=INK2, pad=2)
        ax.axis("off")
    fig.suptitle("2014 original segmentation vs Session 0's rerun (ilastik 1.3.3post3): 36 random frames, "
                 "one random 96 × 96 px crop each", x=0.01, ha="left", fontsize=12, fontweight="bold", y=0.995)
    n_diff = sum(a != b for a, b in counts)
    fig.text(0.01, 0.968, f"Whole movie: cell-mask IoU {100 * total_iou:.2f}%; objects per frame "
             f"{min(c[0] for c in counts)}–{max(c[0] for c in counts)} (2014) vs "
             f"{min(c[1] for c in counts)}–{max(c[1] for c in counts)} (Session 0); counts differ in "
             f"{n_diff} of {len(counts)} frames, by at most {max(abs(a - b) for a, b in counts)}.",
             fontsize=9.5, color=INK2)
    fig.legend(handles=[Patch(fc="white", ec=INK2, label="outline drawn by both"),
                        Patch(color=BLUE, label="outline only in the 2014 original"),
                        Patch(color=ORANGE, label="outline only in Session 0's rerun")],
               loc="lower center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(0.5, 0.0))
    fig.patch.set_facecolor(SURFACE)
    fig.tight_layout(rect=(0, 0.025, 1, 0.962))
    fig.savefig(OUT, dpi=100, facecolor=SURFACE)
    print(OUT, "frames:", frames)


if __name__ == "__main__":
    main()
