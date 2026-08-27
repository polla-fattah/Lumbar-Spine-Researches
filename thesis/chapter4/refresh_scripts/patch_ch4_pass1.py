"""Refresh Chapter 4 from three seeds to seven: prose, then table bodies."""
import io, re

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
s = io.open(P, encoding='utf-8').read()
N = 0


def sub(old, new, why):
    global s, N
    assert s.count(old) == 1, 'anchor failed: ' + why
    s = s.replace(old, new)
    N += 1


# ---- header comment ------------------------------------------------------ #
sub("""%  DRAFT 1 -- written 2026-08-27 against the completed three-seed campaign.
%  A seven-seed campaign is running; every number tagged [3-SEED] below is to be
%  refreshed from data/reports/chapter4_tables.md when it completes. The
%  narrative is not expected to change: the comparisons that separate do so on
%  3/3 seeds and the ones that do not are one to two orders of magnitude below
%  the seed-to-seed standard deviation.""",
    """%  DRAFT 2 -- written 2026-08-27 against the COMPLETED seven-seed campaign.
%  70 runs, 0 failures, 955.8 minutes. All figures are seven-seed.
%
%  The extra four seeds changed two verdicts, both in the direction of more
%  evidence rather than less: typed edges and the ordinal head crossed FDR
%  correction, while anatomical topology and cross-sequence SSL weakened. The
%  step decomposition also changed shape and its prose was rewritten to match.""",
    'header')

# ---- overview ------------------------------------------------------------ #
sub("""  Quadratic weighted kappa rises from $0.7276$ to $0.7448$, a paired difference
  of $+0.0172$ (95\\% CI $[+0.0064, +0.0285]$) that holds on every seed and is the
  only pre-specified comparison surviving false discovery rate correction.""",
    """  Quadratic weighted kappa rises from $0.7270$ to $0.7447$, a paired difference
  of $+0.0177$ (95\\% CI $[+0.0097, +0.0260]$) that holds on all seven seeds and
  survives false discovery rate correction. Two further comparisons also survive:
  typed heterogeneous edges and the ordinal, cost-sensitive head.""",
    'overview 1')

sub("""  \\item \\textbf{Most of the proposed mechanisms do not account for that gain.}
  Anatomically aligned self-supervision (RQ2) and disease-conditioned routing
  (RQ3) produce effects of $+0.0051$ and $+0.0010$ QWK respectively, between two
  and twenty times smaller than the standard deviation induced by changing the
  training seed alone. Relational structure (RQ1) helps, but the anatomical
  content of that structure does not: a typed graph beats a homogeneous one,
  while an anatomically correct topology does not beat a degree-preserving
  random shuffle.""",
    """  \\item \\textbf{Most of the proposed mechanisms do not account for that gain.}
  Anatomically aligned self-supervision (RQ2) and disease-conditioned routing
  (RQ3) produce effects of $+0.0020$ and $+0.0053$ QWK, bounded by the paired
  intervals at $1.22\\%$ and $1.55\\%$ of baseline performance respectively.
  Relational structure (RQ1) helps, but the anatomical content of that structure
  does not: a typed graph beats a homogeneous one on every seed, while an
  anatomically correct topology does not beat a degree-preserving random shuffle
  and is bounded at $1.05\\%$ of baseline.""",
    'overview 2')

# ---- what was run -------------------------------------------------------- #
sub("""the LumbarDISC public benchmark: ten configurations $\\times$ three training seeds
$(42, 43, 44)$, fifty epochs each, thirty runs in total, completed in
$669.4$~minutes on a single RTX~5090. No run failed. A seven-seed extension is
in progress at the time of writing.""",
    """the LumbarDISC public benchmark: ten configurations $\\times$ seven training
seeds $(42$--$48)$, fifty epochs each, seventy runs in total, completed in
$955.8$~minutes on a single RTX~5090. No run failed.

The campaign was extended from three seeds to seven after the three-seed
analysis left two comparisons close to the corrected significance threshold and
the power analysis of Section~\\ref{sec:results-power} indicated roughly ten
seeds would resolve them. The extension is reported because it changed two
verdicts, and Section~\\ref{sec:results-sevenseed} states what changed and in
which direction.""",
    'what was run')

