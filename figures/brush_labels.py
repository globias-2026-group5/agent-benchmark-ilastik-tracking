"""Where the only real annotation lives: the 2014 brush strokes stored in pixelClassification.ilp.

Draws frame 0 with every painted pixel (blue = label 1, background; orange = label 2, nucleus), plus
zoomed crops, and the strokes on frames 22 and 39.
usage: python figures/brush_labels.py   (see the README for ILASTIK_RUN)
"""
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Rectangle

import os
REPO = Path(__file__).resolve().parents[1]
START = Path.cwd()
# data/, results/ and scripts/ come from a checkout of globias-2026-group5/ilastik-mitocheck-run.
ORIGINAL = Path(os.environ.get("ILASTIK_RUN", REPO.parent / "ilastik-mitocheck-run")).resolve()
os.chdir(ORIGINAL)
sys.path.insert(0, str(ORIGINAL / "scripts"))
from overlay import contrast_limits  # noqa: E402

OUT = REPO / "img" / "brush_labels_2014.png"
BLUE, ORANGE, INK2, SURFACE = "#2a78d6", "#eb6834", "#52514e", "#fcfcfb"

raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
lo, hi = contrast_limits(raw)
labels = np.zeros(raw.shape[:3], np.uint8)  # t, x, y as stored
with h5py.File("data/mitocheck_2d+t/pixelClassification.ilp", "r") as p:
    for block in p["PixelClassification/LabelSets/labels000"].values():
        sl = tuple(slice(*map(int, s.split(":"))) for s in block.attrs["blockSlice"].strip("[]").split(","))
        labels[sl[:3]] = np.maximum(labels[sl[:3]], block[()][..., 0])


def painted(t, win=None):
    g = np.clip((raw[t, ..., 0].T - lo) / (hi - lo), 0, 1)
    lab = labels[t].T
    if win:
        g, lab = g[win], lab[win]
    rgb = np.repeat(g[..., None], 3, axis=2)
    rgb[lab == 1] = matplotlib.colors.to_rgb(BLUE)
    rgb[lab == 2] = matplotlib.colors.to_rgb(ORANGE)
    return rgb, lab


fig = plt.figure(figsize=(13, 8.4))
gs = fig.add_gridspec(2, 4, height_ratios=[2.2, 1])
ax = fig.add_subplot(gs[0, :3])
img, lab = painted(0)
ax.imshow(img)
ax.set_title(f"Frame 0: all {int((lab == 1).sum()):,} background and {int((lab == 2).sum()):,} nucleus pixels painted "
             "in 2014", loc="left", fontsize=11, fontweight="bold")
ax.axis("off")
# Zoom on the three largest nucleus strokes of frame 0.
from scipy import ndimage
comp, n = ndimage.label(lab == 2)
sizes = ndimage.sum(lab == 2, comp, range(1, n + 1))
crops = []
for k in np.argsort(sizes)[::-1][:3]:
    cy, cx = ndimage.center_of_mass(comp == k + 1)
    crops.append((int(cx) - 30, int(cy) - 30, 60))  # (x, y, size)
for i, (x, y, s) in enumerate(crops, 1):
    ax.add_patch(Rectangle((x, y), s, s, fill=False, ec="white", lw=1.2))
    ax.text(x, y - 8, str(i), color="white", fontsize=10, fontweight="bold")
side = fig.add_subplot(gs[0, 3])
side.axis("off")
side.text(0, 0.95, "How it was made", fontsize=11, fontweight="bold", va="top")
side.text(0, 0.86, "A person painted strokes with ilastik's\nbrush in the GUI: blue on background,\n"
          "orange inside nuclei. ilastik stores\nthem in 64 × 64 px blocks (27 blocks).\n\n"
          "A random forest learned from these\npixels, using 6 filter types at\nσ = 1.6 and 3.5, and then "
          "labelled\nevery pixel of all 53 frames.\n\nEvery 'annotator' in the blind\nsessions is derived from "
          "these\n5,157 pixels.", fontsize=9.5, color=INK2, va="top")
for i, (x, y, s) in enumerate(crops):
    a = fig.add_subplot(gs[1, i])
    a.imshow(painted(0, (slice(y, y + s), slice(x, x + s)))[0], interpolation="nearest")
    a.set_title(f"{i + 1}: nucleus stroke, x {x} y {y}", fontsize=9, loc="left")
    a.axis("off")
a = fig.add_subplot(gs[1, 3])
counts = [(t, int((labels[t] == 1).sum()), int((labels[t] == 2).sum())) for t in range(raw.shape[0])
          if labels[t].any()]
a.axis("off")
a.text(0, 0.95, "Painted pixels per frame", fontsize=10, fontweight="bold", va="top")
a.text(0, 0.75, "\n".join(f"frame {t:>2}: {b:>5,} background, {n:>4,} nucleus" for t, b, n in counts),
       fontsize=9, family="monospace", va="top", color=INK2)
fig.legend(handles=[Patch(color=BLUE, label="label 1: background stroke"),
                    Patch(color=ORANGE, label="label 2: nucleus stroke")],
           loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))
fig.patch.set_facecolor(SURFACE)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT, dpi=100, facecolor=SURFACE)
print(OUT, counts)
