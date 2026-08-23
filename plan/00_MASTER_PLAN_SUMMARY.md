# Lumbar Spine MRI Research Program — Master Plan Summary

**Project Title:** Lumbar Spine MRI AI & Clinical Studies (Rizgary Teaching Hospital & International Benchmarks)  
**Lead Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Primary PhD Candidate:** Selar  
**Date:** 2026-08-23  

---

## 1. Program Vision & Core Philosophy

This master plan establishes a modular, risk-mitigated research program that bridges **Computer Science / Deep Learning innovation** with **Genuinely Actionable Clinical Utility**.

To avoid the common pitfall of medical AI projects—where a single student attempts a massive scope and risks stalling out—the research is partitioned into:
1. **One Clear, High-Impact PhD Path (Selar)** focusing on algorithmic methodology, cross-institutional domain transfer, and multi-sequence graph deep learning.
2. **Four Modular MSc Spin-Off Projects** that utilize the data infrastructure, pre-trained models, and clinical datasets created during Phase 1 to produce independent, high-ROI research publications.

```mermaid
flowchart TD
    subgraph Data Infrastructure & Audit
        D1[299 Local English Radiology Reports]
        D2[294 Local Multi-Sequence DICOMs]
        D3[1,975 RSNA Kaggle Studies Held]
        
        D1 -->|NLP Extract & Manual Dual Audit| Gold[Local Gold Standard Matrix<br/>canal + foraminal + herniation]
    end

    subgraph Primary PhD Core: Selar
        Gold & D3 --> PhD["Selar PhD Roadmap: AMOG-Net & Cross-Institutional Domain Transfer"]
        PhD --> Paper1["📄 Paper 1 (CS/AI): IEEE TMI / MedIA / MICCAI"]
        PhD --> Paper2["📄 Paper 2 (Medical AI): Radiology: AI / Eur. Radiol."]
    end

    subgraph Modular MSc Spin-Off Projects
        Gold --> MSc1["📚 MSc 1: Kurdish Population Lumbar Epidemiology"]
        PhD --> MSc2["📚 MSc 2: Rapid Triage Protocol Optimization"]
        D1 --> MSc3["📚 MSc 3: Clinical NLP Report Structuring Benchmark"]
        Gold --> MSc4["📚 MSc 4: Clinical Symptom & Surgical Prognostics"]
    end
```

---

## 2. Allocation Matrix & Publication Strategy

| Project | Primary Focus | Required Assets | Target Venues | Estimated Duration |
| :--- | :--- | :--- | :--- | :---: |
| **Selar PhD Roadmap** | Multi-sequence Graph Transformers, Zero-Shot & Few-Shot Domain Transfer | RSNA Benchmark (1,975 held) + Rizgary DICOMs (294) + Audited Matrix | *IEEE TMI*, *Medical Image Analysis*, *Radiology: AI* | 21–24 Months |
| **MSc Project 1** | First Kurdish/Iraqi Lumbar Degeneration Population Epidemiology | Audited 25-Target Matrix (299 cases) | *European Spine Journal*, *J. Orthop. Surg. Res.* | 4–6 Months |
| **MSc Project 2** | Sequence-Sparing Rapid Triage Protocol Optimization | AMOG-Net Trained Model + 294 Local DICOM Studies | *European Journal of Radiology*, *BMC Med. Imaging* | 6 Months |
| **MSc Project 3** | Clinical NLP & Information Extraction for Unstructured Reports | 299 Narrative `.docx` Radiology Reports | *Journal of Biomedical Informatics*, *IEEE JBHI* | 6–8 Months |
| **MSc Project 4** | Radiological Severity vs. Clinical Symptom & Surgical Outcome Prognostics | Audited Matrix + Hospital Symptom Logs | *The Spine Journal*, *Spine* | 6 Months (Bonus) |

---

## 3. Data Governance & Hard Rules

