"""Figures for docs/session_comparison.md (run from the repo root with the ilastik 1.5 env's python).

Sources of the numbers (all hand-copied into DATA below):
  Session 0  this repository's logs, file times and README timeline (21 Oct 2026)
  Session 1  REPRO_REPORT.md on branch repro/opus-5.5-high, plus its committed result files
  Session 2  REPRO_REPORT.md on branch repro/sonnet-5.5-medium
  Session 3  its transcript (no repository), read in full
  Session 4  its transcript (no repository), read in full
Session 3 and 4 results are re-plotted from the numbers those sessions reported; they are not
re-computed here. The reproduction figure is computed from Session 1's result files in data/session1/.

usage: python figures/make_figures.py [DIR_WITH_SESSION1_FILES, e.g. data/session1]   (see the README for ILASTIK_RUN)
"""
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

import os
REPO = Path(__file__).resolve().parents[1]
START = Path.cwd()
# data/, results/ and scripts/ come from a checkout of globias-2026-group5/ilastik-mitocheck-run.
ORIGINAL = Path(os.environ.get("ILASTIK_RUN", REPO.parent / "ilastik-mitocheck-run")).resolve()
os.chdir(ORIGINAL)
sys.path.insert(0, str(ORIGINAL / "scripts"))
from overlay import contrast_limits, lineage_colours, overlay  # noqa: E402

OUT = REPO / "img"
OUT.mkdir(exist_ok=True)

# Reference palette (dataviz skill), validated in this order for adjacent use.
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
GRAY, LIGHT, INK, INK2, GRID, SURFACE = "#a8a7a2", "#e9e8e4", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

SESSIONS = ["Session 0\noriginal · Opus", "Session 1\nrepro · Opus high", "Session 2\nrepro · Sonnet med",
            "Session 3\nblind · Sonnet med", "Session 4\nblind · Opus high"]

PHASES = {  # name: colour
    "reading and planning": GRAY,
    "downloads and installs": BLUE,
    "ilastik runs and debugging": ORANGE,
    "analysis and comparison": AQUA,
    "waiting for the user": YELLOW,
    "writing the report": MAGENTA,
    "compression for git": GREEN,
}

# (phase, start, end) in minutes from each session's first message; walls: (minute, label).
TIMELINE = {
    0: dict(phases=[("reading and planning", 0, 7), ("downloads and installs", 7, 17),
                    ("waiting for the user", 17, 117), ("ilastik runs and debugging", 117, 133),
                    ("analysis and comparison", 133, 162), ("ilastik runs and debugging", 162, 171),
                    ("compression for git", 171, 191)],
            walls=[(0, "network blocked"), (7, "conda: 1.4.1 won't install"), (118, "relative path"),
                   (120, "axis order"), (123, "needs 2014 map"), (124, "size_range"),
                   (129, "1.3.2 crash")],
            first=125),
    1: dict(phases=[("reading and planning", 0, 0.8), ("downloads and installs", 0.8, 4),
                    ("ilastik runs and debugging", 4, 12), ("compression for git", 12, 32),
                    ("analysis and comparison", 32, 35.5), ("writing the report", 35.5, 41)],
            walls=[(37, "push refused")], first=8),
    2: dict(phases=[("reading and planning", 0, 1.2), ("downloads and installs", 1.2, 6),
                    ("ilastik runs and debugging", 6, 13), ("analysis and comparison", 13, 14),
                    ("writing the report", 14, 15.5)],
            walls=[(14.2, "push refused")], first=10),
    3: dict(phases=[("reading and planning", 0, 0.5), ("waiting for the user", 0.5, 3),
                    ("downloads and installs", 3.05, 4.1), ("waiting for the user", 4.1, 8.0),
                    ("analysis and comparison", 8.1, 10.6), ("writing the report", 10.6, 10.8)],
            walls=[(0.5, '"ilastik is GUI-only"'), (3.4, "packages missing")], first=None),
    4: dict(phases=[("reading and planning", 0, 0.3), ("downloads and installs", 0.3, 0.6),
                    ("analysis and comparison", 0.6, 3.2), ("ilastik runs and debugging", 3.2, 15),
                    ("analysis and comparison", 15, 18), ("ilastik runs and debugging", 18, 27),
                    ("analysis and comparison", 27, 33), ("writing the report", 33, 34.3)],
            walls=[(0.6, "packages missing"), (3.5, "read-only project"), (4.0, "label blocks rejected (axis order)"),
                   (16, "axis order: labels land in the wrong place"), (18, "own shell killed"),
                   (29, "out of memory")], first=27),
}

