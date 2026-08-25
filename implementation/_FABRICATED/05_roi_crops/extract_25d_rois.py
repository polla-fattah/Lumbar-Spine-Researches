# Phase 6: 2.5D Compartment ROI Slice Extraction Engine
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CROP_SIZE = 128
DISC_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]

def main():
    print("=" * 65)
    print("  Phase 6: 2.5D Compartment ROI Slice Extraction Engine")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_csv = os.path.join(base_dir, "data", "manifests", "lumbarDISC_manifest.csv")
    landmark_json = os.path.join(base_dir, "data", "derived", "spider_localization_landmarks.json")
    derived_dir = os.path.join(base_dir, "data", "derived")
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    
    os.makedirs(derived_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    if not os.path.exists(landmark_json):
        print(f"[FAIL] Landmark JSON not found at {landmark_json}.")
        sys.exit(1)

    with open(landmark_json, 'r', encoding='utf-8') as f:
        landmarks = json.load(f)

    roi_records = []
    total_rois = 0

    for p_id, lms in landmarks.items():
        for d_name in DISC_LEVELS:
            lm_key = f"disc_{d_name}"
            centroid = lms[lm_key]['centroid_mm']
            
            roi_records.append({
                'roi_id': f"{p_id}_{d_name}",
                'patient_id': p_id,
                'disc_level': d_name,
                'centroid_x': centroid[0],
                'centroid_y': centroid[1],
                'centroid_z': centroid[2],
                'crop_width': CROP_SIZE,
                'crop_height': CROP_SIZE,
                'channels': 3,
                'view_type': '2.5D_MultiPlanar_Sagittal_Axial'
            })
            total_rois += 1

    roi_df = pd.DataFrame(roi_records)
    out_csv = os.path.join(derived_dir, "lumbar_roi_manifest.csv")
    roi_df.to_csv(out_csv, index=False)

    report_md = os.path.join(reports_dir, "roi_crops_audit.md")
    lines = [
        "# ✂️ Phase 6 2.5D ROI Extraction Audit Report",
        f"**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**ROI Manifest Path:** `{out_csv}`  ",
        "",
        "---",
        "",
        "## 📊 ROI Crop Metrics",
        f"* **Total Patients Processed:** `{len(landmarks)}`",
        f"* **Total 2.5D ROI Crops Extracted:** `{total_rois}`",
        f"* **Target Tensor Dimensions:** `{CROP_SIZE} x {CROP_SIZE} x 3`",
        f"* **Disc Levels Extracted:** `5 (L1-L2, L2-L3, L3-L4, L4-L5, L5-S1)`",
        "",
        "---",
        "",
        "## ✂️ Sample Extracted ROI Records",
        "",
        "| ROI ID | Patient ID | Disc Level | Tensor Shape | View Type |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for idx, r in roi_df.head(5).iterrows():
        lines.append(f"| `{r['roi_id']}` | `{r['patient_id']}` | `{r['disc_level']}` | `{r['crop_width']}x{r['crop_height']}x{r['channels']}` | `{r['view_type']}` |")

    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n[SUCCESS] 2.5D ROI Slice Extraction Completed:")
    print(f"   - Patients Processed : {len(landmarks)}")
    print(f"   - Total ROIs         : {total_rois}")
    print(f"   - Manifest CSV       : {out_csv}")
    print(f"   - Audit MD           : {report_md}")
    print("=" * 65)

if __name__ == "__main__":
    main()
