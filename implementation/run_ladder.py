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
    patient_bootstrap_ci, paired_bootstrap_diff, paired_bootstrap_diff_seeds,
    benjamini_hochberg, aggregate_seeds,
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
    ("E7", "E0", "full system vs single-sequence baseline"),
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
        # Existence is not enough. A result written under different epochs, a
        # different backbone, or before augmentation existed is not the run this
        # campaign is asking for, and reusing it would confound every comparison
        # against it with whatever else changed.
        stale = None
        try:
            with open(js, "r", encoding="utf-8") as fh:
                got = (json.load(fh).get("run_config") or {})
            want = {"stage": stage, "epochs": prof["epochs"], "mode": prof["mode"],
                    "shuffled": "--shuffled" in flags,
                    "ungated": "--ungated" in flags}
            if prof.get("backbone"):
                want["backbone"] = prof["backbone"]
            if not got:
                stale = "no run_config recorded (predates fingerprinting)"
            else:
                diff = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
                if diff:
                    stale = ", ".join("{} {}->{}".format(k, a, b)
                                      for k, (a, b) in diff.items())
        except Exception as e:
            stale = "unreadable ({})".format(e)

        if stale is None:
            print("  [skip] {} seed {} already complete".format(tag, seed))
            return True, 0.0
        print("  [stale] {} seed {} will be re-run: {}".format(tag, seed, stale))

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
    """Primary comparisons: one pooled test per comparison x metric, then FDR.

    A row with seed="pooled" is the inferential row -- the difference averaged
    over training seeds, with the patient resample shared across seeds (see
    amog_stats.paired_bootstrap_diff_seeds for why the per-seed interval is not
    the right one to test). The per-seed rows are retained for transparency but
    are NOT part of the FDR family: they are three views of one comparison, not
    three independent tests, and on this campaign they disagree in sign.
    """
    f1 = lambda t, p: compute_metrics(t, p)["macro_f1"]
    qwk = lambda t, p: compute_metrics(t, p)["qwk"]
    out = []

    for a_tag, b_tag, what in PRIMARY:
        pool_a, pool_b, pool_pat, pool_y = [], [], None, None
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
            # pooling requires every seed to sit on the same frozen test rows
            if pool_y is None:
                pool_pat, pool_y = pa, ya
            elif not (np.array_equal(pool_y, ya) and np.array_equal(pool_pat, pa)):
                out.append(dict(comparison="{} vs {}".format(a_tag, b_tag),
                                tests=what, seed=seed, metric="-",
                                diff=np.nan, lo=np.nan, hi=np.nan, p_value=np.nan,
                                note="test rows differ across seeds; not pooled"))
                continue
            pool_a.append(ypa)
            pool_b.append(ypb)
            for name, fn in (("macro_f1", f1), ("qwk", qwk)):
                d = paired_bootstrap_diff(pa, ya, ypa, ypb, fn, n_boot=n_boot)
                out.append(dict(comparison="{} vs {}".format(a_tag, b_tag),
                                tests=what, seed=seed, metric=name,
                                diff=d["diff"], lo=d["lo"], hi=d["hi"],
                                p_value=d["p_value"], note="per-seed, descriptive"))

        if len(pool_a) > 1:
            for name, fn in (("macro_f1", f1), ("qwk", qwk)):
                d = paired_bootstrap_diff_seeds(pool_pat, pool_y, pool_a, pool_b,
                                                fn, n_boot=n_boot)
                out.append(dict(comparison="{} vs {}".format(a_tag, b_tag),
                                tests=what, seed="pooled", metric=name,
                                diff=d["diff"], lo=d["lo"], hi=d["hi"],
                                p_value=d["p_value"], note="",
                                sd_between_seeds=d["sd_between_seeds"],
                                seed_wins="{}/{}".format(d["seed_wins"],
                                                         d["n_seeds"])))

    cdf = pd.DataFrame(out)
    if len(cdf):
        cdf["p_adjusted"] = np.nan
        cdf["significant_fdr05"] = False
        # FDR family = the pooled rows only, one per comparison x metric
        fam = (cdf.seed == "pooled") & cdf.p_value.notna()
        if fam.any():
            rej, adj = benjamini_hochberg(cdf.loc[fam, "p_value"].to_numpy())
            cdf.loc[fam, "p_adjusted"] = adj
            cdf.loc[fam, "significant_fdr05"] = rej
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
    L.append("Difference averaged over training seeds, with one patient-level "
             "bootstrap resample shared across seeds. FDR is controlled across "
             "these rows only — one test per comparison and metric.\n")
    L.append("| Comparison | Tests | Metric | Δ | 95% CI | sd(seeds) | seeds + | p | p(FDR) | Sig |")
    L.append("| :-- | :-- | :-- | --: | :-- | --: | :-: | --: | --: | :-: |")
    pooled = cdf[cdf.seed == "pooled"] if len(cdf) else cdf
    if len(pooled):
        for _, r in pooled.iterrows():
            sig = "yes" if r.get("significant_fdr05") else "no"
            L.append("| {} | {} | {} | {:+.4f} | [{:+.4f}, {:+.4f}] | {:.4f} | {} | {:.4f} | {:.4f} | {} |"
                     .format(r.comparison, r.tests, r.metric, r["diff"], r.lo, r.hi,
                             r.get("sd_between_seeds", np.nan),
                             r.get("seed_wins", "—"),
                             r.p_value, r.get("p_adjusted", np.nan), sig))
    else:
        L.append("| — | no comparable runs yet | | | | | | | | |")

    if len(cdf):
        bad = cdf.note.astype(str).str.contains("not pooled|not directly pairable",
                                                na=False)
        for _, r in cdf[bad].iterrows():
            L.append("| {} | {} | — | — | — | — | — | — | — | {} |".format(
                r.comparison, r.tests, r["note"]))

    L.append("\n### Table 4.3b — Per-seed differences (descriptive, not tested)\n")
    L.append("Each row resamples patients with that seed's trained model held "
             "fixed, so its interval covers test-set sampling only and excludes "
             "training stochasticity. On this campaign that omission is decisive: "
             "several comparisons reverse sign between seeds with narrow "
             "intervals on both sides. These rows are shown for transparency and "
             "carry no significance claim.\n")
    L.append("| Comparison | Seed | Metric | Δ | 95% CI | p |")
    L.append("| :-- | :-: | :-- | --: | :-- | --: |")
    if len(cdf):
        per = cdf[(cdf.seed != "pooled") & cdf.p_value.notna()]
        for _, r in per.iterrows():
            L.append("| {} | {} | {} | {:+.4f} | [{:+.4f}, {:+.4f}] | {:.4f} |".format(
                r.comparison, r.seed, r.metric, r["diff"], r.lo, r.hi, r.p_value))

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
    ap.add_argument("--force", action="store_true",
                    help="re-run completed ladder runs. Does NOT redo ACSSL "
                         "pretraining: that representation is shared by every "
                         "E4 seed, and E4-vs-E3 is meant to hold it fixed.")
    ap.add_argument("--repretrain_acssl", action="store_true",
                    help="discard the ACSSL checkpoint and pretrain again, "
                         "even if its fingerprint matches")
    ap.add_argument("--analyse_only", action="store_true",
                    help="skip training, just rebuild the tables from existing runs")
    ap.add_argument("--n_boot", type=int, default=1000)
    ap.add_argument("--seeds", type=str, default=None,
                    help="comma-separated seeds, overriding the profile's. "
                         "Completed runs are skipped, so extending 42,43,44 to "
                         "42,43,44,45,46,47,48 only trains the new ones.")
    args = ap.parse_args()

    prof = dict(PROFILES[args.profile])
    prof["_name"] = args.profile
    if args.seeds:
        prof["seeds"] = [int(x) for x in args.seeds.split(",")]
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

        # E4 is the ACSSL transfer, so the encoders must exist before it runs.
        # Pretrain ONCE and let every seed reuse it: pretraining per seed would
        # make the three seeds three different representations, and the
        # E4-vs-E3 comparison would then confound the representation with the
        # seed it was drawn from.
        if any(t == "E4" for _s, _f, t in runs):
            ck_dir = os.path.join(PROJECT_ROOT, "data",
                                  "smoke" if prof["mode"] == "smoke" else "",
                                  "checkpoints").replace(os.sep + os.sep, os.sep)
            ck = os.path.join(ck_dir, "acssl_encoders.pt")
            # The pretrained encoders must be built with the SAME backbone the
            # stage will train, or the transfer is refused at load time. Needed
            # here, before the reuse check, because it is part of what makes a
            # checkpoint reusable.
            bb = prof.get("backbone") or (
                "smallcnn" if prof["mode"] == "smoke" else "resnet18")
            reuse, why = False, ""
            if os.path.exists(ck) and not args.repretrain_acssl:
                try:
                    import torch as _t
                    pc = (_t.load(ck, map_location="cpu", weights_only=False)
                          .get("pretrain_config") or {})
                    # pretrained_backbone is part of the fingerprint because a
                    # checkpoint pretrained from random weights and one
                    # pretrained from ImageNet are different experiments. The
                    # original campaign silently inherited a random-init
                    # checkpoint into an ImageNet-init ladder, which made E4 vs
                    # E3 a comparison RQ2 never asked for. A checkpoint lacking
                    # the field predates the fix and is treated as random.
                    want = {"backbone": bb, "epochs": prof["epochs"],
                            "mode": prof["mode"], "pretrained_backbone": True}
                    diff = {k: (pc.get(k), v) for k, v in want.items()
                            if pc.get(k) != v}
                    if not pc:
                        why = "no pretrain_config recorded"
                    elif diff:
                        why = ", ".join("{} {}->{}".format(k, x, y)
                                        for k, (x, y) in diff.items())
                    else:
                        reuse = True
                except Exception as e:
                    why = "unreadable ({})".format(e)

            if reuse:
                print("  ACSSL encoders already present, reusing {}".format(
                    os.path.relpath(ck, PROJECT_ROOT)))
            elif os.path.exists(ck) and not args.repretrain_acssl:
                print("  ACSSL encoders present but stale, re-pretraining: {}"
                      .format(why))
            if not reuse:
                print("  pretraining ACSSL encoders (once, shared by all seeds)")
                cmd = [sys.executable,
                       os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "amog_acssl.py"),
                       "--mode", prof["mode"], "--epochs", str(prof["epochs"]),
                       "--backbone", bb]
                rc = subprocess.run(cmd, cwd=PROJECT_ROOT).returncode
                if rc != 0:
                    print("  [FAIL] ACSSL pretraining failed; E4 will be skipped "
                          "rather than run as an unlabelled E3")
                    runs = [r for r in runs if r[2] != "E4"]

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
