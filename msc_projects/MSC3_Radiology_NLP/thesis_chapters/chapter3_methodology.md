# Chapter 3 — Methodology and System Architecture

**Project Title:** Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  

---

## 3.1 Overview of Extraction Architecture

This chapter details the design, implementation, and evaluation framework for extracting level-resolved findings from narrative radiology reports. The system architecture consists of three modular components:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      NARRATIVE RADIOLOGY REPORTS                        │
│                195 .docx files (Rizgary Teaching Hospital)              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│  RULE-BASED REGEX ENGINE        │     │  OPEN-WEIGHT LLM PIPELINE       │
│  • msc3_regex_extractor.py      │     │  • msc3_llm_extractor.py        │
│  • Sentence segmentation        │     │  • Zero-shot & 3-shot JSON      │
│  • Multi-level list expansion   │     │  • Constrained JSON decoding    │
│  • Negation boundary parsing    │     │  • Llama-3-8B / BioMistral      │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BENCHMARK EVALUATION ENGINE                          │
│                    • msc3_evaluate_nlp.py                               │
│                    • Precision, Recall, F1-Score, Level-Binding Acc     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3.2 Reference Annotation Guidelines & Ground Truth

To construct an auditable reference standard, 195 narrative reports from Rizgary Teaching Hospital were extracted and structured across five lumbar levels (`L1-L2`, `L2-L3`, `L3-L4`, `L4-L5`, `L5-S1`), yielding a total of **975 level-resolved ground-truth observations**.

### Target Pathology Definitions
1. **Disc Bulge:** Circumferential, symmetrical extension of disc material beyond the vertebral border.
2. **Disc Protrusion:** Focal, asymmetrical displacement of disc material where the base is wider than any other dimension.
3. **Disc Extrusion:** Focal displacement where the disc material extends beyond the disc space with narrow base.
4. **Central Canal Stenosis:** Narrowing of the central spinal canal resulting in dural sac compression.
5. **Facet Joint Arthrosis:** Hypertrophic degenerative changes of the posterior facet joint.
6. **Osteophytes:** Marginal osseous spurring along vertebral body endplates.

---

## 3.3 Rule-Based Regex Extraction Engine (`msc3_regex_extractor.py`)

The deterministic Rule-Based Regex Extractor executes in four sequential stages:

### Stage 1: Document Parsing & Text Normalization
The engine utilizes Python's standard `zipfile` and `xml.etree.ElementTree` modules to read `word/document.xml` directly from `.docx` files. This avoids external binary dependencies while preserving document order. Whitespace and non-standard punctuation are normalized.

### Stage 2: Sentence Segmentation & Level Binding
Reports are segmented into sentence blocks using punctuation delimiters (`.`, `;`, `\n`). Each sentence is scanned for level-matching patterns using regex aliases:

```python
LEVEL_PATTERNS = {
    "L1-L2": [r"\bl1[-_ /]*2\b", r"\bl1[-_ /]*l2\b"],
    "L2-L3": [r"\bl2[-_ /]*3\b", r"\bl2[-_ /]*l3\b"],
    "L3-L4": [r"\bl3[-_ /]*4\b", r"\bl3[-_ /]*l4\b"],
    "L4-L5": [r"\bl4[-_ /]*5\b", r"\bl4[-_ /]*l5\b"],
    "L5-S1": [r"\bl5[-_ /]*s1\b", r"\bl5[-_ /]*1\b"]
}
```

### Stage 3: Negation & Context Scoping
Within each level-matched sentence, a scope-bound negation check is performed for trigger phrases:
$$\text{IsNegated} = \text{RegexMatch}(\text{sentence}, \text{`\b(no|normal|without|absent|unremarkable)\b`})$$

If a negation trigger is present, findings within that sentence block are assigned a `0` status, preventing false positive extraction.

### Stage 4: Multi-Level List Expansion
When a sentence references multiple levels (e.g., *"L4-5 and L5-S1 discs show bulge"*), the extracted finding is expanded to all referenced levels simultaneously.

---

## 3.4 Open-Weight LLM Prompt Engineering (`msc3_llm_extractor.py`)

To evaluate generative relation extraction, structured JSON prompt templates were designed for local open-weight instruction models.

### System Prompt Specification
```text
System: You are an expert clinical AI assistant specialized in radiology report relation extraction.
Your task is to parse an English Lumbar Spine MRI radiology report and extract findings for 5 spinal levels: L1-L2, L2-L3, L3-L4, L4-L5, L5-S1.

Return ONLY a valid JSON object matching this exact schema:
{
  "findings": {
    "L1-L2": {"disc_bulge": 0, "disc_protrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0},
    "L2-L3": {"disc_bulge": 0, "disc_protrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0},
    "L3-L4": {"disc_bulge": 0, "disc_protrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0},
    "L4-L5": {"disc_bulge": 0, "disc_protrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0},
    "L5-S1": {"disc_bulge": 0, "disc_protrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0}
  }
}
```

Both **Zero-Shot** and **Few-Shot (3-Shot)** in-context learning configurations were implemented to evaluate schema adherence and extraction accuracy.

---

## 3.5 Evaluation Protocol (`msc3_evaluate_nlp.py`)

The evaluation script compares extracted outputs from both engines against the audited ground-truth reference matrix (`elaf_audited_cohort_matrix.csv`). Precision, Recall, Macro F1-Score, Negation Accuracy, and Level-Binding Accuracy are calculated across all 975 level observations.
