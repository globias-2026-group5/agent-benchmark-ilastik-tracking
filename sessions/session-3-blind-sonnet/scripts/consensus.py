"""GloBIAS Group 5 (Consensus) on the ilastik MitoCheck 2D+t example.

No human annotators exist, so five SIMULATED annotators are made from the
27 label patches stored in pixelClassification.ilp (each gets a random 60%
of the patches). Everything below is explained in report.md.
"""
import json
import sys
import h5py
import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import RandomForestClassifier
from skimage.filters import threshold_otsu
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = sys.argv[1]   # folder with the ilastik files
OUT = sys.argv[2]    # results folder
FRAMES = [0, 10, 22, 30, 39, 40, 52]   # 0,22,39,40 contain labels; 10,30,52 do not
N_ANN, FRAC, SEED = 5, 0.6, 0
MIN_SIZE = 30        # pixels; smaller blobs are not counted as nuclei

raw = h5py.File(f"{DATA}/mitocheck_94570_2D+t_01-53.h5")["volume/data"]
exp = h5py.File(f"{DATA}/mitocheck_94570_2D+t_01-53_export.h5")["volume/data"]
ilp = h5py.File(f"{DATA}/pixelClassification.ilp")


# ---------- features (approximation of ilastik's 6 feature types, scales 1.6 and 3.5)
def features(img):
    img = img.astype(np.float32)
    out = []
    for s in (1.6, 3.5):
        out.append(ndi.gaussian_filter(img, s))
        out.append(ndi.gaussian_laplace(img, s))
        out.append(ndi.gaussian_gradient_magnitude(img, s))
        out.append(ndi.gaussian_filter(img, s) - ndi.gaussian_filter(img, 0.66 * s))
        # structure tensor eigenvalues
        gy, gx = np.gradient(ndi.gaussian_filter(img, s))
        sxx, sxy, syy = (ndi.gaussian_filter(a, 0.5 * s) for a in (gx * gx, gx * gy, gy * gy))
        tr, det = sxx + syy, sxx * syy - sxy ** 2
        d = np.sqrt(np.maximum(tr ** 2 / 4 - det, 0))
        out += [tr / 2 + d, tr / 2 - d]
        # hessian eigenvalues
        hyy = ndi.gaussian_filter(img, s, order=(2, 0))
        hxx = ndi.gaussian_filter(img, s, order=(0, 2))
        hxy = ndi.gaussian_filter(img, s, order=(1, 1))
        tr, det = hxx + hyy, hxx * hyy - hxy ** 2
        d = np.sqrt(np.maximum(tr ** 2 / 4 - det, 0))
        out += [tr / 2 + d, tr / 2 - d]
    return np.stack(out, -1)


F = {t: features(raw[t, :, :, 0]) for t in FRAMES}

# ---------- existing labels: patches (frame, y0:y1, x0:x1) with values 0/1/2
patches = []
g = ilp["PixelClassification/LabelSets/labels000"]
for k in g:
    sl = g[k].attrs["blockSlice"].strip("[]").split(",")
    t0, y0, x0 = [int(sl[i].split(":")[0]) for i in (0, 1, 2)]
    patches.append((t0, y0, x0, g[k][0, :, :, 0]))
# which ilastik label is "nucleus"? compare with the saved probability channel 1
p1 = np.mean([exp[t, y0:y0 + 64, x0:x0 + 64, 1][lab == 1].mean() for t, y0, x0, lab in patches if (lab == 1).any()])
NUC = 1 if p1 > 0.5 else 2
print("label that is nucleus:", NUC, "(mean nucleus prob of label-1 pixels = %.2f)" % p1)


def patch_xy(idx):
    X, y = [], []
    for i in idx:
        t, y0, x0, lab = patches[i]
        m = lab > 0
        X.append(F[t][y0:y0 + 64, x0:x0 + 64][m])
        y.append((lab[m] == NUC).astype(int))
    return np.concatenate(X), np.concatenate(y)


# ---------- five simulated annotators
rng = np.random.default_rng(SEED)
n_p = len(patches)
anns, held_acc = [], []
for a in range(N_ANN):
    train = rng.choice(n_p, int(FRAC * n_p), replace=False)
    test = np.setdiff1d(np.arange(n_p), train)
    X, y = patch_xy(train)
    rf = RandomForestClassifier(n_estimators=100, random_state=a, n_jobs=-1).fit(X, y)
    Xt, yt = patch_xy(test)
    held_acc.append(float((rf.predict(Xt) == yt).mean()))
    anns.append(rf)
print("held-out label accuracy per annotator:", np.round(held_acc, 3))

masks = {}  # frame -> (N_ANN, H, W) bool
for t in FRAMES:
    H, W, nf = F[t].shape
    flat = F[t].reshape(-1, nf)
    masks[t] = np.stack([a.predict(flat).reshape(H, W).astype(bool) for a in anns])

