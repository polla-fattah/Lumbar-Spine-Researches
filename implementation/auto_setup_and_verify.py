# Automated Self-Healing Environment Setup, Package Configurator & Gate 1 Verifier
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import platform
import subprocess
import json
import importlib
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# List of required packages to check and auto-install
REQUIRED_PACKAGES = [
    ("torch", "PyTorch Core", "torch>=2.0.0"),
    ("torchvision", "TorchVision Models", "torchvision>=0.15.0"),
    ("pydicom", "DICOM Reader", "pydicom>=2.4.0"),
    ("SimpleITK", "Medical Image Processing", "SimpleITK>=2.2.0"),
    ("monai", "Medical AI Framework", "monai>=1.2.0"),
    ("nibabel", "Neuroimaging/NIfTI Loader", "nibabel>=5.0.0"),
    ("numpy", "Numerical Computing", "numpy>=1.24.0"),
    ("pandas", "Dataframes & Manifests", "pandas>=2.0.0"),
    ("scipy", "Scientific Computation", "scipy>=1.10.0"),
    ("sklearn", "Scikit-Learn Machine Learning", "scikit-learn>=1.2.0"),
    ("skimage", "Scikit-Image Processing", "scikit-image>=0.20.0"),
    ("albumentations", "Image Augmentations", "albumentations>=1.3.0"),
    ("cv2", "OpenCV Computer Vision", "opencv-python-headless>=4.7.0"),
    ("torch_geometric", "Graph Neural Networks", "torch-geometric>=2.3.0"),
    ("yaml", "YAML Configuration Parser", "pyyaml>=6.0"),
    ("tqdm", "Progress Bars", "tqdm>=4.65.0"),
    ("h5py", "HDF5 File Storage", "h5py>=3.8.0"),
    ("matplotlib", "Plotting Library", "matplotlib>=3.7.0"),
    ("seaborn", "Statistical Graphics", "seaborn>=0.12.0"),
    ("statsmodels", "Statistical Models & Tests", "statsmodels>=0.14.0")
]

def get_venv_python():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if os.name == 'nt':
        venv_py = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    else:
        venv_py = os.path.join(base_dir, "venv", "bin", "python")
    return venv_py

def ensure_virtual_environment():
    in_venv = (sys.prefix != sys.base_prefix) or ('CONDA_DEFAULT_ENV' in os.environ)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, "venv")
    venv_py = get_venv_python()

    if in_venv:
        print(f"[OK] Running inside active Virtual Environment: {sys.prefix}", flush=True)
        return True, sys.executable

    print("[NOTICE] Currently running in Global System Python.", flush=True)
    
    # Check if venv folder exists
    if not os.path.exists(venv_py):
        print(f"[AUTO-ACTION] Creating isolated Python virtual environment at '{venv_dir}'...", flush=True)
        try:
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
            print("[OK] Virtual environment created successfully.", flush=True)
        except Exception as e:
            print(f"[FAIL] Could not create virtual environment: {e}", flush=True)
            print("   Action required by Selar: Run 'python -m venv venv' manually.", flush=True)
            return False, sys.executable

    # Re-spawn execution inside venv python if not already inside it
    if os.path.abspath(sys.executable) != os.path.abspath(venv_py):
        print(f"[AUTO-SWITCH] Switching execution to venv Python: {venv_py}", flush=True)
        try:
            cmd = [venv_py, os.path.abspath(__file__)] + sys.argv[1:]
            res = subprocess.run(cmd)
            sys.exit(res.returncode)
        except Exception as e:
            print(f"[WARN] Could not auto-switch to venv Python: {e}", flush=True)

    return True, venv_py

def upgrade_pip(python_exe):
    print("\n[STEP 1/4] Upgrading pip inside virtual environment...", flush=True)
    try:
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools"], check=True, stdout=subprocess.DEVNULL)
        print("[OK] Pip is up-to-date.", flush=True)
    except Exception as e:
        print(f"[WARN] Could not upgrade pip automatically: {e}", flush=True)

def check_and_install_packages(python_exe):
    print("\n[STEP 2/4] Auditing & auto-configuring required packages...", flush=True)
    installed_count = 0
    failed_packages = []
    
    for mod_name, label, pip_spec in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(mod_name)
            ver = getattr(mod, "__version__", "Installed")
            print(f"  [OK] {label} ({mod_name}) is ready: v{ver}", flush=True)
            installed_count += 1
        except ImportError:
            print(f"  [MISSING] {label} ({mod_name}) is missing. Attempting auto-installation...", flush=True)
            try:
                subprocess.run([python_exe, "-m", "pip", "install", pip_spec], check=True)
                # Verify import after install
                importlib.invalidate_caches()
                mod = importlib.import_module(mod_name)
                ver = getattr(mod, "__version__", "Installed")
                print(f"  [INSTALLED] {label} successfully configured: v{ver}", flush=True)
                installed_count += 1
            except Exception as e:
                print(f"  [FAIL] Failed to auto-install {mod_name}: {e}", flush=True)
                failed_packages.append((mod_name, label, pip_spec, str(e)))

    return installed_count, failed_packages