SCORES = {  # per session 0..4
    "minutes to the final deliverable": [191, 41, 15.5, 10.8, 34.3],
    "of which waiting for the user": [100, 0, 0, 6.4, 0],
    "walls hit": [7, 1, 1, 2, 4],  # distinct walls, as in the walls matrix
    "times the user unblocked it": [1, 0, 0, 2, 0],
    "cost (USD)": [None, 2.48, 0.61, 0.65, 2.62],
}

COVERAGE_COLS = ["downloaded\nthe data", "installed\nilastik", "ran 2014 pixel\nclassification",
                 "ran 2014\ntracking", "retrained ilastik\nclassifiers", "simulated\nannotators",
                 "compared\nconsensus rules", "checked results\npixel by pixel", "committed\noutputs"]
COVERAGE = [  # y = yes, p = partly, n = no
    "yyyynnnyy",   # 0
    "yyyynnnyy",   # 1
    "yyyynnnpp",   # 2: compared arrays but left the CSV check open; no HDF5 committed
    "ynnnnyypn",   # 3: no ilastik; Dice vs the 2014 map only
    "yynnyyynn",   # 4: ilastik 1.4.2
]
COVERAGE_NOTE = ["1.5.0a3 + 1.3.3post3", "same", "same", "scikit-learn instead", "1.4.2"]

WALL_ROWS = ["network to ilastik.org blocked", "conda: ilastik 1.4.1 won't install",
             "raw-data path relative to the .ilp", "headless opens projects read-only",
             "label axis order t,x,y vs t,y,x", "tracking needs the 2014 probability map",
             "tracking parameters one level deeper (size_range)", "1.3.2post1 crashes on current glibc",
             "git push refused (repo not attached)", "Python packages missing",
             "tool limits (timeout, memory, own shell)", 'wrong belief: "ilastik is GUI-only"']
# h = hit, s = avoided by the repo's scripts, o = avoided another way, - = not reached
WALLS = [  # columns: sessions 0..4
    "h----", "hss--", "hss-o", "----h", "hss-h", "hss--", "hss--", "hss--",
    "-hh--", "---hh", "----h", "---h-",
]


def save(fig, name):
    fig.savefig(OUT / name, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(OUT / name)


def timeline():
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.2), gridspec_kw=dict(height_ratios=[1, 3.4]))
    groups = [([0], 0, 195), ([1, 2, 3, 4], 0, 43)]
    for ax, (ids, lo, hi) in zip(axes, groups):
        for row, s in enumerate(ids):
            y = len(ids) - 1 - row
            for name, a, b in TIMELINE[s]["phases"]:
                ax.barh(y, b - a, left=a, height=0.5, color=PHASES[name], edgecolor=SURFACE, linewidth=1.5)
            for i, (m, label) in enumerate(TIMELINE[s]["walls"], start=1):
                ax.plot(m, y + 0.36, marker="v", ms=8, color=INK, zorder=3)
                ax.annotate(str(i), (m, y + 0.36), xytext=(0, 6 + 8 * ((i - 1) % 2)), textcoords="offset points",
                            ha="center", fontsize=8, color=INK)
            if TIMELINE[s]["first"] is not None:
                ax.plot(TIMELINE[s]["first"], y - 0.36, marker="*", ms=12, color=INK, zorder=3)
        ax.set_yticks(range(len(ids)))
        ax.set_yticklabels([SESSIONS[s] for s in reversed(ids)])
        ax.set_xlim(lo, hi)
        ax.set_ylim(-0.7, len(ids) - 0.1 + 0.5)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel("minutes since the session's first message")
    axes[0].set_title("Session 0 (21 Oct): 191 minutes, 100 of them waiting for network access")
    axes[1].set_title("Sessions 1–4 (23 Oct), on a 4× finer time scale")
    handles = [Patch(color=c, label=n) for n, c in PHASES.items()]
    handles += [plt.Line2D([], [], marker="v", ls="", color=INK, label="a wall, numbered as in the text"),
                plt.Line2D([], [], marker="*", ls="", ms=11, color=INK, label="first usable ilastik result")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "timeline.png")


