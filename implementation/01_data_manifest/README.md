# Phase 2 & 3: LumbarDISC DICOM Manifest & Patient Split Construction

This directory (`implementation/01_data_manifest/`) handles **Track A (Data Foundation)**:
* **Phase 2:** Traverse DICOM study folders, parse DICOM attributes, validate sequence geometries, and output `lumbarDISC_manifest.csv`.
* **Phase 3 (Gate 2):** Construct patient-level train/validation/public-test splits with strict zero-patient-leakage verification (`isdisjoint()`).

---

## 🚀 How Selar Runs Phase 2 & 3

### Step 1: Generate Master DICOM Manifest (Phase 2)
Point the manifest builder script to your local raw DICOM folder:

```bash
python build_lumbarDISC_manifest.py --dicom_dir "C:\path\to\raw_lumbarDISC_dicom"
```

If testing with a synthetic/mock dataset or default directory layout:
```bash
python build_lumbarDISC_manifest.py --use_synthetic
```

This generates:
* `../../data/manifests/lumbarDISC_manifest.csv`
* `reports/manifest_audit.md`

---

### Step 2: Construct Patient-Level Dataset Splits (Phase 3 & Gate 2)
Generate patient-stratified splits and verify zero leakage across sets:

```bash
python create_patient_splits.py
```

This generates:
* `../../data/splits/train_ids.txt`
* `../../data/splits/val_ids.txt`
* `../../data/splits/public_test_ids.txt`
* `reports/dataset_splits_summary.md`

---

### ⚡ 1-Click Master Pipeline
Run both Phase 2 and Phase 3 together:
```bash
python run_data_foundation.py --dicom_dir "C:\path\to\raw_lumbarDISC_dicom"
```
