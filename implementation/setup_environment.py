"""
Environment Setup & Project Workspace Initializer (Phase 1)
Author: Dr. Polla Fattah / Selar's PhD Research Team
Project: AMOG-Net Lumbar Spine MRI Automated Grading

This script:
1. Installs required python dependencies from requirements.txt
2. Creates the mandatory Phase 1 research workspace directory structure
3. Initializes empty __init__.py files in module folders
"""

import sys
import os
import subprocess
import shutil

# Recommended repository layout from implementationTODO.md (Phase 1)
WORKSPACE_DIRECTORIES = [
    "configs/datasets",
    "configs/models",
    "configs/experiments",
    "configs/adaptation",
    "data/manifests",
    "data/splits",
    "data/derived",
    "src/dicom",
    "src/preprocessing",
    "src/localisation",
    "src/roi",
    "src/encoders",
    "src/ssl",
    "src/routing",
    "src/graph",
    "src/losses",
    "src/calibration",
    "src/evaluation",
    "scripts",
    "tests",
    "experiments",
    "reports",
    "notebooks",
    "docs"
]

def install_dependencies():
    print("\n📦 Checking and installing dependencies from requirements.txt...")
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(req_file):
        print(f"❌ Error: {req_file} not found.")
        return False
        
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("✅ All dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return False

def create_workspace():
    print("\n📁 Initializing Phase 1 Project Workspace Structure...")
    base_dir = os.path.dirname(__file__)
    
    for folder in WORKSPACE_DIRECTORIES:
        full_path = os.path.join(base_dir, folder)
        os.makedirs(full_path, exist_ok=True)
        
        # Add __init__.py if inside src/
        if folder.startswith("src/"):
            init_file = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(f"# {folder} module initialization\n")
        print(f"  [OK] Created directory: {folder}")
        
    print("✅ Project directory structure created cleanly.")

def main():
    print("=" * 65)
    print("  AMOG-Net Environment Setup & Workspace Initializer (Phase 1)")
    print("=" * 65)
    
    # 1. Install packages
    install_dependencies()
    
    # 2. Build directory skeleton
    create_workspace()
    
    print("\n🎉 Workspace Setup Complete!")
    print("   Next step: Run 'python verify_determinism.py' to run Gate 1 tests.")
    print("=" * 65)

if __name__ == "__main__":
    main()
