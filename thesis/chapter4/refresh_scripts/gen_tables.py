"""Emit LaTeX table bodies for Chapter 4 from the seven-seed results.

Typing these by hand is how a thesis acquires numbers that do not match its own
data files. Every row here is computed.
"""
import json, os, sys
import numpy as np
import pandas as pd

ROOT = r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
os.chdir(ROOT)
S = (42, 43, 44, 45, 46, 47, 48)


def L(t, s, f='qwk'):
    with open('data/derived/%s_real_seed%d_test.json' % (t, s), encoding='utf-8') as fh:
        return json.load(fh)[f]


RUNGS = [('E0', 'E0 single sequence'), ('E1', 'E1 multi-sequence'),
         ('E2', 'E2 + disease routing'), ('E3', 'E3 + modality dropout'),
         ('E4', 'E4 + ACSSL'), ('E5', 'E5 + homogeneous graph'),
         ('E6', 'E6 + typed graph'),
         ('E6_shuffled', r'\quad E6 shuffled edges'),
         ('E6_ungated', r'\quad E6 ungated residual'),
         ('E7', 'E7 + ordinal, cost-sensitive')]

print('%% ---- TABLE 4.1 ladder (7 seeds) ----')
for tag, name in RUNGS:
    q = [L(tag, s) for s in S]
    f = [L(tag, s, 'macro_f1') for s in S]
    b = np.mean([L(tag, s, 'balanced_accuracy') for s in S])
    bold = tag == 'E7'
    fmt = (r'$\mathbf{%.4f \pm %.4f}$' if bold else r'$%.4f \pm %.4f$')
    fmt2 = (r'$\mathbf{%.3f \pm %.3f}$' if bold else r'$%.3f \pm %.3f$')
    bb = (r'\textbf{%.1f\%%}' if bold else r'%.1f\%%') % (b * 100)
    print('%s & %s & %s & %s \\\\' % (
        name, fmt % (np.mean(q), np.std(q, ddof=1)),
        fmt2 % (np.mean(f), np.std(f, ddof=1)), bb))

print()
print('%% ---- TABLE 4.2 step decomposition (7 seeds) ----')
CHAIN = [('E0', 'E1', 'Multi-sequence input'),
         ('E1', 'E2', 'Disease-conditioned routing'),
         ('E2', 'E3', 'Modality dropout'),
         ('E3', 'E4', 'Anatomical cross-sequence SSL'),
         ('E4', 'E5', 'Homogeneous graph'),
         ('E5', 'E6', 'Typed heterogeneous edges'),
         ('E6', 'E7', 'Ordinal and cost-sensitive head')]
run = 0.0
for a, b, lab in CHAIN:
    d = np.array([L(b, s) - L(a, s) for s in S])
    run += d.mean()
    last = lab.startswith('Ordinal')
    cum = (r'$\mathbf{%+.4f}$' if last else '$%+.4f$') % run
    print('%s & $%+.4f$ & %d/7 & %s \\\\' % (lab, d.mean(), int((d > 0).sum()), cum))

print()
print('%% ---- TABLE 4.3 comparisons (7 seeds, FDR) ----')
cdf = pd.read_csv('data/reports/chapter4_comparisons.csv')
p = cdf[(cdf.seed.astype(str) == 'pooled') & (cdf.metric == 'qwk')]
NAME = {'E7 vs E0': ('E7 vs E0', 'full system'),
        'E6 vs E5': ('E6 vs E5', 'typed edges (RQ1)'),
        'E7 vs E6': ('E7 vs E6', 'ordinal head (RQ5)'),
        'E6 vs E6_shuffled': (r'E6 vs E6\_shuf', 'anatomy (RQ1)'),
        'E4 vs E3': ('E4 vs E3', 'ACSSL (RQ2)'),
        'E2 vs E1': ('E2 vs E1', 'routing (RQ3)'),
        'E6 vs E6_ungated': (r'E6 vs E6\_ung', 'gating'),
        'E3 vs E2': ('E3 vs E2', 'modality dropout'),
        'E5 vs E0': ('E5 vs E0', 'message passing')}
for _, r in p.sort_values('diff', ascending=False).iterrows():
    if r.comparison not in NAME:
        continue
    nm, desc = NAME[r.comparison]
    sig = r'\textbf{yes}' if r.significant_fdr05 else 'no'
    padj = (r'$\mathbf{<0.001}$' if r.p_adjusted < 0.001
            else (r'$\mathbf{%.3f}$' if r.significant_fdr05 else '$%.3f$') % r.p_adjusted)
    print('%s & %s & $%+.4f$ & $[%+.4f, %+.4f]$ & %s & %s & %s \\\\' % (
        nm, desc, r['diff'], r.lo, r.hi, str(r.seed_wins), padj, sig))

print()
print('%% ---- TABLE 4.4 effect size and power (7 seeds) ----')
e = pd.read_csv('data/reports/chapter4_effect_sizes.csv')
for _, r in e.iterrows():
    need = '---' if pd.isna(r.seeds_needed) else (
        '%d' % r.seeds_needed if r.seeds_needed < 100000 else r'$>10^5$')
    d = (r'$\mathbf{%.2f}$' if abs(r.cohens_d) >= 0.8 else '$%.2f$') % r.cohens_d
    print('%s & $%+.4f$ & %s & %s \\\\' % (r['name'], r.delta, d, need))

print()
print('%% ---- TABLE 4.5 equivalence bounds ----')
for _, r in e[~e.significant].sort_values('bound_qwk').iterrows():
    print(r'%s & $%.4f$ & $%.2f\%%$ \\' % (r['name'], r.bound_qwk, r.bound_pct))

print()
print('%% ---- TABLE 4.6 clinical error structure ----')
for tag, name in RUNGS:
    sr = np.mean([L(tag, s, 'severe_recall') for s in S])
    sn = np.mean([L(tag, s, 'severe_to_normal_rate') for s in S])
    d2 = np.mean([L(tag, s, 'grade_distance')['d2_or_more'] for s in S])
    bold = tag == 'E7'
    f = (r'\textbf{%.1f\%%}' if bold else r'%.1f\%%')
    f3 = (r'\textbf{%.3f\%%}' if bold else r'%.3f\%%')
    print('%s & %s & %s & %s \\\\' % (name, f % (sr * 100), f % (sn * 100),
                                      f3 % (d2 * 100)))

print()
print('%% ---- TABLE 4.7 calibration ----')
for tag, name in RUNGS:
    if tag.startswith('E6_'):
        continue
    u = np.mean([L(tag, s, 'ece') for s in S])
    c = np.mean([L(tag, s, 'calibrated')['ece'] for s in S])
    t = np.mean([L(tag, s, 'calibration')['temperature'] for s in S])
    print('%s & $%.4f$ & $%.4f$ & $%.3f$ \\\\' % (name, u, c, t))
