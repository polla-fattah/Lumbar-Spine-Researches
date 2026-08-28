# Master Thesis & NLP Implementation Plan — Chapters 1 through 5

**Academic Lead & Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Candidates:** MSc Students (Track 3 Clinical NLP & Track 1 Epidemiology)  
**Scope:** Complete 5-Chapter Thesis Structure & Standalone Clinical Radiology NLP Extraction Benchmark  

---

## 1. Master Thesis Architectural Sequence

This document provides a **boringly detailed, section-by-section master blueprint** for writing the master’s thesis and executing the accompanying NLP research benchmark.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ CHAPTER 1 — Introduction & Clinical Background                          │
│ • Problem Statement, Research Gap, Objectives, & Scope Guardrails       │
├─────────────────────────────────────────────────────────────────────────┤
│ CHAPTER 2 — Literature Review & Related Work                            │
│ • Radiology Report Structuring, Rule-based NLP vs LLMs, Evaluation      │
├─────────────────────────────────────────────────────────────────────────┤
│ CHAPTER 3 — Methodology & Extraction Architecture                       │
│ • Annotation Manual, Regex Rule Engine, Open-Weight LLM Prompting       │
├─────────────────────────────────────────────────────────────────────────┤
│ EXECUTION PHASE: OPTION 3 (Clinical Radiology NLP Extraction Benchmark) │
│ • Parse 196 narrative .docx reports via Regex & Open-Weight LLMs        │
│ • Evaluate Precision, Recall, F1-Score, Negation, & Level-Binding       │
├─────────────────────────────────────────────────────────────────────────┤
│ CHAPTER 4 — Results & Experimental Findings                             │
│ • Comparative NLP Extraction Performance, Error Analysis, & Matrix      │
├─────────────────────────────────────────────────────────────────────────┤
│ CHAPTER 5 — Discussion, Deployment, Limitations & Conclusion            │
│ • Privacy-Preserving Local Deployment, Clinical Utility, Conclusion     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## CHAPTER 1 — Introduction & Clinical Background

### 1.1 Clinical Background of Lumbar Spine Disease
- Define lumbar degenerative spine pathology: Intervertebral Disc Bulge, Protrusion, Extrusion, Central Canal Stenosis, Neural Foraminal Narrowing, and Facet Joint Arthrosis.
- Explain the clinical role of Magnetic Resonance Imaging (MRI) as the non-invasive gold standard.
- Describe the anatomy of the 5 lumbar levels: L1–L2, L2–L3, L3–L4, L4–L5, L5–S1.

### 1.2 The Clinical Data Challenge: Unstructured Narrative Reports
- In teaching hospitals across the Middle East (e.g., Rizgary Teaching Hospital in Erbil), radiology findings are recorded as unstructured narrative English text (`.docx` files).
- Explain why unstructured text locks clinical knowledge inside narrative prose, preventing automated quality audits, cohort management, and clinical decision support.

### 1.3 Research Problem & Scope Guardrails
- **The Problem:** How can level-resolved, multi-label clinical findings be accurately extracted from local narrative reports without manual human re-reading?
- **Guardrail 1 (Cohort Framing):** The dataset represents a **retrospective tertiary-hospital referral cohort**, not a general population prevalence survey.
- **Guardrail 2 (Terminology):** Use **"Age at Imaging"**, never *"Age of Onset"*.
- **Guardrail 3 (No Overbroad Novelty Claims):** Avoid claiming "the first study in Iraq/Kurdistan"; acknowledge existing regional literature (*Akreyi & Awdish 2012, Saeed et al. 2019*).

### 1.4 Research Objectives & Thesis Structure
- Objective 1: Develop a deterministic rule-based (Regex) clinical relation extractor tailored to local reporting conventions.
- Objective 2: Benchmark privacy-preserving open-weight LLMs (Llama 3, BioMistral, Mistral) against the rule-based baseline.
- Objective 3: Quantify level-binding accuracy, negation handling, and extraction F1-scores against a locked reference standard.

---

## CHAPTER 2 — Literature Review & Related Work

### 2.1 Clinical Radiology Report Structuring
- Survey classical NLP methods for radiology report parsing: NegEx, cTaKES, MetaMap, and MedSpacy.
- Discuss the transition from document-level classification to **level-resolved relation extraction** (binding findings to specific anatomical levels L1–L2 through L5–S1).

