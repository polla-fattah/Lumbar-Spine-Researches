# Selar's Lumbar Spine MRI PhD Implementation Environment (Phase 1)

Welcome to the implementation codebase for **AMOG-Net** (Adaptive Multi-sequence Anatomical-Graph Network).

This directory (`implementation/`) contains the system diagnostic, virtual environment manager, dependency installer, and Phase 1 reproducibility verification tools for Selar's PhD research project.

---

## 💡 Environment Strategy: Virtual Environment Isolation (`venv` or `conda`)

To prevent package conflicts and ensure reproducibility, **Selar must run in an isolated Python virtual environment**. 

Choose one of the two options below:

### Option A: Standard Python `venv` (Recommended for lightweight setups)

**On Windows (PowerShell / Command Prompt):**
```bash
# 1. Create a virtual environment named 'venv'
python -m venv venv

# 2. Activate the virtual environment
.\venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip
```

**On Linux / macOS (Bash / Zsh):**
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate
source venv/bin/activate

# 3. Upgrade pip
python -m pip install --upgrade pip
```

---

### Option B: Conda / Mamba Environment (Recommended if using Anaconda)

```bash
# 1. Create environment from environment.yml
conda env create -f environment.yml

# 2. Activate environment
conda activate lumbar_phd
```

---

## 🚀 Quick Start Workflow for Selar (Once Environment is Activated)

Follow these 3 steps:

### Step 1: Run System Diagnostic & Availability Check
Inspect Python version, active environment (`venv`/`conda`), GPU availability, CUDA setup, and medical imaging packages:

```bash
python check_environment.py
```

This will print a diagnostic summary and generate two detailed reports:
* `reports/ENVIRONMENT_REPORT.md` (Human-readable markdown summary)
* `reports/environment_report.json` (Structured JSON system log)

---

### Step 2: Install Missing Dependencies (Auto-Installer)
If `check_environment.py` flags missing libraries, run the automated setup script:

```bash
python setup_environment.py
```

Or install dependencies manually via `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

### Step 3: Run Gate 1 Determinism & Reproducibility Test
Before launching any training, verify PyTorch seed determinism:

```bash
python verify_determinism.py
```

When you see `[PASS] Gate 1 Reproducibility Verified`, your environment is fully prepared for Phase 2 (LumbarDISC DICOM Manifest & Dataset Split Construction).

---

## 📁 Implementation Directory Structure

```text
implementation/
├── README.md                 # Environment guide and workflow instructions
├── check_environment.py      # System & virtual environment diagnostic scanner
├── setup_environment.py      # Virtual environment helper & dependency installer
├── verify_determinism.py     # Gate 1 PyTorch reproducibility and seed test script
├── requirements.txt          # Production pip dependency list
├── environment.yml           # Conda environment specification
└── reports/                  # Auto-generated system diagnostic reports
    ├── ENVIRONMENT_REPORT.md # Markdown environment report
    └── environment_report.json # JSON system specs log
```