# ---- table 4.1 ----------------------------------------------------------- #
sub("""Table~\\ref{tab:ladder} reports each configuration averaged over the three seeds.
[3-SEED]""",
    """Table~\\ref{tab:ladder} reports each configuration averaged over the seven
seeds.""",
    'table 4.1 lead')

sub("""\\caption{Ablation ladder on the held-out test partition, mean $\\pm$ standard
deviation over three training seeds.}""",
    """\\caption{Ablation ladder on the held-out test partition, mean $\\pm$ standard
deviation over seven training seeds.}""",
    'table 4.1 caption')

old_body = """E0 single sequence          & $0.7276 \\pm 0.0070$ & $0.694 \\pm 0.004$ & 69.0\\% \\\\
E1 multi-sequence           & $0.7221 \\pm 0.0058$ & $0.693 \\pm 0.004$ & 68.5\\% \\\\
E2 + disease routing        & $0.7231 \\pm 0.0150$ & $0.697 \\pm 0.014$ & 69.5\\% \\\\
E3 + modality dropout       & $0.7263 \\pm 0.0151$ & $0.700 \\pm 0.009$ & 69.2\\% \\\\
E4 + ACSSL                  & $0.7314 \\pm 0.0110$ & $0.697 \\pm 0.011$ & 69.1\\% \\\\
E5 + homogeneous graph      & $0.7226 \\pm 0.0077$ & $0.694 \\pm 0.009$ & 68.3\\% \\\\
E6 + typed graph            & $0.7349 \\pm 0.0066$ & $0.710 \\pm 0.001$ & 70.3\\% \\\\
\\quad E6 shuffled edges     & $0.7298 \\pm 0.0032$ & $0.701 \\pm 0.010$ & 69.9\\% \\\\
\\quad E6 ungated residual   & $0.7358 \\pm 0.0184$ & $0.704 \\pm 0.019$ & 70.9\\% \\\\
E7 + ordinal, cost-sensitive & $\\mathbf{0.7448 \\pm 0.0072}$ & $\\mathbf{0.714 \\pm 0.006}$ & \\textbf{72.0\\%} \\\\"""
new_body = """E0 single sequence          & $0.7270 \\pm 0.0108$ & $0.693 \\pm 0.009$ & 69.2\\% \\\\
E1 multi-sequence           & $0.7246 \\pm 0.0075$ & $0.694 \\pm 0.004$ & 68.9\\% \\\\
E2 + disease routing        & $0.7298 \\pm 0.0123$ & $0.701 \\pm 0.009$ & 69.6\\% \\\\
E3 + modality dropout       & $0.7273 \\pm 0.0125$ & $0.700 \\pm 0.009$ & 70.1\\% \\\\
E4 + ACSSL                  & $0.7293 \\pm 0.0109$ & $0.697 \\pm 0.008$ & 69.3\\% \\\\
E5 + homogeneous graph      & $0.7272 \\pm 0.0091$ & $0.698 \\pm 0.008$ & 69.1\\% \\\\
E6 + typed graph            & $0.7364 \\pm 0.0073$ & $0.706 \\pm 0.010$ & 70.7\\% \\\\
\\quad E6 shuffled edges     & $0.7344 \\pm 0.0052$ & $0.704 \\pm 0.007$ & 69.9\\% \\\\
\\quad E6 ungated residual   & $0.7350 \\pm 0.0167$ & $0.700 \\pm 0.014$ & 70.6\\% \\\\
E7 + ordinal, cost-sensitive & $\\mathbf{0.7447 \\pm 0.0051}$ & $\\mathbf{0.712 \\pm 0.005}$ & \\textbf{71.0\\%} \\\\"""
sub(old_body, new_body, 'table 4.1 body')

io.open(P, 'w', encoding='utf-8').write(s)
print('pass 1: %d edits applied' % N)
