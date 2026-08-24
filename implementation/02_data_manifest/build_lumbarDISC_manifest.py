# Phase 2: LumbarDISC DICOM Manifest Construction
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import argparse
import pandas as pd
import json
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

def extract_dicom_attributes(dicom_filepath):
    if not PYDICOM_AVAILABLE:
        return None

    try:
        ds = pydicom.dcmread(dicom_filepath, stop_before_pixels=True, force=True)
        
        patient_id = getattr(ds, 'PatientID', os.path.basename(os.path.dirname(dicom_filepath)))
        study_uid = getattr(ds, 'StudyInstanceUID', 'UNKNOWN_STUDY')
        series_uid = getattr(ds, 'SeriesInstanceUID', 'UNKNOWN_SERIES')
        series_desc = getattr(ds, 'SeriesDescription', 'UNKNOWN_DESC')
        seq_name = getattr(ds, 'SequenceName', 'UNKNOWN_SEQ')
        modality = getattr(ds, 'Modality', 'MR')
        
        slice_thick = getattr(ds, 'SliceThickness', None)
        pixel_spacing = getattr(ds, 'PixelSpacing', [None, None])
        img_pos = getattr(ds, 'ImagePositionPatient', [None, None, None])
        img_orient = getattr(ds, 'ImageOrientationPatient', [None, None, None, None, None, None])

        return {
            'filepath': dicom_filepath,
            'patient_id': str(patient_id),
            'study_instance_uid': str(study_uid),
            'series_instance_uid': str(series_uid),
            'series_description': str(series_desc),
            'sequence_name': str(seq_name),
            'modality': str(modality),
            'slice_thickness': float(slice_thick) if slice_thick is not None else None,
            'pixel_spacing_row': float(pixel_spacing[0]) if pixel_spacing[0] is not None else None,
            'pixel_spacing_col': float(pixel_spacing[1]) if pixel_spacing[1] is not None else None,
            'pos_x': float(img_pos[0]) if img_pos[0] is not None else None,
            'pos_y': float(img_pos[1]) if img_pos[1] is not None else None,
            'pos_z': float(img_pos[2]) if img_pos[2] is not None else None
        }
    except Exception as e:
        return {
            'filepath': dicom_filepath,
            'error': str(e)
        }

def build_synthetic_manifest():
    records = []
    series_types = ['T2_SAG', 'T1_SAG', 'T2_AXIAL', 'T1_AXIAL']
    
    for p_idx in range(1, 101):
        patient_id = f"PATIENT_{p_idx:03d}"
        study_uid = f"1.2.840.113619.2.55.3.{p_idx}.100"
        
        for s_idx, stype in enumerate(series_types):
            series_uid = f"1.2.840.113619.2.55.3.{p_idx}.20{s_idx}"
            records.append({
                'filepath': f"data/raw/{patient_id}/{stype}/slice_01.dcm",
                'patient_id': patient_id,
                'study_instance_uid': study_uid,
                'series_instance_uid': series_uid,
                'series_description': f"Lumbar Spine {stype}",
                'sequence_name': stype,
                'modality': 'MR',
                'slice_thickness': 4.0 if 'SAG' in stype else 3.5,
                'pixel_spacing_row': 0.5,
                'pixel_spacing_col': 0.5,
                'pos_x': 0.0,
                'pos_y': 0.0,
                'pos_z': 0.0
            })
    return pd.DataFrame(records)

def scan_dicom_directory(dicom_dir):
    records = []
    for root, _, files in os.walk(dicom_dir):
        for file in files:
            if file.lower().endswith(('.dcm', '.dicom')) or file.startswith('IM'):
                filepath = os.path.join(root, file)
                info = extract_dicom_attributes(filepath)
                if info and 'error' not in info:
                    records.append(info)
    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser(description="Phase 2 LumbarDISC DICOM Manifest Builder")
    parser.add_argument("--dicom_dir", type=str, default="", help="Path to raw DICOM directory")
    parser.add_argument("--use_synthetic", action="store_true", help="Generate synthetic testing manifest")
    args = parser.parse_args()

    print("=" * 65)
    print("  Phase 2: LumbarDISC DICOM Master Manifest Builder")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_dir = os.path.join(base_dir, "data", "manifests")
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(manifest_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    if args.use_synthetic or not args.dicom_dir or not os.path.exists(args.dicom_dir):
        print("[NOTICE] No valid DICOM directory supplied or --use_synthetic specified.")
        print("         Building synthetic manifest (100 patients, 400 series) for split testing...")
        df = build_synthetic_manifest()
    else:
        print(f"[SCAN] Scanning DICOM directory: {args.dicom_dir}...")
        df = scan_dicom_directory(args.dicom_dir)

    out_csv = os.path.join(manifest_dir, "lumbarDISC_manifest.csv")
    df.to_csv(out_csv, index=False)

    num_patients = df['patient_id'].nunique()
    num_studies = df['study_instance_uid'].nunique()
    num_series = df['series_instance_uid'].nunique()

    audit_md = os.path.join(reports_dir, "manifest_audit.md")
    lines = [
        "# LumbarDISC Master Manifest Audit Report",
        f"**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Manifest Output Path:** `{out_csv}`  ",
        "",
        "---",
        "",
        "## Cohort Statistics",
        f"* **Total Unique Patients:** `{num_patients}`",
        f"* **Total Unique Studies:** `{num_studies}`",
        f"* **Total Unique Series:** `{num_series}`",
        f"* **Total Image Records:** `{len(df)}`",
        "",
        "---",
        "",
        "## Series Description Breakdown",
        "",
        "| Series Description / Sequence Name | Count | Percentage |",
        "| :--- | :--- | :--- |"
    ]

    seq_counts = df['series_description'].value_counts()
    for seq, count in seq_counts.items():
        lines.append(f"| `{seq}` | `{count}` | `{count / len(df) * 100:.2f}%` |")

    with open(audit_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print("\n[SUCCESS] Manifest generated cleanly:")
    print(f"   - Patients : {num_patients}")
    print(f"   - Studies  : {num_studies}")
    print(f"   - Series   : {num_series}")
    print(f"   - CSV Path : {out_csv}")
    print(f"   - Audit MD : {audit_md}")
    print("=" * 65)

if __name__ == "__main__":
    main()
