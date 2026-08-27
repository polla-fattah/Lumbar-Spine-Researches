"""Update the RQ sections to seven seeds.

The ladder comparisons refresh. The input-ablation and attribution analyses were
run on seeds 42-44 only and are NOT silently restated as seven-seed results;
they keep their figures and gain an explicit note.
"""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
txt = io.open(P, encoding='utf-8').read()
N = 0


def sub(old, new, why):
    global txt, N
    assert txt.count(old) == 1, 'anchor failed: ' + why
    txt = txt.replace(old, new)
    N += 1


# ---------------------------------------------------------------- RQ1 typed
sub("""A typed heterogeneous graph outperforms a homogeneous one by $+0.0123$ QWK
($[+0.0028, +0.0216]$, 3/3 seeds). Macro-F1 rises from $0.694$ to $0.710$, and
E6 has the lowest across-seed macro-F1 variance of any configuration
($\\pm 0.001$). The comparison narrowly misses the corrected threshold
($p_{\\mathrm{FDR}} = 0.054$) but is detectable with ten seeds per
Table~\\ref{tab:power}, and its interval excludes zero.""",
    """A typed heterogeneous graph outperforms a homogeneous one by $+0.0093$ QWK
($[+0.0027, +0.0156]$), and does so on \\textbf{every one of seven seeds}. The
comparison survives false discovery rate correction at
$p_{\\mathrm{FDR}} = 0.009$, with $d = 1.06$.

This is one of the two verdicts the seven-seed extension changed. At three seeds
the same comparison stood at $+0.0123$ with $p_{\\mathrm{FDR}} = 0.054$, narrowly
outside correction, and the power analysis then indicated roughly ten seeds would
be needed. Seven sufficed, because the additional runs reduced the between-seed
standard deviation faster than they reduced the point estimate.""",
    'RQ1 typed')

sub("""Relational message passing alone does not help: E5 against E0 is $-0.0050$. The
benefit appears only once relations are typed. Message passing over an untyped
graph is, on this evidence, slightly worse than no graph at all.""",
    """Relational message passing alone does not help: E5 against E0 is $+0.0002$
($[-0.0073, +0.0074]$, $p_{\\mathrm{FDR}} = 0.967$), which is as close to exactly
nothing as this study measures. The benefit appears only once relations are
typed. Message passing over an untyped graph is, on this evidence, worth
precisely its parameter count and no more.""",
    'RQ1 message passing')

sub("""meaningfully. E6 exceeds its shuffled control by $+0.0051$ QWK
($[-0.0036, +0.0141]$, 2/3 seeds, $p_{\\mathrm{FDR}} = 0.570$). The control""",
    """meaningfully. E6 exceeds its shuffled control by $+0.0020$ QWK
($[-0.0038, +0.0076]$, 4/7 seeds, $p_{\\mathrm{FDR}} = 0.688$), and the paired
interval bounds any advantage at $1.05\\%$ of baseline performance. The control""",
    'RQ1 anatomy')

sub("""Chapter~\\ref{ch:methodology} designates the ungated residual a mandatory
ablation. The gated and ungated formulations are indistinguishable
($-0.0009$, 1/3 seeds); the ungated variant is marginally higher in the mean.
The gate can be removed without cost.""",
    """Chapter~\\ref{ch:methodology} designates the ungated residual a mandatory
ablation. The gated and ungated formulations are indistinguishable
($+0.0014$, 3/7 seeds, $p_{\\mathrm{FDR}} = 0.713$), with any difference bounded
at $0.89\\%$ of baseline --- the tightest bound in the study. The gate can be
removed without cost.""",
    'RQ1 gating')

# ---------------------------------------------------------------- RQ2
sub("""\\emph{Accuracy.} E4 against E3 is $+0.0051$ QWK ($[-0.0038, +0.0148]$, 2/3
seeds, $p_{\\mathrm{FDR}} = 0.570$). The between-seed standard deviation
($0.0258$) is five times the effect.""",
    """\\emph{Accuracy.} E4 against E3 is $+0.0020$ QWK ($[-0.0043, +0.0089]$, 4/7
seeds, $p_{\\mathrm{FDR}} = 0.688$, $d = 0.12$), with any benefit bounded at
$1.22\\%$ of baseline. The seven-seed extension moved this comparison
\\emph{away} from significance, not toward it: at three seeds it stood at
$+0.0051$ on 2/3 seeds.""",
    'RQ2 accuracy')

sub("""annotated sequence by $-0.0069 \\pm 0.0304$ on 2/3 seeds --- indistinguishable""",
    """annotated sequence by $-0.0069 \\pm 0.0304$ on 2/3 seeds (this probe was run on
seeds 42--44 only) --- indistinguishable""",
    'RQ2 robustness note')

# ---------------------------------------------------------------- RQ3
sub("""clinically sensible. But they do not improve grading ($+0.0010$ QWK, 1/3 seeds)""",
    """clinically sensible. But they do not improve grading ($+0.0053$ QWK, 5/7 seeds,
$p_{\\mathrm{FDR}} = 0.131$, bounded at $1.55\\%$ of baseline)""",
    'RQ3 benefit')

# ---------------------------------------------------------------- RQ5
sub("""and cost-sensitive head improves QWK by $+0.0099$ ($[+0.0017, +0.0186]$) on 3/3""",
    """and cost-sensitive head improves QWK by $+0.0082$ ($[+0.0025, +0.0143]$,
$p_{\\mathrm{FDR}} = 0.009$, $d = 1.97$ --- the largest standardised effect in the
study) on 7/7""",
    'RQ5 effect')

# ------------------------------------------- label the 3-seed probes as such
sub("""\\begin{center}
\\begin{tabular}{lcc}
\\toprule
Step & $\\Delta$ reliance & Seeds lower \\\\
\\midrule""",
    """The input ablation was run on seeds 42--44, before the campaign was extended,
and its figures are three-seed.

\\begin{center}
\\begin{tabular}{lcc}
\\toprule
Step & $\\Delta$ reliance & Seeds lower \\\\
\\midrule""",
    'input ablation seed note')

io.open(P, 'w', encoding='utf-8').write(txt)
print('RQ sections updated: %d edits' % N)
