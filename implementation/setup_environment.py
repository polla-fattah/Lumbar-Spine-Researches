# Environment Setup & Project Workspace Initializer (Phase 1)
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import subprocess

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

def check_or_create_venv():
    in_venv = (sys.prefix != sys.base_prefix) or ('CONDA_DEFAULT_ENV' in os.environ)
    if in_venv:
        print("[OK] Active virtual environment detected.")
        return True
    else:
        print("[NOTICE] You are currently running in Global System Python.")
        base_dir = os.path.dirname(__file__)
        venv_dir = os.path.join(base_dir, "venv")
        
        if not os.path.exists(venv_dir):
            print(f"   Creating a virtual environment 'venv' in {venv_dir}...")
            try:
                subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
                print("[OK] Virtual environment created successfully.")
                print(f"   Activate it with:")
                if os.name == 'nt':
                    print("     .\\venv\\Scripts\\activate")
                else:
                    print("     source venv/bin/activate")
            except Exception as e:
                print(f"[FAIL] Failed to create virtual environment: {e}")
        else:
            print(f"   Virtual environment folder 'venv' exists. Activate it with:")
            if os.name == 'nt':
                print("     .\\venv\\Scripts\\activate")
            else:
                print("     source venv/bin/activate")
        return False

def install_dependencies():
    print("\n[PACKAGES] Checking and installing dependencies from requirements.txt...")
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(req_file):
        print(f"[FAIL] Error: {req_file} not found.")
        return False
        
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("[OK] All dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Dependency installation failed: {e}")
        return False

def create_workspace():
    print("\n[WORKSPACE] Initializing Phase 1 Project Workspace Structure...")
    base_dir = os.path.dirname(__file__)
    
    for folder in WORKSPACE_DIRECTORIES:
        full_path = os.path.join(base_dir, folder)
        os.makedirs(full_path, exist_ok=True)
        
        if folder.startswith("src/"):
            init_file = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(f"# {folder} module initialization\n")
        print(f"  [OK] Created directory: {folder}")
        
    print("[OK] Project directory structure created cleanly.")

def main():
    print("=" * 65)
    print("  AMOG-Net Environment Setup & Workspace Initializer (Phase 1)")
    print("=" * 65)
    
    check_or_create_venv()
    install_dependencies()
    create_workspace()
    
    print("\n[COMPLETE] Workspace Setup Complete!")
    print("   Next step: Run 'python verify_determinism.py' to run Gate 1 tests.")
    print("=" * 65)

if __name__ == "__main__":
    main()
