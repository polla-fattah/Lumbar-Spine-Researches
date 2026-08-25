#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run the whole E0-E7 ladder, then produce the Chapter 4 tables.

This is the campaign driver: it executes every rung and every control in order,
survives interruption, and at the end runs the statistical comparisons Chapter 3
pre-specifies rather than leaving a pile of point estimates.

    --profile smoke   synthetic, minutes            proves the campaign runs
    --profile quick   1 seed, 20 epochs, resnet18   overnight, real data
    --profile full    3 seeds, 50 epochs            the Chapter 4 campaign

RESUMABLE
    A run whose test JSON already exists is skipped. Kill it and restart and it
    picks up where it stopped, which matters for a multi-day campaign on a laptop.

WHAT IT PRODUCES
    data/reports/chapter4_results.csv        one row per run
    data/reports/chapter4_comparisons.csv    paired differences, CIs, FDR
    data/reports/chapter4_tables.md          ready to paste into Chapter 4
    data/reports/ladder_run_log.txt

THE COMPARISON THAT MATTERS MOST
    E6 vs E6_shuffled. If the anatomical graph does not separate from a graph
    with permuted edges and identical capacity, the honest conclusion is that
    extra message passing helped and anatomy did not. Chapter 3 commits to
    reporting that either way, and this driver reports it either way.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import PROJECT_ROOT, compute_metrics  # noqa: E402
