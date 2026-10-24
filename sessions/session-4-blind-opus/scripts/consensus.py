"""Build consensus "ground truth" from several ilastik annotators and compare the rules.

Input : out/probs/<annotator>.h5 (ilastik probability export, channel 1 = nucleus)
Output: out/consensus_metrics.json, out/*.png, out/consensus/<rule>.h5
Usage : python consensus.py A0_ilastik_human A1_tight ...   (default: all files in out/probs)
"""
import json, sys
from itertools import combinations
from pathlib import Path
import h5py
import numpy as np
from scipy import ndimage as ndi
from skimage import measure, morphology
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROBS = ROOT / "out/probs"
MIN_SIZE = 20          # px; objects smaller than this are treated as noise
NUC = 1                # probability channel of label 2 ("nucleus")


def load(names):
    P, M = {}, {}
    for n in names:
        with h5py.File(PROBS / f"{n}.h5", "r") as f:
            p = f["probs"][..., NUC].astype(np.float32)
        P[n] = p
        m = p > 0.5
        for t in range(m.shape[0]):
            m[t] = morphology.remove_small_objects(ndi.binary_fill_holes(m[t]), max_size=MIN_SIZE)
        M[n] = m
    return P, M


def dice(a, b):
    s = a.sum() + b.sum()
    return float(2 * (a & b).sum() / s) if s else 1.0


def staple(masks, iters=50):
    """Binary STAPLE (Warfield 2004) via EM over the 2^N vote patterns."""
    n = len(masks)
    code = np.zeros(masks[0].shape, np.int64)
    for j, m in enumerate(masks):
        code |= m.astype(np.int64) << j
    counts = np.bincount(code.ravel(), minlength=2 ** n).astype(float)
    D = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).astype(float)  # pattern x annotator
    prior = (D.mean(1) * counts).sum() / counts.sum()
    p = np.full(n, 0.9); q = np.full(n, 0.9)
    for _ in range(iters):
        a = prior * np.prod(np.where(D == 1, p, 1 - p), axis=1)
        b = (1 - prior) * np.prod(np.where(D == 0, q, 1 - q), axis=1)
        W = a / (a + b)
        p = (counts * W) @ D / (counts * W).sum()
        q = (counts * (1 - W)) @ (1 - D) / (counts * (1 - W)).sum()
    return W[code] > 0.5, dict(sensitivity=p.tolist(), specificity=q.tolist())


def objects_per_frame(m):
    labs = [measure.label(m[t]) for t in range(m.shape[0])]
    counts = [int(l.max()) for l in labs]
    areas = np.concatenate([np.bincount(l.ravel())[1:] for l in labs])
    return labs, counts, areas


def flicker(labs):
    """Objects present at t with no overlapping object at t-1 AND t+1 (not touching the border).
    Nuclei do not appear for a single frame, so this is a time-based plausibility check that is
    independent of the annotators."""
    bad = tot = 0
    for t in range(1, len(labs) - 1):
        l = labs[t]
        for r in measure.regionprops(l):
            y0, x0, y1, x1 = r.bbox
            if y0 == 0 or x0 == 0 or y1 == l.shape[0] or x1 == l.shape[1]:
                continue
            tot += 1
            c = tuple(r.coords.T)
            if not labs[t - 1][c].any() and not labs[t + 1][c].any():
                bad += 1
    return bad, tot


def object_votes(union_labs, M, names):
    """For every object of the union mask: how many annotators detect it (>=50% overlap)."""
    votes, area, inten = [], [], []
    for t, l in enumerate(union_labs):
        for r in measure.regionprops(l):
            c = tuple(r.coords.T)
            v = sum(M[n][t][c].mean() >= 0.5 for n in names)
            votes.append(v); area.append(r.area)
    return np.array(votes), np.array(area)


