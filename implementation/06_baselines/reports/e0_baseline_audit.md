# Phase 6 -- E0 Baseline Audit (Track A, RSNA 2024)

Generated from `results/*.json` on 2026-08-25T18:44:51. Every number below is read from a results file written by `train_e0.py`; none is entered by hand.

## Cohort and splits

- ROI crops used: **48,575**
- Studies: **1382** train / **296** val / **296** test
- Crops: 33,988 / 7,280 / 7,307

Splits are grouped by `study_id`, asserted at runtime, so no patient contributes crops to more than one partition.

**Test-set majority-class accuracy: 78.42%.** A model that always predicts Normal/Mild scores this accuracy and QWK 0.0000. Accuracy alone cannot distinguish that model from a useful one, which is why balanced accuracy and QWK are reported beside it throughout.

## Held-out test results

| Run | Accuracy | Balanced acc. | Macro F1 | QWK | ECE |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `resnet50` | 86.36% | 70.39% | 0.7252 | 0.7500 | 0.1046 |
| `resnet50_SHUFFLED` *(control)* | 73.61% | 33.05% | 0.3146 | 0.0004 | 0.1370 |
| *majority-class* | 78.42% | 33.33% | 0.2921 | 0.0000 | -- |

### `resnet50` -- confusion and per-class behaviour

| truth \ predicted | Normal/Mild | Moderate | Severe | recall |
| :--- | ---: | ---: | ---: | ---: |
| **Normal/Mild** | 5,399 | 324 | 7 | 94.2% |
| **Moderate** | 418 | 656 | 78 | 56.9% |
| **Severe** | 23 | 147 | 255 | 60.0% |

- Two-grade errors (Normal/Mild <-> Severe): **30** of 7,307 (0.41%). Errors are almost entirely between adjacent grades, which is the behaviour an ordinal target should produce.
- Severe is the rarest grade (6.3% of the corpus) and is still recovered at 60.0% recall, so the score is not an artefact of ignoring it.
- ECE 0.1046: the model is over-confident. Trained to a near-zero training loss without calibration, this is expected; temperature scaling on the validation split is the standard remedy and is not applied here.

## Negative control: permuted labels

Labels were permuted *within* each split, leaving the class distribution untouched and destroying only the image-to-label correspondence. A pipeline that leaks information would still score well here.

- QWK **0.0004**
- Balanced accuracy **33.05%** (chance is 33.33%)
- Accuracy **73.61%**, which is *below* the 78.42% majority-class rate

The control collapses to chance while the real run reaches QWK 0.7500. The signal comes from the images, not from the split.

## What this result is and is not

- It **is** a single-backbone, cross-entropy baseline over all five conditions pooled, trained on 2.5D crops centred on the released annotation coordinates.
- It is **not** a state-of-the-art RSNA result. It uses ground-truth annotation coordinates at inference time, so it does not solve localisation, and it is not comparable to Kaggle leaderboard scores, which are computed with a different weighted-log-loss metric on a held-out test set.
- It is the reference point that E1-E7 must improve on. Any later experiment reporting a gain must report it against these numbers, on this split, with this control re-run.

## Reproducing

```bash
python implementation/04_rsna_targets/build_rsna_targets.py --rsna_dir <RSNA>
python implementation/05_rsna_rois/extract_rsna_rois.py --rsna_dir <RSNA>
python -u implementation/06_baselines/train_e0.py --backbone resnet50
python -u implementation/06_baselines/train_e0.py --backbone resnet50 --shuffle_labels
python implementation/06_baselines/make_report.py
```

