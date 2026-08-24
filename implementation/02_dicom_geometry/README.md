# Phase 4: Physical Coordinate DICOM Geometry & Oblique Axial Matrix Alignment

This directory (`implementation/02_dicom_geometry/`) implements **Phase 4 DICOM Geometry Parsing & Oblique Axial Transformation**:
* Reconstructs $4 \times 4$ Physical Affine Transformation Matrices ($M_{affine} \in \mathbb{R}^{4 \times 4}$).
* Maps 2D image pixel coordinates $(u, v)$ to physical 3D patient coordinates $(X, Y, Z)_{\text{mm}}$.
* Calculates slice normal vectors $\mathbf{n} = \mathbf{r} \times \mathbf{c}$, inter-slice distances $\Delta d$, and oblique axial tilt angles $\theta$.
* Enforces **Gate 3 DICOM Geometry Reconstructibility Assertion** ($\\det(M_{affine}) \neq 0$).

---

## 🚀 How to Run Phase 4

### Step 1: Run DICOM Geometry Affine Parser
```bash
python dicom_geometry_parser.py
```

Outputs:
* `../../data/derived/dicom_geometry_matrices.json`
* `reports/dicom_geometry_audit.md`

---

### Step 2: Run Gate 3 Geometry Invertibility & Coordinate Verification Audit
```bash
python verify_geometry.py
```

If all affine matrices are invertible ($\\det(M) \neq 0$), outputs:
`[PASS] Gate 3 Verified: 100% Non-Singular Invertible DICOM Affine Matrices.`