def scorecard():
    keys = ["minutes to the final deliverable", "walls hit", "times the user unblocked it", "cost (USD)"]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True)
    y = np.arange(5)[::-1]
    for ax, key in zip(axes, keys):
        vals = SCORES[key]
        for yi, v in zip(y, vals):
            if v is None:
                ax.text(0, yi, " n/a (3-day session)", va="center", fontsize=8.5, color=INK2)
                continue
            ax.barh(yi, v, height=0.55, color=BLUE)
            label = f"{v:g}" if key != "cost (USD)" else f"${v:.2f}"
            ax.text(v, yi, f" {label}", va="center", fontsize=9, color=INK)
        if key == "minutes to the final deliverable":
            wait = SCORES["of which waiting for the user"]
            for yi, w in zip(y, wait):
                if w:
                    ax.barh(yi, w, height=0.55, color=YELLOW)
            ax.legend(handles=[Patch(color=BLUE, label="working"), Patch(color=YELLOW, label="waiting for the user")],
                      frameon=False, fontsize=8, loc="lower right")
        ax.set_title(key)
        ax.set_xlim(0, max(v for v in vals if v is not None) * 1.35)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(SESSIONS)
    fig.tight_layout()
    save(fig, "scorecard.png")


def matrix(rows, cols, cells, colours, labels, title, name, row_notes=None, figsize=(12, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    for r, line in enumerate(cells):
        for c, v in enumerate(line):
            ax.add_patch(plt.Rectangle((c + 0.04, r + 0.06), 0.92, 0.88, color=colours[v]))
            ax.text(c + 0.5, r + 0.5, labels[v], ha="center", va="center", fontsize=8.5,
                    color=SURFACE if v in "yhs" else INK)
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(rows), 0)
    ax.set_xticks(np.arange(len(cols)) + 0.5)
    ax.set_xticklabels(cols, fontsize=8.5)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(rows)) + 0.5)
    ax.set_yticklabels(rows, fontsize=9)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if row_notes:
        for r, note in enumerate(row_notes):
            ax.text(len(cols) + 0.1, r + 0.5, note, va="center", fontsize=8.5, color=INK2)
    ax.set_title(title, pad=38)
    fig.tight_layout()
    save(fig, name)


def coverage():
    matrix([s.replace("\n", " · ") for s in SESSIONS], COVERAGE_COLS, COVERAGE,
           {"y": BLUE, "p": "#a9c8ee", "n": LIGHT}, {"y": "yes", "p": "partly", "n": "no"},
           "What each session actually did", "coverage.png",
           row_notes=["ilastik: " + n for n in COVERAGE_NOTE], figsize=(13.5, 3.6))


def walls():
    cells = ["".join(WALLS[r][s] for r in range(len(WALL_ROWS))) for s in range(5)]
    cells = [list(c) for c in zip(*cells)]  # rows = walls
    matrix(WALL_ROWS, [s for s in SESSIONS], cells,
           {"h": ORANGE, "s": BLUE, "o": AQUA, "-": LIGHT},
           {"h": "hit", "s": "fixed in\nrepo scripts", "o": "avoided\nown way", "-": "—"},
           "Walls: who hit what", "walls.png", figsize=(11, 6.2))


