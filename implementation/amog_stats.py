#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Statistical machinery required by Chapter 3. None of it existed before.

A single-run point estimate with no interval is the most common reason work in
this area is rejected, and it is what the fabricated implementation reported.
Every number that reaches Chapter 4 needs an interval, a paired comparison
against its control, and correction for the number of comparisons made.

    patient_bootstrap_ci   resample PATIENTS, not targets
    paired_bootstrap_diff  paired difference between two models on one cohort
    delong_test            correlated AUCs (DeLong et al. 1988)
    benjamini_hochberg     FDR control across the primary comparisons
    aggregate_seeds        mean and spread across repeated training seeds

WHY PATIENT-LEVEL RESAMPLING
----------------------------
One patient contributes up to 25 targets and those errors are correlated. Bootstrapping
targets treats them as independent, which understates the variance and produces
intervals that are too narrow -- the same failure mode as an image-level split.
Resampling patients keeps each patient's targets together.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


# --------------------------------------------------------------------------- #
def _metric(fn, y_true, y_pred, y_prob=None):
    return fn(y_true, y_pred) if y_prob is None else fn(y_true, y_pred, y_prob)


def patient_bootstrap_ci(patient_ids, y_true, y_pred, metric_fn, y_prob=None,
                         n_boot: int = 2000, alpha: float = 0.05, seed: int = 0):
    """Percentile CI by resampling patients with replacement.

    Returns (point_estimate, lo, hi, bootstrap_distribution).
    """
    patient_ids = np.asarray(patient_ids)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rng = np.random.default_rng(seed)

    point = _metric(metric_fn, y_true, y_pred, y_prob)

    uniq = np.unique(patient_ids)
    by_patient = {p: np.flatnonzero(patient_ids == p) for p in uniq}

    boots = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        take = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_patient[p] for p in take])
        try:
            boots[b] = _metric(metric_fn, y_true[idx], y_pred[idx],
                               None if y_prob is None else np.asarray(y_prob)[idx])
        except Exception:
            boots[b] = np.nan
    ok = boots[np.isfinite(boots)]
    if ok.size == 0:
        return point, np.nan, np.nan, boots
    lo, hi = np.percentile(ok, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(point), float(lo), float(hi), boots


def paired_bootstrap_diff(patient_ids, y_true, pred_a, pred_b, metric_fn,
                          prob_a=None, prob_b=None, n_boot: int = 2000,
                          alpha: float = 0.05, seed: int = 0):
    """Paired difference (A - B) with a CI and a two-sided bootstrap p-value.

    Ablation models are evaluated on the SAME patients, so comparisons are paired.
    An unpaired test would misstate the variance of the difference.
    """
    patient_ids = np.asarray(patient_ids)
    y_true = np.asarray(y_true)
    pred_a, pred_b = np.asarray(pred_a), np.asarray(pred_b)
    rng = np.random.default_rng(seed)

    point = (_metric(metric_fn, y_true, pred_a, prob_a)
             - _metric(metric_fn, y_true, pred_b, prob_b))

    uniq = np.unique(patient_ids)
    by_patient = {p: np.flatnonzero(patient_ids == p) for p in uniq}

    diffs = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        take = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_patient[p] for p in take])
        try:
            da = _metric(metric_fn, y_true[idx], pred_a[idx],
                         None if prob_a is None else np.asarray(prob_a)[idx])
            db = _metric(metric_fn, y_true[idx], pred_b[idx],
                         None if prob_b is None else np.asarray(prob_b)[idx])
            diffs[b] = da - db
        except Exception:
            diffs[b] = np.nan

    ok = diffs[np.isfinite(diffs)]
    if ok.size == 0:
        return dict(diff=float(point), lo=np.nan, hi=np.nan, p_value=np.nan, n_boot=0)
    lo, hi = np.percentile(ok, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    # two-sided p: proportion of the bootstrap distribution on the other side of 0
    p = 2.0 * min((ok <= 0).mean(), (ok >= 0).mean())
    return dict(diff=float(point), lo=float(lo), hi=float(hi),
                p_value=float(min(p, 1.0)), n_boot=int(ok.size))


# --------------------------------------------------------------------------- #
def _midrank(x):
    order = np.argsort(x)
    sorted_x = x[order]
    n = len(x)
    ranks = np.empty(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[i:j + 1] = 0.5 * (i + j) + 1
        i = j + 1
    out = np.empty(n, dtype=float)
    out[order] = ranks
    return out


def delong_test(y_true, score_a, score_b):
    """DeLong's test for two correlated ROC AUCs on the same cases.

    Returns dict with auc_a, auc_b, difference, z and a two-sided p-value.
    Binary labels only; for the three-grade task apply it one-versus-rest, which
    is how Chapter 3 reports Severe-versus-rest.
    """
    y_true = np.asarray(y_true).astype(int)
    a, b = np.asarray(score_a, dtype=float), np.asarray(score_b, dtype=float)
    pos, neg = y_true == 1, y_true == 0
    m, n = int(pos.sum()), int(neg.sum())
    if m == 0 or n == 0:
        return dict(auc_a=np.nan, auc_b=np.nan, diff=np.nan, z=np.nan,
                    p_value=np.nan, note="one class absent")

    def structural(s):
        x, y = s[pos], s[neg]
        tx, ty, tz = _midrank(x), _midrank(y), _midrank(np.concatenate([x, y]))
        auc = (tz[:m].sum() - m * (m + 1) / 2.0) / (m * n)
        v01 = (tz[:m] - tx) / n
        v10 = 1.0 - (tz[m:] - ty) / m
        return auc, v01, v10

    auc_a, v01a, v10a = structural(a)
    auc_b, v01b, v10b = structural(b)

    s01 = np.cov(np.vstack([v01a, v01b]))
    s10 = np.cov(np.vstack([v10a, v10b]))
    S = s01 / m + s10 / n
    var = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    if var <= 0:
        return dict(auc_a=float(auc_a), auc_b=float(auc_b),
                    diff=float(auc_a - auc_b), z=np.nan, p_value=np.nan,
                    note="degenerate variance")
    z = (auc_a - auc_b) / np.sqrt(var)
    p = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
    return dict(auc_a=float(auc_a), auc_b=float(auc_b),
                diff=float(auc_a - auc_b), z=float(z), p_value=float(p))


# --------------------------------------------------------------------------- #
def benjamini_hochberg(p_values, alpha: float = 0.05):
    """FDR control. Returns (rejected mask, adjusted p-values).

    Chapter 3 declares a limited set of primary comparisons; everything else is
    exploratory. This is what keeps a ladder of many target-level analyses from
    being presented as many independent discoveries.
    """
    p = np.asarray(p_values, dtype=float)
    n = p.size
    if n == 0:
        return np.array([], dtype=bool), np.array([])
    order = np.argsort(p)
    ranked = p[order]
    adj = ranked * n / (np.arange(n) + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    out = np.empty(n, dtype=float)
    out[order] = adj
    return out <= alpha, out


def aggregate_seeds(values):
    """Mean, sd and range across repeated training seeds.

    Chapter 3: a one-off run is insufficient to attribute a small improvement to
    a method, because optimisation is stochastic.
    """
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if v.size == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, lo=np.nan, hi=np.nan)
    return dict(n=int(v.size), mean=float(v.mean()),
                sd=float(v.std(ddof=1)) if v.size > 1 else 0.0,
                lo=float(v.min()), hi=float(v.max()))


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from amog_modes import compute_metrics

    rng = np.random.default_rng(0)
    n_pat, per = 120, 25
    pid = np.repeat(np.arange(n_pat), per)
    y = rng.choice([0, 1, 2], size=n_pat * per, p=[0.77, 0.16, 0.07])

    # model B is deliberately a little better than A
    pa = np.where(rng.random(y.size) < 0.55, y, rng.integers(0, 3, y.size))
    pb = np.where(rng.random(y.size) < 0.65, y, rng.integers(0, 3, y.size))

    qwk = lambda t, p: compute_metrics(t, p)["qwk"]
    f1 = lambda t, p: compute_metrics(t, p)["macro_f1"]

    print("amog_stats self-test  ({} patients x {} targets)".format(n_pat, per))
    print("-" * 66)
    pt, lo, hi, _ = patient_bootstrap_ci(pid, y, pb, qwk, n_boot=400)
    print("QWK model B          : {:.4f}  95% CI [{:.4f}, {:.4f}]".format(pt, lo, hi))

    d = paired_bootstrap_diff(pid, y, pb, pa, f1, n_boot=400)
    print("macro-F1  B - A      : {:+.4f}  CI [{:+.4f}, {:+.4f}]  p={:.4f}".format(
        d["diff"], d["lo"], d["hi"], d["p_value"]))

    ybin = (y == 2).astype(int)
    sa = rng.random(y.size) * 0.5 + 0.25 * ybin
    sb = rng.random(y.size) * 0.5 + 0.45 * ybin
    dl = delong_test(ybin, sb, sa)
    print("DeLong Severe-vs-rest: AUC {:.4f} vs {:.4f}, z={:.3f}, p={:.2e}".format(
        dl["auc_a"], dl["auc_b"], dl["z"], dl["p_value"]))

    ps = [0.001, 0.012, 0.04, 0.21, 0.6]
    rej, adj = benjamini_hochberg(ps)
    print("BH-FDR on {}: rejected {}".format(ps, rej.tolist()))
    print("  adjusted: {}".format(np.round(adj, 4).tolist()))

    print("seeds                : {}".format(
        {k: round(v, 4) if isinstance(v, float) else v
         for k, v in aggregate_seeds([0.71, 0.74, 0.69, 0.73]).items()}))
    print("-" * 66)
