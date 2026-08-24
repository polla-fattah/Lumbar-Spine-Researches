# System & Virtual Environment Diagnostic Scanner (Phase 1)
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import platform
import json
import importlib
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Package list to check
PACKAGES_TO_CHECK = [
    ("torch", "PyTorch Core"),
    ("torchvision", "TorchVision Vision Models"),
    ("pydicom", "DICOM File Parsing"),
    ("SimpleITK", "Medical Image Processing & Geometry"),
    ("monai", "Medical Open Network for AI"),
    ("nibabel", "Neuroimaging / NIfTI & DICOM Utilities"),
    ("numpy", "Numerical Computing"),
    ("pandas", "Dataframes & Manifest Handling"),
    ("scipy", "Scientific Computing & Interpolation"),
    ("sklearn", "Scikit-Learn Machine Learning & Metrics"),
    ("skimage", "Scikit-Image Image Analysis"),
    ("albumentations", "Fast Image Augmentations"),
    ("cv2", "OpenCV Computer Vision"),
    ("torch_geometric", "PyTorch Geometric (GNN Support)"),
    ("yaml", "YAML Configuration Parsing"),
    ("tqdm", "Progress Bars"),
    ("h5py", "HDF5 File Storage"),
    ("matplotlib", "Data Plotting"),
    ("seaborn", "Statistical Visualization"),
    ("statsmodels", "Statistical Hypotheses Testing")
]

def is_virtual_environment():
    in_venv = (sys.prefix != sys.base_prefix)
    in_conda = 'CONDA_DEFAULT_ENV' in os.environ
    
    if in_conda:
        env_type = "Conda"
        env_name = os.environ.get('CONDA_DEFAULT_ENV', 'lumbar_phd')
    elif in_venv:
        env_type = "venv"
        env_name = os.path.basename(sys.prefix)
    else:
        env_type = "Global Python"
        env_name = "None (System Global)"
        
    return {
        "is_isolated": in_venv or in_conda,
        "env_type": env_type,
        "env_name": env_name,
        "sys_prefix": sys.prefix,
        "sys_executable": sys.executable
    }

def check_system():
    env_info = is_virtual_environment()
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
        "os_platform": platform.platform(),
        "system_architecture": platform.architecture()[0],
        "processor": platform.processor() or "Unknown",
        "cpu_count_logical": os.cpu_count() or 1,
        "virtual_environment": env_info,
        "gpu_available": False,
        "gpus": [],
        "packages": {}
    }

    # RAM Check
    try:
        import psutil
        ram = psutil.virtual_memory()
        report["ram_total_gb"] = round(ram.total / (1024**3), 2)
        report["ram_available_gb"] = round(ram.available / (1024**3), 2)
    except ImportError:
        report["ram_total_gb"] = "Unknown (install psutil for detailed RAM specs)"

    # PyTorch & GPU / CUDA check
    try:
        import torch
        report["pytorch_version"] = torch.__version__
        report["cuda_available"] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            report["gpu_available"] = True
            report["cuda_version"] = torch.version.cuda
            report["cudnn_version"] = str(torch.backends.cudnn.version()) if torch.backends.cudnn.is_available() else "N/A"
            report["gpu_count"] = torch.cuda.device_count()
            
            for i in range(torch.cuda.device_count()):
                prop = torch.cuda.get_device_properties(i)
                gpu_info = {
                    "id": i,
                    "name": prop.name,
                    "total_vram_gb": round(prop.total_memory / (1024**3), 2),
                    "compute_capability": f"{prop.major}.{prop.minor}"
                }
                report["gpus"].append(gpu_info)
    except Exception as e:
        report["pytorch_check_error"] = str(e)

    # Package check
    missing_packages = []
    for pkg_import_name, label in PACKAGES_TO_CHECK:
        try:
            mod = importlib.import_module(pkg_import_name)
            ver = getattr(mod, "__version__", "Installed")
            report["packages"][label] = {"status": "Installed", "version": str(ver), "import_name": pkg_import_name}
        except ImportError:
            report["packages"][label] = {"status": "Missing", "version": None, "import_name": pkg_import_name}
            missing_packages.append(pkg_import_name)

    report["missing_packages_count"] = len(missing_packages)
    report["missing_package_names"] = missing_packages
    return report

