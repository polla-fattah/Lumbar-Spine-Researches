# Chapter 1 — Introduction and Clinical Background

**Project Title:** Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Degree:** MSc in Computer Science / Health Informatics / Artificial Intelligence  

---

## 1.1 Clinical Background of Lumbar Spine Disease

Lumbar spine degenerative disc disease and spinal canal stenosis represent leading causes of chronic low back pain, lower extremity radiculopathy, and functional disability worldwide. The lumbar spine consists of five movable vertebral bodies (L1 through L5) separated by intervertebral discs and articulating posteriorly via paired facet joints. 

Magnetic Resonance Imaging (MRI) is the undisputed non-invasive gold standard diagnostic modality for evaluating lumbar degenerative pathology. MRI provides high-contrast visualization of multi-planar soft tissue structures, enabling radiologists to evaluate:
1. **Intervertebral Disc Herniation Morphology:** Ranging from circumferential disc bulge to focal protrusion and free-fragment extrusion.
2. **Central Spinal Canal Stenosis:** Narrowing of the main dural sac space containing the cauda equina nerve roots.
3. **Neural Foraminal Narrowing:** Stenosis of the lateral exit canals accommodating individual spinal nerve roots.
4. **Posterior Element Pathology:** Facet joint arthrosis, ligamentum flavum hypertrophy, and marginal osteophytosis.

---

## 1.2 The Clinical Data Challenge: Unstructured Narrative Reports

In major regional teaching hospitals across the Middle East—such as Rizgary Teaching Hospital in Erbil, Kurdistan Region of Iraq—radiologists document MRI findings in free-text narrative English radiology reports.

While narrative prose allows radiologists flexible expression, free-text reporting creates a major clinical informatics bottleneck:
* **Information Lock:** Critical diagnostic findings (such as severe L4–L5 canal stenosis or L5–S1 foraminal compression) are buried within narrative sentences.
* **Lack of Interoperability:** Unstructured text cannot be directly queried by hospital electronic health record (EHR) systems, epidemiological auditing tools, or clinical decision support engines.
* **Manual Bottleneck:** Conducting hospital-wide quality audits or research studies requires clinicians to manually read hundreds of individual text documents.

---

## 1.3 Research Gap and Clinical Scope Guardrails

### The Research Gap
While commercial biomedical Natural Language Processing (NLP) tools exist for document-level classification, very few open systems address **level-resolved clinical relation extraction** under local Middle Eastern reporting variations. Specifically, an automated pipeline must accurately bind pathology findings to exact spinal levels (`L1-L2` through `L5-S1`) while resolving negations (*"no spinal canal stenosis"*) and multi-level list structures (*"L4-5 and L5-S1 show circumferential bulges"*).

### Mandatory Clinical Scope Guardrails
To ensure scientific integrity, this research strictly adheres to three supervisory framing rules:
1. **Retrospective Referral Cohort Framing:** The hospital dataset represents a **symptomatic tertiary-hospital referral cohort**, not a general population prevalence survey. Observed finding rates reflect hospital referral patterns.
2. **Standardized Terminology:** Age metrics are reported strictly as **"Age at Imaging"**, never *"Age of Onset"*, as the dataset records when the MRI was performed.
3. **Contextualized Literature Positioning:** The thesis explicitly avoids overbroad claims such as *"the first study in Iraq or Kurdistan"*, citing established regional literature (*Akreyi & Awdish 2012, Saeed et al. 2019*) while focusing on the specific relation extraction contribution.

---

## 1.4 Research Objectives

This master's thesis investigates three core research objectives:

1. **Rule-Based Baseline Development:** Design and implement a deterministic, rule-based Regex relation extraction engine (`msc3_regex_extractor.py`) tailored to local reporting syntax and level-binding patterns.
2. **Open-Weight LLM Benchmarking:** Benchmark privacy-preserving, open-weight instruction-tuned Large Language Models (e.g. Llama 3 8B Instruct, BioMistral 7B) using constrained zero-shot and few-shot JSON prompt templates.
3. **Quantitative Performance & Error Evaluation:** Evaluate extraction accuracy, level-binding precision, negation resolution, and computational efficiency against an audited reference standard across 975 lumbar level observations.

---

## 1.5 Thesis Structure

The remainder of this thesis is organized as follows:
* **Chapter 2 (Literature Review):** Reviews classical biomedical NLP systems, recent Vision-Language Models, and privacy-preserving open-weight LLMs.
* **Chapter 3 (Methodology):** Details the annotation guidelines, Regex parser design, LLM JSON prompt engineering, and evaluation protocols.
* **Chapter 4 (Results):** Presents comparative extraction accuracy metrics (Precision, Recall, F1, Level-Binding Accuracy) and detailed radiological error analyses.
* **Chapter 5 (Discussion & Conclusion):** Discusses clinical deployment on hospital infrastructure, study limitations, and future research directions.
