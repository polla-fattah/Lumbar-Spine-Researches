# Which scripts are live, and which are superseded

Written 2026-08-27 after surveying all 67 Python files in the numbered phase
directories by whether anything still references them.

## Why nothing here is deleted

The numbered phase directories (`07_aligned_e1` through `13_track_b`) contain
the earlier pipeline, in which several phases hardcoded their own metrics rather
than computing them. That pipeline is the reason this project was audited at all,
and its files are the evidence of what was found.

Chapter 1 requires that components not supported by the executed experiments
\"be reported as negative findings, not retrospectively removed from the research
history\". Deleting the superseded implementations would apply the opposite
principle to code. It also saves nothing measurable: 67 files, none large.

So the files stay and this table records what replaced them. If a reader or
examiner asks what the earlier pipeline did, the answer should be inspectable
rather than reconstructed from commit messages.

## The live pipeline

Everything the thesis results depend on:

| File | Role |
| :-- | :-- |
| `amog_train.py` | the ladder engine; AMOGNet, run_epoch, model selection |
| `amog_models.py` | encoders, fusion, router, GNNs, ordinal head, cost matrix |
| `amog_acssl.py` | ACSSL pretraining |
| `amog_augment.py` | GPU-batched augmentation |
| `amog_stats.py` | bootstrap, FDR, across-seed inference |
| `amog_eval.py`, `amog_modes.py` | metrics, mode/context resolution |
| `rsna_data.py` | cache building, frozen split, ROI decoding |
| `geometry.py` | DICOM patient-space transforms |
| `run_ladder.py` | campaign driver, tables, comparisons |
| `amog_input_ablation.py` | controlled input ablation (RQ3) |
| `amog_attribution.py` | Grad-CAM, target rungs E0-E4 |
| `amog_attribution_graph.py` | Grad-CAM, graph rungs E5-E7 |
| `amog_attribution_figures.py` | attribution figures |
| `roi_qc.py` | ROI quality control, two-plane sheets |
| `dicom_to_nifti.py` | DICOM to NIfTI with correct affine |
| `99_audit/test_components.py` | 113 behavioural tests |
| `99_audit/verify_integrity.py` | tree-level integrity check |

## Superseded implementations

Each of these is unreferenced by any live code and has a direct replacement.

| Superseded | Replaced by |
| :-- | :-- |
| `06_baselines/train_e0_twomode.py` | `amog_train.py` (stage E0) |
| `06_baselines/evaluate_baselines.py` | `run_ladder.py` |
| `06_baselines/make_report.py` | `run_ladder.py` table generation |
| `07_aligned_e1/aligned_fusion_model.py` | `amog_models.FixedFusion` |
| `08_routing_e2_e3/disease_conditioned_router.py` | `amog_models.DiseaseConditionedRouter` |
| `10_graph_e5_e6/build_hetero_graph.py` | `amog_models.build_edges` |
| `11_ordinal_e7/ordinal_losses.py` | `amog_models.OrdinalCORNHead`, `clinical_cost_matrix` |
| `01_prepare/check_environment.py` | `amog_modes.configure_backend` |
| `02_data_manifest/run_data_foundation.py` | `rsna_data.py` cache builder |

## Track B, unreferenced but not superseded

`13_track_b/merge_reference.py` has no caller in the live pipeline but is not
replaced by anything. Track B is the Rizgary cohort work, which is paused rather
than finished: RQ4 was not executed. Treat it as dormant, not dead.

## Standalone analyses

`99_audit/annotation_laterality.py` and `99_audit/per_condition_vs_readers.py`
are unreferenced by design. They are one-shot analyses whose results are cited in
`thesis/chapter4/roi_quality_control.md` and Chapter 5 respectively. They are kept
so those numbers can be regenerated rather than taken on trust.

## How this list was produced

`survey_scripts.py` counts, for every phase script, how many other source files
and how many documentation or thesis files mention its module name, then reports
the ones with zero of both alongside their last commit date. Twelve of
sixty-seven had no reference anywhere; two of those were the standalone analyses
above.