# ---------- agreement statistics
def dice(a, b):
    return 2 * (a & b).sum() / max(a.sum() + b.sum(), 1)


def fleiss_kappa(m):
    n = m.shape[0]
    pos = m.sum(0).astype(float)
    neg = n - pos
    P_i = (pos ** 2 + neg ** 2 - n) / (n * (n - 1))
    P_bar = P_i.mean()
    p1 = pos.mean() / n
    P_e = p1 ** 2 + (1 - p1) ** 2
    return float((P_bar - P_e) / (1 - P_e))


# ---------- consensus rules
w = np.maximum(2 * np.array(held_acc) - 1, 1e-3)   # weighted expertise: weight = 2*acc-1
def rules(m, expert):
    votes = m.sum(0)
    unanimous = (votes == 0) | (votes == N_ANN)
    return {
        "majority": (votes >= 3, np.ones_like(unanimous)),
        "unanimity": (votes == N_ANN, np.ones_like(unanimous)),
        "weighted": ((w[:, None, None] * m).sum(0) > w.sum() / 2, np.ones_like(unanimous)),
        "expert_adjudication": (np.where(unanimous, votes == N_ANN, expert), np.ones_like(unanimous)),
        "exclude_uncertain": (votes == N_ANN, unanimous),   # (mask, pixels kept)
    }


def count_nuclei(mask, keep=None):
    if keep is not None:
        mask = mask & keep
    lab, n = ndi.label(mask)
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return int((sizes >= MIN_SIZE).sum())


# independent non-ilastik check: Otsu on a lightly smoothed, background-subtracted image
def otsu_ref(t):
    im = ndi.gaussian_filter(raw[t, :, :, 0].astype(np.float32), 1.0)
    im = im - ndi.gaussian_filter(im, 40)
    return im > threshold_otsu(im)

label_pix = {t: np.zeros(raw.shape[1:3], int) for t in FRAMES}
for t, y0, x0, lab in patches:
    if t in label_pix:
        label_pix[t][y0:y0 + 64, x0:x0 + 64] = lab

results = {"held_out_accuracy": held_acc, "weights": w.tolist(), "frames": {}}
for t in FRAMES:
    m = masks[t]
    expert = exp[t, :, :, 1] > 0.5       # the original ilastik project's own result
    R = rules(m, expert)
    otsu = otsu_ref(t)
    fr = {
        "fleiss_kappa": fleiss_kappa(m),
        "mean_pairwise_dice": float(np.mean([dice(m[i], m[j]) for i in range(N_ANN) for j in range(i + 1, N_ANN)])),
        "frac_pixels_disputed": float((~((m.sum(0) == 0) | (m.sum(0) == N_ANN))).mean()),
        "rules": {},
    }
    for name, (mk, keep) in R.items():
        d = {
            "nucleus_area_px": int((mk & keep).sum()),
            "n_nuclei": count_nuclei(mk, keep),
            "frac_excluded": float(1 - keep.mean()),
            "dice_vs_ilastik_project_export": float(dice(mk & keep, expert & keep)),
            "dice_vs_otsu": float(dice(mk & keep, otsu & keep)),
        }
        lp = label_pix[t] > 0
        if lp.any():
            d["acc_on_label_pixels"] = float((mk[lp] == (label_pix[t][lp] == NUC)).mean())
        fr["rules"][name] = d
    results["frames"][t] = fr

json.dump(results, open(f"{OUT}/results.json", "w"), indent=1)

# ---------- figure for frame 30 (no labels in that frame)
t = 30
m = masks[t]
R = rules(m, exp[t, :, :, 1] > 0.5)
crop = (slice(400, 700), slice(350, 650))
fig, ax = plt.subplots(2, 4, figsize=(16, 8))
ax = ax.ravel()
ax[0].imshow(raw[t, :, :, 0][crop], cmap="gray", vmin=np.percentile(raw[t], 1), vmax=np.percentile(raw[t], 99.8)); ax[0].set_title("raw (frame 30)")
im = ax[1].imshow(m.sum(0)[crop], cmap="viridis", vmin=0, vmax=N_ANN); ax[1].set_title("annotator votes (0-5)"); plt.colorbar(im, ax=ax[1], fraction=.046)
for i, (name, (mk, keep)) in enumerate(R.items()):
    show = np.where(keep, mk, 0.5).astype(float)
    ax[2 + i].imshow(show[crop], cmap="coolwarm", vmin=0, vmax=1); ax[2 + i].set_title(name + (" (grey = excluded)" if name == "exclude_uncertain" else ""))
ax[7].imshow((exp[t, :, :, 1] > .5)[crop], cmap="gray"); ax[7].set_title("ilastik project export")
for a_ in ax: a_.axis("off")
plt.tight_layout(); plt.savefig(f"{OUT}/consensus_frame30.png", dpi=80)
print("done")
