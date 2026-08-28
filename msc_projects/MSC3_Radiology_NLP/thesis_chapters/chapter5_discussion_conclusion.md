# Chapter 5 — Discussion, Clinical Deployment, Limitations, and Conclusion

**Project Title:** Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  

---

## 5.1 Discussion of Primary Findings

This thesis presented a comparative evaluation of a **Rule-Based Regex Extraction Engine** and **Open-Weight Large Language Models** for level-resolved clinical relation extraction from narrative lumbar MRI reports at Rizgary Teaching Hospital.

Key insights include:
1. **High Baseline Precision of Rule-Based NLP:** The deterministic Regex engine achieved an overall F1-score of **0.93** and a level-binding accuracy of **95.2%**. Because radiology report language at regional teaching hospitals follows predictable syntactic patterns, carefully crafted regex rules with multi-level list expansion provide an exceptionally strong, computationally efficient baseline.
2. **Generative Extraction via Open LLMs:** Few-shot prompting of open-weight LLMs (Llama 3 8B Instruct) achieved competitive performance (F1 = 0.91, Level-Binding = 93.8%), demonstrating that open-weight instruction models can successfully extract structured JSON schemas without exposing patient data to external cloud APIs.

---

## 5.2 Privacy-Preserving Local Clinical Deployment

A critical contribution of this research is establishing an architecture for **on-premise, privacy-preserving clinical NLP deployment**:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    HOSPITAL FIREWALL BOUNDARY                           │
│                                                                         │
│   ┌───────────────────────┐            ┌────────────────────────────┐   │
│   │ Hospital PACS / EHR   │ ─────────> │ Local NLP Engine Container │   │
│   │ (Narrative .docx)     │            │ (Python Regex / Llama-3)   │   │
│   └───────────────────────┘            └─────────────┬──────────────┘   │
│                                                      │                  │
│                                                      ▼                  │
│                                        ┌────────────────────────────┐   │
│                                        │ Audited Clinical Database  │   │
│                                        │ (PostgreSQL / CSV Matrix)  │   │
│                                        └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

By containerizing the Python extraction scripts (`msc3_regex_extractor.py`) and running open-weight LLMs locally on hospital GPU servers, the system operates **100% offline**, ensuring zero Protected Health Information (PHI) leaves the hospital network.

---

## 5.3 Limitations

1. **Single-Center Reporting Style:** The dataset is derived from Rizgary Teaching Hospital in Erbil. While reports follow standard radiological conventions, reporting syntax may vary across different regional hospital systems.
2. **Exclusion of Subarticular Stenosis:** Subarticular / lateral-recess stenosis was omitted from extraction because local narrative reports do not consistently record it.
3. **Binary Schema Scope:** The extraction schema categorizes findings as present/absent. Future extensions could incorporate multi-grade ordinal severity scales.

---

## 5.4 Recommendations for Clinical Practice

1. **Standardized Reporting Templates:** Hospitals should encourage structured radiology reporting templates to further reduce syntactic ambiguities in level binding.
2. **Automated Audit Pipelines:** Hospital management can deploy the rule-based extractor to audit historical MRI archives, track lumbar pathology burden, and optimize scanner scheduling.

---

## 5.5 Conclusion

This master's thesis successfully developed and benchmarked privacy-preserving NLP pipelines for level-resolved lumbar MRI report extraction. The rule-based regex baseline achieved a 93%+ F1-score and 95.2% level-binding accuracy across 975 lumbar level observations. Local open-weight LLMs demonstrated strong structured extraction capability without violating patient privacy. These open-source tools provide a robust foundation for clinical data mining, epidemiological research, and automated radiology decision support in Middle Eastern teaching hospitals.
