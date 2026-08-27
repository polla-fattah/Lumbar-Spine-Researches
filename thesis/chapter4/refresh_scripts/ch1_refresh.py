"""Refresh Chapter 1's demonstrated-contribution figures to seven seeds."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter1.tex')
txt = io.open(P, encoding='utf-8').read()
N = 0


def sub(old, new, why):
    global txt, N
    assert txt.count(old) == 1, 'anchor failed: ' + why
    txt = txt.replace(old, new)
    N += 1


sub("""with the reference standard over a single-sequence baseline by $+0.0172$
quadratic weighted kappa, reproducibly and after correction for multiple
comparisons, but that the anatomical mechanisms proposed to achieve this do not
account for the improvement: attribution analysis indicates the convolutional
encoder already localises the graded structure without them.""",
    """with the reference standard over a single-sequence baseline by $+0.0177$
quadratic weighted kappa, on every one of seven training seeds and after
correction for multiple comparisons, but that the anatomical mechanisms proposed
to achieve this do not account for the improvement: attribution analysis
indicates the convolutional encoder already localises the graded structure
without them.""",
    'outcome sentence')

sub("""errors. Quadratic weighted kappa improves by $+0.0172$ over a single-sequence
baseline and recall on Severe targets rises from $62.7\\%$ to $65.0\\%$, the latter
attributable to the ordinal and cost-sensitive objective rather than to any
proposed structural mechanism.""",
    """errors. Quadratic weighted kappa improves by $+0.0177$ over a single-sequence
baseline, Severe$\\rightarrow$Normal confusions fall from $5.7\\%$ to $3.8\\%$ and
recall on Severe targets rises from $61.1\\%$ to $63.1\\%$, the last two
attributable to the ordinal and cost-sensitive objective rather than to any
proposed structural mechanism.""",
    'significance claims')

sub("""$+0.0172$ (95\\% CI $[+0.0064, +0.0285]$), reproducibly across training seeds and
surviving false discovery rate correction across the pre-specified comparison
family. The system, its frozen data partition and its behavioural test suite are
released.""",
    """$+0.0177$ (95\\% CI $[+0.0097, +0.0260]$), on every one of seven training seeds
and surviving false discovery rate correction across the pre-specified
comparison family. Two further comparisons also survive: typed heterogeneous
edges and the ordinal, cost-sensitive objective. The system, its frozen data
partition and its behavioural test suite are released.""",
    'D1')

# D3 gains the equivalence bounds, which are the stronger form of the claim
sub("""grading at this data scale, with a mechanism.} Neither anatomically aligned
cross-sequence self-supervision nor disease-conditioned routing produces a
detectable improvement, and anatomically correct graph topology does not
outperform a degree-preserving random shuffle.""",
    """grading at this data scale, with a mechanism.} Neither anatomically aligned
cross-sequence self-supervision nor disease-conditioned routing produces a
detectable improvement, and anatomically correct graph topology does not
outperform a degree-preserving random shuffle. These are bounds rather than
absences: the paired intervals constrain the three mechanisms to at most
$1.22\\%$, $1.55\\%$ and $1.05\\%$ of baseline performance respectively.""",
    'D3')

# the negative-findings subsection
sub("""Contribution~3 (heterogeneous disease--anatomy graph) is partly supported. Typed
relational structure improves grading over a homogeneous graph ($+0.0123$ QWK,
every seed); the anatomical identity of the relations does not.""",
    """Contribution~3 (heterogeneous disease--anatomy graph) is partly supported. Typed
relational structure improves grading over a homogeneous graph ($+0.0093$ QWK on
every one of seven seeds, surviving correction at $p_{\\mathrm{FDR}} = 0.009$);
the anatomical identity of the relations does not.""",
    'contribution 3 negative')

sub("""Contribution~2 (disease-conditioned routing) divides. The router does learn
clinically sensible target-dependent sequence weights, reproducing the expected
allocation in all fifteen runs in which a gate is present. It does not improve
grading ($+0.0010$ QWK) and it does not improve robustness to missing sequences.""",
    """Contribution~2 (disease-conditioned routing) divides. The router does learn
clinically sensible target-dependent sequence weights, reproducing the expected
allocation in all fifteen runs in which a gate is present. It does not improve
grading ($+0.0053$ QWK, five seeds of seven, bounded at $1.55\\%$ of baseline)
and it does not improve robustness to missing sequences.""",
    'contribution 2 negative')

io.open(P, 'w', encoding='utf-8').write(txt)
print('Chapter 1 refreshed: %d edits' % N)
