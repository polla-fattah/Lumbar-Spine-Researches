"""Fix the escaped apostrophe and rewrite the power-section prose."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
txt = io.open(P, encoding='utf-8').read()
N = 0

# \' is the LaTeX acute accent, so "Cohen\'s" would typeset as Cohen's with an
# accented s. A plain apostrophe is wanted.
BS = chr(92)
n = txt.count(BS + "'s")
txt = txt.replace(BS + "'s", "'s")
print("apostrophes fixed: %d" % n)


def prose(old, new, why):
    global txt, N
    assert txt.count(old) == 1, 'anchor failed: ' + why
    txt = txt.replace(old, new)
    N += 1


prose("""\\subsection{Statistical Power}
\\label{sec:results-power}

A null result is uninterpretable without knowing what the study could have
detected. Table~\\ref{tab:power} converts each observed effect and its
between-seed standard deviation into the number of training seeds that would be
required to detect an effect of that size at 80\\% power.""",
      """\\subsection{Effect Size and Statistical Power}
\\label{sec:results-power}

A p-value confounds effect size with sample size, and a null result is
uninterpretable without knowing what the study could have detected.
Table~\\ref{tab:power} therefore reports Cohen's $d$ on the paired across-seed
differences alongside the number of training seeds that would be required to
detect an effect of the observed size at 80\\% power.""",
      'power lead')

prose("""The distinction this table draws is important and is carried through the rest of
the chapter. The ladder is not an instrument that reports nothing everywhere: two
effects are detectable with a single seed and a third with ten. Where it reports
nothing, that is a statement about the effect, not about the instrument.

For disease-conditioned routing in particular, roughly three and a half thousand
training runs would be needed to separate the observed effect from zero. At the
measured $22$~minutes per run this is approximately three years of continuous
computation. The effect is not merely unproven; it is unprovable at any
plausible scale, and a $+0.0010$ improvement on a $0.7276$ baseline would carry
no clinical meaning if it were established.""",
      """The table separates into two groups with nothing in between. Three effects are
large by any convention, $d$ between $1.06$ and $1.97$, and all three are the
comparisons that survive correction. Everything else is $d < 0.4$. That gap
matters: a study genuinely starved of power would show a spread of intermediate
effects rather than a clean division, and would not resolve any comparison at
three seeds.

The ladder is therefore not an instrument that reports nothing everywhere. Two
effects are detectable with a single seed and a third with seven, which is what
the campaign used. Where it reports nothing, that is a statement about the
effect rather than about the instrument.

The largest standardised effect in the study is the ordinal and cost-sensitive
head at $d = 1.97$, exceeding the full-system comparison it forms part of. Its
between-seed standard deviation is $0.0042$, the smallest of any comparison, so
its modest raw difference is also the most reliably reproduced.

These figures supersede a three-seed version of the same table, and the
differences are instructive. Three-seed variance estimates are themselves noisy:
routing moved from an estimated $3{,}467$ seeds to $52$, and cross-sequence
self-supervision from $216$ to $545$. The ordering is stable and the two groups
are unchanged, but individual requirements should be read as order-of-magnitude
guidance rather than as precise targets.""",
      'power prose')

io.open(P, 'w', encoding='utf-8').write(txt)
print('prose edits: %d' % N)
