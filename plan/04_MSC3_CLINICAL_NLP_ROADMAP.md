# MSc Project Plan — Student 3: Clinical Radiology NLP Benchmark

**Project Title:** Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Degree:** MSc in Computer Science / Artificial Intelligence / Data Science / Health Informatics  
**Duration:** 6–8 Months

---

## 1. Research Problem

The novelty is **not** simply applying an LLM to radiology reports; that has already been demonstrated in several imaging domains. The useful local research question is more specific:

> **How accurately can privacy-preserving rule-based and open-weight language models extract level-resolved, multi-label lumbar findings from locally written English radiology reports containing variable shorthand, negation, hedging, multi-level spans and incomplete laterality?**

The study uses one hospital, so the title and claims must use **"a Middle Eastern teaching hospital"**, not plural hospitals.

---

## 2. Target Schema

Do not force the RSNA 25-target schema onto reports that do not contain it.

Primary local extraction schema:

- spinal level;
- disc bulge;
- protrusion;
- extrusion;
- dehydration / signal loss where stated;
- disc height loss where stated;
- central canal stenosis;
- neural foraminal narrowing;
- laterality where explicitly stated;
- ventral thecal indentation;
- nerve-root pressure / compression;
- ligamentum flavum hypertrophy;
- facet arthrosis;
- osteophytes / related degenerative descriptors;
- uncertainty / hedging status;
- negation status.

Known reporting facts:

- subarticular / lateral-recess labels are not available as a reliable local target;
- laterality is incomplete;
- missingness / non-reporting is itself a result, but absence from text must not automatically be treated as a clinically confirmed negative unless the annotation guideline explicitly defines that rule.

---

## 3. Research Questions

**RQ1.** How do deterministic rules, classical NLP and current open-weight instruction models compare for exact level–finding extraction?

**RQ2.** Does constrained structured output reduce invalid / hallucinated entities compared with unconstrained prompting?

**RQ3.** What are the dominant failure modes for negation, hedging, multi-level spans, laterality and finding-to-level binding?

**RQ4.** How does performance change under zero-shot, few-shot and parameter-efficient fine-tuning while preserving a locked test set?

---

## 4. Gold Standard — Required Design

The NLP student may build annotation tools, but the test reference standard must not be created solely by the same person whose model is being evaluated.

### Recommended annotation design

1. Create a written annotation manual before modelling.
2. Split the 299 reports at document level, for example:
   - training / development: ~100;
   - validation / prompt-development: ~50;
   - locked test: ~149.
3. **Lock the test set before prompt engineering or fine-tuning.**
4. Have the full test set independently annotated by two qualified human reviewers where feasible.
5. Resolve disagreements by adjudication.
6. Report inter-annotator agreement:
   - entity / relation F1;
   - Cohen's kappa for categorical fields where appropriate;
   - exact level–finding agreement.
7. For train / validation data, one primary annotation with a substantial second-reader audit is acceptable if resources are limited.

The final structured matrix is a **programme / hospital research asset**. The MSc student owns the NLP methodological contribution, not exclusive ownership of the dataset.

---

## 5. Compared Methods

Model names should be finalised at study start because open-weight LLMs change rapidly. At minimum compare:

1. **Regex / heuristic baseline**  
   Level binding + negation + span rules.

2. **Classical / statistical NLP baseline**  
   spaCy / clinical NER pipeline with explicit negation and relation rules.

3. **General open-weight instruction model**  
   A current 7B–14B class model that can be run locally.

4. **Biomedical / clinical open-weight model**  
   If a credible current model is available and licence terms permit use.

5. **Few-shot / PEFT model**  
   LoRA or other parameter-efficient fine-tuning on the training subset.

Use constrained JSON / schema decoding where possible.

Do not hard-code Llama-3 / Qwen-2.5 as the only acceptable models in a catalogue published months before the student begins; choose contemporary models and record exact versions in the thesis.

---

## 6. Evaluation

Primary evaluation unit:

> **exact `(level, finding, laterality, status)` relation**, not just whether a word was found somewhere in the report.

Report:

- exact-match precision / recall / F1;
- macro F1 across finding types;
- micro F1;
- hallucination / unsupported-finding rate;
- negation error rate;
- level-binding error rate;
- laterality error rate;
- structured-output validity rate;
- inference time and hardware footprint.

Provide bootstrap confidence intervals and paired comparison on the same locked test reports.

---

## 7. Workflow

### Month 1

- finalise annotation schema and manual;
- create document-level splits;
- complete / adjudicate gold-standard test annotation;
- clean boilerplate without altering clinical meaning.

### Month 2

- implement regex and classical NLP baselines;
- establish exact relation-level evaluation code.

### Months 3–4

- benchmark zero-shot and few-shot local open-weight LLMs;
- add constrained schema decoding;
- fine-tune one selected model using PEFT if justified.

### Month 5

- locked test evaluation;
- linguistic / clinical error taxonomy;
- analyse reporting omissions separately from extraction errors.

### Months 6–7

- dissertation and manuscript preparation;
- release parsing code where hospital policy permits, but do not release clinical text.

---

## 8. Student Fit

**Technical difficulty:** MEDIUM.

Requires:

- strong Python;
- text processing / regex;
- basic NLP and LLM deployment;
- careful evaluation design;
- patience with manual error analysis.

No medical-image processing is required.

---

## 9. Expected Outputs

- MSc dissertation;
- annotation guideline / schema;
- reproducible extraction benchmark code;
- privacy-preserving local extraction tool;
- **one manuscript prepared for peer-reviewed submission**.

The regional reporting style and level-resolved relation-extraction problem support the contribution; dataset size should be treated honestly as modest.
