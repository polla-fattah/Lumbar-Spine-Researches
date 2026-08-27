"""Refresh Chapter 4 to seven seeds and add the new analysis sections.

Tables are replaced by locating their own \\label and rewriting the whole
table environment, which is robust to whitespace. Prose uses short anchors.
"""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
txt = io.open(P, encoding='utf-8').read()
NT, NP = 0, 0


def replace_table(label, new_lines):
    """Rewrite the table environment containing \\label{label}."""
    global txt, NT
    lines = txt.split('\n')
    lab = next(i for i, l in enumerate(lines) if 'label{%s}' % label in l)
    start = max(i for i in range(lab) if lines[i].startswith(r'\begin{table}'))
    end = next(i for i in range(lab, len(lines)) if lines[i].startswith(r'\end{table}'))
    txt = '\n'.join(lines[:start] + new_lines + lines[end + 1:])
    NT += 1


def prose(old, new, why):
    global txt, NP
    assert txt.count(old) == 1, 'prose anchor failed: ' + why
    txt = txt.replace(old, new)
    NP += 1


# ------------------------------------------------------------------ tab:steps
replace_table('tab:steps', [
    r'\begin{table}[htbp]',
    r'\centering',
    r'\caption{Step-by-step decomposition from E0 to E7 over seven seeds.',
    r'\enquote{Seeds $+$} counts the seeds on which the step improved QWK.}',
    r'\label{tab:steps}',
    r'\begin{tabular}{lccr}',
    r'\toprule',
    r'Step & $\Delta$ QWK & Seeds $+$ & Cumulative \\',
    r'\midrule',
    r'Multi-sequence input & $-0.0024$ & 4/7 & $-0.0024$ \\',
    r'Disease-conditioned routing & $+0.0053$ & 5/7 & $+0.0028$ \\',
    r'Modality dropout & $-0.0026$ & 4/7 & $+0.0003$ \\',
    r'Anatomical cross-sequence SSL & $+0.0020$ & 4/7 & $+0.0023$ \\',
    r'Homogeneous graph & $-0.0021$ & 4/7 & $+0.0002$ \\',
    r'\midrule',
    r'Typed heterogeneous edges & $+0.0093$ & \textbf{7/7} & $+0.0094$ \\',
    r'Ordinal and cost-sensitive head & $+0.0082$ & \textbf{7/7} & $\mathbf{+0.0177}$ \\',
    r'\bottomrule',
    r'\end{tabular}',
    r'\end{table}',
])

prose('Table~\\ref{tab:steps} decomposes the $+0.0172$ into its seven successive steps.',
      'Table~\\ref{tab:steps} decomposes the $+0.0177$ into its seven successive\n'
      'steps.', 'steps lead')

prose("""After six of the seven steps the system sits \\emph{below} the baseline it began
from. The entire improvement arrives in the final two steps, and those two are
the only steps that improve on all three seeds.""",
      """Through the first five steps the accumulated system goes nowhere. It moves
within $\\pm 0.003$~QWK of the baseline it began from and ends those five steps
$+0.0002$ ahead, and not one of them improves on more than five of seven seeds.
\\textbf{The entire gain arrives in the final two steps, and those two are the
only steps in the ladder that improve on every seed.}""",
      'steps prose')

# ------------------------------------------------------------------ tab:power
replace_table('tab:power', [
    r'\begin{table}[htbp]',
    r'\centering',
    r'\caption{Effect size and detectability over seven seeds. Cohen\'s $d$ is',
    r'computed on the paired across-seed differences. \enquote{Seeds required} is',
    r'for 80\% power at the observed effect size and between-seed variance.}',
    r'\label{tab:power}',
    r'\begin{tabular}{lcrr}',
    r'\toprule',
    r'Effect & $\Delta$ QWK & Cohen\'s $d$ & Seeds required \\',
    r'\midrule',
    r'Ordinal and cost-sensitive head (RQ5) & $+0.0082$ & $\mathbf{1.97}$ & 3 \\',
    r'Full system vs baseline & $+0.0177$ & $\mathbf{1.91}$ & 3 \\',
    r'Typed heterogeneous edges (RQ1) & $+0.0093$ & $\mathbf{1.06}$ & 7 \\',
    r'\midrule',
    r'Disease-conditioned routing (RQ3) & $+0.0053$ & $0.39$ & 52 \\',
    r'Anatomical topology vs shuffle (RQ1) & $+0.0020$ & $0.20$ & 205 \\',
    r'Modality dropout & $-0.0026$ & $-0.13$ & 442 \\',
    r'Cross-sequence self-supervision (RQ2) & $+0.0020$ & $0.12$ & 545 \\',
    r'Gated residual & $+0.0014$ & $0.07$ & 1{,}615 \\',
    r'Relational message passing & $+0.0002$ & $0.01$ & 65{,}489 \\',
    r'\bottomrule',
    r'\end{tabular}',
    r'\end{table}',
])

io.open(P, 'w', encoding='utf-8').write(txt)
print('tables replaced: %d   prose edits: %d' % (NT, NP))