def repro_bars():
    rows = [
        ("1.5.0a3: Session 1 rerun vs committed", 0, BLUE),
        ("1.5.0a3: Session 2 rerun vs committed", 0, BLUE),
        ("1.3.3post3: Session 2 rerun vs committed", 50, ORANGE),
        ("1.3.3post3: Session 1 rerun vs committed", 57_881, ORANGE),
        ("   … after undoing the 117↔118 renumbering", 97, ORANGE),
        ("between versions: committed (Session 0)", 161, AQUA),
        ("between versions: Session 1, renumbering undone", 69, AQUA),
        ("between versions: Session 2", 125, AQUA),
    ]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    y = np.arange(len(rows))[::-1]
    for yi, (label, v, c) in zip(y, rows):
        if v == 0:
            ax.text(1.05, yi, "0  (bit-identical)", va="center", fontsize=9, color=INK)
        else:
            ax.barh(yi, v, left=1, height=0.55, color=c)
            ax.text(v + 1, yi, f"  {v:,}", va="center", fontsize=9, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(1, 4e5)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("label pixels with a different value (of 3,605,410 labelled pixels; log scale)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Tracking labels on rerun: 1.5.0a3 repeats exactly, 1.3.3post3 does not")
    ax.legend(handles=[Patch(color=BLUE, label="same version, ilastik 1.5.0a3"),
                       Patch(color=ORANGE, label="same version, ilastik 1.3.3post3"),
                       Patch(color=AQUA, label="1.3.3post3 vs 1.5.0a3")],
              frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout()
    save(fig, "repro_pixels.png")


def moved_pixels(la, lb):
    """Pixels that changed object, ignoring renumbering.

    Each object in run A is matched to the run-B object it overlaps most. A labelled pixel counts as
    "moved" if its run-B object is not the one its run-A object was matched to (or it is labelled in only
    one run). A pure renumbering moves no pixels.
    """
    fg = (la > 0) | (lb > 0)
    keys, counts = np.unique(la[fg].astype(np.int64) * 1_000_000 + lb[fg], return_counts=True)
    best = {}
    for k, c in zip(keys, counts):
        a, b = int(k // 1_000_000), int(k % 1_000_000)
        if a and b and c > best.get(a, (0, 0))[1]:
            best[a] = (b, c)
    match = np.zeros(int(la.max()) + 1, dtype=np.int64)
    for a, (b, _) in best.items():
        match[a] = b
    return fg & (match[la] != lb)


def repro_images(s1_dir):
    """Committed 1.3.3post3 tracking (Session 0) vs Session 1's rerun.

    Extract Session 1's files first, e.g. for Tracking-Result and Object-Identities:
      git show "origin/repro/opus-5.5-high:results/ilastik-1.3.3post3/03_tracking/<file>" > DIR/<kind>.h5
    """
    from scipy import ndimage

    name = "results/ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_"
    raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
    lo, hi = contrast_limits(raw)
    gray = lambda t: np.clip((raw[t, ..., 0].T - lo) / (hi - lo), 0, 1)
    a = h5py.File(name + "Tracking-Result.h5", "r")["exported_data"]
    b = h5py.File(Path(s1_dir) / "Tracking-Result.h5", "r")["exported_data"]
    oa = h5py.File(name + "Object-Identities.h5", "r")["exported_data"]
    ob = h5py.File(Path(s1_dir) / "Object-Identities.h5", "r")["exported_data"]
    zoom = 4

    # 1. The renumbering: lineages 117 and 118, zoomed.
    t = 26
    labs = [a[t, ..., 0].T, b[t, ..., 0].T]
    ys, xs = np.nonzero(np.isin(labs[0], [117, 118]))
    cy, cx, r = int(ys.mean()), int(xs.mean()), 45
    win = (slice(cy - r, cy + r), slice(cx - r, cx + r))
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 5.2))
    for ax, lab, title in zip(axes, labs, ["Session 0 (committed)", "Session 1 (rerun)"]):
        rgb = np.repeat(gray(t)[win][..., None] * 0.85, 3, axis=2)
        for lid, colour in [(117, BLUE), (118, ORANGE)]:
            rgb[lab[win] == lid] = matplotlib.colors.to_rgb(colour)
        ax.imshow(rgb, interpolation="nearest")
        ax.set_title(title)
        ax.axis("off")
        for lid, colour in [(117, BLUE), (118, ORANGE)]:
            yy, xx = np.nonzero(lab[win] == lid)
            ax.annotate(f"lineage {lid}", (xx.mean(), yy.max()), xytext=(0, -16), textcoords="offset points",
                        ha="center", va="top", fontsize=10, color=INK,
                        bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec=colour, lw=1.5))
    fig.suptitle(f"Same two cells, numbers swapped (ilastik 1.3.3post3, frame {t}, crop x {cx - r}–{cx + r}, "
                 f"y {cy - r}–{cy + r})", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "This swap holds in every frame and accounts for 57,784 of the 57,881 differing label pixels.",
             fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "repro_renumbering.png")

    # 2. Pixels that really changed object (renumbering ignored), frame where most changed.
    moved = [int(moved_pixels(oa[k, ..., 0], ob[k, ..., 0]).sum()) for k in range(raw.shape[0])]
    print("moved object pixels per frame:", moved, "total", sum(moved))
    t = int(np.argmax(moved))
    la, lb = oa[t, ..., 0].T, ob[t, ..., 0].T
    d = moved_pixels(la, lb)
    spots, n = ndimage.label(ndimage.binary_dilation(d, iterations=3))
    sizes = ndimage.sum(d, spots, range(1, n + 1))
    cy, cx = (int(v) for v in ndimage.center_of_mass(d, spots, 1 + int(np.argmax(sizes))))
    r = 40
    y0, x0 = max(cy - r, 0), max(cx - r, 0)
    win = (slice(y0, y0 + 2 * r), slice(x0, x0 + 2 * r))
    colours = lineage_colours(int(max(la.max(), lb.max())))
    size = (2 * r * zoom, 2 * r * zoom)
    tiles = [overlay(gray(t)[win], lab[win], colours, size) for lab in (la, lb)]
    mask = np.repeat(gray(t)[win][..., None] * 0.5, 3, axis=2)
    mask[d[win]] = matplotlib.colors.to_rgb(MAGENTA)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.9))
    for ax, img, title in zip(axes, tiles + [mask], ["Session 0 (committed): object outlines",
                                                      "Session 1 (rerun): object outlines",
                                                      f"pixels that moved to another object ({int(d[win].sum())})"]):
        ax.imshow(img, interpolation="nearest")
        ax.set_title(title)
        ax.axis("off")
    fig.suptitle(f"Touching nuclei split differently on rerun: frame {t}, crop x {x0}–{x0 + 2 * r}, "
                 f"y {y0}–{y0 + 2 * r}, {zoom}×", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, f"Over the whole movie {sum(moved):,} object pixels changed object, in "
             f"{sum(1 for m in moved if m)} frames; renumbering alone is not counted. Outline colours are "
             "per object id, so they can differ between the panels.", fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "repro_merged_split.png")


