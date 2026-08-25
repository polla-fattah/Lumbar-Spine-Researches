# Patient-Level Dataset Splits Summary (Gate 2)
**Generated At:** `2026-08-25 03:18:32`  
**Random Seed:** `42`  

---

## Patient Leakage Status
**Status:** [PASS] Gate 2 Verified – ZERO Patient Leakage  
* `train_ids.isdisjoint(val_ids) == True`
* `train_ids.isdisjoint(public_test_ids) == True`
* `val_ids.isdisjoint(public_test_ids) == True`

---

## Patient Partition Distribution

| Partition Set | Patient Count | Percentage | Output File Path |
| :--- | :--- | :--- | :--- |
| **Training** | `31` | `68.9%` | `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\splits\train_ids.txt` |
| **Validation** | `6` | `13.3%` | `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\splits\val_ids.txt` |
| **Public Test** | `8` | `17.8%` | `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\splits\public_test_ids.txt` |
| **Total Cohort** | `45` | `100.0%` | `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\manifests\lumbarDISC_manifest.csv` |