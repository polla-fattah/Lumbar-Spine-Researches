# Patient-Level Dataset Splits Summary (Gate 2)
**Generated At:** `2026-08-25 20:19:55`  
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
| **Training** | `70` | `70.0%` | `C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches\data\splits\train_ids.txt` |
| **Validation** | `15` | `15.0%` | `C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches\data\splits\val_ids.txt` |
| **Public Test** | `15` | `15.0%` | `C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches\data\splits\public_test_ids.txt` |
| **Total Cohort** | `100` | `100.0%` | `C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches\data\manifests\lumbarDISC_manifest.csv` |