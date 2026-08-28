# What automating localisation actually costs

Run 2026-08-28. Scripts: `implementation/derived_coordinates.py`,
`implementation/eval_derived_coordinates.py`.
Output: `data/reports/derived_coordinate_cost.csv`.

**This measurement reverses the conclusion of `localisation_feasibility.md`.**
That note found derived coordinates place 99--100% of targets inside the model's
crop and concluded the localisation path was viable. Containment is not
centring, and the difference turns out to be worth almost a quarter of the
system's performance.

## Result

The same checkpoints, the same 297 test patients, the same 7,310 targets, the
same labels and crop geometry. Only the coordinate differs: human annotation
versus segmentation plus a per-condition offset fitted on the dev partition.

| Configuration | Human coords | Derived coords | Delta | Seeds worse |
| :-- | --: | --: | --: | :-: |
| E0 | 0.7276 | 0.5650 | $-0.1626 \pm 0.0279$ | 3/3 |
| E2 | 0.7106 | 0.5615 | $-0.1491 \pm 0.0160$ | 3/3 |
| E4 | 0.7082 | 0.5290 | $-0.1791 \pm 0.0206$ | 3/3 |

**Overall $-0.1636$ QWK: 22.9% of the human-coordinate result, on every one of
nine runs.**

For scale, the entire contribution of this thesis --- the full system over its
baseline, the one comparison that survives correction --- is $+0.0177$ QWK.
**Automating localisation costs roughly nine times what the whole architectural
programme gains.**

## Which conditions fail, and why

Per condition, E0 seed 42:

| Condition | Human | Derived | Delta |
| :-- | --: | --: | --: |
| central canal | 0.7995 | 0.7464 | $-0.0531$ |
| left foraminal | 0.6671 | 0.5240 | $-0.1432$ |
| right foraminal | 0.7109 | 0.5597 | $-0.1513$ |
| right subarticular | 0.7260 | 0.5102 | $-0.2158$ |
| left subarticular | 0.7534 | 0.5007 | $-0.2526$ |

The central canal barely degrades. Everything lateral collapses.

That pattern has a clear explanation and it is the useful part of this result.
The canal sits on the midline, so its offset is essentially zero laterally
($x = +0.4$ mm) and a few millimetres of error moves the crop along the spine
rather than off the structure. The lateral compartments require the crop to be
placed *laterally* to within a few millimetres, and the foramen or lateral
recess is a small structure. A 6 mm error that is harmless in the midline is
disqualifying off it.

Attribution supplies the mechanism: the encoder concentrates roughly half its
evidence in a disc covering a fifth of the crop. Moving the structure off that
disc removes most of the evidence the model uses, even though the structure is
still inside the frame.

## Why the earlier verdict was wrong

`localisation_feasibility.md` measured whether the derived coordinate keeps the
target inside a 60 mm crop, and answered yes for 99--100% of targets. That was
a true measurement of a quantity that turned out not to be the operative one. It
was flagged at the time --- \"containment is not centring\" --- but the verdict
line still read *viable*, and it should not have until this was measured.

The general lesson is that a proxy chosen because it is cheap to compute should
not be reported with a verdict attached. The direct measurement cost about two
hours and reversed the conclusion.

## Consequences

**For the clinical system.** `SYSTEM_DESIGN.md` proposes segmentation plus a
constant offset as the localisation stage, with a human review screen. That
screen is not a nicety, it is load-bearing: unattended grading on derived
coordinates loses 23% of performance, and the loss is concentrated in the four
lateral conditions that are already the hardest. Either the radiologist confirms
placement, or localisation needs a trained detector rather than a constant.

**For RQ4.** This is the more important consequence. Running the transfer
experiment on a cohort without annotated coordinates would confound domain shift
with localisation error --- and localisation error here is an order of magnitude
larger than any effect the thesis measures. A degraded transfer result would be
uninterpretable: there would be no way to attribute it. Chapter 1 anticipated
exactly this in asking \"how much of that degradation is attributable to
localisation versus grading\", and Chapter 3 provides for a verified-localisation
control. This measurement is what makes that provision necessary rather than
precautionary.

**What would make it work.** The bound is not on segmentation quality --- level
identification was 140/140 --- but on the constant-offset assumption for lateral
targets. Three routes, in increasing cost: keep the human in the loop for
placement; learn a per-patient rather than per-condition offset, conditioning on
something like vertebral width; or train a detector on the 48,657 annotated
coordinates RSNA already provides.

## Method notes

Offsets are fitted on 40 dev studies and applied unchanged to the 297 test
studies. Fitting and evaluating on the same data would report how well a
constant can be fitted, not how well it transfers.

No retraining. A deployed system would use the released checkpoints, so those
are what is tested. Retraining on derived coordinates measures whether a model
can adapt to a systematically offset crop, which is a different question.

Targets are matched on (study, level, condition) and scored only when valid in
both caches, so the two runs score exactly the same 7,310 rows.

Series selection was corrected during this work. Taking the first series of each
modality placed 4.4% of derived targets in a series that did not cover them, one
of them 95 slices away. Choosing which series to read is a separate problem from
choosing where to read in it, and the principled answer uses no human
annotation: pick the series whose slices come closest to the derived point. That
raised series agreement to 97.3% and improved the result by $+0.007$ QWK, which
does not change the conclusion.
