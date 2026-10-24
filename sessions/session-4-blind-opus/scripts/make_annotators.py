"""Create several ilastik Pixel Classification projects that differ ONLY in their brush labels.

Each project = one "annotator". A0 uses the real human labels shipped with the ilastik
mitocheck example; A1..A5 are SIMULATED annotators with explicit, documented labelling styles.
ilastik is then re-trained headless on each project (see run_ilastik.sh).

Label values follow the shipped project: 1 = background, 2 = nucleus, 0 = unlabelled.
"""
import shutil, sys
from pathlib import Path
import h5py
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, draw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/mitocheck/mitocheck_2d+t"
RAW = DATA / "mitocheck_94570_2D+t_01-53.h5"
TEMPLATE = DATA / "pixelClassification.ilp"
OUT = ROOT / "projects"
BG, FG = 1, 2


def reference_objects(frame):
    """Rough nucleus candidates, used ONLY to decide where a simulated annotator places strokes."""
    img = ndi.gaussian_filter(frame.astype(np.float32), 1.0)
    img -= np.median(img)
    t = filters.threshold_triangle(img)  # low threshold -> also keeps dim nuclei
    mask = morphology.remove_small_objects(img > t, max_size=30)
    lab = measure.label(mask)
    props = measure.regionprops(lab, intensity_image=img)
    return img, lab, props


def stroke_in(region_mask, rng, n_px=25):
    """A short brush stroke (3-px wide line) through random interior points of a region."""
    ys, xs = np.nonzero(region_mask)
    if len(ys) < 2:
        return ys, xs
    i, j = rng.choice(len(ys), 2, replace=False)
    rr, cc = draw.line(ys[i], xs[i], ys[j], xs[j])
    out = np.zeros_like(region_mask)
    out[rr, cc] = True
    out = ndi.binary_dilation(out, iterations=1) & region_mask
    return np.nonzero(out)


def annotate(frame, style, rng):
    """Return a uint8 label image for one frame according to an annotator style dict."""
    img, lab, props = reference_objects(frame)
    labels = np.zeros(frame.shape, np.uint8)
    fg_all = lab > 0
    intens = np.array([p.intensity_mean for p in props])
    dim_cut = np.percentile(intens, 33) if len(intens) else 0

    chosen = rng.permutation(len(props))[: style["n_nuclei"]]
    for k in chosen:
        p = props[k]
        obj = lab == p.label
        is_dim = p.intensity_mean < dim_cut
        if is_dim and style["dim_as_background"]:
            labels[obj] = BG  # annotator does not consider dim nuclei as nuclei
            continue
        core = ndi.binary_erosion(obj, iterations=2)
        if core.sum() < 5:
            core = obj
        labels[stroke_in(core, rng)] = FG
        # boundary convention: +k px = halo counted as nucleus, -k px = tight edge
        b = style["boundary_px"]
        if b > 0:
            ring = ndi.binary_dilation(obj, iterations=b) & ~obj
            labels[ring & rng.random(obj.shape).__lt__(0.5)] = FG
            outer = ndi.binary_dilation(obj, iterations=b + 3) & ~ndi.binary_dilation(obj, iterations=b + 1)
            labels[outer & ~fg_all & (rng.random(obj.shape) < 0.5)] = BG
        else:
            inner_ring = obj & ~ndi.binary_erosion(obj, iterations=-b) if b < 0 else np.zeros_like(obj)
            labels[inner_ring & (rng.random(obj.shape) < 0.5)] = BG
            outer = ndi.binary_dilation(obj, iterations=3) & ~ndi.binary_dilation(obj, iterations=1)
            labels[outer & ~fg_all & (rng.random(obj.shape) < 0.5)] = BG

    far_bg = ~ndi.binary_dilation(fg_all, iterations=10)
    for _ in range(style["n_bg_strokes"]):
        y, x = rng.integers(0, frame.shape[0]), rng.integers(0, frame.shape[1])
        win = np.zeros_like(far_bg)
        win[max(0, y - 40): y + 40, max(0, x - 40): x + 40] = True
        labels[stroke_in(win & far_bg, rng)] = BG
    return labels


