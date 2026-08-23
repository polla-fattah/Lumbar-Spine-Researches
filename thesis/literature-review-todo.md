# Chapter 2 — Literature Review: Build Checklist

**Output file:** `thesis/chapter2.tex` (single LaTeX file)
**Bibliography:** `../lumbar_spine_mri_ai_literature_inventory.bib` -- SINGLE source, 108 records (92 curated lumbar papers + 16 foundational method/clinical papers, PDFs 93-108). `references-extra.bib` has been merged in and removed.

Each item is ticked as it is written into `chapter2.tex`.

---

## 2.1 Introduction
- [x] 2.1.1 Scope and objectives of the review
- [x] 2.1.2 Search strategy, sources, and inclusion criteria
- [x] 2.1.3 Structure of the chapter

## 2.2 Clinical Background: Lumbar Degenerative Disease
- [x] 2.2.1 Epidemiology and socioeconomic burden of low back pain
- [x] 2.2.2 The degenerative cascade: disc, ligament, and facet pathology
- [x] 2.2.3 The three anatomical forms of stenosis
- [x] 2.2.4 Clinical presentation and the conservative-versus-surgical decision

## 2.3 MRI Acquisition: Sequences, Planes, and Diagnostic Yield
- [x] 2.3.1 Why MRI is the reference modality
- [x] 2.3.2 Sagittal T2/STIR, Sagittal T1, and Axial T2 as complementary evidence
- [x] 2.3.3 Matching each pathology to the sequence that best depicts it
- [x] 2.3.4 Sources of acquisition variability

## 2.4 Clinical Grading Systems as the Origin of Ground Truth
- [x] 2.4.1 Disc degeneration: Pfirrmann and the Modified 8-level extension
- [x] 2.4.2 Central canal stenosis: Schizas and Lee
- [x] 2.4.3 Neural foraminal stenosis: Lee and Sartoretti
- [x] 2.4.4 Subarticular and lateral recess stenosis
- [x] 2.4.5 Disc herniation: nomenclature and the MSU classification
- [x] 2.4.6 Inter- and intra-observer reliability across grading systems
- [x] 2.4.7 Label noise as an upper bound on achievable performance
- [x] 2.4.8 The ordinal, non-interchangeable nature of severity labels

## 2.5 Evolution of Automated Lumbar MRI Analysis
- [x] 2.5.1 Handcrafted features and classical machine learning
- [x] 2.5.2 The first end-to-end deep learning systems
- [x] 2.5.3 From binary detection to multi-level, multi-pathology grading
- [x] 2.5.4 Chronological synthesis of the field

## 2.6 Anatomical Localization as a Design Principle
- [x] 2.6.1 Disc and vertebra detection, labelling, and level assignment
- [x] 2.6.2 Semantic and instance segmentation of lumbar structures
- [x] 2.6.3 Public segmentation resources and benchmarks
- [x] 2.6.4 Quantitative morphometry: DSCA and related measures
- [x] 2.6.5 Evidence that localization before classification improves grading
- [x] 2.6.6 Reduced-annotation, weakly supervised, and unsupervised alternatives

## 2.7 Backbone Architectures for Severity Classification
- [x] 2.7.1 Convolutional networks: ResNet, EfficientNet, and modern variants
- [x] 2.7.2 Vision Transformers and the quadratic self-attention bottleneck
- [x] 2.7.3 The Swin Transformer
- [x] 2.7.4 Hybrid CNN–Transformer architectures
- [x] 2.7.5 Published CNN-versus-Transformer comparisons and their limits
- [x] 2.7.6 Transfer learning, domain pretraining, and self-supervision

## 2.8 Exploiting Spatial Context: Slices, Volumes, and Views
- [x] 2.8.1 2D, 2.5D, and 3D input representations
- [x] 2.8.2 Cross-sequence and cross-plane fusion strategies
- [x] 2.8.3 Geometric correspondence between sagittal and axial data
- [x] 2.8.4 Multi-sequence versus single-sequence input
- [x] 2.8.5 Robustness to missing or incomplete sequences

## 2.9 Class Imbalance and Ordinal Severity Modelling
- [x] 2.9.1 Severity distributions in lumbar MRI datasets
- [x] 2.9.2 Data-level strategies: weighted sampling and augmentation
- [x] 2.9.3 Loss-level strategies: weighted cross-entropy and focal loss
- [x] 2.9.4 Ordinal-aware objectives and whether they help
- [x] 2.9.5 Contrastive and representation-learning approaches
- [x] 2.9.6 Clinical asymmetry of error

## 2.10 Datasets and Benchmarks
- [x] 2.10.1 Private and single-institution cohorts
- [x] 2.10.2 Population and epidemiological cohorts
- [x] 2.10.3 Public lumbar MRI datasets
- [x] 2.10.4 The RSNA 2024 Challenge and the LumbarDISC dataset
- [x] 2.10.5 Label structure, severity distribution, weighted evaluation metric
- [x] 2.10.6 Challenge solutions and the practices they standardised

## 2.11 Evaluation, Validation, and Generalization
- [x] 2.11.1 Metrics and their appropriateness for ordinal, imbalanced tasks
- [x] 2.11.2 Internal validation and optimistic reporting
- [x] 2.11.3 External validation and domain shift
- [x] 2.11.4 Detection versus fine-grained severity grading
- [x] 2.11.5 Benchmarking against radiologists and surgeons
- [x] 2.11.6 Longitudinal stability and reproducibility
- [x] 2.11.7 Reporting quality and recurring methodological weaknesses

## 2.12 Interpretability and Clinical Integration
- [x] 2.12.1 Saliency maps, evidence hotspots, and Grad-CAM
- [x] 2.12.2 Inherently interpretable models
- [x] 2.12.3 Vision–language models and automated report generation
- [x] 2.12.4 Reader-assistance studies and workflow impact
- [x] 2.12.5 Uncertainty estimation and calibration

## 2.13 Synthesis and Research Gap
- [x] 2.13.1 What the literature has established
- [x] 2.13.2 What remains contested or unresolved
- [x] 2.13.3 Gap 1: architecture comparison under controlled conditions
- [x] 2.13.4 Gap 2: sequence configuration and the accuracy–efficiency trade-off
- [x] 2.13.5 Research questions and objectives of this thesis
- [x] 2.13.6 Scope and delimitations

## 2.14 Chapter Summary
- [x] 2.14 Chapter Summary

---

## Notes

- Do **not** cite `silveira2023automated` — it is a duplicate record of `silveira2025automated` (same paper, wrong year/venue in the inventory).
- Records `pfirrmann2001magnetic`, `wang2024deep`, `hallinan2021deep` have correct bibliographic metadata but the wrong PDF filed against them; the citations are valid, the local PDFs are not.
- The 16 merged foundational references were verified against arXiv/publisher records on 2026-08-23. Twelve are free on arXiv; Modic 1988 and Mysliwiec 2010 are paywalled.
- Chapter 2 cites 107 of the 108 records; the one uncited record is the duplicate noted above.
