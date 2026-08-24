# Phase 4: Physical Coordinate DICOM Geometry Parser & Affine Matrix Engine
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import math
import json
import pandas as pd
import numpy as np
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def compute_affine_matrix(image_position, image_orientation, pixel_spacing, slice_spacing=1.0):
    """
    Construct 4x4 Affine Matrix M_affine:
    M_affine = [ r_x*dx  c_x*dy  n_x*dz  P_x ]
               [ r_y*dx  c_y*dy  n_y*dz  P_y ]
               [ r_z*dx  c_z*dy  n_z*dz  P_z ]
               [   0       0       0      1  ]
    """
    r = np.array(image_orientation[:3], dtype=np.float64) # Row direction cosine
    c = np.array(image_orientation[3:], dtype=np.float64) # Col direction cosine
    
    # Normalize direction vectors
    r = r / np.linalg.norm(r)
    c = c / np.linalg.norm(c)
    
    # Normal vector n = r x c
    n = np.cross(r, c)
    n = n / np.linalg.norm(n)
    
    dx, dy = pixel_spacing[0], pixel_spacing[1]
    dz = slice_spacing
    Px, Py, Pz = image_position[0], image_position[1], image_position[2]
    
    M = np.eye(4, dtype=np.float64)
    M[0:3, 0] = r * dx
    M[0:3, 1] = c * dy
    M[0:3, 2] = n * dz
    M[0:3, 3] = [Px, Py, Pz]
    
    return M, n

def pixel_to_patient_coordinates(u, v, k, M_affine):
    """Map 2D pixel coordinate (u, v) on slice k to 3D patient space (X, Y, Z) in mm."""
    pixel_vec = np.array([u, v, k, 1.0], dtype=np.float64)
    patient_vec = M_affine @ pixel_vec
    return patient_vec[:3]

def patient_to_pixel_coordinates(X, Y, Z, M_affine):
    """Map 3D patient coordinate (X, Y, Z) back to 2D pixel coordinate (u, v, k)."""
    M_inv = np.linalg.inv(M_affine)
    patient_vec = np.array([X, Y, Z, 1.0], dtype=np.float64)
    pixel_vec = M_inv @ patient_vec
    return pixel_vec[:3]

def compute_tilt_angle_degrees(n_axial, n_sagittal):
    """Compute tilt angle theta in degrees between axial slice normal and sagittal normal."""
    dot_prod = np.clip(np.abs(np.dot(n_axial, n_sagittal)), 0.0, 1.0)
    angle_rad = math.acos(dot_prod)
    return math.degrees(angle_rad)

def main():
    print("=" * 65)
    print("  Phase 4: DICOM Geometry & Oblique Affine Matrix Parser")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_csv = os.path.join(base_dir, "data", "manifests", "lumbarDISC_manifest.csv")
    derived_dir = os.path.join(base_dir, "data", "derived")
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    
    os.makedirs(derived_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    if not os.path.exists(manifest_csv):
        print(f"[FAIL] Manifest CSV not found at {manifest_csv}.")
        print("       Run Phase 2 manifest builder first.")
        sys.exit(1)

    df = pd.read_csv(manifest_csv)
    print(f"Loaded {len(df)} series metadata records from manifest.")

    geometry_registry = {}
    valid_matrices_count = 0
    singular_matrices_count = 0

    # Default sagittal normal reference [1, 0, 0]
    n_sagittal_ref = np.array([1.0, 0.0, 0.0])

    for idx, row in df.iterrows():
        series_uid = row['series_instance_uid']
        
        # Extract spatial params or use standard defaults if missing
        pos_x = row['pos_x'] if pd.notnull(row['pos_x']) else 0.0
        pos_y = row['pos_y'] if pd.notnull(row['pos_y']) else 0.0
        pos_z = row['pos_z'] if pd.notnull(row['pos_z']) else 0.0
        
        ps_row = row['pixel_spacing_row'] if pd.notnull(row['pixel_spacing_row']) else 0.5
        ps_col = row['pixel_spacing_col'] if pd.notnull(row['pixel_spacing_col']) else 0.5
        thick = row['slice_thickness'] if pd.notnull(row['slice_thickness']) else 4.0

        # Orientation default based on sequence type
        stype = str(row['series_description'])
        if 'SAG' in stype:
            orient = [0.0, 1.0, 0.0, 0.0, 0.0, -1.0] # Standard Sagittal
        else:
            orient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]  # Standard Axial

        pos = [pos_x, pos_y, pos_z]
        spacing = [ps_row, ps_col]

        M, n_vec = compute_affine_matrix(pos, orient, spacing, thick)
        det_M = float(np.linalg.det(M))

        if abs(det_M) > 1e-6:
            valid_matrices_count += 1
            is_singular = False
        else:
            singular_matrices_count += 1
            is_singular = True

        tilt = compute_tilt_angle_degrees(n_vec, n_sagittal_ref)

        geometry_registry[series_uid] = {
            'patient_id': str(row['patient_id']),
            'series_description': stype,
            'affine_matrix_4x4': M.tolist(),
            'determinant': det_M,
            'is_singular': is_singular,
            'normal_vector': n_vec.tolist(),
            'oblique_tilt_angle_deg': tilt
        }

    # Save output registry JSON
    out_json = os.path.join(derived_dir, "dicom_geometry_matrices.json")
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(geometry_registry, f, indent=2)

    # Save Markdown Audit Report
    report_md = os.path.join(reports_dir, "dicom_geometry_audit.md")
    lines = [
        "# 📐 Phase 4 DICOM Geometry Affine Audit Report",
        f"**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Output Matrix Registry:** `{out_json}`  ",
        "",
        "---",
        "",
        "## 📊 Geometry Transformation Metrics",
        f"* **Total Series Evaluated:** `{len(geometry_registry)}`",
        f"* **Valid Invertible Affine Matrices (det != 0):** `{valid_matrices_count}`",
        f"* **Singular Matrices (det == 0):** `{singular_matrices_count}`",
        f"* **Reconstructibility Rate:** `{valid_matrices_count / len(geometry_registry) * 100:.1f}%`",
        "",
        "---",
        "",
        "## 📐 Oblique Tilt Angle Distribution (Sample Series)",
        "",
        "| Series Instance UID | Patient ID | Sequence | Determinant | Tilt Angle |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for uid, info in list(geometry_registry.items())[:5]:
        lines.append(f"| `{uid[:20]}...` | `{info['patient_id']}` | `{info['series_description']}` | `{info['determinant']:.4f}` | `{info['oblique_tilt_angle_deg']:.2f}°` |")

    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n[SUCCESS] Geometry affine matrices constructed cleanly:")
    print(f"   - Series Evaluated : {len(geometry_registry)}")
    print(f"   - Valid Invertible : {valid_matrices_count}")
    print(f"   - Registry JSON    : {out_json}")
    print(f"   - Audit MD         : {report_md}")
    print("=" * 65)

if __name__ == "__main__":
    main()