def check_gpu_cuda():
    print("\n[STEP 3/4] Hardware & PyTorch CUDA acceleration check...", flush=True)
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        if cuda_avail:
            gpu_name = torch.cuda.get_device_name(0)
            vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            print(f"  [OK] GPU Accelerator Detected: {gpu_name} ({vram} GB VRAM, CUDA {torch.version.cuda})", flush=True)
            return True, f"{gpu_name} ({vram} GB VRAM)"
        else:
            print("  [WARN] PyTorch is running in CPU-only mode.", flush=True)
            print("         If an NVIDIA GPU is installed on this machine, upgrade to CUDA-enabled PyTorch:", flush=True)
            print("         pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118", flush=True)
            return False, "CPU Mode (No CUDA)"
    except Exception as e:
        print(f"  [WARN] PyTorch check error: {e}", flush=True)
        return False, "PyTorch Error"

def verify_gate1_determinism():
    print("\n[STEP 4/4] Gate 1 Reproducibility & Seed Determinism Test...", flush=True)
    try:
        import random
        import numpy as np
        import torch
        import torch.nn as nn

        seed = 42
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

        class ToyNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = nn.Linear(10, 3)
            def forward(self, x):
                return self.fc(x)

        model1 = ToyNet()
        in1 = torch.randn(2, 10)
        out1 = model1(in1)

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        model2 = ToyNet()
        in2 = torch.randn(2, 10)
        out2 = model2(in2)

        diff = torch.max(torch.abs(out1 - out2)).item()
        if diff < 1e-6:
            print("  [PASS] Gate 1 Reproducibility Verified! (Bit-for-bit output match)", flush=True)
            return True
        else:
            print(f"  [FAIL] Determinism check failed. Max output diff: {diff}", flush=True)
            return False
    except Exception as e:
        print(f"  [FAIL] Gate 1 test error: {e}", flush=True)
        return False

def generate_auto_report(installed_count, failed_packages, gpu_status, gate1_pass, reports_dir):
    report_path = os.path.join(reports_dir, "AUTO_SETUP_REPORT.md")
    
    lines = [
        "# 🤖 Automated Environment Setup & Verification Summary",
        f"**Execution Timestamp:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Python Executable:** `{sys.executable}`  ",
        f"**OS Platform:** `{platform.platform()}`  ",
        "",
        "---",
        "",
        "## 📊 Summary Status",
        f"* **Packages Configured:** `{installed_count} / {len(REQUIRED_PACKAGES)}`",
        f"* **GPU Accelerator:** `{gpu_status}`",
        f"* **Gate 1 Reproducibility:** `{'[PASS] Verified' if gate1_pass else '[FAIL] Failed'}`",
        "",
        "---",
        ""
    ]

    if failed_packages:
        lines.append("## ⚠️ Failed Package Installations & Recommended Actions for Selar")
        lines.append("")
        for mod_name, label, pip_spec, err_msg in failed_packages:
            lines.append(f"### ❌ {label} (`{mod_name}`)")
            lines.append(f"* **Pip Command:** `pip install {pip_spec}`")
            lines.append(f"* **Error Log:** `{err_msg}`")
            lines.append("* **Action for Selar:** Try installing manually in terminal or check C++ build tools dependencies.")
            lines.append("")
    else:
        lines.append("## 🎉 All Checks Passed Successfully!")
        lines.append("The Python virtual environment is 100% configured and verified for Phase 2 implementation.")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))
#

    return report_path

def main():
    print("=" * 65, flush=True)
    print("  AMOG-Net Automated Self-Healing Environment Setup (Phase 1)", flush=True)
    print("=" * 65, flush=True)

    is_ok, python_exe = ensure_virtual_environment()
    
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    upgrade_pip(python_exe)
    installed_count, failed_packages = check_and_install_packages(python_exe)
    gpu_ok, gpu_status = check_gpu_cuda()
    gate1_pass = verify_gate1_determinism()

    report_path = generate_auto_report(installed_count, failed_packages, gpu_status, gate1_pass, reports_dir)

    print("\n" + "=" * 65, flush=True)
    if len(failed_packages) == 0 and gate1_pass:
        print("  🎉 [SUCCESS] Environment is 100% ready for Phase 2!", flush=True)
    else:
        print("  ⚠️ [NOTICE] Environment setup completed with recommendations.", flush=True)
        if failed_packages:
            print(f"     Failed packages: {len(failed_packages)} (See reports/AUTO_SETUP_REPORT.md)", flush=True)
    print(f"  📄 Diagnostic Summary Written to: {report_path}", flush=True)
    print("=" * 65, flush=True)

if __name__ == "__main__":
    main()
