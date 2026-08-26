# Grad-CAM attribution: where does the model look?

Run 2026-08-27, inference only, on the frozen test split against the campaign
checkpoints. Script: `implementation/amog_attribution.py`.
Raw output: `data/reports/attribution_E{0..4}_layer3.json`.

## Why this experiment exists

The campaign returned nulls for all three contributions. A null is an answer,
but a null with a *mechanism* is a much stronger chapter than a null with only a
p-value. The obvious mechanism to test: if the convolutional encoder already
localises the lesion, then structural priors layered on top of it have little
left to contribute, and the nulls follow.

## What is measured

Every crop is centred by construction on its target's annotated coordinate
(`rsna_data.decode_roi` cuts a fixed physical field of view around it), so the
pathology sits at the middle of the frame and "attends to the right place"
becomes measurable: the fraction of Grad-CAM mass inside a central disc of
diameter half the crop, i.e. a 15 mm radius at the 60 mm field of view.

That disc covers **19.7%** of the frame, which is exactly what a uniform map
would score. Two further floors are reported, because a convolutional network is
centre-biased whatever it learned:

- **RANDOM_INIT** -- the identical architecture with untrained weights: 0.204.
  This is the architectural centre bias with no learning in it.
- **E0_LABELSHUF** -- trained on shuffled labels. Stronger in principle, since it
  also controls for having trained on this data, but on this tree it was trained
  as resnet50 while E0 is resnet18. It is therefore **not** a matched control and
  its gap is reported flagged, not relied on. A matched resnet18 label-shuffled
  run would be the better floor if one is ever needed.

## Result 1 -- the encoder localises, strongly

| Rung | CAM mass in disc | vs RANDOM_INIT |
| :-- | --: | --: |
| E0 single sequence | 0.490 +- 0.058 | +0.286 |
| E1 multi-sequence | 0.578 +- 0.073 | +0.374 |
| E2 + router | 0.580 +- 0.063 | +0.376 |
| E3 + modality dropout | 0.515 +- 0.071 | +0.311 |
| E4 + ACSSL | 0.462 +- 0.027 | +0.258 |

Every trained model puts 2.3-2.9x the chance share of its attention on the
annotated centre. **Even E0 -- a plain single-sequence CNN with no routing, no
SSL and no graph -- concentrates 0.490 against a 0.204 untrained floor.**

That is the mechanism the null results needed. The localisation problem the
structural priors were designed to help with is already largely solved by the
encoder before any of them is added.

## Result 2 -- multi-sequence input helps localisation, but not grading

| Step | delta concentration | seeds higher |
| :-- | --: | :-: |
| E1 - E0, add the other two sequences | **+0.089 +- 0.062** | **3/3** |
| E2 - E0, add the router | +0.090 +- 0.119 | 2/3 |
| E3 - E0, add modality dropout | +0.026 +- 0.093 | 2/3 |
| E4 - E0, add ACSSL | -0.027 +- 0.034 | 1/3 |

Seeing all three sequences makes the model look in the right place more
consistently -- the only step in the ladder that improves attention on all three
seeds. It does **not** improve accuracy: E1 vs E0 is -0.0055 QWK. The extra
sequences sharpen *where* the model looks without improving *what it concludes*.

The router adds nothing further (0.580 vs 0.578). ACSSL makes attention slightly
worse and is the only step below E0, which agrees with the input ablation, where
ACSSL also failed to reduce dependence on any single sequence. Both probes put
Contribution I in the same place.

## A probe artefact that had to be fixed first

The first version of this experiment hooked `encoders[0]` and reported that no
rung improved on E0. That was wrong, and wrong in the direction that flattered
the conclusion already in hand.

E0 selects its annotated sequence *inside* `forward_target`, so its
`encoders[0]` genuinely sees the graded image. The multi-sequence rungs run one
encoder per modality, so `encoders[0]` is always sagittal T1 -- and the probe was
measuring the T1 encoder's attention on subarticular targets that are graded from
axial T2. Every rung above E0 was penalised by the instrument.

All encoders are now hooked and each sample takes the map from the encoder
matching its own annotated slot. The corrected E1 - E0 is +0.089 on 3/3 seeds,
where the broken probe reported -0.036 on 1/3.

## Choice of depth

Concentration is strongly depth-dependent, and the depth was chosen on
resolution grounds before the numbers were compared:

| Layer | Spatial size | E0 | RANDOM_INIT | gap |
| :-- | :-: | --: | --: | --: |
| layer2 | 16x16 | 0.270 | 0.253 | +0.017 |
| **layer3** | **8x8** | **0.497** | 0.261 | **+0.235** |
| layer4 | 4x4 | 0.236 | 0.224 | +0.012 |

A resnet downsamples by 32, so at these 128 px crops layer4 is 4x4 -- sixteen
cells for a 60 mm field of view, one cell spanning 15 mm, far too coarse to
resolve a disc covering 19.7% of the frame. Standard Grad-CAM practice attributes
at 7x7 (224 px input through layer4); the matching resolution here is layer3 at
8x8. layer2 is early enough that its features are generic edges.

layer3 is therefore the principled choice given the crop size, not the choice
that produced the largest number -- but since it *is* also the largest, all three
depths are reported so a reader can see the dependence rather than take the
selection on trust. Single seed, 1500 samples for the depth sweep; three seeds
and 3000 samples for the results above.

## Caveats

- For multi-sequence rungs the map is the annotated-sequence encoder's. That
  encoder is one of three inputs to the fused decision, so the measure describes
  where the *primary* encoder looked, not the whole model's evidence.
- Centre concentration presumes the annotation is the lesion centre. RSNA's
  coordinates are point annotations from one reader; a systematically offset
  coordinate would depress the measure for every model equally.
- Grad-CAM is one attribution method with known failure modes. The floors make
  the comparison meaningful, but the absolute value is method-dependent.
- E5-E7 are not covered: `forward_target` is reached through `forward_graph`
  there with a different batch layout.