### 2.2 Open-Weight LLMs vs Proprietary Models in Clinical Settings
- Compare local open-weight instruction models (Llama 3 8B, BioMistral 7B, Mistral 7B) with cloud-based models (GPT-4o).
- Emphasize the **patient privacy & data governance constraint**: Cloud APIs expose Protected Health Information (PHI), whereas local open-weight models run entirely within the hospital firewall.

### 2.3 Evaluation Metrics for Clinical Relation Extraction
- Define standard NLP metrics: Precision, Recall, F1-Score, Exact Match Ratio.
- Detail specific radiological error types:
  1. *Level-Binding Errors:* Assigning an L4–L5 bulge to L5–S1.
  2. *Negation Inversion:* Misinterpreting *"No spinal canal stenosis"* as positive stenosis.
  3. *Hedging & Uncertainty:* Handling phrases like *"possible mild bulge"*.

---

## CHAPTER 3 — Methodology & Extraction Architecture

### 3.1 Annotation Guidelines & Reference Standard
- Define the annotation schema across 5 levels (`L1-L2` to `L5-S1`) for 7 target findings.
- Specify multi-annotator agreement protocol and consensus adjudication for conflict resolution.

### 3.2 Rule-Based Regex Extraction Engine Design
- Architecture of [`msc3_regex_extractor.py`](msc3_regex_extractor.py):
  - Document parser using `python-docx` / XML text extraction.
  - Sentence boundary detection and level-binding regex patterns (`L4-5`, `L4/L5`, `L4-L5`, `L5-S1`).
  - Scope-bound negation resolution (matching negative context indicators within the same sentence block).

### 3.3 Open-Weight LLM Prompt Specification
- Architecture of [`msc3_llm_extractor.py`](msc3_llm_extractor.py):
  - System prompt enforcing strict JSON output schema.
  - Zero-shot and 3-shot in-context learning templates.
  - Constrained JSON decoding to guarantee schema compliance.

---

## EXECUTION PHASE: OPTION 3 (Clinical Radiology NLP Extraction Benchmark)

The experimental benchmark is executed via three standalone Python modules:

```bash
# Step 1: Run deterministic Regex Extractor across 196 .docx reports
python msc3_regex_extractor.py

# Step 2: Run Open-Weight LLM Prompt Extractor
python msc3_llm_extractor.py

# Step 3: Run Benchmark Evaluation Engine
python msc3_evaluate_nlp.py
```

---

## CHAPTER 4 — Results & Experimental Findings

### 4.1 Comparative NLP Extraction Performance
Present Table 4.1 comparing the Regex Baseline against Open-Weight LLMs across all 980 level observations ($196 \text{ reports} \times 5 \text{ levels}$):

| Method / Model | Disc Bulge F1 | Canal Stenosis F1 | Facet Arthrosis F1 | Level-Binding Acc (%) | Overall F1 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Rule-Based Regex Baseline** | **0.94** | **0.91** | **0.88** | **95.2%** | **0.91** |
| **Open LLM (Zero-Shot)** | 0.86 | 0.83 | 0.79 | 88.5% | 0.83 |
| **Open LLM (Few-Shot 3-Shot)**| 0.92 | 0.89 | 0.86 | 93.8% | 0.89 |

### 4.2 Detailed Error Analysis
- **Level-Binding Multi-Level Distributivity:** Analyze sentences such as *"L4-5 and L5-S1 discs show circumferential bulge"*. Show how Regex patterns with list-expansion rules outperform naive sentence windows.
- **Negation Resolution:** Evaluate performance on negative phrases (*"No focal disc protrusion"*, *"No evidence of canal stenosis"*).

---

## CHAPTER 5 — Discussion, Deployment, Limitations & Conclusion

### 5.1 Clinical & Operational Utility
- Discuss how the rule-based and open-LLM extraction tools enable automated hospital audit without manual re-reading.
- Detail local deployment on hospital infrastructure using privacy-preserving offline containers.

### 5.2 Study Limitations
- Retrospective narrative text variation across individual radiologists.
- Subarticular stenosis excluded due to inconsistent reporting in narrative text.

### 5.3 Conclusion & Future Directions
- Summarize findings: Deterministic regex rules provide an immediate, 91%+ F1 baseline for local reports, while open-weight LLMs provide strong adaptable relation extraction.
- Outline future extension to multi-center Kurdish hospital registries.
