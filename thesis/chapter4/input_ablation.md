# Controlled input ablation (Chapter 3, sec:method-router-interpretation)

Run 2026-08-26, inference only, on the frozen test split against the campaign
checkpoints. Script: `implementation/amog_input_ablation.py`.
Raw output: `data/reports/input_ablation_E{1,2,3,4}.{json,csv}`.

## Why this experiment exists

Chapter 3 commits to it explicitly, and warns against the shortcut:

> The gate weights are model allocations, not causal estimates of sequence
> importance. A high axial T2 weight does not prove that axial T2 caused a
> correct decision. [...] Second, controlled input ablation tests whether
> removing the sequence with high routing weight causes a greater performance
> loss than removing a low-weight sequence. Agreement between learned allocation
> and intervention strengthens the interpretation; disagreement is reported
> rather than rationalised post hoc.

The main campaign reported only the first check -- aggregate gate weights by
target, which reproduced foraminal->sag_T1, canal->sag_T2 and
subarticular->ax_T2 in 15/15 runs. That is the correlation the chapter
disclaims. This is the intervention.

## Method

For each modality the availability mask is forced to zero -- the same channel
the fusion and router already consult, so the sequence is *absent* rather than
zeroed-but-present -- and the per-condition QWK is recompared with the
unablated baseline. `drop = baseline - ablated`; larger means greater
dependence. Targets whose only sequence was the ablated one are excluded, since
they would score the class prior and their number differs per modality.

All three sequences are never ablated together: with no evidence at all the
number measures the head's prior, not any sequence's contribution.

## Result 1 -- the system depends on the radiologically correct sequence

Agreement with the Chapter 3 expectation, per seed:

| Rung | seed 42 | seed 43 | seed 44 |
| :-- | :-: | :-: | :-: |
| E1 fixed fusion | 5/5 | 4/5 | 5/5 |
| E2 router | 5/5 | 5/5 | 5/5 |
| E3 + modality dropout | 5/5 | 5/5 | 5/5 |
| E4 + ACSSL | 5/5 | 5/5 | 5/5 |

The effects are large -- 0.06 to 0.35 QWK, an order of magnitude above any rung
difference in the ladder (0.005-0.017). Removing the sequence a condition is
graded from is catastrophic for that condition and near-neutral for the others;
several off-target ablations are slightly *negative*, i.e. the model does
marginally better without them.

This is a genuine clinical-validity result and should be reported as one: the
network's sequence dependence matches radiological practice, and it was not
told to behave that way.

## Result 2 -- but the router did not cause it

E1 has no router. It fuses the three sequences with fixed weights, and it scores
the same 5/5 pattern with drops as large or larger. The dependence is a property
of the data: in LumbarDISC each condition is *annotated* on one particular
sequence, so ablating that sequence removes the only crop actually centred on
the pathology. Any model would suffer.

Mean reliance on the annotated sequence (QWK lost when it is removed), by seed:

| seed | E1 | E2 | E3 | E4 |
| :-: | --: | --: | --: | --: |
| 42 | 0.2011 | 0.1601 | 0.1362 | 0.1075 |
| 43 | 0.1396 | 0.1746 | 0.1456 | 0.1257 |
| 44 | 0.2163 | 0.2192 | 0.0957 | 0.1235 |

| Step | delta reliance | seeds lower |
| :-- | --: | :-: |
| E2 - E1, add the router | -0.0010 +- 0.0382 | 1/3 |
| E3 - E2, add modality dropout | **-0.0588 +- 0.0561** | **3/3** |
| E4 - E3, add ACSSL | -0.0069 +- 0.0304 | 2/3 |

**The disease-conditioned router changes sequence reliance by essentially zero.**
Its gate weights track the annotation structure of the dataset without creating
any causal dependence beyond what fixed fusion already has. Combined with the
null accuracy result (E2 vs E1, +0.0010 QWK, 1/3 seeds), Contribution II is not
supported on either axis -- allocation or intervention. Chapter 3 requires this
be reported rather than rationalised, and it is.

**Contribution I is likewise unsupported on a second axis.** Cross-sequence SSL
is designed to teach the encoders that one anatomy appears in all three
sequences, which should show up precisely here as reduced dependence on any one
of them. It does not (-0.0069, within noise, 2/3 seeds).

**The robustness that does exist comes from modality dropout** -- a standard
regulariser, not a claimed contribution. It cuts reliance on the annotated
sequence by roughly a third, consistently across all three seeds. That is worth
stating plainly: the pipeline degrades more gracefully when a sequence is
missing, which matters clinically because not every patient receives all three,
but the credit belongs to E3, not to Contributions I or II.

## What this changes

A single-arm version of this experiment -- E2 alone, 5/5, large effects -- would
have read as strong causal support for Contribution II and would have been
wrong. The E1 control is what makes the result interpretable, and it is the
reason Chapter 3's insistence on intervention over allocation was correct.

## Caveats

- Ablation is at the mask, so the encoder still runs on a sequence that is then
  excluded from fusion. This measures the fusion/routing stage's dependence, not
  the encoder's.
- Per-condition QWK on a single test split; no bootstrap interval is attached to
  a single cell. The seed-level aggregate above is the inferential quantity.
- E5-E7 are not covered: `forward_target` is reached through `forward_graph`
  there with a different batch layout, and the routing claim is cleanest to test
  at E2 with the graph out of the path.
