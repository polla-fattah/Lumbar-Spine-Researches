# Chapter 2 — Literature Review and Related Work

**Project Title:** Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  

---

## 2.1 Clinical Radiology Report Structuring

Automated structuring of radiology reports has been a central focus of medical informatics for over three decades. Early systems relied on rule-based regular expressions and medical vocabularies (UMLS, SNOMED CT) to identify diagnostic concepts.

Key foundational frameworks include:
* **NegEx / ConText Algorithm:** Developed by *Harkema et al. (2009)*, NegEx utilizes trigger terms preceding or following clinical concepts to determine negation (*"no evidence of"*, *"rules out"*), uncertainty (*"possible"*, *"versus"*), and historical context.
* **cTaKES & MetaMap:** Clinical Text Analysis and Knowledge Extraction System (*Savova et al., 2010*) and NCBI MetaMap provide named entity recognition (NER) for unified medical concepts but require substantial domain tuning for level-specific anatomical relation extraction.
* **MedSpacy & Clinical Regex Systems:** Recent open-source pipelines combine spaCy dependency parsing with regular expression rules to match clinical entities within sentence boundaries.

---

## 2.2 Level-Resolved Anatomical Relation Extraction

While document-level classification determines whether a report contains *any* mention of stenosis, lumbar MRI evaluation requires **level-resolved relation extraction**—binding specific pathological findings to exact spinal levels (`L1-L2` through `L5-S1`).

### The Challenge of Anatomical Distributivity
In English radiology reports, findings are frequently expressed using multi-level list structures:
> *"L4-5 and L5-S1 intervertebral discs show circumferential bulge with pressure on corresponding exiting nerve roots."*

Naive sentence-window NLP systems often fail on such structures, assigning the bulge finding only to the first mentioned level (`L4-L5`) and ignoring the second (`L5-S1`). Robust relation extraction must implement list-expansion logic to distribute findings correctly across all referenced anatomical levels.

---

## 2.3 Open-Weight Large Language Models in Healthcare

The emergence of Large Language Models (LLMs) has transformed clinical text processing. While proprietary APIs (e.g. OpenAI GPT-4o, Anthropic Claude 3.5) demonstrate impressive zero-shot medical extraction capabilities, their deployment in clinical hospital environments is restricted by stringent **data privacy and governance regulations**:

### Data Privacy & Firewall Constraints (HIPAA / GDPR)
* Transmitting patient radiology reports to external cloud endpoints violates patient confidentiality regulations unless strict business associate agreements (BAAs) and anonymization pipelines are established.
* **The Open-Weight Solution:** Modern open-weight instruction-tuned LLMs—such as **Llama 3 8B Instruct** (*Meta, 2024*), **BioMistral 7B** (*Labrak et al., 2024*), and **Mistral 7B Instruct** (*Jiang et al., 2023*)—can be deployed locally on hospital hardware behind the institutional firewall. This guarantees 100% data privacy while providing state-of-the-art generative extraction capabilities.

---

## 2.4 Evaluation Metrics for Clinical Relation Extraction

To evaluate clinical text extraction systems rigorously, standard information retrieval and classification metrics are employed:

1. **Precision ($P$):** Proportion of extracted positive findings that are correct:
   $$P = \frac{TP}{TP + FP}$$
2. **Recall ($R$):** Proportion of true clinical findings correctly extracted by the model:
   $$R = \frac{TP}{TP + FN}$$
3. **F1-Score ($F_1$):** Harmonic mean of Precision and Recall:
   $$F_1 = 2 \times \frac{P \times R}{P + R}$$
4. **Exact Level-Binding Accuracy:** Percentage of lumbar levels where all findings are correctly extracted without level-assignment errors.
5. **Negation Resolution Rate:** Accuracy in distinguishing true pathological presence from negated control phrases (*"No canal stenosis"*).

---

## 2.5 Summary & Position of the Thesis

The literature indicates that while cloud-based proprietary LLMs are widely benchmarked, **locally deployable, privacy-preserving open-weight LLMs** and **optimized deterministic regex parsers** remain the most practical solutions for resource-constrained teaching hospitals. This thesis establishes the first comparative benchmark of these approaches on aMiddle Eastern tertiary-hospital lumbar MRI report dataset.
