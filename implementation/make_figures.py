#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the Chapter 3 and Chapter 4 figures from derived results.

WHY A SCRIPT AND NOT HAND-DRAWN FIGURES
---------------------------------------
Every number plotted here is read from a file under data/reports or
data/derived at run time. Nothing is typed in. That matters for two reasons:

  1. E4 is being re-run after the ACSSL initialisation fix, so any figure with
     a hand-copied E4 number would silently go stale. Regenerating is one
     command.
  2. A reader who wants to check a figure can run this and diff the output.

The script writes a provenance record beside the figures: git commit, library
versions, and the sha256 of every input file it read. A figure whose provenance
does not match the committed results is detectable rather than merely doubted.

WHAT IS DELIBERATELY NOT PLOTTED
--------------------------------
No figure here shows a predicted lesion location. The system does not predict
coordinates; measured separately, deriving them automatically costs 22.9% of
QWK. The ROI overlays in Chapter 3 draw the RSNA *annotation*, and their
captions must say so, because an overlay circle is very easily misread as a
detection.
"""
import os
import sys
import csv
import json
import glob
import hashlib
import subprocess
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPORTS = os.path.join(ROOT, "data", "reports")
OUTDIR = os.path.join(REPORTS, "figures")

LADDER = ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"]

# Rungs whose attribution value cannot be compared with the rest. E7 replaces
# the three-way class head with a CORN ordinal head emitting two cumulative
# logits, so "gradient of the predicted class logit" is not the same quantity
# it is at E0-E6.
INCOMPARABLE_ATTRIBUTION = {"E7"}

# Short labels for what each rung ADDS relative to the one before it. Kept here
# rather than in the plotting code so the ladder's meaning lives in one place.
RUNG_ADDS = {
    "E0": "single-sequence\nbaseline",
    "E1": "multi-sequence",
    "E2": "routing (C-II)",
    "E3": "modality dropout",
    "E4": "ACSSL (C-I)",
    "E5": "graph (generic)",
    "E6": "typed edges (C-III)",
    "E7": "ordinal + cost",
}

_READ = {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def track(path):
    """Record every input file so the figures can be tied to their source."""
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    if rel not in _READ:
        _READ[rel] = sha256(path)[:16]
    return path


def read_csv(path):
    with open(track(path), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(path):
    with open(track(path), encoding="utf-8") as fh:
        return json.load(fh)


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if v != v else v


def mean(v):
    return sum(v) / float(len(v)) if v else None


def sd(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / float(len(v) - 1)) ** 0.5


def style():
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def save(fig, name):
    os.makedirs(OUTDIR, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUTDIR, name + "." + ext))
    plt.close(fig)
    print("  wrote {}.pdf / .png".format(name))


# --------------------------------------------------------------------------- #
#  Figure 1 -- the ladder, per seed
# --------------------------------------------------------------------------- #
def fig_ladder():
    """QWK at each rung, mean over seeds with between-seed spread.

    The point of this figure is the part that is easy to bury in a table: for
    most of the ladder the system sits at or below the single-sequence
    baseline, and the gain arrives at the end. Plotting the individual seeds
    rather than only the mean shows why the per-rung deltas are not
    distinguishable from seed noise.
    """
    rows = read_csv(os.path.join(REPORTS, "chapter4_results.csv"))
    by = defaultdict(list)
    for r in rows:
        q = fnum(r.get("qwk"))
        if r.get("tag") in LADDER and q is not None:
            by[r["tag"]].append((int(r["seed"]), q))
    stages = [s for s in LADDER if s in by]
    if not stages:
        print("  [skip] ladder: no rows")
        return
    for s in stages:
        by[s].sort()

    seeds = sorted({sd_ for s in stages for sd_, _ in by[s]})
    base = mean([q for _, q in by["E0"]]) if "E0" in by else None

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = list(range(len(stages)))

    # individual seed traces, so the reader sees the spread not just the mean
    for sd_ in seeds:
        ys = []
        for s in stages:
            m = dict(by[s]).get(sd_)
            ys.append(m)
        if all(y is not None for y in ys):
            ax.plot(x, ys, color="0.75", lw=0.7, zorder=1)

    mu = [mean([q for _, q in by[s]]) for s in stages]
    er = [sd([q for _, q in by[s]]) for s in stages]
    ax.errorbar(x, mu, yerr=er, color="black", lw=1.6, marker="o", ms=4.5,
                capsize=3, zorder=3, label="mean $\\pm$ SD over seeds")

    if base is not None:
        ax.axhline(base, color="black", ls=":", lw=1.0, zorder=2,
                   label="E0 baseline")

    # Rotated, because the rung descriptions are long enough to collide when
    # set horizontally and an unreadable axis is worse than a tilted one.
    ax.set_xticks(x)
    ax.set_xticklabels([s + ": " + RUNG_ADDS.get(s, "").replace("\n", " ")
                        for s in stages],
                       fontsize=7.5, rotation=30, ha="right")
    ax.set_ylabel("Quadratic weighted $\\kappa$ (test)")
    ax.set_xlabel("Ablation rung (each adds one component to the rung at its left)")
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="y", color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "fig_ladder_qwk")

    n = len(seeds)
    below = sum(1 for s, m in zip(stages, mu)
                if base is not None and m <= base and s != "E0")
    print("    {} seeds, {} rungs, {} rungs at or below E0".format(
        n, len(stages), below))


# --------------------------------------------------------------------------- #
#  Figure 2 -- forest plot of the pre-specified comparisons
# --------------------------------------------------------------------------- #
def fig_forest():
    """Every pre-specified comparison with its interval and FDR outcome.

    A negative-results thesis lives or dies on whether its nulls are legible.
    A forest plot shows at a glance which intervals exclude zero, how wide the
    others are, and therefore what the study can and cannot rule out.
    """
    path = os.path.join(REPORTS, "chapter4_effect_sizes.csv")
    rows = read_csv(path)
    keep = []
    for r in rows:
        d, lo, hi = fnum(r.get("delta")), fnum(r.get("lo")), fnum(r.get("hi"))
        if None in (d, lo, hi):
            continue
        keep.append({
            "label": (r.get("name") or r.get("comparison") or "?").strip(),
            "rq": (r.get("rq") or "").strip(),
            "d": d, "lo": lo, "hi": hi,
            "wins": (r.get("wins") or "").strip(),
            "sig": str(r.get("significant", "")).strip().lower() == "true",
        })
    if not keep:
        print("  [skip] forest: no rows")
        return
    keep.reverse()   # first row of the CSV at the top of the plot

    fig, ax = plt.subplots(figsize=(7.0, 0.42 * len(keep) + 1.3))
    ys = list(range(len(keep)))
    for y, k in zip(ys, keep):
        ax.plot([k["lo"], k["hi"]], [y, y], color="black", lw=1.2, zorder=2)
        ax.plot([k["lo"], k["lo"]], [y - .12, y + .12], color="black", lw=1.2)
        ax.plot([k["hi"], k["hi"]], [y - .12, y + .12], color="black", lw=1.2)
        ax.plot([k["d"]], [y], marker="o", ms=6, zorder=3, color="black",
                mfc="black" if k["sig"] else "white")

    ax.axvline(0.0, color="black", ls=":", lw=1.0, zorder=1)
    ax.set_yticks(ys)
    lab = []
    for k in keep:
        t = k["label"]
        if k["rq"] and k["rq"] not in ("--", "-"):
            t += "  ({})".format(k["rq"])
        if k["wins"]:
            t += "  {}".format(k["wins"])
        lab.append(t)
    ax.set_yticklabels(lab, fontsize=7.5)
    # NB: matplotlib is not LaTeX here -- an escaped percent renders literally.
    ax.set_xlabel("Difference in quadratic weighted $\\kappa$ "
                  "(paired across-seed bootstrap, 95% CI)")
    ax.set_ylim(-0.7, len(keep) - 0.3)
    ax.grid(axis="x", color="0.9", lw=0.6)
    ax.set_axisbelow(True)

    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], marker="o", color="black", mfc="black", ls="none",
               ms=6, label="survives FDR at 0.05"),
        Line2D([], [], marker="o", color="black", mfc="white", ls="none",
               ms=6, label="does not"),
    ], loc="lower right", frameon=False)
    save(fig, "fig_forest_comparisons")
    print("    {} comparisons, {} survive FDR".format(
        len(keep), sum(1 for k in keep if k["sig"])))


# --------------------------------------------------------------------------- #
#  Figure 3 -- attribution concentration against its untrained floor
# --------------------------------------------------------------------------- #
def fig_attribution():
    """Share of Grad-CAM mass inside the annotated-target disc, by rung.

    Reported as a ratio to the disc's own area share, so 1.0 is what a uniform
    map scores. The architecture-matched untrained floor is the control: it
    shows how much of any concentration is the architecture rather than
    learning.
    """
    # The floor is ARCHITECTURE-MATCHED, so it is a different number at each
    # rung: an untrained E7 with its graph and ordinal head does not score what
    # an untrained E0 scores (1.04x at E0-E4, 0.90x at E5-E6, 0.71x at E7).
    # Averaging them into one flat line, as an earlier version of this figure
    # did, simultaneously understates the floor early in the ladder and
    # overstates it at the end -- which is exactly where the interesting
    # comparison is. Each rung is now plotted against its own control.
    pts, floor = [], []
    for stage in LADDER:
        p = os.path.join(REPORTS, "attribution_{}_layer3.json".format(stage))
        if not os.path.exists(p):
            continue
        d = read_json(p)
        area = fnum(d.get("disc_area"))
        if not area:
            continue
        res = d.get("results", {})
        v = [fnum(e.get("mean")) for e in res.get(stage, [])]
        v = [x / area for x in v if x is not None]
        f = [fnum(e.get("mean")) for e in res.get("RANDOM_INIT", [])]
        f = [x / area for x in f if x is not None]
        if v:
            pts.append((stage, mean(v), sd(v), len(v)))
            floor.append(mean(f) if f else None)

    if not pts:
        print("  [skip] attribution: no rows")
        return

    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    x = list(range(len(pts)))
    ax.errorbar(x, [p[1] for p in pts], yerr=[p[2] for p in pts],
                color="black", lw=1.5, ls="-", marker="", capsize=3, zorder=3)
    # E7 is drawn hollow because its value is NOT on the same footing as the
    # others. Grad-CAM is taken with respect to the predicted class logit, and
    # the CORN head emits two cumulative-threshold logits rather than three
    # class logits, so the quantity differentiated is not the same one. Its
    # apparent collapse to chance is an artefact of that change, not evidence
    # that the best model stops attending to the target. Plotting it
    # unmarked would invite exactly that misreading.
    for xi, p in zip(x, pts):
        hollow = p[0] in INCOMPARABLE_ATTRIBUTION
        ax.plot([xi], [p[1]], marker="o", ms=5.5, color="black",
                mfc="white" if hollow else "black", zorder=4)
    ax.axhline(1.0, color="black", ls=":", lw=1.0,
               label="chance (uniform attribution)")
    if any(f is not None for f in floor):
        fx = [xi for xi, f in zip(x, floor) if f is not None]
        fy = [f for f in floor if f is not None]
        ax.plot(fx, fy, color="0.45", ls="--", lw=1.2, marker="s", ms=3.5,
                label="untrained floor (matched to each rung)")
        ax.fill_between(fx, [0.0] * len(fy), fy, color="0.90", zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels([p[0] for p in pts])
    ax.set_xlim(-0.4, len(pts) - 0.6)
    ax.set_ylabel("Attribution concentration\n(x chance) on annotated target")
    ax.set_xlabel("Ablation rung")
    from matplotlib.lines import Line2D
    h, lab = ax.get_legend_handles_labels()
    h = [Line2D([], [], color="black", lw=1.5, marker="o", ms=5.5,
                label="trained model")] + h
    if any(p[0] in INCOMPARABLE_ATTRIBUTION for p in pts):
        h.append(Line2D([], [], color="black", ls="none", marker="o", ms=5.5,
                        mfc="white", label="ordinal head: not comparable"))
    ax.legend(handles=h, loc="best", frameon=False)
    ax.grid(axis="y", color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "fig_attribution_concentration")
    for (st_, m_, _s, _n), f_ in zip(pts, floor):
        print("    {}  trained {:.2f}x   floor {}".format(
            st_, m_, "n/a" if f_ is None else "{:.2f}x".format(f_)))


# --------------------------------------------------------------------------- #
#  Table -- geometry correspondence (Chapter 3)
# --------------------------------------------------------------------------- #
def table_practical_significance():
    """Translate the surviving kappa differences into targets and patients.

    A quadratic weighted kappa difference of +0.0093 is statistically
    detectable here and means almost nothing clinically, and a thesis that
    reports only the kappa leaves a reader to discover that for themselves. This
    table counts, on the actual test predictions, how many graded targets change
    and how many of those changes are improvements rather than churn.

    The churn column is the point. A rung can rewrite eight hundred predictions
    and be right about twelve more of them than the rung below it.
    """
    import numpy as np

    seeds = [42, 43, 44, 45, 46, 47, 48]

    def preds(tag, seed):
        p = os.path.join(REPORTS,
                         "{}_real_seed{}_predictions.npz".format(tag, seed))
        if not os.path.exists(p):
            return None
        d = np.load(track(p))
        return d["y_true"], d["y_pred"], d["patient_id"]

    pairs = [("E5", "E6", "Typed heterogeneous edges"),
             ("E6", "E7", "Ordinal and cost-sensitive head"),
             ("E0", "E7", "Complete system vs baseline")]
    rows = []
    n_targets = n_patients = 0
    for a, b, label in pairs:
        ch, fix, brk = [], [], []
        for s in seeds:
            pa, pb = preds(a, s), preds(b, s)
            if pa is None or pb is None:
                continue
            ya, qa, _ = pa
            yb, qb, pid = pb
            if not (ya == yb).all():
                print("  [skip] {} vs {}: reference labels differ".format(a, b))
                return
            ch.append(int((qa != qb).sum()))
            fix.append(int(((qa != ya) & (qb == ya)).sum()))
            brk.append(int(((qa == ya) & (qb != ya)).sum()))
            n_targets = len(ya)
            n_patients = len(set(pid.tolist()))
        if ch:
            rows.append((label, mean(ch), mean(fix), mean(brk),
                         mean(fix) - mean(brk)))
    if not rows:
        print("  [skip] practical significance: no prediction files")
        return

    out = os.path.join(OUTDIR, "table_practical_significance.tex")
    L = ["% GENERATED by implementation/make_figures.py -- do not hand-edit.",
         "\\begin{tabular}{lrrrr}", "\\toprule",
         "Comparison & Changed & Fixed & Broken & Net \\\\",
         "\\midrule"]
    for label, c, f, b, net in rows:
        L.append("{} & {:,.0f} & {:,.0f} & {:,.0f} & "
                 "\\textbf{{{:+,.0f}}} \\\\".format(label, c, f, b, net))
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("  wrote table_practical_significance.tex")
    for label, c, f, b, net in rows:
        print("    {:<34} {:>5.0f} changed of {} -> net {:+.0f} "
              "(1 per {:.0f} patients)".format(
                  label, c, n_targets, net,
                  n_patients / abs(net) if net else float("inf")))


def table_geometry():
    """Out-of-plane distance between the annotated point and the chosen slice.

    This is the evidence that the DICOM correspondence underpinning ACSSL is
    real. Emitted as a .tex fragment so the numbers in the thesis cannot drift
    from the numbers in the CSV.
    """
    qc = os.path.join(REPORTS, "roi_qc")
    parts = [("Development", "geometry_crosscheck_dev.csv"),
             ("Test", "geometry_crosscheck_test.csv")]
    rows = []
    for name, fn in parts:
        p = os.path.join(qc, fn)
        if not os.path.exists(p):
            continue
        v = sorted(x for x in (fnum(r.get("out_of_plane_mm"))
                               for r in read_csv(p)) if x is not None)
        if not v:
            continue
        med = v[len(v) // 2]
        p90 = v[max(0, int(0.9 * len(v)) - 1)]
        ok = sum(1 for x in v if x <= 10.0)
        rows.append((name, len(v), med, p90, v[-1], 100.0 * ok / len(v)))
    if not rows:
        print("  [skip] geometry table: no data")
        return

    out = os.path.join(OUTDIR, "table_geometry_correspondence.tex")
    L = []
    L.append("% GENERATED by implementation/make_figures.py -- do not hand-edit.")
    L.append("\\begin{tabular}{lrrrrr}")
    L.append("\\toprule")
    L.append("Partition & $n$ & Median & p90 & Max & Within \\\\")
    L.append(" & & (mm) & (mm) & (mm) & 10\\,mm \\\\")
    L.append("\\midrule")
    for name, n, med, p90, mx, pct in rows:
        L.append("{} & {:,} & {:.2f} & {:.2f} & {:.1f} & {:.1f}\\% \\\\".format(
            name, n, med, p90, mx, pct))
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("  wrote table_geometry_correspondence.tex")
    for r in rows:
        print("    {:<12} n={:<6} median {:.2f} mm  within 10mm {:.1f}%".format(
            r[0], r[1], r[2], r[5]))


def provenance():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT).decode().strip())
    except Exception:
        commit, dirty = None, None
    import numpy
    rec = {
        "generated_by": "implementation/make_figures.py",
        "git_commit": commit,
        "git_dirty": dirty,
        "python": sys.version.split()[0],
        "libraries": {"matplotlib": matplotlib.__version__,
                      "numpy": numpy.__version__},
        "inputs_sha256_16": _READ,
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "provenance.json"), "w",
              encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    print("  wrote provenance.json ({} inputs tracked)".format(len(_READ)))


def main():
    style()
    print("Chapter 4 figures")
    fig_ladder()
    fig_forest()
    fig_attribution()
    print("Chapter 4 table")
    table_practical_significance()
    print("Chapter 3 table")
    table_geometry()
    provenance()
    print("\nfigures -> {}".format(os.path.relpath(OUTDIR, ROOT)))


if __name__ == "__main__":
    main()
