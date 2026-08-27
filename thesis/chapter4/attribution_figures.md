# Attribution figures, and an unplanned laterality finding

Generated 2026-08-27 from E2 seed 42, layer3, 3,840 test targets.
Script: `implementation/amog_attribution_figures.py`.
Figures: `data/reports/figures/cam_{mean_by_condition,panels}_E2_seed42.png`.

## What these figures are, and what they are not

They do **not** show lesion detection. The model receives a crop already centred
on the annotated coordinate; it never searches a study. Nor does it name a
pathology: LumbarDISC labels the *severity* of stenosis at a condition and level,
not its cause, so nothing here distinguishes a disc bulge from facet hypertrophy
or ligamentum flavum thickening. Any caption claiming the model "finds a bulge"
would be wrong.

What they show is where, *within* a 60 mm crop, the evidence for the assigned
grade comes from. That is a real question with a non-guaranteed answer: an
untrained network of the same architecture places 0.204 of its mass in the
central disc against the 0.197 a uniform map scores, while trained models reach
0.55-0.63 per condition.

## Figure 1 -- mean attention per condition

Averaging every test target of a condition cancels individual anatomy and leaves
the systematic pattern, so this figure cannot be cherry-picked. It is the one
that belongs in the chapter.

| Condition | n | Mean CAM mass in disc |
| :-- | --: | --: |
| left foraminal | 782 | 60.1\% |
| left subarticular | 756 | 61.9\% |
| central canal | 766 | 55.4\% |
| right subarticular | 755 | 63.0\% |
| right foraminal | 781 | 59.7\% |

The shapes are anatomically coherent and were not designed for: foraminal
attention is a compact focal blob, matching a small aperture; central canal
attention is vertically elongated, matching a vertical channel in sagittal view;
subarticular attention is a horizontal band.

## Figure 2 -- individual targets, failures included

Panels are chosen to span correct Severe, correct Moderate, correct Normal and
misses, rather than to flatter the model.

The most useful single panel is a left foraminal L2-L3 target with **2\% of CAM
mass in the disc** -- attention almost entirely on the far edge of the crop --
which the model nonetheless graded correctly. Right answer, wrong reason. It is
worth reproducing in the thesis precisely because aggregate concentration of
0.60 conceals cases like it.

Three misses in the sample are all Normal/Mild predicted as Moderate, consistent
with the over-calling direction the cost matrix deliberately encourages.

## An unplanned finding: attention is lateralised, in the plane where laterality exists

The mean maps place left- and right-subarticular attention on opposite sides of
the midline. This was not predicted by any hypothesis and was noticed from the
figure, so it is reported as an observation, not a tested claim -- but it comes
with a built-in negative control that makes it interpretable.

The prediction differs by condition, which is what gives the test its force:

- **Subarticular** is graded on **axial T2**, where left-right is an **in-plane**
  axis. A left/right pair should separate horizontally.
- **Foraminal** is graded on **sagittal T1**, where left-right is
  **through-plane** -- the two sides are different *slices*, not different
  in-plane positions. The pair should **not** separate.

Horizontal centroid offset from the midline, in pixels (positive = right):

| Condition | Offset |
| :-- | --: |
| left foraminal | $+12.79$ |
| right foraminal | $+12.26$ |
| central canal | $-4.58$ |
| left subarticular | $-11.30$ |
| right subarticular | $+0.94$ |

| Pair | Separation | Expected |
| :-- | --: | :-- |
| Subarticular (in-plane L-R) | **12.25 px** ($\approx 5.7$ mm) | separated |
| Foraminal (through-plane L-R) | **0.53 px** | not separated |

The foraminal pair separates by half a pixel. That near-zero is what makes the
subarticular 12.25 px meaningful: a model producing an artefact of the crop or
the colour map would separate both pairs.

### Caveats, which are substantial

- **One seed, one configuration.** Not replicated across seeds or rungs.
- **Not a symmetric mirror.** A clean mirror would be roughly $-11$ and $+11$;
  the observed pair is $-11.30$ and $+0.94$. The left condition is displaced and
  the right sits near the midline. Whatever produces the separation is not a
  simple reflection.
- **NOT inherited from the annotations.** The obvious explanation -- that RSNA
  annotates the two sides asymmetrically -- was tested and rejected: across 2,881
  axial annotations the left/right subarticular means are +8.99 mm and -8.14 mm,
  0.85 mm from a perfect mirror (see roi_quality_control.md). The asymmetry is a
  property of the model, of this seed, or of the measurement.
- **An unexplained common offset.** Both foraminal conditions sit $+12$ px right
  of centre. A systematic displacement of that size in the annotated crop is not
  accounted for and should be understood before the laterality claim is made in
  print -- it may indicate an offset between the annotated point and the
  structure actually graded.
- **Post hoc.** This was observed after the fact. It belongs in the thesis as an
  observation motivating future work, not as a confirmatory result.

If it replicates across seeds, it is a genuinely interesting claim: the model
recovers laterality from the data without ever being told which side is which,
and does so only along the axis where laterality is physically present in the
image.