from amog_stats import (  # noqa: E402
    patient_bootstrap_ci, paired_bootstrap_diff, benjamini_hochberg, aggregate_seeds,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
TRAINER = os.path.join(HERE, "amog_train.py")

# (stage, extra flags, tag)
RUNS = [
    ("E0", [], "E0"),
    ("E1", [], "E1"),
    ("E2", [], "E2"),
    ("E3", [], "E3"),
    ("E4", [], "E4"),
    ("E5", [], "E5"),
    ("E6", [], "E6"),
    ("E6", ["--shuffled"], "E6_shuffled"),
    ("E6", ["--ungated"], "E6_ungated"),
    ("E7", ["--cost_weight", "0.5"], "E7"),
]

# Chapter 3 declares a limited set of primary comparisons; everything else is
# exploratory. (A, B, what it tests)
PRIMARY = [
    ("E6", "E6_shuffled", "anatomical topology vs arbitrary topology (CC III)"),
    ("E6", "E5", "typed heterogeneous vs homogeneous graph"),
    ("E6", "E6_ungated", "gated residual vs ungated"),
    ("E5", "E0", "relational message passing vs independent heads"),
    ("E2", "E1", "disease-conditioned routing vs fixed fusion (CC II)"),
    ("E3", "E2", "modality dropout"),
    ("E4", "E3", "anatomical cross-sequence SSL (CC I)"),
    ("E7", "E6", "ordinal + clinical cost"),
]

PROFILES = {
    "smoke": dict(mode="smoke", epochs=1, seeds=[42], backbone=None, extra=[]),
    "quick": dict(mode="real", epochs=20, seeds=[42], backbone="resnet18", extra=[]),
    "full": dict(mode="real", epochs=50, seeds=[42, 43, 44], backbone="resnet18", extra=[]),
}


def out_paths(tag, mode, seed):
    root = os.path.join(PROJECT_ROOT, "data", "smoke" if mode == "smoke" else "")
    derived = os.path.join(root, "derived") if mode == "smoke" else \
        os.path.join(PROJECT_ROOT, "data", "derived")
    reports = os.path.join(root, "reports") if mode == "smoke" else \
        os.path.join(PROJECT_ROOT, "data", "reports")
    return (os.path.join(derived, "{}_{}_seed{}_test.json".format(tag, mode, seed)),
            os.path.join(reports, "{}_{}_seed{}_predictions.npz".format(tag, mode, seed)))


def run_one(stage, flags, tag, prof, seed, log, force=False):
    js, npz = out_paths(tag, prof["mode"], seed)
    if os.path.exists(js) and os.path.exists(npz) and not force:
        print("  [skip] {} seed {} already complete".format(tag, seed))
        return True, 0.0

    cmd = [sys.executable, TRAINER, "--stage", stage, "--mode", prof["mode"],
           "--epochs", str(prof["epochs"]), "--seed", str(seed)] + flags + prof["extra"]
    if prof["backbone"]:
        cmd += ["--backbone", prof["backbone"]]

    print("  [run ] {} seed {}  ...".format(tag, seed), flush=True)
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as lf:
        lf.write("\n{}\n$ {}\n".format("=" * 70, " ".join(cmd)))
        lf.flush()
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    ok = p.returncode == 0 and os.path.exists(js)
    print("  [{}] {} seed {}  ({:.1f} min)".format(
        " ok " if ok else "FAIL", tag, seed, dt / 60.0))
    return ok, dt


def collect(prof):
    rows = []
    for stage, flags, tag in RUNS:
        for seed in prof["seeds"]:
            js, npz = out_paths(tag, prof["mode"], seed)
            if not os.path.exists(js):
                continue
            with open(js, "r", encoding="utf-8") as fh:
                m = json.load(fh)
            rows.append(dict(
                tag=tag, stage=stage, seed=seed,
                accuracy=m.get("accuracy"), macro_f1=m.get("macro_f1"),
                qwk=m.get("qwk"), ece=m.get("ece"), brier=m.get("brier"),
                severe_recall=m.get("severe_recall"),
                severe_to_normal=m.get("severe_to_normal_rate"),
                d0=(m.get("grade_distance") or {}).get("d0"),
                d2plus=(m.get("grade_distance") or {}).get("d2_or_more"),
                gate_entropy=m.get("gate_entropy"),
                n_parameters=m.get("n_parameters"), loss=m.get("loss"),
                predictions=npz if os.path.exists(npz) else None))
    return pd.DataFrame(rows)


def load_preds(path):
    d = np.load(path)
    return d["patient_id"], d["y_true"], d["y_pred"], d["y_prob"]


def compare(prof, df, n_boot):
    """Paired bootstrap on the primary comparisons, then FDR."""
    f1 = lambda t, p: compute_metrics(t, p)["macro_f1"]
    qwk = lambda t, p: compute_metrics(t, p)["qwk"]
    out = []

    for a_tag, b_tag, what in PRIMARY:
        for seed in prof["seeds"]:
            _, npz_a = out_paths(a_tag, prof["mode"], seed)
            _, npz_b = out_paths(b_tag, prof["mode"], seed)
            if not (os.path.exists(npz_a) and os.path.exists(npz_b)):
                continue
            pa, ya, ypa, _ = load_preds(npz_a)
            pb, yb, ypb, _ = load_preds(npz_b)
            if len(ya) != len(yb) or not np.array_equal(ya, yb):
                out.append(dict(comparison="{} vs {}".format(a_tag, b_tag),
                                tests=what, seed=seed, metric="-",
                                diff=np.nan, lo=np.nan, hi=np.nan, p_value=np.nan,
                                note="test sets differ; not directly pairable"))
                continue
            for name, fn in (("macro_f1", f1), ("qwk", qwk)):
                d = paired_bootstrap_diff(pa, ya, ypa, ypb, fn, n_boot=n_boot)
                out.append(dict(comparison="{} vs {}".format(a_tag, b_tag),
                                tests=what, seed=seed, metric=name,
                                diff=d["diff"], lo=d["lo"], hi=d["hi"],
                                p_value=d["p_value"], note=""))

    cdf = pd.DataFrame(out)
    if len(cdf):
        valid = cdf.p_value.notna()
        if valid.any():
            rej, adj = benjamini_hochberg(cdf.loc[valid, "p_value"].to_numpy())
            cdf.loc[valid, "p_adjusted"] = adj
            cdf.loc[valid, "significant_fdr05"] = rej
    return cdf


def write_tables(prof, df, cdf, path):
    L = []
    L.append("# Chapter 4 — Results (auto-generated)\n")
    L.append("Generated {} · profile `{}` · mode `{}` · {} epochs · seeds {}\n".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), prof["_name"], prof["mode"],
        prof["epochs"], prof["seeds"]))
    if prof["mode"] == "smoke":
        L.append("\n> **SMOKE PROFILE — synthetic data. These are not results.**\n")

    L.append("\n## Table 4.1 — Ablation ladder, held-out test set\n")
    L.append("| Run | Acc | Macro-F1 | QWK | ECE | Severe recall | Severe→Normal | d≥2 | Params |")
    L.append("| :-- | --: | --: | --: | --: | --: | --: | --: | --: |")
    for _, r in df.iterrows():
        fmt = lambda v, n=3: "—" if v is None or (isinstance(v, float) and np.isnan(v)) \
            else "{:.{}f}".format(v, n)
        L.append("| {} (s{}) | {} | {} | {} | {} | {} | {} | {} | {:.2f}M |".format(
            r.tag, r.seed, fmt(r.accuracy), fmt(r.macro_f1), fmt(r.qwk), fmt(r.ece),
            fmt(r.severe_recall), fmt(r.severe_to_normal), fmt(r.d2plus),
            (r.n_parameters or 0) / 1e6))

    if len(prof["seeds"]) > 1:
        L.append("\n## Table 4.2 — Across seeds (mean ± sd)\n")
        L.append("| Run | Macro-F1 | QWK |")
        L.append("| :-- | --: | --: |")
        for tag, g in df.groupby("tag", sort=False):
            a = aggregate_seeds(g.macro_f1.tolist())
            b = aggregate_seeds(g.qwk.tolist())
            L.append("| {} | {:.3f} ± {:.3f} | {:.3f} ± {:.3f} |".format(
                tag, a["mean"], a["sd"], b["mean"], b["sd"]))

    L.append("\n## Table 4.3 — Pre-specified primary comparisons\n")
    L.append("Paired patient-level bootstrap. FDR controlled across all rows.\n")
    L.append("| Comparison | Tests | Metric | Δ | 95% CI | p | p(FDR) | Sig |")
    L.append("| :-- | :-- | :-- | --: | :-- | --: | --: | :-: |")
    if len(cdf):
        for _, r in cdf.iterrows():
            if r.get("note"):
                L.append("| {} | {} | — | — | — | — | — | {} |".format(
                    r.comparison, r.tests, r["note"]))
                continue
            sig = "yes" if r.get("significant_fdr05") else "no"
            L.append("| {} | {} | {} | {:+.4f} | [{:+.4f}, {:+.4f}] | {:.4f} | {:.4f} | {} |"
                     .format(r.comparison, r.tests, r.metric, r["diff"], r.lo, r.hi,
                             r.p_value, r.get("p_adjusted", np.nan), sig))
    else:
        L.append("| — | no comparable runs yet | | | | | | |")

    L.append("\n## Reading Table 4.3\n")
    L.append("The decisive row is **E6 vs E6_shuffled**. E6_shuffled has the same 25 "
             "nodes and the same 160 edges, with endpoints permuted. If the two do not "
             "separate, the finding is that additional message-passing capacity helped "
             "and anatomical topology did not — which answers RQ1 and belongs in the "
             "thesis exactly as stated.\n")
    L.append("A negative or null result on any row is an answer, not a failure. "
             "Chapter 3 commits to reporting each comparison whichever way it falls.\n")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="Run the E0-E7 ladder and build Chapter 4")
    ap.add_argument("--profile", choices=list(PROFILES), default="quick")
    ap.add_argument("--only", type=str, default=None,
                    help="comma-separated tags to run, e.g. E6,E6_shuffled")
    ap.add_argument("--force", action="store_true", help="re-run completed runs")
    ap.add_argument("--analyse_only", action="store_true",
                    help="skip training, just rebuild the tables from existing runs")
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()

    prof = dict(PROFILES[args.profile])
    prof["_name"] = args.profile
    reports = os.path.join(PROJECT_ROOT, "data",
                           "smoke" if prof["mode"] == "smoke" else "", "reports")
    reports = reports.replace(os.sep + os.sep, os.sep)
    os.makedirs(reports, exist_ok=True)
    log = os.path.join(reports, "ladder_run_log.txt")

    runs = RUNS
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        runs = [r for r in RUNS if r[2] in want]

    print("=" * 74)
    print("  AMOG-Net Ablation Ladder")
    print("=" * 74)
    print("  profile {}   mode {}   epochs {}   seeds {}".format(
        args.profile, prof["mode"], prof["epochs"], prof["seeds"]))
    print("  {} runs x {} seeds = {} total".format(
        len(runs), len(prof["seeds"]), len(runs) * len(prof["seeds"])))
    print()

    if not args.analyse_only:
        t0 = time.time()
        done = failed = 0
        for stage, flags, tag in runs:
            for seed in prof["seeds"]:
                ok, _ = run_one(stage, flags, tag, prof, seed, log, args.force)
                done += int(ok)
                failed += int(not ok)
        print("\n  {} succeeded, {} failed, {:.1f} min total".format(
            done, failed, (time.time() - t0) / 60.0))

    print("\nCollecting results...")
    df = collect(prof)
    if df.empty:
        print("  no completed runs found.")
        return 1
    print("  {} runs".format(len(df)))

    print("Running pre-specified comparisons ({} bootstrap resamples)...".format(args.n_boot))
    cdf = compare(prof, df, args.n_boot)

    res_csv = os.path.join(reports, "chapter4_results.csv")
    cmp_csv = os.path.join(reports, "chapter4_comparisons.csv")
    md = os.path.join(reports, "chapter4_tables.md")
    df.drop(columns=["predictions"]).to_csv(res_csv, index=False)
    cdf.to_csv(cmp_csv, index=False)
    write_tables(prof, df, cdf, md)

    print("\n" + "-" * 74)
    for p in (res_csv, cmp_csv, md):
        print("  {}".format(os.path.relpath(p, PROJECT_ROOT)))
    print("-" * 74)

    key = cdf[cdf.comparison == "E6 vs E6_shuffled"] if len(cdf) else pd.DataFrame()
    if len(key):
        print("\n  Decisive comparison, E6 vs shuffled-edge control:")
        for _, r in key.iterrows():
            if r.get("note"):
                continue
            print("    {:<9} delta {:+.4f}  CI [{:+.4f}, {:+.4f}]  p {:.4f}".format(
                r.metric, r["diff"], r.lo, r.hi, r.p_value))
    return 0


if __name__ == "__main__":
    sys.exit(main())
