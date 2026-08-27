# ROI quality control (Chapter 3, sec:method-roi-qc)

Run 2026-08-27. Script: `implementation/roi_qc.py`.
Outputs: `data/reports/roi_qc/` -- two-plane review sheets, a reader checklist,
and `geometry_crosscheck.csv`.

## Why this exists

Chapter 3 commits to it:

> A validation subset is visually inspected using overlays of the detected level,
> crop boundary and corresponding axial slices. The inspection records: correct
> lumbar level; inclusion of the relevant canal/foramen/recess; correct
> left/right orientation; adequate axial coverage; crop truncation;
> correspondence failure caused by unusual axial angulation.

and adds that "a final inclusion/exclusion table will report every such
decision". Neither the inspection nor the table existed. This is the second
unexecuted methodological commitment found in this codebase, after the
controlled input ablation.

It also carries more weight than a figure-generation task, because **Core
Contribution I rests entirely on DICOM-defined anatomical correspondence**. If
that correspondence is wrong, ACSSL's pretext task was matching misaligned
patches and RQ2's null is an artefact rather than a finding. Before this run
there was no data-grounded evidence either way: `geometry.py` records that the
previous implementation never read `ImageOrientationPatient`, substituting
textbook cosines chosen by a substring match on the series description, and that
its "0.00000000 mm" validation was vacuous because inverting a matrix returns
the original point whatever the matrix contains.

## Result 1 -- the correspondence is real

The validation is external, not a round-trip. LumbarDISC annotates different
conditions of the *same level* on *different sequences*: central canal on
sagittal T2, subarticular on axial T2. So the sagittal canal annotation can be
projected into the axial series and asked a falsifiable question -- does it
select the slice carrying that level's own axial annotations? Two independent
human annotations are compared through the transform; nothing can pass by
algebraic identity.

144 sagittal canal annotations projected into axial, over 30 sampled test
studies:

| Slice offset from that level's own axial annotation | Count | Share |
| :-- | --: | --: |
| exactly 0 slices | 101 | 70% |
| exactly 1 slice | 31 | 22% |
| exactly 2 slices | 1 | 1% |
| more than 2 | 11 | 8% |

Median offset **0.0 mm**; 90th percentile **4.0 mm**, i.e. one slice thickness.
**92% land within one slice of an independently annotated target at the same
level** (95% on the 8-study rendering subset).

**The DICOM correspondence behaves as Chapter 3 assumes.** RQ2's rejection is
therefore interpretable: ACSSL was given a fair test and still conferred no
measurable benefit. Before this check, that could not be asserted.

The 8% beyond two slices are candidates for the "correspondence failure caused
by unusual axial angulation" category Chapter 3 asks to be recorded, and are
listed in `geometry_crosscheck.csv` for a reader.

## Result 2 -- left/right orientation is correct, quantitatively

Chapter 3 lists "correct left/right orientation" as a checklist item. It is
measurable rather than impressionistic. Axial annotation positions relative to
each slice's own horizontal centre, in mm, across 2,881 axial annotations on all
297 test studies:

| Condition | n | Mean offset |
| :-- | --: | --: |
| left_subarticular | 1,441 | **+8.99 mm** |
| right_subarticular | 1,440 | **-8.14 mm** |

Positive is right of image centre. Radiological convention renders patient-left
on the image right, so left targets appearing at +9 mm is correct. Separation
17.12 mm; departure from a perfect mirror **0.85 mm**.

The annotations are symmetric and correctly oriented. The review sheets show the
same thing visually: left foraminal projects to image-right and right foraminal
to image-left.

## Result 3 -- a correction to the lateralisation observation

`attribution_figures.md` reported that mean Grad-CAM centroids for left and
right subarticular sat on opposite sides of the crop midline (-11.30 px and
+0.94 px), and flagged that this was not a clean mirror. One plausible
explanation was that the annotations were themselves asymmetric.

They are not: 0.85 mm from perfect symmetry. So the asymmetry in the attention
maps is **not** inherited from the data. It is a property of the model, of that
single seed, or of the measurement -- and until it replicates across seeds, the
third possibility cannot be excluded. The observation stands as an observation
and must not be reported as a finding.

## Review sheets

One sheet per study, one row per target, two panels per row: the annotated plane
with a solid circle, and the same 3D point projected into the orthogonal plane
with a dashed circle. Circles are 10 mm in physical radius, sized per slice from
`PixelSpacing`, so they are comparable across scanners. Colour encodes the
reference grade; a red border marks a crop truncated at the image edge.

Each panel reports its **native** pixel size. Panels are rendered from a 100 mm
physical field of view, which is 213 px at 0.469 mm spacing but only 107 px at
0.938 mm; upsampling without stating the native size would imply detail that is
not present.

On the 8-study sample: 40 targets, **0% truncated crops**, median out-of-plane
distance for cross-plane projection **1.5 mm** -- well inside the 3.5-4.8 mm
slice thickness, so the projected point genuinely lies within the displayed
slice rather than being an extrapolation.

`roi_qc_checklist.csv` carries one row per target with blank columns for the
reader: `correct_level`, `canal_foramen_included`, `left_right_correct`,
`axial_coverage_adequate`, `correspondence_ok`, `reviewer_note`. Completing it
produces the inclusion/exclusion table Chapter 3 promised.

## What these figures are not

Not detection. The model receives a crop centred on a supplied coordinate and
grades severity there; it never searches a study. Not pathology naming either --
LumbarDISC labels stenosis severity, not its cause, so nothing distinguishes a
disc bulge from facet hypertrophy or ligamentum flavum thickening. The figure
legend states both, because a two-plane view invites exactly that misreading.

## Sampling

Studies are drawn at random from the frozen test partition with a fixed seed
(20260827), so the QC subset is reproducible and cannot be reselected after
seeing a result. The check above used 30 studies; the rendering sample used 8 at
L4-L5. Both should be enlarged before the inclusion/exclusion table is finalised.
