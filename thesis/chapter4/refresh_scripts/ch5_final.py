"""Final Chapter 5 pass: power limitation, per-condition seed note, calibration."""
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


# ---- the limitation on power, rewritten now the extension has happened ---- #
sub("""of training seeds required to detect it: one for the full system and for the
ordinal head, ten for typed edges, but 216 for cross-sequence self-supervision
and 3{,}467 for routing. The last is roughly three years of continuous
computation on the hardware used. Those two components are not merely unproven
here; effects of the size observed are not establishable at any plausible scale,
and would carry no clinical meaning if they were.""",
    """of training seeds required to detect it: three for the full system and for the
ordinal head, seven for typed edges, but $205$ for anatomical topology and $545$
for cross-sequence self-supervision. Those components are not merely unproven
here; effects of the size observed are not establishable at any plausible scale,
and the equivalence bounds show they would carry no clinical meaning if they
were.

The word \\emph{underpowered} should nevertheless be used carefully in this
chapter. The campaign was extended from three seeds to seven specifically to
test that explanation, and the extension carried two comparisons across the
corrected threshold while moving two others further from it. A study genuinely
starved of power does not resolve half its comparisons and weaken the other
half; it produces a spread of intermediate effects. Cohen's $d$ here separates
into $1.06$--$1.97$ for the three significant comparisons and below $0.4$ for
everything else, with nothing in between.""",
    'power limitation')

# ---- the per-condition table is genuinely three-seed ---------------------- #
sub("""Reader $\\kappa$ from Lurie et al.; model QWK averaged over three seeds. The two""",
    """Reader $\\kappa$ from Lurie et al.; model QWK averaged over seeds 42--44, this
analysis having been run before the campaign was extended. The two""",
    'per-condition seed note')

# ---- routing figure in the RQ3 discussion --------------------------------- #
sub("""gives $-0.0010 \\pm 0.0382$ across seeds, indistinguishable from zero.""",
    """gives $-0.0010 \\pm 0.0382$ across seeds 42--44, indistinguishable from zero.
The grading effect over the full seven seeds is $+0.0053$, bounded by its
interval at $1.55\\%$ of baseline.""",
    'routing figure')

# ---- calibration belongs in the limitations ------------------------------- #
sub("""\\emph{No clinical outcome is measured.}""",
    """\\emph{Calibration does not improve with the ladder.} Temperature scaling roughly
halves expected calibration error at every rung, but the calibrated figure at E7
($0.0245$) is worse than at E0 ($0.0130$). Agreement improves as components
accumulate; the reliability of the probabilities does not. RQ5 asked whether
calibrated uncertainty could support selective prediction, and on this evidence
the agreement half of that question is answered and the calibration half is not.
The homogeneous graph is a separate concern: at $0.1024$ uncalibrated with a
fitted temperature of $2.019$ it is by a wide margin the most overconfident
configuration, and it is also the rung that fails to improve accuracy.

\\emph{No clinical outcome is measured.}""",
    'calibration limitation')

io.open(P, 'w', encoding='utf-8').write(txt)
print('Chapter 5 final pass: %d edits' % N)
