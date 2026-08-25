# Chapter 4 — Evidence Folder

Working material for the Implementation and Results chapter. Nothing here is
chapter prose; these are the experiments, decisions and verification records
that Chapter 4 will draw on, kept in one place so a figure can be traced back to
the run that produced it.

## Status of the contents

**Nothing in this folder is a confirmatory thesis result yet.** The E0 baseline
is real and reproducible, but the full E0–E7 campaign has not been run, and the
open items listed in `protocol_decisions.md` must be closed first.

## The documents

| File | What it is | Generated? |
| :--- | :--- | :--- |
| `e0_baseline.md` | The E0 reference result on RSNA, with a permuted-label negative control | Yes — `implementation/99_audit/make_e0_report.py` |
| `roi_geometry_ablation.md` | Four ROI geometries compared, and which was adopted | Yes — `implementation/05_rsna_rois/make_roi_ablation_report.py` |
| `component_verification.md` | The Chapter 3 conformance test suite and its outcome | Yes — `implementation/99_audit/make_verification_report.py` |
| `protocol_decisions.md` | Methodological decisions with the measurement behind each | No — written, updated by hand |

Three of the four are **generated from result files**, so no number in them can
be typed in or drift from what was measured. Regenerate all of them with:

```bash
python implementation/99_audit/make_e0_report.py
python implementation/05_rsna_rois/make_roi_ablation_report.py
python implementation/99_audit/make_verification_report.py
```

`e0_baseline.md` is generated from `data/derived/`, the output of
`amog_train.py` — the same engine the whole ladder runs on, so E0 and every
later rung are produced by identical code. A separate standalone E0 harness
exists in `implementation/06_baselines/`; its numbers use a different split and
are **not** comparable, and it writes outside this folder deliberately. Its
purpose is to be a second implementation: the disagreement between the two is
what exposed E0 grading 59.5% of targets from the wrong MRI sequence.

## How to use these when writing Chapter 4

**Quote the generated documents, do not retype them.** The specific failure this
project is recovering from is a results chapter assembled from numbers that were
written by hand into source code. Every figure here traces to a JSON written by
a training run; keep that chain intact.

**Carry the caveats with the numbers.** Each document states what its result is
*not*, and those sentences matter more than the headline figures:

- The E0 baseline consumes ground-truth annotation coordinates at inference, so
  it does **not** solve localisation and is **not** comparable to RSNA Kaggle
  leaderboard scores, which use a different metric on a different test set.
- The ROI ablation ran on a 500-study subset with three seeds and E0 only. Its
  r=2 comparison is confounded by the need to widen a three-channel ImageNet
  stem, and the document says so rather than claiming Chapter 3 is refuted.
- The verification suite exits non-zero while findings remain open. A failing
  test there is a known deviation with a decision attached, not a hidden defect.

**Report the negative results.** Chapter 3 `sec:method-negative-results` commits
to reporting components that fail to help, with confidence intervals. Two are
already on record: r=2 did not improve on r=1 in this setup, and temperature
scaling made E7's held-out ECE worse while improving E0's and E6's.

**Prefer QWK, balanced accuracy and Severe recall over accuracy.** The majority
class is 77.3% of the corpus. A model predicting Normal/Mild for every target
scores that accuracy with QWK exactly 0.0000, and accuracy alone cannot
distinguish it from a working model.

## What is missing before Chapter 4 can be written

Listed in full at the end of `protocol_decisions.md`. The short version: the
E0–E7 campaign itself, training augmentation, Track B on the real Rizgary
cohort, and the competitive baselines and ablations Chapter 3 specifies.
