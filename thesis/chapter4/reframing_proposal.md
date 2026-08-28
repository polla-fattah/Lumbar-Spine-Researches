# Reframing proposal: what to change in Chapters 1-3, and what not to

Written 2026-08-27, after the 3-seed campaign, the input ablation and the
attribution study. Addressed to the question "can we go back and tweak the
earlier chapters to save the day".

## The short answer

Yes -- but the change needed is smaller than it feels, and the honest version is
a stronger thesis than the original plan was.

Nothing about the *findings* needs rescuing. What needs changing is that
Chapters 1-3 sell three architectural components as improvements, and the
evidence does not support that sale. The fix is to sell the **evaluation**
instead, which is the part that actually came out well.

## The line, stated plainly

**Legitimate:** rewriting how a contribution is *described* -- from "we propose
X, which improves grading" to "we propose X and test it against a matched
control". A thesis is finalised after its results; describing accurately what a
study establishes is normal practice, not concealment.

**Not legitimate:** changing the hypotheses, the predicted directions, or the
pre-specified comparison list so the results appear to confirm predictions. That
is HARKing. It is also the risky option rather than the safe one: the git
history records when every comparison was specified, and "when did you decide
E6_shuffled was the decisive test?" is a question an examiner can and does ask.
A thesis that survives that question is worth more than one that needs it not to
be asked.

## Why Chapter 3 does not actually need much

Chapter 3 is already written falsificationist. It commits, in its own words, to

> disagreement is reported rather than rationalised post hoc

and

> every claimed contribution requires an ablation

That is the reason these results are credible rather than embarrassing. The
methodology chapter anticipated the possibility of nulls and pre-committed to
reporting them. **Chapter 3 is the asset here, not the problem.** The required
edits are to Chapter 1's contribution claims, not to the methodology.

## Proposed contribution statements

Current framing (approximate):

1. ACSSL cross-sequence self-supervised pretraining improves grading.
2. Disease-conditioned routing improves grading.
3. A heterogeneous disease-anatomy graph improves grading.

Proposed:

1. **An anatomy-aware multi-sequence architecture for lumbar stenosis grading**
   that outperforms a single-sequence baseline by +0.0172 QWK (95% CI
   [+0.0064, +0.0285], 3/3 seeds, FDR-corrected). Reproducible, verified,
   released.

2. **A controlled ablation protocol for anatomical priors in medical imaging**,
   in which every claimed mechanism is tested against a matched control that
   preserves capacity: a degree-preserving edge shuffle for topology, a
   router-free fixed-fusion arm for routing, an architecture-matched untrained
   floor for attribution, and a label-shuffled negative control for the pipeline
   itself. This is the contribution most of the field omits.

3. **Evidence that anatomical structural priors do not improve grading at this
   data scale, and a mechanism for why.** Grad-CAM shows the convolutional
   encoder already concentrates 2.4x above chance on the annotated target before
   any prior is added, leaving the priors little to contribute. Controlled input
   ablation shows the routing gate tracks the dataset's annotation structure
   rather than creating any causal dependence.

Note that (3) is a *finding*, not a failure, and it generalises beyond this
architecture. It is the part most likely to be citable.

## What must be reported as it fell

- **Contribution II (routing)** fails on both axes Chapter 3 names. Allocation:
  the gate pattern replicates 15/15, but a router-free model shows the same
  sequence dependence. Intervention: +0.0010 QWK, 1/3 seeds. The effect is
  20x smaller than seed-to-seed noise; roughly 3,500 training runs would be
  needed to distinguish it from zero.
- **Contribution I (ACSSL)** fails on three separate axes -- accuracy (+0.0051,
  2/3 seeds), cross-sequence robustness (input ablation, -0.0069, within noise),
  and attention concentration (the only step below E0).
- **Contribution III splits.** Typed heterogeneous edges beat a homogeneous
  graph: +0.0123 QWK, 3/3 seeds -- that part holds. Anatomically correct
  topology does not beat a degree-preserving shuffle: +0.0051, 2/3 seeds. So
  relational structure helps and the anatomy inside it does not, which is a
  sharper and more interesting claim than the original.

Do not drop E2 or E4 from the ladder, do not narrow the pre-specified
comparisons, and do not report the gate-weight replication without the E1
control beside it.

## The honest headline

The step decomposition is worth putting in Chapter 4 exactly as it is:

| Step | delta QWK | seeds + | running total |
| :-- | --: | :-: | --: |
| multi-sequence | -0.0055 | 2/3 | -0.0055 |
| C-II routing | +0.0010 | 1/3 | -0.0045 |
| modality dropout | +0.0032 | 2/3 | -0.0013 |
| C-I ACSSL | +0.0051 | 2/3 | +0.0038 |
| graph (generic) | -0.0088 | 1/3 | -0.0050 |
| C-III typed edges | +0.0123 | 3/3 | +0.0073 |
| ordinal + cost head | +0.0099 | 3/3 | **+0.0172** |

After six of seven steps the system is *below* baseline. The entire gain arrives
in the last two. Stating that plainly is far stronger than obscuring it, because
it is exactly the kind of thing an ablation study exists to reveal, and a reader
who works it out independently will trust nothing else in the chapter.

## Methodological findings worth their own section

Three ways these results could have been reported wrongly, all caught and all
fixed. This section will do more for the viva than any accuracy number.

1. **Per-seed bootstrap intervals understate variance.** Resampling patients with
   the trained model fixed excludes training stochasticity. E4 vs E3 came out
   +0.0270 (p = 0.000) on one seed and -0.0234 (p = 0.000) on another --
   opposite signs, both "significant". Any claim could have been supported by
   choosing a seed. Fixed by averaging seeds inside each bootstrap replicate.

2. **A mechanism check without a control read as proof.** E2 showed 5/5
   agreement between routing weights and intervention, with effects an order of
   magnitude larger than any ladder delta. E1, which has no router at all,
   scored the same -- the pattern belongs to the dataset's annotation structure.

3. **An attribution probe measured the wrong encoder.** Hooking `encoders[0]`
   read the sagittal T1 encoder's attention on subarticular targets graded from
   axial T2, penalising every multi-sequence rung and reporting E1 - E0 = -0.036
   (1/3 seeds). Hooking all encoders and selecting by annotated slot gives
   +0.089 (3/3) -- the opposite sign.

All three errors pointed toward the conclusion already in hand. That is worth
saying explicitly.

## What is out of scope

Predictive lesion localisation is a separate paper, not a thesis chapter. It
requires new methodology, new validation and realistically 2-3 months of writing
on top of the experiments. It reuses this infrastructure, so it will be fast
after submission, and the Rizgary cohort with its reports is the natural
external-validation partner for it.
