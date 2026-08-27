# Research Plan

## Working title

Finding-Specific Evaluation of Sequence-Sparing Lumbar MRI for Rapid Triage: A Matched-Model Ablation Study

## Research questions

1. How does performance change when sequence combinations are reduced?
2. Which sequence contributes most for each finding and level?
3. What sensitivity/specificity trade-off is obtained for severe radiological findings?
4. What time and throughput change follows from the shortened protocol?

## Primary configurations

- A: sagittal T1 + sagittal T2/STIR + axial T2.
- B: sagittal T1 + sagittal T2/STIR.
- C: sagittal T2/STIR only.
- D: sagittal T2/STIR + axial T2.

Train each configuration independently with the same patient folds, architecture family, optimisation budget, and evaluation set. Zeroing a sequence only at test time is not the primary experiment.

## Evaluation

Report sensitivity for severe/high-risk radiological findings, specificity, balanced accuracy, macro F1, AUROC with confidence intervals, false-negative counts, and absolute differences from the full protocol. Measure scan time from verified local sources.

## Extension space

Possible extensions include radiologist adjudication, quality-degraded sequences, modality dropout, scanner/protocol subgroup analysis, or cost/throughput simulation.
