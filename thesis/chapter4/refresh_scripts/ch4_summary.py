"""Refresh Chapter 4's summary-of-answers table to seven seeds."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
txt = io.open(P, encoding='utf-8').read()

OLD = r"""RQ1 & Partly & Typed edges $+0.0123$, 3/3 seeds. Anatomical topology does not
beat a degree-preserving shuffle ($+0.0051$, 2/3). \\
RQ2 & No & $+0.0051$, 2/3 seeds; no robustness benefit; attention below
baseline. Rejected on three axes. \\
RQ3 & Mechanism yes, benefit no & Allocation replicates 15/15 but a router-free
model matches it under intervention. $+0.0010$ QWK, 1/3 seeds. \\
RQ4 & Not executed & Cohort preparation complete; blocked on reader adjudication
and de-identification. \\
RQ5 & Yes & $+0.0099$, 3/3 seeds, smallest variance in the study. Severe recall
$62.7\% \rightarrow 65.0\%$. \\
\midrule
System & Yes & $+0.0172$ QWK $[+0.0064, +0.0285]$, 3/3 seeds, survives FDR. \\"""

NEW = r"""RQ1 & Partly & Typed edges $+0.0093$, \textbf{7/7 seeds},
$p_{\mathrm{FDR}} = 0.009$. Anatomical topology does not beat a
degree-preserving shuffle ($+0.0020$, 4/7), bounded at $1.05\%$ of baseline. \\
RQ2 & No & $+0.0020$, 4/7 seeds, bounded at $1.22\%$; no robustness benefit;
attention below baseline. Rejected on three axes, and weakened by the
seven-seed extension. \\
RQ3 & Mechanism yes, benefit no & Allocation replicates 15/15 but a router-free
model matches it under intervention. $+0.0053$ QWK, 5/7 seeds, bounded at
$1.55\%$. \\
RQ4 & Not executed & Cohort preparation complete; blocked on reader
adjudication, de-identification, and the absence of localisation coordinates. \\
RQ5 & Yes & $+0.0082$, \textbf{7/7 seeds}, $p_{\mathrm{FDR}} = 0.009$, $d = 1.97$
--- the largest standardised effect in the study. Severe$\rightarrow$Normal
errors fall $5.7\% \rightarrow 3.8\%$. \\
\midrule
System & Yes & $+0.0177$ QWK $[+0.0097, +0.0260]$, \textbf{7/7 seeds},
$p_{\mathrm{FDR}} < 0.001$. \\"""

assert txt.count(OLD) == 1, 'summary anchor'
txt = txt.replace(OLD, NEW)

# the closing paragraph gains the calibration caveat, which is a real negative
OLD2 = r"""or disease-conditioned routing."""
NEW2 = r"""or disease-conditioned routing.

Two qualifications belong with that summary. The improvement is bounded by a
reference standard on which expert readers agree at $\kappa$ between $0.49$ and
$0.73$, so its ceiling is set by the labels rather than by the architecture. And
the accumulating ladder improves agreement without improving the reliability of
its probabilities: calibrated ECE is worse at E7 than at E0."""
assert txt.count(OLD2) == 1, 'closing anchor'
txt = txt.replace(OLD2, NEW2)

io.open(P, 'w', encoding='utf-8').write(txt)
print('summary table and closing paragraph updated')
