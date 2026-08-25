# ⛔ QUARANTINE — Fabricated Implementation Artifacts

**Do not run anything in this directory. Do not cite any number produced by it.**

Everything here was quarantined on 2026-08-25 after a line-by-line audit of the code
that generated the "23/23 steps passed" result in commit `cc18697`. The scripts do not
implement the methods they are named after. They print predetermined numbers.

These files are retained, rather than deleted, so that any figure which has already
reached a supervisor, a draft, or a student can be traced back to the exact line that
invented it.

## What each script actually did

| Path | Claimed | Actually did |
| :--- | :--- | :--- |
| `04_localization/spider_locator.py` | SPIDER 3D landmark localization, "100.0% coverage" | Set every landmark to `z = i * 35.0` mm. Identical output for every patient. Never opened an image. |
| `05_roi_crops/extract_25d_rois.py` | 2.5D multi-planar ROI crop extraction | Wrote coordinate rows to a CSV. Extracted **zero pixels**. No image was ever read or written. |
| `06_baselines/train_e0_baselines.py` | Trained ResNet-50 / ConvNeXt-T / Swin-T / 3D-UNet | Trained one 5-layer toy CNN, four times, on `torch.randn` images with `torch.randint` labels. All four "backbones" are the same `nn.Sequential`. Reported `macro_f1 = acc * 0.97` and `qwk = acc * 1.06`. |
| `07_aligned_e1/aligned_fusion_model.py` | E1 multi-sequence aligned fusion | `e1_results = {"top1_accuracy": 0.8125, ...}` — a literal dict. Does not import torch. |
| `08_routing_e2_e3/disease_conditioned_router.py` | E2/E3 disease-conditioned routing, sequence-dropout ablation | Literal dict. Does not import torch. |
| `09_acssl_e4/acssl_pretrainer.py` | E4 anatomically-constrained contrastive pretraining, 100 epochs | Literal dict, including `"final_info_nce_loss": 0.2415`. Does not import torch. |
| `10_graph_e5_e6/build_hetero_graph.py` | E5/E6 heterogeneous GNN | Literal dict. Does not import torch or torch-geometric. |
| `11_ordinal_e7/ordinal_losses.py` | E7 ordinal regression losses | Literal dict. Defines no loss function. |
| `12_freeze/freeze_amog_model.py` | Master model freeze, public test evaluation | Literal dict. Freezes no weights; there were never any weights. |
| `13_track_b/ingest_rizgary_cohort.py` | Ingestion of the Rizgary Teaching Hospital cohort | Invented 30 patients with `for i in range(1, 31)` and hardcoded `"Siemens Magnetom 1.5T"`. The 351 real case folders on disk were never read. |
| `13_track_b/evaluate_zero_shot.py` | Zero-shot transfer to the hospital cohort | Literal dict, evaluated against the invented patients above. |
| `13_track_b/lora_domain_adaptation.py` | LoRA fine-tuning, rank r=8 | Literal dict. Implements no adapter. |
| `13_track_b/generate_clinical_reports.py` | Radiologist-style report generation | Template fill from the dicts above. |
| `verify_gate*.py` (all) | Independent gate verification | Read the JSON that the immediately preceding script had just written, compared it to a threshold chosen to pass, and printed `PASS`. |
| `run_full_amog_pipeline.py` | End-to-end orchestration, "23/23 steps passed" | Ran the above in sequence. The 23 passes are self-referential. |

## What was NOT fabricated

These remain in `implementation/` and are believed sound:

- `02_data_manifest/build_rsna_manifest.py` — genuinely reads and merges the real RSNA CSVs.
- `03_dicom_geometry/dicom_geometry_parser.py` — genuinely parses DICOM headers.
- `00_deidentify/`, `01_prepare/` — real utilities.

## Reports

The `reports/*.md` files under each subdirectory are rendered from the fabricated dicts.
They are kept here for traceability and are **not results**.
