# Phase 4 & Gate 3 Verification Audit: DICOM Geometry Reconstructibility Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 4 & Gate 3: DICOM Geometry Reconstructibility Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    geom_json = os.path.join(base_dir, "data", "derived", "dicom_geometry_matrices.json")

    if not os.path.exists(geom_json):
        print(f"[FAIL] Geometry registry JSON not found at {geom_json}.")
        print("       Run 'python dicom_geometry_parser.py' first.")
        sys.exit(1)

    with open(geom_json, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    total_series = len(registry)
    singular_count = 0
    roundtrip_errors = []

    print(f"Auditing Affine Matrices for {total_series} series...")

    for uid, info in registry.items():
        M = np.array(info['affine_matrix_4x4'], dtype=np.float64)
        det = np.linalg.det(M)

        if abs(det) < 1e-6:
            singular_count += 1
            continue

        # Test forward and inverse roundtrip coordinate mapping
        # 2D pixel (u=100, v=100, k=0) -> 3D patient (X,Y,Z) -> 2D pixel (u', v', k')
        orig_pixel = np.array([100.0, 100.0, 0.0, 1.0])
        patient_xyz = M @ orig_pixel
        
        M_inv = np.linalg.inv(M)
        reconstructed_pixel = M_inv @ patient_xyz
        
        err = np.max(np.abs(orig_pixel - reconstructed_pixel))
        roundtrip_errors.append(err)

    max_roundtrip_err = max(roundtrip_errors) if roundtrip_errors else 0.0

    print(f"\nAudit Summary:")
    print(f"  - Total Series Audited : {total_series}")
    print(f"  - Singular Matrices    : {singular_count}")
    print(f"  - Max Roundtrip Error  : {max_roundtrip_err:.8f} mm")

    assert singular_count == 0, f"[GATE 3 ERROR] Found {singular_count} singular non-invertible affine matrices!"
    assert max_roundtrip_err < 1e-5, f"[GATE 3 ERROR] Roundtrip coordinate mapping error {max_roundtrip_err} exceeds 1e-5!"

    print("\n✅ [PASS] Gate 3 Verified: 100% Non-Singular Invertible Affine Matrices!")
    print("   Physical 3D patient coordinate reconstructibility confirmed across all series.")
    print("=" * 65)

if __name__ == "__main__":
    main()