1. **Do NOT Train on Folder Names (`normal/bulge/protrusion/extrusion`):** The folder classification is lossy and contains errors (multi-level hernia co-occurrence, duplicate cases). All ground truth must derive from the audited local matrix. NOTE: this is NOT RSNA's 25-target schema. Verified across all 299 reports -- spinal canal stenosis appears in 97%, neural foraminal narrowing in 78%, but subarticular/lateral recess stenosis in **0%** (six spellings checked) and laterality is stated in only 27%. Ten of RSNA's 25 targets (left/right subarticular) cannot be evaluated on this cohort at all.
2. **Reports are Primary; Spreadsheet is Secondary:** The manual spreadsheet (`research LSS 1.xlsx`) covers only 195 cases and contains 14 age transcription errors. The 299 narrative `.docx` reports are the single source of truth.
3. **Ground truth must be verified before any model is evaluated against it.** The 299
   reports must be structured and manually checked before they are used as a reference
   standard. This is a *quality* rule, not a *sequencing* rule.

> [!IMPORTANT]
> **Sequencing correction — the original dependency chain was fragile.**
>
> As first written, every MSc project waited on Selar's Phase 1, and MSc 2 additionally
> waited on Selar's Phase 2 (~month 10). That routes four students' graduations through
> one student's research risk: if Selar's PhD slips, everything slips.
>
> **Revised sequencing, which removes every avoidable dependency:**
>
> | Project | Starts | Depends on |
> | :--- | :--- | :--- |
> | **MSc 1 — Epidemiology** | **Immediately** | Nothing. Extract the 299 reports by hand (~25–40 h). |
> | **MSc 3 — Clinical NLP** | **Immediately** | Nothing. *Owns* the automated extraction and delivers the gold-standard matrix to everyone else. |
> | **MSc 2 — Protocol Optimisation** | **Immediately** | A simple ResNet/EfficientNet baseline, *not* AMOG-Net. |
> | **Selar PhD** | **Immediately** | RSNA data only until Phase 3. Local cohort not needed until month ~11. |
> | **MSc 4 — Prognostics** | **Not yet** | Unconfirmed clinical data. See the caution in its roadmap. |
>
> The natural cross-check falls out of this for free: MSc 1's manual extraction and MSc 3's
> automated extraction cover the same 299 reports, so their agreement becomes a validation
> result for MSc 3 rather than a scheduling conflict.
>
> **Move report extraction out of Selar's Phase 1 and into MSc 3.** It shortens the PhD's
> critical path and gives MSc 3 a genuine deliverable to own.

---

## 4. Directory Structure of the Plan

All detailed individual roadmaps are stored in `c:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\plan\`:

- [`00_MASTER_PLAN_SUMMARY.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/00_MASTER_PLAN_SUMMARY.md) — This master overview.
- [`01_SELAR_PHD_ROADMAP.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/01_SELAR_PHD_ROADMAP.md) — Selar's complete PhD research plan and execution strategy.
- [`02_MSC1_EPIDEMIOLOGY_ROADMAP.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/02_MSC1_EPIDEMIOLOGY_ROADMAP.md) — MSc 1: Population Epidemiology Study.
- [`03_MSC2_PROTOCOL_OPTIMIZATION_ROADMAP.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/03_MSC2_PROTOCOL_OPTIMIZATION_ROADMAP.md) — MSc 2: Rapid Triage Protocol Optimization.
- [`04_MSC3_CLINICAL_NLP_ROADMAP.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/04_MSC3_CLINICAL_NLP_ROADMAP.md) — MSc 3: Clinical Information Extraction NLP Benchmark.
- [`05_MSC4_CLINICAL_PROGNOSTICS_ROADMAP.md`](file:///c:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/plan/05_MSC4_CLINICAL_PROGNOSTICS_ROADMAP.md) — MSc 4: Clinical Symptom & Surgical Outcome Prognostics.
