# Rizgary pathology classification: what the cohort can and cannot support

Written 2026-08-29. Addressed to whoever builds a bulge / protrusion / extrusion
classifier on the Rizgary cohort — most likely an MSc candidate, not the PhD.

This note exists because the measurements below were made once, quickly, and
would otherwise have to be rediscovered. Everything here is computed from the
files on disk, not estimated.

---

## 1. What labels actually exist

Three sources, all keyed on the same case number.

| source | content | n |
| :-- | :-- | --: |
| `rizgary/cases/<diagnosis>/` | folders: disc bulge, disc protrusion, dics extrusion *(sic)*, normal | 297 unique cases |
| `rizgary/research LSS 1.xlsx` | 19 fields, **per level** (`L3-4,L4-5,L5-S1`), some with position (`right paracentral`, `left foraminal`) | 195 patients |
| `rizgary/reports/case N.docx` | free-text radiology reports | 196 |

The Excel carries more than the folders do: disc dehydration, disc height,
vertebral body height, ventral theca indentation, pressure on nerve roots,
ligamentum flavum, facet joint arthrosis, osteophyte, spinal canal stenosis,
alignment, lordotic curve.

Patients positive, per the Excel: disc bulge 145, nerve-root pressure 130,
spinal canal stenosis 68, extrusion 49, protrusion 37, ligamentum flavum 29,
facet arthrosis 13. Facet arthrosis is too rare here to model.

43 cases appear in more than one folder, so the task is multi-label, not
multi-class.

## 2. The labels disagree, and the negative class is contaminated

193 cases carry both a folder and an Excel row. Agreement:

| label | both positive | folder only | Excel only | agreement |
| :-- | --: | --: | --: | --: |
| disc bulge | 121 | 4 | 23 | 86.0% |
| disc protrusion | 26 | 8 | 10 | 90.7% |
| disc extrusion | 31 | 2 | 16 | 90.7% |

**The finding that matters: of 44 cases filed under `normal`, 13 have a bulge,
protrusion or extrusion recorded in the Excel — about 30% of the negative
class.**

Train on the folder split as it stands and roughly a third of the healthy
examples are diseased. The model will underperform and the architecture will get
the blame. Reconcile first, with the **reports as the source of truth** — the
Excel and the folders are both derived from them — and have a radiologist
adjudicate the conflicts.

Also note: 297 cases have folder labels but only 195 have Excel rows, and IDs 51
and 52 have an Excel row with no folder. Do not assume the three sources cover
the same patients.

## 3. Is 297 enough? Only if the model is good

Bulge prevalence is 165/297 = **55.6%**, so answering "bulge" every time scores
55.6%. That is the number to beat, not 50%.

Patients required to beat it at 80% power:

| target accuracy | test patients needed | total needed | have 297? |
| :-- | --: | --: | :-- |
| 65% | 200 | ~1,000 | no |
| 70% | 79 | ~395 | no |
| 75% | 39 | ~195 | **yes** |

With a 20% test split (59 patients), an observed 65% returns a 95% interval of
**[53%, 77%]** — which contains 55.6%. You would have trained a model and be
unable to show it beat a constant answer.

So a 60–70% result is precisely what this cohort cannot establish. At 75% and
above it can.

## 4. How to make the cohort adequate

1. **Report AUC, not accuracy.** At 56% prevalence accuracy is a trap metric.
   AUC 0.85 on 59 test patients gives roughly [0.75, 0.95] — clearly above
   chance.
2. **Use the per-level labels.** 195 patients x 5 levels is about 975 instances.
   Not a 5x gain, because levels within a patient are correlated and splits must
   remain **patient-level**, but a real one.
3. **Cross-validate.** With n this small a single split wastes data and the
   result swings on which 59 patients were drawn.
4. **Fine-tune the project's RSNA encoder** (see below).
5. **Fix the labels first.** No initialisation survives training against wrong
   ones.

## 5. Which pretrained model to start from

Not TotalSpineSeg, despite it being the spine model already installed.

| | TotalSpineSeg | RSNA encoder (this repo) |
| :-- | :-- | :-- |
| trained on | spine MRI, segmentation | 1,974 lumbar studies, 48,657 targets |
| task | delineate structures | grade stenosis severity at disc levels |
| input | 3D NIfTI volumes | 2D crops — same as the bulge pipeline |
| adaptation | encoder surgery on an nnU-Net pipeline | swap the head |

Segmentation features encode shape and boundaries; severity grading needs
texture and encroachment. A model that segments a disc perfectly has not learned
whether it bulges. The RSNA encoder was trained on the *causally adjacent* task —
bulge is one of the things that produces the stenosis it grades — at the same
sites, through the same preprocessing.

Use both, for different jobs: **TotalSpineSeg localises the levels, the RSNA
encoder supplies the features.**

Caveat worth holding: this project measured that better pretraining is not
automatically a win. ACSSL self-supervised pretraining returned +0.0020 QWK,
nothing. Supervised transfer to a small dataset is a better-established gain than
that was, but "it knows about spine" is a hypothesis to test, not a guarantee.

## 6. How to state the result

This is the rule, and it is the difference between a defensible claim and one
that will not survive a reviewer:

> **Defensible:** "AUC 0.82 [0.72, 0.92] on 297 cases, single centre, pending
> external validation."
>
> **Not defensible:** "70% accurate at detecting disc bulge."

Frame the work as a **feasibility study** with AUC and cross-validation, not as
an accuracy claim. State the interval, the n, the single-centre limitation and
the prevalence baseline every time the number appears.

## 7. Why this is not in the PhD thesis

Three reasons, in order of weight:

1. **It is already allocated.** MSC1 (Elaf) characterises this cohort, MSC3
   extracts findings from these reports, MSC2 depends on the same labels.
   Pulling it into the PhD takes work from two supervised projects and
   duplicates a third.
2. **It is a different task.** The thesis grades *severity* of five stenosis
   conditions at supplied coordinates. This is *pathology type*. RQ4 is transfer
   of the same task, and Rizgary has neither per-target severity grades nor
   annotated coordinates, so it cannot test RQ4 as specified.
3. **It would weaken the thesis.** Its strength is disciplined ablation with
   honestly reported nulls. An underpowered new-task study on 297 uncurated
   cases with a 30%-contaminated negative class is the softest target in the
   document.

What *does* belong in the thesis is the characterisation above, reported against
RQ4: the external cohort exists, and here is the measured reason it cannot
answer the question. That converts an omission into a finding.

## 8. Before anything else: de-identification

The Rizgary DICOMs carry unredacted `PatientName`, `BirthDate`, `Sex` and
`StudyDate` in 100% of the 379 files sampled, plus private tags.

Use `tools/deidentify_dicom.py`.

**Do not use `implementation/00_deidentify/deidentify_dicom.py`** — it keys on
`PatientID`, where 45 distinct values cover 346 cases, and would merge different
patients into one pseudonymous identity.
