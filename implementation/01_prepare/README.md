# Selar's Lumbar Spine MRI PhD Implementation Environment (Phase 1)

Welcome to the implementation codebase for **AMOG-Net** (Adaptive Multi-sequence Anatomical-Graph Network).

This directory (`implementation/`) contains the automated self-healing environment setup, dependency configurator, system diagnostic, and Phase 1 reproducibility verification tools for Selar's PhD research project.

---

## ⚡ 1-Click Automated Setup Strategy (Recommended for Selar)

You can set up your entire environment with **a single command**.

The automated setup script will:
1. **Detect / Create Virtual Environment (`venv`):** Automatically creates `venv/` if missing and switches execution into it.
2. **Upgrade Pip & Tools:** Ensures package installation tools are up to date.
3. **Audit & Self-Heal Dependencies:** Inspects all 20 medical AI libraries (`torch`, `pydicom`, `SimpleITK`, `monai`, `nibabel`, `albumentations`, `torch_geometric`, etc.) and automatically installs any missing packages.
4. **Hardware & CUDA Diagnostic:** Checks GPU availability and VRAM specs.
5. **Gate 1 Seed Determinism Test:** Runs PyTorch bit-for-bit output reproducibility verification.
6. **Generate Executive Report:** Writes `reports/AUTO_SETUP_REPORT.md` telling you if everything passed or what action to take if a package failed.

### How to Run:

**On Windows:**
Double-click `run_env_check.bat` or run in terminal:
```bash
python auto_setup_and_verify.py
```

**On Linux / macOS:**
```bash
chmod +x run_env_check.sh
./run_env_check.sh
```

---

## 📁 Implementation Directory Structure

```text
implementation/
├── README.md                 # Environment guide and workflow instructions
├── auto_setup_and_verify.py  # Master 1-click self-healing environment & Gate 1 script
├── run_env_check.bat         # 1-Click Windows batch launcher
├── run_env_check.sh          # 1-Click Linux/macOS shell launcher
├── check_environment.py      # System & virtual environment diagnostic scanner
├── setup_environment.py      # Workspace directory skeleton builder
├── verify_determinism.py     # Gate 1 PyTorch reproducibility and seed test script
├── requirements.txt          # Production pip dependency list
├── environment.yml           # Conda environment specification
└── reports/                  # Auto-generated system diagnostic reports
    ├── AUTO_SETUP_REPORT.md  # Master automated setup & self-healing log
    ├── ENVIRONMENT_REPORT.md # Markdown environment report
    └── environment_report.json # JSON system specs log
```