def main():
    names = sys.argv[1:] or sorted(p.stem for p in PROBS.glob("*.h5"))
    n = len(names)
    P, M = load(names)
    stack = np.stack([M[k] for k in names])
    votes = stack.sum(0)
    w = np.array([2.0 if k.startswith("A0") else 1.0 for k in names])  # "expert" weight for real human labels

    rules = {
        "union (>=1)": votes >= 1,
        f"majority (>={n // 2 + 1}/{n})": votes >= n // 2 + 1,
        f"unanimity ({n}/{n})": votes == n,
        "mean probability > 0.5": np.mean([P[k] for k in names], axis=0) > 0.5,
        "weighted vote (A0 x2)": np.tensordot(w, stack, axes=1) > w.sum() / 2,
    }
    st_mask, st_par = staple([M[k] for k in names])
    rules["STAPLE"] = st_mask
    uncertain = (votes > 0) & (votes < n)

    res = {"annotators": names, "rules": {}, "staple": dict(zip(["sensitivity", "specificity"],
           [dict(zip(names, st_par["sensitivity"])), dict(zip(names, st_par["specificity"]))]))}
    res["pairwise_dice"] = {f"{a}|{b}": dice(M[a], M[b]) for a, b in combinations(names, 2)}
    res["leave_one_out_dice"] = {}
    for k in names:
        others = np.stack([M[o] for o in names if o != k]).sum(0) >= (n - 1) // 2 + 1
        res["leave_one_out_dice"][k] = dice(M[k], others)
    res["uncertain_fraction_of_union"] = float(uncertain.sum() / (votes > 0).sum())

    per_frame_counts, labs_cache = {}, {}
    for name, m in {**{k: M[k] for k in names}, **rules}.items():
        labs, counts, areas = objects_per_frame(m)
        bad, tot = flicker(labs)
        labs_cache[name] = labs
        per_frame_counts[name] = counts
        entry = dict(mean_count=float(np.mean(counts)), mean_area=float(areas.mean()),
                     median_area=float(np.median(areas)), fg_pixels=int(m.sum()),
                     flicker_objects=bad, flicker_rate=bad / max(tot, 1))
        if name in rules:
            entry["dice_vs_annotators"] = {k: dice(m, M[k]) for k in names}
            res["rules"][name] = entry
        else:
            res.setdefault("per_annotator", {})[name] = entry

    v, a = object_votes(labs_cache["union (>=1)"], M, names)
    res["object_vote_histogram"] = {int(i): int((v == i).sum()) for i in range(n + 1)}
    res["object_median_area_by_votes"] = {int(i): float(np.median(a[v == i])) for i in range(n + 1) if (v == i).any()}

    out = ROOT / "out"; tag = "_".join(k.split("_")[0] for k in names)
    (out / f"consensus_metrics_{tag}.json").write_text(json.dumps(res, indent=1))
    (out / "consensus").mkdir(exist_ok=True)
    with h5py.File(out / "consensus" / f"consensus_{tag}.h5", "w") as f:
        for k, m in rules.items():
            f.create_dataset(k.replace("/", "of"), data=m.astype(np.uint8), compression="gzip")
        three = np.where(votes == n, 2, np.where(votes == 0, 1, 0)).astype(np.uint8)
        f.create_dataset("three_class (1=bg,2=nucleus,0=ignore)", data=three, compression="gzip")
        f.create_dataset("vote_count", data=votes.astype(np.uint8), compression="gzip")

    # figure 1: per-frame nucleus counts for annotators and rules
    fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
    for k in names:
        ax[0].plot(per_frame_counts[k], label=k)
    ax[0].set(title="Nuclei per frame: individual annotators", xlabel="frame", ylabel="count")
    for k in rules:
        ax[1].plot(per_frame_counts[k], label=k)
    ax[1].set(title="Nuclei per frame: consensus rules", xlabel="frame")
    for x in ax: x.legend(fontsize=7)
    fig.savefig(out / f"counts_{tag}.png", dpi=110, bbox_inches="tight")

    # figure 2: vote map crop on one frame
    with h5py.File(ROOT / "data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r") as f:
        raw = f["volume/data"][26, ..., 0].astype(float)
    t, (y0, y1, x0, x1) = 26, (300, 700, 250, 750)
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    ax[0].imshow(raw[y0:y1, x0:x1], cmap="gray", vmax=np.percentile(raw, 99.8)); ax[0].set_title("raw, frame 26")
    im = ax[1].imshow(votes[t, y0:y1, x0:x1], cmap="magma", vmin=0, vmax=n)
    ax[1].set_title(f"# annotators calling 'nucleus' (0..{n})"); fig.colorbar(im, ax=ax[1])
    three = np.where(votes[t] == n, 2, np.where(votes[t] == 0, 1, 0))[y0:y1, x0:x1]
    ax[2].imshow(three, cmap=matplotlib.colors.ListedColormap(["orange", "black", "white"]))
    ax[2].set_title("3-class GT: white=unanimous nucleus, orange=disputed (ignore)")
    for x in ax: x.axis("off")
    fig.savefig(out / f"votes_{tag}.png", dpi=110, bbox_inches="tight")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
