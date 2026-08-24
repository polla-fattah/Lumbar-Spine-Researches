# Selar's Lumbar Spine MRI PhD Implementation Environment (Phase 1)

Welcome to the implementation codebase for **AMOG-Net** (Adaptive Multi-sequence Anatomical-Graph Network).

This directory (implementation/) contains the foundational system diagnostic, dependency installer, and Phase 1 reproducibility verification tools for Selar's research project.

---

## 🚀 Quick Start Guide for Selar

Follow these 3 simple steps to prepare your development environment and verify hardware availability:

### Step 1: Run System Diagnostic & Availability Check
Run the system diagnostic script to inspect your Python version, GPU availability, CUDA setup, and medical imaging libraries:

`bash
python check_environment.py
`

This will print a summary to your terminal and auto-generate two detailed diagnostic reports:
* 
eports/ENVIRONMENT_REPORT.md (Human-readable summary of installed vs. missing dependencies and hardware specs)
* 
eports/environment_report.json (Structured JSON log of system specs and package versions)

---

### Step 2: Install Missing Packages (Auto-Installer)
If check_environment.py identifies missing packages, run the automated setup script:

`ash
python setup_environment.py
`

Or install dependencies manually via 
equirements.txt:

`ash
pip install -r requirements.txt
`

---

### Step 3: Run Gate 1 Determinism & Reproducibility Test
Before launching any model training, verify that PyTorch GPU random seed setting and deterministic operations are working cleanly:

`ash
python verify_determinism.py
`

If the test outputs [PASS] Gate 1 Reproducibility Verified, your environment is fully prepared for Phase 2 (LumbarDISC DICOM Manifest & Dataset Split Construction).

---

## 📁 Implementation Directory Structure

`	ext
implementation/
├── README.md                 # This instruction guide
├── check_environment.py      # System diagnostic & availability scanner
├── setup_environment.py      # Automated package installer & workspace initializer
├── verify_determinism.py     # Gate 1 PyTorch reproducibility and seed verification script
├── requirements.txt          # Production pip package requirements
├── environment.yml           # Conda environment specification
└── reports/                  # Auto-generated system diagnostic reports
`
