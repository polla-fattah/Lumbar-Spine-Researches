# Phase 0: Operational DICOM De-identification & PHI Anonymization Protocol

This directory (`implementation/00_deidentify/`) implements **Phase 0 Data Governance & De-identification** in accordance with **DICOM PS 3.15 Annex E (Basic Application Level Confidentiality Profile)** and HIPAA/GDPR clinical privacy regulations.

---

## 🔒 Why Phase 0 is Mandatory

Before any manifest builder, localization network, or deep learning model processes clinical DICOM files, all **Protected Health Information (PHI)** must be stripped or pseudonymized:
* **Patient Name (`(0010,0010)`):** Completely erased and replaced with a deterministic anonymized ID (`ANON_P_xxxx`).
* **Patient Birth Date (`(0010,0030)`):** Erased or sanitized to year-only.
* **Physician & Operator Names (`(0008,0090)`, `(0008,1048)`):** Erased.
* **Institution Name & Address (`(0008,0080)`, `(0008,0081)`):** Erased or standardized to `ANON_INSTITUTION`.
* **Patient ID Mapping Table:** Stored securely in `data/governance/deidentification_key_mapping.csv` (never committed to open repositories).

---

## 🚀 How to Run Phase 0 De-identification

### Step 1: Run DICOM Anonymization Engine
Point the script to your raw input DICOM directory and output anonymized directory:

```bash
python deidentify_dicom.py --input_dir "C:\path\to\raw_dicoms" --output_dir "C:\path\to\deidentified_dicoms"
```

If testing with a synthetic/mock dataset:
```bash
python deidentify_dicom.py --use_synthetic
```

This generates:
* Anonymized DICOM files in `--output_dir`
* Secure key lookup table in `../../data/governance/deidentification_key_mapping.csv`
* Audit report in `reports/deidentification_audit.md`

---

### Step 2: Run De-identification Verification Audit
Verify that 100% of DICOM files in the output folder are completely clean of PHI:

```bash
python verify_deidentification.py --check_dir "C:\path\to\deidentified_dicoms"
```

If all PHI tags are clear, the verification test outputs:
`[PASS] Phase 0 Governance Audit Verified – 0 PHI Tags Detected.`
