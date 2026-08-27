#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Deeper statistical analysis for Chapter 4, over the seven-seed campaign.

The campaign driver produces the ladder table and the pre-specified comparisons.
This adds four things a results chapter needs and those do not supply.

1. EQUIVALENCE BOUNDS FOR THE NULLS.
   "p > 0.05" says only that an effect was not detected, which is the weakest
   possible statement and invites the reader to assume the study was too small.
   The paired interval already bounds the effect; stating that bound converts
   "we found nothing" into "any effect is smaller than X", which is a result.
   Reported as the tighter of the two interval limits, in QWK and as a
   percentage of the E0 baseline.

2. EFFECT SIZES.
   A p-value confounds effect and sample size. Cohen's d on the paired
   across-seed differences separates them, and standardises comparisons whose
   raw magnitudes differ by an order of magnitude.

3. POWER, RECOMPUTED AT SEVEN SEEDS.
   The three-seed power table used three-seed variance estimates, which are
   themselves noisy. Seven seeds give a better variance estimate and therefore a
   better answer to "how many runs would this need".

4. CLINICAL ERROR STRUCTURE.
   Aggregate agreement hides the errors that matter. Severe-to-Normal confusions
   are the clinically consequential direction, and RQ5's objective was chosen to
   suppress them, so they are reported per rung with the distance profile.

Everything is computed from the frozen per-seed result files; nothing is typed.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from amog_modes import PROJECT_ROOT  # noqa: E402

SEEDS = (42, 43, 44, 45, 46, 47, 48)

# The comparisons Chapter 3 pre-specifies, with the research question each
# serves. Order is the order they are discussed in Chapter 4.
COMPARISONS = [
    ("E7", "E0", "Full system vs baseline", "--"),
    ("E6", "E5", "Typed heterogeneous edges", "RQ1"),
    ("E7", "E6", "Ordinal and cost-sensitive head", "RQ5"),
    ("E6", "E6_shuffled", "Anatomical topology vs shuffle", "RQ1"),
    ("E4", "E3", "Cross-sequence self-supervision", "RQ2"),
    ("E2", "E1", "Disease-conditioned routing", "RQ3"),
    ("E6", "E6_ungated", "Gated residual", "--"),
    ("E3", "E2", "Modality dropout", "--"),
    ("E5", "E0", "Relational message passing", "--"),
]


def load(tag, seed, field="qwk"):
    p = os.path.join(PROJECT_ROOT, "data", "derived",
                     "{}_real_seed{}_test.json".format(tag, seed))
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)[field]


def paired(a, b, field="qwk"):
    return np.array([load(a, s, field) - load(b, s, field) for s in SEEDS])


def cohens_d(d):
    """Paired Cohen's d: mean difference over its own standard deviation."""
    sd = d.std(ddof=1)
    return float(d.mean() / sd) if sd > 0 else float("inf")


def seeds_for_power(d, power_z=2.8):
    """Runs needed to detect an effect of the observed size at ~80% power."""
    m, sd = abs(d.mean()), d.std(ddof=1)
    if m <= 0:
        return None
    return int(np.ceil((power_z * sd / m) ** 2))


