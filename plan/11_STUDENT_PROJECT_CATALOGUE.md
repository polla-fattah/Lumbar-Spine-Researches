# Postgraduate Research Opportunities — Lumbar Spine MRI Programme

**For prospective MSc / PhD students**  
**Supervisor:** Dr. Polla Abdulhamid Fattah  
**Status:** Draft for departmental / committee publication after ethics and data-access conditions are confirmed

---

## How to read this catalogue

These projects share a research programme and some data infrastructure, but each student has an independent research question. Choosing one project does not require another student to finish first.

Expected output for every active project is:

- a postgraduate dissertation;
- reproducible analysis / code appropriate to the topic;
- a manuscript prepared for peer-reviewed journal submission.

Publication and model-performance outcomes are not guaranteed.

---

# MSc 1 — Level-Specific Lumbar MRI Findings in a Tertiary-Hospital Cohort

**Status:** 🟢 Available once report-data access is approved  
**Best fit:** Data Science, Medical Informatics, Public Health, Clinical Data Science  
**Difficulty:** Low–Medium  
**GPU:** Not required

### Research question

What lumbar degenerative MRI findings are observed at L1–L2 through L5–S1 among patients who underwent lumbar MRI at Rizgary Teaching Hospital, and how do these patterns vary with age, sex and spinal level?

### What you will do

- structure / audit 299 anonymised radiology reports;
- compute level-specific frequencies and confidence intervals;
- use GEE or mixed-effects regression to account for repeated levels within a patient;
- compare the pattern with published cohorts;
- prepare a STROBE-compliant manuscript.

### Important scope

This is a **hospital referral cohort**, not a population-prevalence survey. The study does not claim to be the first lumbar MRI study in Iraq / Kurdistan.

---

# MSc 2 — Sequence-Sparing Lumbar MRI Triage / Protocol Optimisation

**Status:** 🟡 Available after de-identified DICOM release  
**Best fit:** Computer Science, AI, Biomedical Engineering  
**Difficulty:** Medium–High  
**GPU:** Required

### Research question

Which MRI sequence combinations preserve diagnostic information for selected lumbar findings, and what measured scanner-time trade-off follows from shortening the protocol?

### What you will do

- train matched models separately for full and reduced sequence configurations;
- evaluate central canal stenosis and other defensibly labelled findings;
- analyse false negatives for radiologically severe cases;
- measure local sequence acquisition times;
- model potential scanner-throughput effects.

### Important scope

This is a **triage / screening evaluation**, not a replacement for comprehensive diagnostic MRI and not a claim that abbreviated MRI is a new concept.

---

# MSc 3 — Clinical NLP for Structured Lumbar MRI Reports

**Status:** 🟢 Available once report-data access is approved  
**Best fit:** Computer Science, AI, Data Science, Health Informatics  
**Difficulty:** Medium  
**GPU:** Helpful, not always essential

### Research question

How accurately can rule-based NLP and current open-weight LLMs extract level-resolved lumbar findings from English radiology reports written at a Middle Eastern teaching hospital?

### What you will do

- create / follow a structured annotation guideline;
- benchmark regex, classical NLP and current open-weight LLMs;
- use a locked, independently annotated test set;
- analyse negation, hedging, laterality and level-binding errors;
- develop a privacy-preserving local extraction tool.

### Important scope

The contribution is **level-resolved clinical relation extraction under local reporting variation**, not merely "using an LLM on radiology reports."

---

# MSc 4 — Imaging–Symptom–Treatment Association

**Status:** 🔴 **Not currently available for allocation**  
**Best fit if activated:** Medical Informatics, Clinical Data Science, Epidemiology, clinical researchers

This project will open only if Rizgary confirms that symptom, treatment and follow-up records can be linked to the imaging under the required ethics approval.

If activated, the study will examine how level-resolved imaging findings relate to symptoms, treatment choice and outcome. Synthetic data will not be used as a substitute if the clinical records do not exist.

---

# PhD — Disease-Adaptive Heterogeneous Graph Learning for Lumbar MRI

**Status:** 🔵 Doctoral research track  
**Best fit:** Computer Science / Artificial Intelligence with strong deep-learning experience  
**Difficulty:** High  
**GPU:** Required

### Central doctoral question

Can lumbar MRI grading be improved by explicitly modelling disease–anatomy relations, learning which MRI sequences matter for each target and case, pretraining across anatomically corresponding MRI sequences, and adapting efficiently to an unseen hospital domain?

### Core contributions under investigation

1. typed heterogeneous graph over condition, spinal level and laterality;
2. disease-conditioned MRI sequence routing with missing-modality robustness;
3. DICOM-aligned cross-sequence self-supervised learning;
4. zero-shot and few-shot cross-institutional transfer.

### Important novelty boundary

Anatomical segmentation, multi-sequence ROIs, inter-level Transformers and ordinal grading already exist in recent literature. The PhD does not claim those elements as novel by themselves.

---

## Data and ethics note

Local DICOM data will not be released to students until de-identification and institutional access conditions are complete. Students work only with the approved de-identified research copy. The public benchmark data can be used according to its published licence / terms.
