"""Refresh Chapter 5 to seven seeds and enrich it with the new analysis."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter5.tex')
txt = io.open(P, encoding='utf-8').read()
N = 0


def sub(old, new, why):
    global txt, N
    assert txt.count(old) == 1, 'anchor failed: ' + why
    txt = txt.replace(old, new)
    N += 1


sub("""%  DRAFT 1 -- written 2026-08-27 against the completed three-seed campaign, the
%  controlled input ablation, the attribution analysis and the ROI quality
%  control. Figures tagged [3-SEED] refresh when the seven-seed campaign lands;
%  the argument of this chapter does not depend on them, because every
%  comparison it leans on either holds on all seeds or is reported as null.""",
    """%  DRAFT 2 -- written 2026-08-27 against the COMPLETED seven-seed campaign,
%  the controlled input ablation, the attribution analysis and the ROI quality
%  control. The extension strengthened the chapter's central claim rather than
%  weakening it: typed edges and the ordinal head crossed FDR correction while
%  the two anatomical mechanisms moved further from it.""",
    'header')

sub("""The complete system improves on a single-sequence baseline by $+0.0172$ QWK
(95\\% CI $[+0.0064, +0.0285]$), reproducibly across seeds and after correction
for multiple comparisons. But the components credited with that improvement in
the original design are not the components responsible for it. Anatomically
aligned self-supervision produced no measurable benefit on any of three axes.
Disease-conditioned routing learned the clinically expected sequence weights
and produced no benefit from having learned them. Relational typing helped;
the anatomical identity of the relations did not.""",
    """The complete system improves on a single-sequence baseline by $+0.0177$ QWK
(95\\% CI $[+0.0097, +0.0260]$), on every one of seven seeds and after correction
for multiple comparisons. But the components credited with that improvement in
the original design are not the components responsible for it. Anatomically
aligned self-supervision produced no measurable benefit on any of three axes.
Disease-conditioned routing learned the clinically expected sequence weights
and produced no benefit from having learned them. Relational typing helped;
the anatomical identity of the relations did not.

The evidence for those statements is stronger than a set of failures to reject.
Each unsupported mechanism is \\emph{bounded}: anatomical topology contributes at
most $1.05\\%$ of baseline performance over a degree-preserving shuffle,
cross-sequence self-supervision at most $1.22\\%$, and disease-conditioned routing
at most $1.55\\%$. And the campaign was extended from three seeds to seven
precisely to test whether these were power failures. It was not: the same four
additional runs that carried typed edges and the ordinal head across the
corrected threshold moved anatomical topology and self-supervision further away
from it.""",
    'summary')

sub("""Two of the three proposed mechanisms are therefore rejected, one is
half-supported in a narrower form than proposed, and the largest single
contributor to final performance is an objective function that
Chapter~\\ref{ch:introduction} explicitly declined to claim as original.""",
    """Two of the three proposed mechanisms are therefore rejected, one is
half-supported in a narrower form than proposed, and the largest standardised
effect in the study --- $d = 1.97$, larger than the full-system comparison it
forms part of --- belongs to an objective function that
Chapter~\\ref{ch:introduction} explicitly declined to claim as original.""",
    'summary 2')

# ---------------------------------------------------------------- RQ1 section
sub("""RQ1 divides, and the division is the more interesting result. Typed
heterogeneous edges improve on a homogeneous graph by $+0.0123$ QWK on every
seed. Anatomically correct topology does not improve on a degree-preserving
random shuffle: $+0.0051$, two seeds of three, well inside the corrected
threshold.""",
    """RQ1 divides, and the division is the more interesting result. Typed
heterogeneous edges improve on a homogeneous graph by $+0.0093$ QWK on every one
of seven seeds, surviving correction at $p_{\\mathrm{FDR}} = 0.009$.
Anatomically correct topology does not improve on a degree-preserving random
shuffle: $+0.0020$, four seeds of seven, bounded at $1.05\\%$ of baseline.""",
    'RQ1')

sub("""it. Relational typing carries information; anatomical adjacency does not.""",
    """it. Relational typing carries information; anatomical adjacency does not.

The seven-seed extension sharpened both halves at once, which is the strongest
form this claim could take. Typed edges went from narrowly missing correction to
clearing it on every seed, while the anatomy comparison halved. A reader
inclined to attribute the second result to insufficient power has to explain why
the same four additional runs resolved the first.""",
    'RQ1 conclusion')

# ---------------------------------------------------------------- RQ5 section
sub("""Here the ordinal and cost-sensitive head improves QWK by $+0.0099$ on every seed,
with the smallest between-seed variance of any comparison in the study
($0.0017$), and raises recall on Severe targets from $59.6\\%$ to $65.0\\%$
relative to the same architecture under categorical cross-entropy.""",
    """Here the ordinal and cost-sensitive head improves QWK by $+0.0082$ on every one
of seven seeds, surviving correction at $p_{\\mathrm{FDR}} = 0.009$. Its
between-seed standard deviation of $0.0042$ is the smallest of any comparison,
which gives it the largest standardised effect in the study at $d = 1.97$.

The clinically material quantity moves further. Across the full ladder,
Severe$\\rightarrow$Normal confusions fall from $5.7\\%$ at the baseline to
$3.8\\%$ at E7 --- a relative reduction of a third --- while recall on Severe
targets rises from $61.1\\%$ to $63.1\\%$ and predictions two or more grades from
the reference fall from $0.526\\%$ to $0.344\\%$. Aggregate agreement was not
bought by trading away the errors clinicians care most about.""",
    'RQ5')

io.open(P, 'w', encoding='utf-8').write(txt)
print('Chapter 5 refreshed: %d edits' % N)
