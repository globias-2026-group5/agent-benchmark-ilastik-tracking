"""Objects found by A0 (real human labels) but rejected by the bias-pool majority vote:
how bright are they and do they persist over time? (evidence independent of the vote)."""
import json
import h5py, numpy as np
from scipy import ndimage as ndi
from skimage import measure
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
raw = h5py.File(ROOT / "data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5")["volume/data"][..., 0].astype(np.float32)
a0 = h5py.File(ROOT / "out/probs/A0_ilastik_human.h5")["probs"][..., 1] > 0.5
c = h5py.File(ROOT / "out/consensus/consensus_A0_A1_A3_A3b_A3c.h5")
mv = c["majority (>=3of5)"][:].astype(bool)
bg = np.median(raw, axis=(1, 2))
rows = []
for t in range(1, raw.shape[0] - 1):
    lab = measure.label(a0[t])
    for r in measure.regionprops(lab, intensity_image=raw[t]):
        if r.area < 20: continue
        cc = tuple(r.coords.T)
        rejected = mv[t][cc].mean() < 0.5
        persist = a0[t - 1][cc].any() and a0[t + 1][cc].any()
        rows.append((t, rejected, r.area, r.intensity_mean - bg[t], persist, r.centroid))
rej = [r for r in rows if r[1]]; acc = [r for r in rows if not r[1]]
noise = raw[:, :50, :50].std()
out = dict(n_A0_objects=len(rows), n_rejected_by_majority=len(rej),
           rejected_median_area=float(np.median([r[2] for r in rej])),
           accepted_median_area=float(np.median([r[2] for r in acc])),
           rejected_median_signal_above_bg=float(np.median([r[3] for r in rej])),
           accepted_median_signal_above_bg=float(np.median([r[3] for r in acc])),
           background_noise_sd=float(noise),
           rejected_persist_frac=float(np.mean([r[4] for r in rej])),
           accepted_persist_frac=float(np.mean([r[4] for r in acc])))
print(json.dumps(out, indent=1))
(ROOT / "out/disputed_objects.json").write_text(json.dumps(out, indent=1))
# figure: frame 26 crop, A0 vs bias majority, rejected objects circled
t, (y0, y1, x0, x1) = 26, (0, 700, 0, 1024)
fig, ax = plt.subplots(1, 2, figsize=(16, 6))
for a, m, title in [(ax[0], a0[t], "A0 (real human labels) - ilastik"), (ax[1], mv[t], "Majority vote, pool with 3/5 'bright-only' annotators")]:
    a.imshow(raw[t, y0:y1, x0:x1], cmap="gray", vmax=np.percentile(raw[t], 99.5))
    a.contour(m[y0:y1, x0:x1], [0.5], colors="lime", linewidths=0.7); a.set_title(title); a.axis("off")
for r in rej:
    if r[0] == t:
        cy, cx = r[5]
        ax[1].add_patch(plt.Circle((cx - x0, cy - y0), 18, fill=False, color="red", lw=1.2))
fig.savefig(ROOT / "out/bias_majority_frame26.png", dpi=110, bbox_inches="tight")
