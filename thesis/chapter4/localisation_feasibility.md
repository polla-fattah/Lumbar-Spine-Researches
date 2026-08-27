# Automated localisation: feasibility measured against RSNA

Run 2026-08-28. Scripts: `implementation/compare_totalspineseg.py`,
`implementation/derive_target_offsets.py`.
Outputs: `data/reports/totalspineseg_vs_rsna.csv`, `data/reports/target_offsets{,_summary}.csv`.

**This is not thesis material.** RQ4 was not executed and nothing here is claimed
in the submission. It is recorded because it removes the largest obstacle to
executing RQ4 later, and because the measurement was cheap and decisive.

## The problem it addresses

The grading model is *given* 25 coordinates per patient. On RSNA those are human
annotations. The Rizgary cohort has none, so zero-shot transfer is blocked on a
missing model **input**, not merely on administration. Automated localisation is
the enabling step.

TotalSpineSeg (Warszawer et al., NeuroPoly) segments and labels vertebrae, discs,
cord and canal in MRI, reporting 99% labelling accuracy. That figure is its own,
on its own benchmark, and says nothing about LumbarDISC or about Kurdish clinical
protocols. It had to be measured where ground truth exists.

## Two questions, measured separately

TotalSpineSeg localises five **discs**. The model needs twenty-five **targets**.
So there are two distinct failure modes and they were tested apart.

### 1. Does it identify the right levels?

This is the failure that would have ended the path immediately: an enumeration
shifted by one, so that its \"L4-L5\" is RSNA's \"L3-L4\".

**140 of 140 levels matched across 28 test studies. No shift, in any study.**

### 2. Can 25 targets be derived from 5 disc centroids?

The proposal is that each condition sits at a roughly fixed offset from its
level's disc centre, so a learned constant per condition supplies the missing
twenty. RSNA can test this because it carries all twenty-five annotations.

Offsets from the TotalSpineSeg disc centroid to the RSNA annotation, in the
patient frame ($+x$ right, $+y$ anterior, $+z$ superior), over 698 target
observations:

| Condition | n | Mean offset (x, y, z) mm | Scatter | In 60 mm crop |
| :-- | --: | --: | --: | --: |
| left foraminal | 140 | $-15.7,\ -19.4,\ +8.1$ | 6.3 mm | 100% |
| left subarticular | 139 | $-9.4,\ -22.3,\ +0.5$ | 5.5 mm | 100% |
| central canal | 140 | $-0.2,\ -25.3,\ +1.8$ | 6.4 mm | 100% |
| right subarticular | 139 | $+8.0,\ -22.5,\ +0.8$ | 5.5 mm | 99% |
| right foraminal | 140 | $+18.2,\ -19.3,\ +7.9$ | 6.8 mm | 100% |

**A per-condition constant offset is sufficient.** Every condition holds its
scatter between 5.5 and 6.8 mm, and 99--100% of derived coordinates place the
target inside the 60 mm crop the model is given.

The offsets are anatomically coherent, which is the check that matters most:

- Central canal sits on the midline ($x = -0.2$ mm) and $25$ mm posterior to the
  disc centre, which is where the thecal sac is.
- Foraminal targets sit further lateral than subarticular ($\pm 16$--$18$ mm
  against $\pm 8$--$9$ mm) and $8$ mm superior, matching the foramen's position
  relative to the disc.
- Left and right land on **opposite sides of the midline** in both paired
  conditions. A pipeline that got this wrong would grade the wrong side.

The subarticular separation of $17.4$ mm independently reproduces the $17.12$ mm
measured directly from RSNA's own axial annotations in
`roi_quality_control.md`, by a completely different route. That agreement is
reassuring about both measurements.

## What this does and does not establish

**Established.** Level identification is reliable on this benchmark, and derived
coordinates place the graded structure inside the model's field of view for
essentially every target. The localisation stage of a clinical pipeline can be
built on segmentation plus a constant, without training a detector.

**Not established.** Containment is not centring. The derived coordinate is off
by about 6 mm in a 60 mm crop, and the attribution analysis shows the model
concentrates its evidence near the centre of that crop. Grading accuracy under
derived coordinates would therefore be *worse* than under human annotation, by an
amount this measurement does not give.

**The decisive experiment**, not yet run, is direct: rebuild the ROI cache from
derived coordinates, run the existing E7 checkpoints, and compare QWK against the
same models on human coordinates. That measures the actual cost of automating
localisation rather than a proxy for it. Everything needed exists.

## Caveats

- 28 studies, all from the RSNA test partition. Nothing here says how
  TotalSpineSeg behaves on Kurdish clinical protocols, which is a separate
  measurement requiring the Rizgary cohort.
- L5--S1 is consistently the worst level: 10.1 mm scatter against 4.3--6.7 mm
  elsewhere, which is where segmental angulation is greatest.
- The paired offsets are not perfectly symmetric ($-15.7$ against $+18.2$ mm for
  foraminal). Whether that is anatomy, annotation convention or a segmentation
  bias is not resolved here.
- Offsets are derived and validated on the same 28 studies. A held-out estimate
  would be better and is cheap to produce.

## Installation notes

Recorded because they cost time and will recur.

TotalSpineSeg installs into the main environment without disturbing the
Blackwell-specific torch build; a `pip install --dry-run` confirms torch is not
in the change set before committing to it. Smart App Control blocks the generated
`.exe` wrappers, so the CLI must be invoked through its entry point
`totalspineseg.inference:main`.

One dependency conflict must be fixed: `auglab` requires `kornia` unpinned, pip
takes 0.8.3, and 0.8.3 no longer exports `Tensor` from `kornia.core`. The nnU-Net
trainer then fails to import and the pipeline stops after \"Running step 1
model\" **while still exiting 0**. Pin `kornia==0.7.4`.

The disc label values are not shipped as a table. They follow from the package's
own labelling command, which assigns 63/71/91/100 to landmark discs C2--C3,
C7--T1, T12--L1 and L5--S and numbers between them, putting the lumbar discs at
92--95 and 100. That inference was verified against the segmentation itself, not
assumed.