def blind_results():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw=dict(width_ratios=[1.25, 1]))
    # Session 4: nuclei per frame by rule (main pool A0–A5), plus the biased pool.
    ax = axes[0]
    rules = ["union", "mean probability", "weighted vote", "majority (≥4/6)", "STAPLE", "unanimity"]
    vals = [124.3, 113.8, 111.7, 110.7, 108.8, 79.1]
    y = np.arange(len(rules))[::-1]
    ax.axvspan(77.3, 138.3, color=LIGHT, zorder=0)
    ax.text(107.8, len(rules) - 0.45, "range of the six annotators (77.3–138.3)", ha="center", fontsize=8.5,
            color=INK2)
    ax.barh(y, vals, height=0.55, color=BLUE)
    for yi, v in zip(y, vals):
        ax.text(v, yi, f" {v:g}", va="center", fontsize=9)
    ax.axvline(138.3, color=ORANGE, lw=2)
    ax.text(138.3, -0.9, " A0 = the real 2014 labels: 138.3", color=INK, fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(rules)
    ax.set_xlim(0, 175)
    ax.set_ylim(-1.2, len(rules) - 0.1)
    ax.set_xlabel("nuclei per frame (mean over frames)")
    ax.set_title("Session 4: the rule decides the count")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.text(0, -3.1, "Biased pool (3 of 5 annotators ignore dim nuclei): majority 84.0, STAPLE 83.3, real labels "
                     "138.3; the real annotator ranks worst.", transform=ax.get_yaxis_transform(), fontsize=8.5,
            color=INK2)
    # Session 3: agreement of five simulated annotators per frame.
    ax = axes[1]
    frames = [0, 10, 22, 30, 39, 40, 52]
    disputed = [1.9, 2.5, 2.9, 3.3, 3.7, 3.8, 4.8]
    ax.plot(frames, disputed, color=ORANGE, lw=2, marker="o", ms=7)
    for f, v in zip(frames, disputed):
        dx = {39: -2.2, 40: 2.2}.get(f, 0)
        ax.text(f + dx, v + 0.2, f"{v:g}%", ha="center", fontsize=8.5)
    ax.set_ylim(0, 6)
    ax.set_xlabel("frame")
    ax.set_ylabel("pixels disputed by the five annotators (%)")
    ax.set_title("Session 3: disagreement rises over the movie")
    ax.text(26, 0.5, "Fleiss' kappa 0.86–0.88, mean pairwise Dice 0.88–0.90\n(scikit-learn annotators, not ilastik)",
            ha="center", fontsize=8.5, color=INK2)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.text(0.01, -0.1, "Re-plotted from the numbers each session reported; not re-computed. "
             "Both sessions' annotators are simulated from the one real set of 2014 labels.",
             fontsize=8.5, color=INK2)
    fig.tight_layout()
    save(fig, "blind_results.png")


if __name__ == "__main__":
    timeline()
    scorecard()
    coverage()
    walls()
    repro_bars()
    blind_results()
    if len(sys.argv) > 1:
        repro_images(START / sys.argv[1])
