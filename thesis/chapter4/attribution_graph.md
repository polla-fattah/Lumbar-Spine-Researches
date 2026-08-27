# Attribution on the graph rungs E5-E7

Run 2026-08-27. Script: `implementation/amog_attribution_graph.py`.
Output: `data/reports/attribution_E{5,6,7}_layer3.json`.

## Why this was needed

`attribution.md` measured concentration on E0-E4 only, because the graph rungs
reach `forward_target` through `forward_graph` with a different batch layout.
Chapter 4 recorded that as a limitation: the mechanism offered for the null
results -- that the encoder already localises -- was **not measured on the final
system**. This closes that gap, and in doing so it corrected the probe twice
more.

## Result

| Rung | CAM mass in disc | Untrained floor | Gap |
| :-- | --: | --: | --: |
| E5 homogeneous graph | 0.341 +- 0.009 | 0.178 | +0.163 |
| E6 typed graph | 0.428 +- 0.015 | 0.177 | +0.251 |
| E7 + ordinal, cost-sensitive | 0.171 +- 0.027 | 0.141 | +0.030 |

Chance, the disc area, is 0.197. E5 and E6 concentrate well above their floors,
in the same band as the target rungs (0.46-0.58). **E7 appears not to.** That
number is real but it does not mean what it looks like, and Section 3 below is
the important part of this note.

## Two probe defects found and fixed first

### Summing node logits smears gradient across the graph

The obvious implementation backpropagates the sum of all node logits and reads
each node's map from its own row. That is valid only when nodes are independent.
The GNN couples them, so the gradient arriving at node k's encoder is the sum
over every node k's features reach, and the map answers "what in this image moved
the whole graph" rather than "what made THIS target look severe".

Measured on E6, three canal nodes:

| Node | Summed | Single-node | Difference |
| :-- | --: | --: | --: |
| 2 | 0.442 | 0.534 | +0.092 |
| 7 | 0.185 | 0.453 | +0.269 |
| 12 | 0.287 | 0.445 | +0.158 |

Mean understatement 0.173. Reported from the summed version, the graph rungs
looked far more diffuse than the target rungs. The fix is one backward pass per
node position, which costs 25x and is the only version measuring the intended
quantity.

### The ordinal head has no argmax

A categorical head emits one logit per class and argmax is the prediction. E7's
head emits cumulative logits, P(y>0) and P(y>1); argmax over those selects
whichever threshold logit is larger, which is not a class choice and carries no
interpretation. The sum of the cumulative logits is monotone in predicted grade
and is used instead.

This choice was tested rather than assumed. Explaining the sum, either threshold
alone, or the threshold the model actually crossed gives means of 0.026, 0.026,
0.074 and 0.026 on a fixed node set -- a spread of 0.048. The result is not an
artefact of the scalar chosen.

Two further candidate explanations were tested and rejected. Degenerate maps: a
Grad-CAM is empty when the gradient-weighted activation sum is negative
everywhere, and the code substitutes a uniform map, which scores exactly chance.
Counted directly, E7 produces **0%** empty maps (E5 1%, E6 0%), so the pooled
figure is not diluted by fallbacks.

## The result that explains E7

Splitting concentration by the target's true grade:

| Grade | n | E6 | E7 |
| :-- | --: | --: | --: |
| Normal/Mild | 589 | 0.429 | **0.098** |
| Moderate | 146 | 0.419 | 0.269 |
| Severe | 56 | 0.448 | **0.415** |

**E6 is flat across grades. E7 rises monotonically with severity, and on Severe
targets it reaches 0.415 -- statistically indistinguishable, at this sample size,
from E6's 0.448.**

The explanation follows from what is being explained. E6's scalar is a class
logit; asking what supports the predicted class is meaningful for any target.
E7's scalar is an accumulated severity score, and asking "what makes this look
severe" of a target with no pathology highlights the *absence* of evidence, which
has no reason to be centred on the annotation. Since 77.33% of targets are
Normal/Mild, the pooled E7 figure is dominated by them.

So the pooled E7 number is a prevalence artefact, and the correct statement is:

> On targets that carry pathology, the full system localises as well as the rung
> below it. The ordinal head changes what attribution *means*, not how well the
> model attends.

The pooled figures for E5, E6 and the target rungs remain comparable with each
other because all of them explain a class logit. E7 is not comparable with them
and should not be placed in the same column without this note.

## What this does for Chapter 4's mechanism

The mechanism offered for the null results is that the convolutional encoder
already localises, leaving structural priors little to add. That claim was
established on E0-E4 and is now confirmed on the graph rungs: E5 and E6
concentrate at 0.34 and 0.43 against untrained floors near 0.18, and E7 reaches
0.415 on the targets where localisation is meaningful.

The limitation recorded in Chapter 4 -- that attribution was not measured on the
final system -- is discharged.

## Caveats

- Sample sizes for the by-grade split are small, particularly Severe (n=56 on the
  batches examined). The monotone trend is clear; the point estimate is not
  precise.
- The condition-to-encoder mapping for graph nodes is derived from node index,
  since `forward_graph` does not carry an annotated slot. Verified against all
  48,657 targets: foraminal to sagittal T1 and subarticular to axial T2 hold
  without exception, and central canal to sagittal T2 holds for 9,748 of 9,753.
- Untrained floors differ per rung (0.141 to 0.178) because the floor is built
  with that rung's own architecture. Gaps, not absolute values, are the
  comparable quantity.
