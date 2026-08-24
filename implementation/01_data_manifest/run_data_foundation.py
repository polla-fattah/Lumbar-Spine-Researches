# Phase 2 & 3 Master Pipeline Runner
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import os
import sys
import subprocess

def main():
    print("=" * 65)
    print("  AMOG-Net Track A: Data Foundation Pipeline (Phases 2 & 3)")
    print("=" * 65)

    py_exe = sys.executable
    base_dir = os.path.dirname(__file__)

    cmd_manifest = [py_exe, os.path.join(base_dir, "build_lumbarDISC_manifest.py")] + sys.argv[1:]
    print("\n---> Running Phase 2: DICOM Manifest Builder...")
    subprocess.run(cmd_manifest, check=True)

    cmd_splits = [py_exe, os.path.join(base_dir, "create_patient_splits.py")]
    print("\n---> Running Phase 3: Patient Split Construction & Gate 2 Test...")
    subprocess.run(cmd_splits, check=True)

    print("\n[SUCCESS] Track A Data Foundation Pipeline Complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
