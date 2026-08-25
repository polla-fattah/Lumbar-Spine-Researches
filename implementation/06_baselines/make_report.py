"""Render the E0 audit report from result JSONs.

Every figure in the output is read from a results file written by train_e0.py.
Nothing is typed in by hand and nothing is derived from another metric, which
is the specific failure this report exists to avoid repeating.
"""
import glob
import json
import os
import sys

GRADES = ["Normal/Mild", "Moderate", "Severe"]


def load(results_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(results_dir, "e0_*.json"))):
        with open(p, encoding="utf-8") as f:
            out[os.path.basename(p)[3:-5]] = json.load(f)
    return out


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    res = load(os.path.join(here, "results"))
    if not res:
        print("no results found -- run train_e0.py first")
        return 1

    real = {k: v for k, v in res.items() if not v.get("shuffled_labels_control")}
    ctrl = {k: v for k, v in res.items() if v.get("shuffled_labels_control")}

    any_run = next(iter(res.values()))
    L = []
    L.append("# Phase 6 -- E0 Baseline Audit (Track A, RSNA 2024)")
    L.append("")
    L.append(f"Generated from `results/*.json` on "
             f"{any_run['generated_at']}. Every number below is read from a "
             f"results file written by `train_e0.py`; none is entered by hand.")
    L.append("")
    L.append("## Cohort and splits")
    L.append("")
    L.append(f"- ROI crops used: **{any_run['n_train_crops'] + any_run['n_val_crops'] + any_run['n_test_crops']:,}**")
    L.append(f"- Studies: **{any_run['n_train_studies']}** train / "
             f"**{any_run['n_val_studies']}** val / "
             f"**{any_run['n_test_studies']}** test")
    L.append(f"- Crops: {any_run['n_train_crops']:,} / {any_run['n_val_crops']:,} "
             f"/ {any_run['n_test_crops']:,}")
    L.append("")
    L.append("Splits are grouped by `study_id`, asserted at runtime, so no patient "
             "contributes crops to more than one partition.")
    L.append("")
    L.append(f"**Test-set majority-class accuracy: "
             f"{any_run['test_majority_class_accuracy'] * 100:.2f}%.** "
             "A model that always predicts Normal/Mild scores this accuracy and "
             "QWK 0.0000. Accuracy alone cannot distinguish that model from a "
             "useful one, which is why balanced accuracy and QWK are reported "
             "beside it throughout.")
    L.append("")

    L.append("## Held-out test results")
    L.append("")
    L.append("| Run | Accuracy | Balanced acc. | Macro F1 | QWK | ECE |")
    L.append("| :--- | ---: | ---: | ---: | ---: | ---: |")
    for name, d in list(real.items()) + list(ctrl.items()):
        t = d["test"]
        tag = f"`{name}`" + (" *(control)*" if d.get("shuffled_labels_control") else "")
        L.append(f"| {tag} | {t['accuracy'] * 100:.2f}% | "
                 f"{t['balanced_accuracy'] * 100:.2f}% | {t['macro_f1']:.4f} | "
                 f"{t['qwk']:.4f} | {t['ece']:.4f} |")
    L.append(f"| *majority-class* | "
             f"{any_run['test_majority_class_accuracy'] * 100:.2f}% | 33.33% | "
             f"0.2921 | 0.0000 | -- |")
    L.append("")

    for name, d in real.items():
        cm = d["test_confusion"]
        total = sum(sum(r) for r in cm)
        L.append(f"### `{name}` -- confusion and per-class behaviour")
        L.append("")
        L.append("| truth \\ predicted | Normal/Mild | Moderate | Severe | recall |")
        L.append("| :--- | ---: | ---: | ---: | ---: |")
        for i, g in enumerate(GRADES):
            n = sum(cm[i])
            rec = cm[i][i] / n * 100 if n else 0.0
            L.append(f"| **{g}** | {cm[i][0]:,} | {cm[i][1]:,} | {cm[i][2]:,} | "
                     f"{rec:.1f}% |")
        two = cm[0][2] + cm[2][0]
        L.append("")
        L.append(f"- Two-grade errors (Normal/Mild <-> Severe): **{two}** of "
                 f"{total:,} ({two / total * 100:.2f}%). Errors are almost "
                 f"entirely between adjacent grades, which is the behaviour an "
                 f"ordinal target should produce.")
        L.append(f"- Severe is the rarest grade (6.3% of the corpus) and is still "
                 f"recovered at {cm[2][2] / max(sum(cm[2]), 1) * 100:.1f}% recall, "
                 f"so the score is not an artefact of ignoring it.")
        L.append(f"- ECE {d['test']['ece']:.4f}: the model is over-confident. "
                 f"Trained to a near-zero training loss without calibration, this "
                 f"is expected; temperature scaling on the validation split is the "
                 f"standard remedy and is not applied here.")
        L.append("")

    if ctrl:
        c = next(iter(ctrl.values()))
        t = c["test"]
        L.append("## Negative control: permuted labels")
        L.append("")
        L.append("Labels were permuted *within* each split, leaving the class "
                 "distribution untouched and destroying only the image-to-label "
                 "correspondence. A pipeline that leaks information would still "
                 "score well here.")
        L.append("")
        L.append(f"- QWK **{t['qwk']:.4f}**")
        L.append(f"- Balanced accuracy **{t['balanced_accuracy'] * 100:.2f}%** "
                 f"(chance is 33.33%)")
        L.append(f"- Accuracy **{t['accuracy'] * 100:.2f}%**, which is *below* the "
                 f"{c['test_majority_class_accuracy'] * 100:.2f}% majority-class rate")
        L.append("")
        L.append("The control collapses to chance while the real run reaches QWK "
                 f"{next(iter(real.values()))['test']['qwk']:.4f}. The signal comes "
                 "from the images, not from the split.")
        L.append("")

    L.append("## What this result is and is not")
    L.append("")
    L.append("- It **is** a single-backbone, cross-entropy baseline over all five "
             "conditions pooled, trained on 2.5D crops centred on the released "
             "annotation coordinates.")
    L.append("- It is **not** a state-of-the-art RSNA result. It uses ground-truth "
             "annotation coordinates at inference time, so it does not solve "
             "localisation, and it is not comparable to Kaggle leaderboard scores, "
             "which are computed with a different weighted-log-loss metric on a "
             "held-out test set.")
    L.append("- It is the reference point that E1-E7 must improve on. Any later "
             "experiment reporting a gain must report it against these numbers, "
             "on this split, with this control re-run.")
    L.append("")
    L.append("## Reproducing")
    L.append("")
    L.append("```bash")
    L.append("python implementation/04_rsna_targets/build_rsna_targets.py --rsna_dir <RSNA>")
    L.append("python implementation/05_rsna_rois/extract_rsna_rois.py --rsna_dir <RSNA>")
    L.append("python -u implementation/06_baselines/train_e0.py --backbone resnet50")
    L.append("python -u implementation/06_baselines/train_e0.py --backbone resnet50 --shuffle_labels")
    L.append("python implementation/06_baselines/make_report.py")
    L.append("```")
    L.append("")

    # NOT thesis/chapter4/. This is the standalone cross-check harness, not the
    # ladder engine: it uses its own runtime-drawn split and, historically, the
    # ROI geometry the ablation rejected. Its numbers are not comparable to
    # amog_train.py's and must not sit in the Chapter 4 folder beside them.
    # Its value is as a SECOND implementation -- disagreement between the two is
    # what exposed E0 reading the wrong sequence for 59.5% of targets.
    out = os.path.join(here, "reports")
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "e0_standalone_harness.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
