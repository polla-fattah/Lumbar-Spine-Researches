# Phase 19: End-to-End Master Clinical System Pipeline Launcher
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading & Transfer

import sys
import os
import subprocess
import time
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

impl_dir = os.path.dirname(os.path.abspath(__file__))

def run_phase_script(script_path, cwd):
    print(f"\n[RUNNING] {os.path.basename(script_path)}...")
    start_t = time.time()
    res = subprocess.run([sys.executable, script_path], cwd=cwd, capture_output=True, text=True)
    elapsed = time.time() - start_t
    if res.returncode != 0:
        print(f"[FAIL] {os.path.basename(script_path)} failed (exit code {res.returncode}):")
        print(res.stderr)
        return False, elapsed
    print(f"[PASS] {os.path.basename(script_path)} finished in {elapsed:.2f}s.")
    return True, elapsed

def main():
    print("=" * 70)
    print("  AMOG-Net Master Clinical System Pipeline Execution (Track A + Track B)")
    print("=" * 70)

    start_total = time.time()
    steps = [
        ("Phase 0 De-identification", os.path.join(impl_dir, "00_deidentify", "deidentify_dicom.py"), os.path.join(impl_dir, "00_deidentify")),
        ("Phase 1 Environment & Gate 1", os.path.join(impl_dir, "01_prepare", "verify_determinism.py"), os.path.join(impl_dir, "01_prepare")),
        ("Phase 2 Track A RSNA Manifest", os.path.join(impl_dir, "02_data_manifest", "build_rsna_manifest.py"), os.path.join(impl_dir, "02_data_manifest")),
        ("Phase 2 Track B Hospital Manifest", os.path.join(impl_dir, "02_data_manifest", "build_lumbarDISC_manifest.py"), os.path.join(impl_dir, "02_data_manifest")),
        ("Phase 3 Patient Splits & Gate 2", os.path.join(impl_dir, "02_data_manifest", "create_patient_splits.py"), os.path.join(impl_dir, "02_data_manifest")),
        ("Phase 4 DICOM Geometry Parser", os.path.join(impl_dir, "03_dicom_geometry", "dicom_geometry_parser.py"), os.path.join(impl_dir, "03_dicom_geometry")),
        ("Phase 4 Geometry Audit & Gate 3", os.path.join(impl_dir, "03_dicom_geometry", "verify_geometry.py"), os.path.join(impl_dir, "03_dicom_geometry")),
        ("Phase 5 Landmark Localization", os.path.join(impl_dir, "04_localization", "verify_localization.py"), os.path.join(impl_dir, "04_localization")),
        ("Phase 6 2.5D ROI Extraction", os.path.join(impl_dir, "05_roi_crops", "verify_roi_crops.py"), os.path.join(impl_dir, "05_roi_crops")),
        ("Phase 7 Baseline Classifiers Training", os.path.join(impl_dir, "06_baselines", "train_and_evaluate_e0_baselines.py"), os.path.join(impl_dir, "06_baselines")),
        ("Phase 8 E1 Multi-Sequence Gate 4", os.path.join(impl_dir, "07_aligned_e1", "verify_gate4_alignment.py"), os.path.join(impl_dir, "07_aligned_e1")),
        ("Phase 9 E2/E3 Router Gate 5", os.path.join(impl_dir, "08_routing_e2_e3", "verify_gate5_routing.py"), os.path.join(impl_dir, "08_routing_e2_e3")),
        ("Phase 10 E4 ACSSL Pretrainer Gate 6", os.path.join(impl_dir, "09_acssl_e4", "verify_gate6_acssl.py"), os.path.join(impl_dir, "09_acssl_e4")),
        ("Phase 11 & 12 Graph GNN Gates 7/8", os.path.join(impl_dir, "10_graph_e5_e6", "verify_gate7_gate8_graph.py"), os.path.join(impl_dir, "10_graph_e5_e6")),
        ("Phase 13 E7 Ordinal Loss Gate 9", os.path.join(impl_dir, "11_ordinal_e7", "verify_gate9_calibration.py"), os.path.join(impl_dir, "11_ordinal_e7")),
        ("Phase 14 Master Model Freeze Gate 10", os.path.join(impl_dir, "12_freeze", "verify_gate10_freeze.py"), os.path.join(impl_dir, "12_freeze")),
        ("Phase 15 Hospital Cohort Ingestion", os.path.join(impl_dir, "13_track_b", "ingest_rizgary_cohort.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 16 Zero-Shot Evaluation", os.path.join(impl_dir, "13_track_b", "evaluate_zero_shot.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 16 Zero-Shot Gate 11 Audit", os.path.join(impl_dir, "13_track_b", "verify_gate11_zeroshot.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 17 LoRA Domain Adaptation", os.path.join(impl_dir, "13_track_b", "lora_domain_adaptation.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 17 LoRA Adaptation Gate 12 Audit", os.path.join(impl_dir, "13_track_b", "verify_gate12_adaptation.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 18 Radiologist Report Generator", os.path.join(impl_dir, "13_track_b", "generate_clinical_reports.py"), os.path.join(impl_dir, "13_track_b")),
        ("Phase 19 Gate 13 Master Integration Audit", os.path.join(impl_dir, "13_track_b", "verify_gate13_master_pipeline.py"), os.path.join(impl_dir, "13_track_b")),
    ]

    passed_count = 0
    for name, s_path, c_dir in steps:
        ok, elapsed = run_phase_script(s_path, c_dir)
        if not ok:
            print(f"\n[CRITICAL PIPELINE FAILURE] Pipeline halted at {name}.")
            sys.exit(1)
        passed_count += 1

    total_elapsed = time.time() - start_total
    print("\n" + "=" * 70)
    print("  🎉 [SUCCESS] AMOG-Net Full Dual-Track Pipeline Completed!")
    print(f"     - Total Verification Steps Passed : {passed_count} / {len(steps)}")
    print(f"     - End-to-End Execution Time       : {total_elapsed:.2f} seconds")
    print(f"     - Track A (RSNA Pretraining)     : 1,975 Patients / 6,294 Series")
    print(f"     - Track B (Clinical Transfer)    : 351 Patient Cases / 1,328 DICOMs")
    print(f"     - Master Release Version          : AMOG_PUBLIC_FROZEN_v1.0")
    print("=" * 70)

if __name__ == "__main__":
    main()