STYLES = {
    # name: description, frames labelled, per-frame parameters
    "A1_tight": dict(desc="tight boundary, labels dim nuclei", frames=[0, 26],
                     n_nuclei=12, boundary_px=-1, dim_as_background=False, n_bg_strokes=6),
    "A2_generous": dict(desc="includes 2-px halo as nucleus", frames=[0, 26],
                        n_nuclei=12, boundary_px=2, dim_as_background=False, n_bg_strokes=6),
    "A3_bright_only": dict(desc="treats dim nuclei as background", frames=[0, 26],
                           n_nuclei=15, boundary_px=0, dim_as_background=True, n_bg_strokes=6),
    "A4_sparse": dict(desc="very few strokes, one frame", frames=[10],
                      n_nuclei=3, boundary_px=0, dim_as_background=False, n_bg_strokes=3),
    "A5_late_frames": dict(desc="standard style, labels late frames only", frames=[45, 52],
                           n_nuclei=12, boundary_px=0, dim_as_background=False, n_bg_strokes=6),
}


def read_shipped_labels(f, raw_shape):
    """Merge the 64x64 label blocks of the shipped project into full frames {t: label image}."""
    full = {}
    g = f["PixelClassification/LabelSets/labels000"]
    for k in g:
        t, y, x = [tuple(map(int, a.split(":"))) for a in g[k].attrs["blockSlice"].strip("[]").split(",")[:3]]
        lab = full.setdefault(t[0], np.zeros(raw_shape[1:], np.uint8))
        block = g[k][0, ..., 0]
        lab[y[0]:y[1], x[0]:x[1]] = np.where(block > 0, block, lab[y[0]:y[1], x[0]:x[1]])
    return full


def write_project(name, label_frames, raw_shape):
    """Copy the shipped .ilp, replace its labels, drop the trained forest, point to absolute raw path."""
    OUT.mkdir(exist_ok=True)
    dst = OUT / f"{name}.ilp"
    shutil.copy(TEMPLATE, dst)
    with h5py.File(dst, "r+") as f:
        for lane in ("Input Data", "BatchDataSelection"):
            p = f"{lane}/infos/lane0000/Raw Data/filePath"
            if p in f:
                del f[p]
                f[p] = f"{RAW}/volume/data".encode()
        if "PixelClassification/ClassifierForests" in f:
            del f["PixelClassification/ClassifierForests"]
        if label_frames is None:  # A0: the original human labels, re-written as full-frame blocks
            label_frames = read_shipped_labels(f, raw_shape)
        del f["PixelClassification/LabelSets/labels000"]
        g = f.create_group("PixelClassification/LabelSets/labels000")
        for i, (t, lab) in enumerate(sorted(label_frames.items())):
            # ilastik 1.4 interprets this HDF5 as t,x,y,c and stores labels internally as t,y,x,c,
            # so each label frame is written transposed relative to the raw array.
            ds = g.create_dataset(f"block{i:04d}", data=lab.T[None, :, :, None], compression="gzip")
            ds.attrs["blockSlice"] = f"[{t}:{t+1},0:{raw_shape[2]},0:{raw_shape[1]},0:1]"
    return dst


def main():
    with h5py.File(RAW, "r") as f:
        raw = f["volume/data"][..., 0]
    write_project("A0_ilastik_human", None, raw.shape)
    for i, (name, st) in enumerate(STYLES.items(), start=1):
        rng = np.random.default_rng(i)
        lf = {t: annotate(raw[t], st, rng) for t in st["frames"]}
        n_fg = sum((l == FG).sum() for l in lf.values())
        n_bg = sum((l == BG).sum() for l in lf.values())
        write_project(name, lf, raw.shape)
        print(f"{name:16s} {st['desc']:42s} frames={st['frames']} fg_px={n_fg} bg_px={n_bg}")


if __name__ == "__main__":
    sys.exit(main())