def main():
    cmp_path = os.path.join(PROJECT_ROOT, "data", "reports",
                            "chapter4_comparisons.csv")
    cdf = pd.read_csv(cmp_path)
    pooled = cdf[(cdf.seed.astype(str) == "pooled") & (cdf.metric == "qwk")]
    ci = {r.comparison: (r["diff"], r.lo, r.hi, r.p_adjusted,
                         bool(r.significant_fdr05))
          for _, r in pooled.iterrows()}

    base = np.mean([load("E0", s) for s in SEEDS])

    rows = []
    for a, b, name, rq in COMPARISONS:
        d = paired(a, b)
        key = "{} vs {}".format(a, b)
        diff, lo, hi, padj, sig = ci.get(key, (d.mean(), np.nan, np.nan,
                                               np.nan, False))
        # the bound: how large could the effect be, at the interval's far edge
        bound = max(abs(lo), abs(hi)) if np.isfinite(lo) else np.nan
        rows.append(dict(
            comparison=key, name=name, rq=rq,
            delta=d.mean(), sd=d.std(ddof=1),
            wins="{}/{}".format(int((d > 0).sum()), len(d)),
            lo=lo, hi=hi, p_adj=padj, significant=sig,
            cohens_d=cohens_d(d), seeds_needed=seeds_for_power(d),
            bound_qwk=bound, bound_pct=100.0 * bound / base
            if np.isfinite(bound) else np.nan))
    res = pd.DataFrame(rows)

    print("=" * 78)
    print("  1. EFFECT SIZE AND DETECTABILITY, seven seeds")
    print("=" * 78)
    print("{:<34}{:>9}{:>9}{:>8}{:>9}".format(
        "comparison", "delta", "Cohen d", "seeds", "p(FDR)"))
    for _, r in res.iterrows():
        need = "--" if r.seeds_needed is None else (
            "{}".format(r.seeds_needed) if r.seeds_needed < 100000 else ">1e5")
        print("{:<34}{:+9.4f}{:>9.2f}{:>8}{:>9.3f}{}".format(
            r["name"][:33], r.delta, r.cohens_d, need, r.p_adj,
            "  SIG" if r.significant else ""))

    print()
    print("=" * 78)
    print("  2. EQUIVALENCE BOUNDS for the comparisons that did not separate")
    print("=" * 78)
    print("  A null is stronger stated as a bound. The figures below are the far")
    print("  edge of the 95% interval: the largest effect still compatible with")
    print("  the data, in QWK and as a percentage of the E0 baseline ({:.4f}).".format(base))
    print()
    print("{:<34}{:>12}{:>12}".format("comparison", "bound QWK", "% of E0"))
    for _, r in res[~res.significant].iterrows():
        print("{:<34}{:>12.4f}{:>11.2f}%".format(r["name"][:33], r.bound_qwk,
                                                 r.bound_pct))

    print()
    print("=" * 78)
    print("  3. CLINICAL ERROR STRUCTURE per rung")
    print("=" * 78)
    print("{:<14}{:>12}{:>16}{:>14}".format(
        "rung", "severe rec", "severe->normal", "dist >=2"))
    for tag in ("E0", "E1", "E2", "E3", "E4", "E5", "E6", "E6_shuffled",
                "E6_ungated", "E7"):
        sr = np.mean([load(tag, s, "severe_recall") for s in SEEDS])
        sn = np.mean([load(tag, s, "severe_to_normal_rate") for s in SEEDS])
        d2 = np.mean([load(tag, s, "grade_distance").get("d2_or_more", 0.0)
                      for s in SEEDS])
        print("{:<14}{:>11.1%}{:>15.1%}{:>14.3%}".format(tag, sr, sn, d2))

    print()
    print("=" * 78)
    print("  4. CALIBRATION per rung (expected calibration error)")
    print("=" * 78)
    # The top-level "ece" field is the UNCALIBRATED test value. Temperature
    # scaling is fitted on validation and its test metrics are stored under
    # "calibration", so reporting only the top-level field would say the ladder
    # gets progressively worse calibrated when the opposite is true after the
    # correction the protocol actually applies.
    print("{:<10}{:>14}{:>14}{:>12}".format(
        "rung", "ECE uncal", "ECE calib", "temperature"))
    for tag in ("E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"):
        u = np.mean([load(tag, s, "ece") for s in SEEDS])
        c, t = [], []
        for s in SEEDS:
            blk = load(tag, s, "calibrated") or {}
            fit = load(tag, s, "calibration") or {}
            if "ece" in blk:
                c.append(blk["ece"])
            if "temperature" in fit:
                t.append(fit["temperature"])
        cm = np.mean(c) if c else float("nan")
        tm = np.mean(t) if t else float("nan")
        print("{:<10}{:>14.4f}{:>14.4f}{:>12.3f}".format(tag, u, cm, tm))

    out = os.path.join(PROJECT_ROOT, "data", "reports",
                       "chapter4_effect_sizes.csv")
    res.to_csv(out, index=False)
    print()
    print("  {}".format(os.path.relpath(out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
