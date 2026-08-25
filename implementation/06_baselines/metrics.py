"""Honest metrics for ordinal severity grading.

Every quantity here is computed from predictions and targets. Nothing is
derived from another metric by a fudge factor.
"""
import numpy as np


def accuracy(y_true, y_pred):
    return float((y_true == y_pred).mean())


def confusion(y_true, y_pred, k):
    m = np.zeros((k, k), dtype=np.int64)
    np.add.at(m, (y_true, y_pred), 1)
    return m


def macro_f1(y_true, y_pred, k):
    """Unweighted mean F1. Classes absent from both truth and prediction are
    skipped rather than scored 0, which would silently reward ignoring them."""
    f1s = []
    for c in range(k):
        tp = int(((y_pred == c) & (y_true == c)).sum())
        fp = int(((y_pred == c) & (y_true != c)).sum())
        fn = int(((y_pred != c) & (y_true == c)).sum())
        if tp + fp + fn == 0:
            continue
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return float(np.mean(f1s)) if f1s else 0.0


def quadratic_weighted_kappa(y_true, y_pred, k):
    """Cohen's kappa with quadratic weights.

    Returns 0.0 when the expected-disagreement matrix is degenerate, which is
    what happens if a model predicts a single class for everything. That 0.0 is
    a genuine result and must not be papered over.
    """
    O = confusion(y_true, y_pred, k).astype(np.float64)
    n = O.sum()
    if n == 0:
        return 0.0
    i, j = np.meshgrid(np.arange(k), np.arange(k), indexing="ij")
    W = ((i - j) ** 2) / ((k - 1) ** 2)
    hist_t = np.bincount(y_true, minlength=k).astype(np.float64)
    hist_p = np.bincount(y_pred, minlength=k).astype(np.float64)
    E = np.outer(hist_t, hist_p) / n
    denom = (W * E).sum()
    if denom == 0:
        return 0.0
    return float(1.0 - (W * O).sum() / denom)


def expected_calibration_error(probs, y_true, n_bins=15):
    """Standard confidence-binned ECE on the top-1 prediction."""
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == y_true).astype(np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        mask = (conf > lo) & (conf <= hi) if b else (conf >= lo) & (conf <= hi)
        if not mask.any():
            continue
        ece += mask.sum() / n * abs(correct[mask].mean() - conf[mask].mean())
    return float(ece)


def balanced_accuracy(y_true, y_pred, k):
    """Mean per-class recall. Unlike accuracy this is not gamed by the 77% class."""
    recs = []
    for c in range(k):
        m = y_true == c
        if m.sum():
            recs.append(float((y_pred[m] == c).mean()))
    return float(np.mean(recs)) if recs else 0.0


def summarise(y_true, y_pred, probs, k=3):
    return {
        "accuracy": accuracy(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy(y_true, y_pred, k),
        "macro_f1": macro_f1(y_true, y_pred, k),
        "qwk": quadratic_weighted_kappa(y_true, y_pred, k),
        "ece": expected_calibration_error(probs, y_true),
    }
