# System Diagnostic & Environment Availability Report
**Generated At:** `2026-08-25 02:27:58`  
**OS Platform:** `Windows-11-10.0.26200-SP0` (`64bit`)  
**Python Version:** `3.13.2`  

---

## Hardware & Accelerators Availability

**Status:** [WARN] **No GPU Accelerator / CUDA Enabled PyTorch Detected**
* *Note: PyTorch is currently running in CPU mode. GPU acceleration is strongly recommended for Phase 7–13 training.*

---

## Medical AI & PyTorch Dependency Status

| Package Name | Purpose / Function | Status | Version |
| :--- | :--- | :--- | :--- |
| PyTorch Core | `torch` | [OK] Installed | `2.9.0+cpu` |
| TorchVision Vision Models | `torchvision` | [OK] Installed | `0.24.0+cpu` |
| DICOM File Parsing | `pydicom` | [OK] Installed | `3.0.1` |
| Medical Image Processing & Geometry | `SimpleITK` | [MISSING] **MISSING** | *Not Found* |
| Medical Open Network for AI | `monai` | [MISSING] **MISSING** | *Not Found* |
| Neuroimaging / NIfTI & DICOM Utilities | `nibabel` | [MISSING] **MISSING** | *Not Found* |
| Numerical Computing | `numpy` | [OK] Installed | `2.3.4` |
| Dataframes & Manifest Handling | `pandas` | [OK] Installed | `2.3.3` |
| Scientific Computing & Interpolation | `scipy` | [OK] Installed | `1.17.1` |
| Scikit-Learn Machine Learning & Metrics | `sklearn` | [OK] Installed | `1.9.0` |
| Scikit-Image Image Analysis | `skimage` | [OK] Installed | `0.26.0` |
| Fast Image Augmentations | `albumentations` | [MISSING] **MISSING** | *Not Found* |
| OpenCV Computer Vision | `cv2` | [OK] Installed | `4.10.0` |
| PyTorch Geometric (GNN Support) | `torch_geometric` | [MISSING] **MISSING** | *Not Found* |
| YAML Configuration Parsing | `yaml` | [OK] Installed | `6.0.2` |
| Progress Bars | `tqdm` | [OK] Installed | `4.67.1` |
| HDF5 File Storage | `h5py` | [MISSING] **MISSING** | *Not Found* |
| Data Plotting | `matplotlib` | [OK] Installed | `3.10.7` |
| Statistical Visualization | `seaborn` | [OK] Installed | `0.13.2` |
| Statistical Hypotheses Testing | `statsmodels` | [MISSING] **MISSING** | *Not Found* |

---

## Installation & Action Plan for Student (Selar)

[WARN] **7 required packages are missing.**

Selar can install all missing packages at once by running:
```bash
python setup_environment.py
```
Or via pip:
```bash
pip install SimpleITK monai nibabel albumentations torch_geometric h5py statsmodels
```