def generate_markdown_report(report, reports_dir):
    md_path = os.path.join(reports_dir, "ENVIRONMENT_REPORT.md")
    
    lines = []
    lines.append("# System Diagnostic & Environment Availability Report")
    lines.append(f"**Generated At:** `{report['timestamp']}`  ")
    lines.append(f"**OS Platform:** `{report['os_platform']}` (`{report['system_architecture']}`)  ")
    lines.append(f"**Python Version:** `{report['python_version']}`  ")
    
    env_info = report["virtual_environment"]
    if env_info["is_isolated"]:
        lines.append(f"**Virtual Environment:** [OK] Active (`{env_info['env_type']}: {env_info['env_name']}`)  ")
    else:
        lines.append(f"**Virtual Environment:** [WARN] None (`Global System Python`)  ")
        
    lines.append(f"**Python Executable:** `{env_info['sys_executable']}`  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Hardware & Accelerators Availability")
    lines.append("")

    if report.get("gpu_available"):
        lines.append("**Status:** [OK] **GPU Hardware Accelerator Detected**")
        lines.append(f"* **CUDA Runtime:** `{report.get('cuda_version', 'N/A')}`")
        lines.append(f"* **cuDNN Version:** `{report.get('cudnn_version', 'N/A')}`")
        lines.append(f"* **Detected GPUs:** {report.get('gpu_count', 0)}")
        lines.append("")
        lines.append("| GPU ID | GPU Model | Total VRAM | Compute Capability | Recommended Batch Size (2.5D ROIs) |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        
        for g in report["gpus"]:
            vram = g["total_vram_gb"]
            if vram >= 20:
                rec_bs = "16 – 32"
            elif vram >= 12:
                rec_bs = "8 – 16"
            elif vram >= 8:
                rec_bs = "4 – 8"
            else:
                rec_bs = "2 – 4 (Use Gradient Accumulation)"
            
            lines.append(f"| {g['id']} | **{g['name']}** | `{vram} GB` | `{g['compute_capability']}` | **{rec_bs}** |")
    else:
        lines.append("**Status:** [WARN] **No GPU Accelerator / CUDA Enabled PyTorch Detected**")
        lines.append("* *Note: PyTorch is currently running in CPU mode. GPU acceleration is strongly recommended for Phase 7–13 training.*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Medical AI & PyTorch Dependency Status")
    lines.append("")
    lines.append("| Package Name | Purpose / Function | Status | Version |")
    lines.append("| :--- | :--- | :--- | :--- |")

    for label, info in report["packages"].items():
        if info["status"] == "Installed":
            status_str = "[OK] Installed"
            ver_str = f"`{info['version']}`"
        else:
            status_str = "[MISSING] **MISSING**"
            ver_str = "*Not Found*"
        lines.append(f"| {label} | `{info['import_name']}` | {status_str} | {ver_str} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Installation & Action Plan for Student (Selar)")
    lines.append("")

    if not env_info["is_isolated"]:
        lines.append("⚠️ **Virtual Environment Notice:** You are currently running in Global System Python.")
        lines.append("It is recommended to activate a `venv` or `conda` environment before installing dependencies:")
        lines.append("```bash")
        lines.append("python -m venv venv")
        lines.append(".\\venv\\Scripts\\activate   # On Windows")
        lines.append("```")
        lines.append("")

    if report["missing_packages_count"] == 0:
        lines.append("[OK] **All required packages are installed and ready for Phase 1 & 2!**")
    else:
        lines.append(f"[WARN] **{report['missing_packages_count']} required packages are missing.**")
        lines.append("")
        lines.append("Selar can install all missing packages at once by running:")
        lines.append("```bash")
        lines.append("python setup_environment.py")
        lines.append("```")
        lines.append("Or via pip:")
        lines.append("```bash")
        lines.append("pip install " + " ".join(report["missing_package_names"]))
        lines.append("```")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))
#
    
    return md_path

def main():
    print("=" * 65)
    print("  AMOG-Net System Diagnostic & Availability Scanner (Phase 1)")
    print("=" * 65)
    
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report = check_system()
    
    # Save JSON report
    json_path = os.path.join(reports_dir, "environment_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    # Save Markdown report
    md_path = generate_markdown_report(report, reports_dir)

    print(f"\nPython Version : {report['python_version']}")
    print(f"OS Platform    : {report['os_platform']}")
    
    env_info = report["virtual_environment"]
    if env_info["is_isolated"]:
        print(f"Environment    : Active ({env_info['env_type']}: {env_info['env_name']})")
    else:
        print(f"Environment    : [NOTICE] Running in Global Python (venv/conda recommended)")
        
    if report.get("gpu_available"):
        print(f"GPU Detected   : YES ({report['gpu_count']} GPU(s))")
        for g in report["gpus"]:
            print(f"  -> GPU {g['id']}: {g['name']} ({g['total_vram_gb']} GB VRAM)")
    else:
        print("GPU Detected   : NO / PyTorch running on CPU")

    print(f"\nPackage Check  : {len(PACKAGES_TO_CHECK) - report['missing_packages_count']} / {len(PACKAGES_TO_CHECK)} Installed")
    
    if report["missing_packages_count"] > 0:
        print(f"\n[WARN] Missing Packages: {', '.join(report['missing_package_names'])}")
        print("   Run 'python setup_environment.py' to install missing dependencies.")
    else:
        print("\n[OK] All required packages are installed!")

    print(f"\nDetailed reports generated:")
    print(f"   - {md_path}")
    print(f"   - {json_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()
