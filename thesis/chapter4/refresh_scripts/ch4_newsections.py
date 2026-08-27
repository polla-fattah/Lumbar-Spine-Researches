"""Insert the equivalence-bound, clinical-error and calibration subsections."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
txt = io.open(P, encoding='utf-8').read()

ANCHOR = r'''% ===========================================================================
\section{RQ1 --- Relational Disease Modelling}'''
assert txt.count(ANCHOR) == 1, 'RQ1 anchor'

NEW = r'''\subsection{What the Nulls Establish}
\label{sec:results-equivalence}

Reporting a comparison as \enquote{not significant} states only that an effect
was not detected. It is the weakest available form of a null, and it invites the
reader to supply the explanation that the study was too small. The paired
interval already bounds the effect, and stating that bound converts an absence
into a measurement.

Table~\ref{tab:bounds} gives, for each comparison that did not separate, the far
edge of its 95\% interval: the largest effect still compatible with the data.

\begin{table}[htbp]
\centering
\caption{Equivalence bounds for the comparisons that did not separate. Each
figure is the largest effect compatible with the 95\% interval, expressed in QWK
and as a percentage of the E0 baseline of $0.7270$.}
\label{tab:bounds}
\begin{tabular}{lrr}
\toprule
Comparison & Effect is at most & As \% of baseline \\
\midrule
Gated residual & $0.0064$ & $0.89\%$ \\
Relational message passing & $0.0074$ & $1.02\%$ \\
Anatomical topology vs shuffle (RQ1) & $0.0076$ & $1.05\%$ \\
Cross-sequence self-supervision (RQ2) & $0.0089$ & $1.22\%$ \\
Modality dropout & $0.0091$ & $1.25\%$ \\
Disease-conditioned routing (RQ3) & $0.0112$ & $1.55\%$ \\
\bottomrule
\end{tabular}
\end{table}

The claims available are therefore considerably stronger than the absence of a
significant result. Anatomically correct graph topology contributes at most
$1.05\%$ of baseline performance over a degree-preserving random shuffle.
Anatomically aligned cross-sequence self-supervision contributes at most
$1.22\%$ over the same architecture without it. Disease-conditioned routing
contributes at most $1.55\%$ over fixed fusion.

Set against the reference standard, these bounds are small in a way that matters.
Section~\ref{sec:lr-reliability} reports inter-reader $\kappa$ between $0.49$ and
$0.73$ depending on compartment. An effect bounded below $1.6\%$ of baseline is
not merely undetectable in this study; it is below the level at which the
reference standard itself could adjudicate the question.

\subsection{The Seven-Seed Extension}
\label{sec:results-sevenseed}

The campaign was extended from three seeds to seven, and the extension is
reported rather than absorbed, because it changed two verdicts.

Typed heterogeneous edges moved from $+0.0123$ on 3/3 seeds with
$p_{\mathrm{FDR}} = 0.054$ --- narrowly missing correction --- to $+0.0093$ on
7/7 seeds with $p_{\mathrm{FDR}} = 0.009$. The point estimate fell while the
between-seed standard deviation fell further, and the comparison crossed the
threshold. The ordinal head moved the same way, from $0.054$ to $0.009$.

Anatomical topology moved in the opposite direction: from $+0.0051$ on 2/3 seeds
to $+0.0020$ on 4/7. So did cross-sequence self-supervision, from $+0.0051$ on
2/3 to $+0.0020$ on 4/7.

That divergence is the reason the extension is worth reporting. The same four
additional runs that promoted two comparisons to significance made two others
weaker. Insufficient power is therefore not available as a blanket explanation
for the nulls in this chapter: the instrument demonstrably resolved effects at
this scale, and the effects it did not resolve moved away from significance as
evidence accumulated rather than toward it.

\subsection{Clinical Error Structure}
\label{sec:results-errors}

Aggregate agreement conceals the errors that matter clinically. A
Severe$\rightarrow$Normal/Mild confusion may withhold treatment from a patient
who needs it, and the cost matrix of Section~\ref{sec:method-cost} was chosen to
suppress that direction specifically.

\begin{table}[htbp]
\centering
\caption{Clinical error structure over seven seeds. \enquote{Distance $\geq 2$}
is the rate of predictions two or more grades from the reference.}
\label{tab:errors}
\begin{tabular}{lrrr}
\toprule
Configuration & Severe recall & Severe $\rightarrow$ Normal & Distance $\geq 2$ \\
\midrule
E0 single sequence & 61.1\% & 5.7\% & 0.526\% \\
E1 multi-sequence & 61.1\% & 4.9\% & 0.500\% \\
E2 + disease routing & 60.7\% & 4.7\% & 0.414\% \\
E3 + modality dropout & 61.4\% & 4.6\% & 0.420\% \\
E4 + ACSSL & 58.8\% & 4.0\% & 0.453\% \\
E5 + homogeneous graph & 59.0\% & 4.1\% & 0.389\% \\
E6 + typed graph & 62.9\% & 4.1\% & 0.375\% \\
\quad E6 shuffled edges & 59.3\% & 3.7\% & 0.330\% \\
\quad E6 ungated residual & \textbf{65.1\%} & 4.3\% & 0.500\% \\
E7 + ordinal, cost-sensitive & 63.1\% & \textbf{3.8\%} & \textbf{0.344\%} \\
\bottomrule
\end{tabular}
\end{table}

Severe$\rightarrow$Normal errors fall from $5.7\%$ at E0 to $3.8\%$ at E7, a
relative reduction of a third, while recall on Severe targets rises from
$61.1\%$ to $63.1\%$. Distant errors fall by a comparable margin, from $0.526\%$
to $0.344\%$. The system does not purchase aggregate agreement by trading away
the errors clinicians care most about; both move in the desired direction
together.

One complication should be stated rather than smoothed over. The ungated variant
achieves the highest Severe recall of any configuration at $65.1\%$, and
simultaneously carries the joint-highest rate of distant errors at $0.500\%$
against E7's $0.344\%$. Greater sensitivity bought with more badly misplaced
predictions is precisely the trade the cost matrix exists to refuse, and E7
makes it in the intended direction.

\subsection{Calibration}
\label{sec:results-calibration}

The expected calibration error recorded for each run is the \emph{uncalibrated}
test value; temperature scaling is fitted on the validation partition and its
test metrics are stored separately. The distinction is material, because the
uncalibrated figures alone would suggest the ladder becomes progressively worse
calibrated, and the correction the protocol actually applies reverses that.

\begin{table}[htbp]
\centering
\caption{Expected calibration error before and after temperature scaling, and
the fitted temperature, over seven seeds.}
\label{tab:calibration}
\begin{tabular}{lrrr}
\toprule
Configuration & ECE uncalibrated & ECE calibrated & Temperature \\
\midrule
E0 single sequence & $0.0293$ & $\mathbf{0.0130}$ & $1.161$ \\
E1 multi-sequence & $0.0214$ & $0.0129$ & $1.131$ \\
E2 + disease routing & $0.0428$ & $0.0168$ & $1.601$ \\
E3 + modality dropout & $0.0326$ & $0.0145$ & $1.200$ \\
E4 + ACSSL & $0.0266$ & $0.0110$ & $1.187$ \\
E5 + homogeneous graph & $0.1024$ & $0.0397$ & $2.019$ \\
E6 + typed graph & $0.0426$ & $0.0209$ & $1.422$ \\
E7 + ordinal, cost-sensitive & $0.0508$ & $0.0245$ & $1.306$ \\
\bottomrule
\end{tabular}
\end{table}

Temperature scaling roughly halves ECE at every rung, and every fitted
temperature exceeds $1$, so every configuration is overconfident before
correction.

Two observations run against the system and are reported for that reason. E5,
the homogeneous graph, is by a wide margin the worst calibrated configuration at
$0.1024$ uncalibrated with a fitted temperature of $2.019$; it is also the rung
that fails to improve accuracy, and its overconfidence is a second symptom of
the same failure. And the accumulating ladder does not improve calibration: E7
at $0.0245$ is worse than E0 at $0.0130$, so the gains in agreement come with
less reliable probabilities. RQ5 asked whether calibrated uncertainty could
support selective prediction. On this evidence the agreement half of that
question is answered affirmatively and the calibration half is not.

'''

txt = txt.replace(ANCHOR, NEW + ANCHOR)
io.open(P, 'w', encoding='utf-8').write(txt)
print('three subsections inserted before RQ1')
