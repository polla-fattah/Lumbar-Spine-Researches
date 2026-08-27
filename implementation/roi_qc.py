#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ROI quality control: two-plane overlays at native resolution.

Discharges the commitment in Chapter 3 sec:method-roi-qc:

    "A validation subset is visually inspected using overlays of the detected
    level, crop boundary and corresponding axial slices. The inspection records:
    correct lumbar level; inclusion of the relevant canal/foramen/recess;
    correct left/right orientation; adequate axial coverage; crop truncation;
    correspondence failure caused by unusual axial angulation."

That inspection was never performed, and a final inclusion/exclusion table was
promised and never produced. This script generates the overlays and the table
skeleton a reader fills in.

WHY THIS IS NOT MERELY A FIGURE GENERATOR
-----------------------------------------
Core Contribution I rests entirely on DICOM-defined anatomical correspondence:
ACSSL's positives are anatomically aligned rather than augmentation-derived. If
that correspondence is wrong, the pretext task was matching misaligned patches
and RQ2's null result is an artefact rather than a finding.

There is currently no data-grounded evidence that the correspondence is correct.
geometry.py records that the previous implementation never read
ImageOrientationPatient and substituted textbook cosines chosen by a substring
match on the series description, and that its "0.00000000 mm" validation was
vacuous because inverting a matrix returns the original point whatever the
matrix contains.

THE VALIDATION USED HERE IS EXTERNAL, NOT A ROUND-TRIP
------------------------------------------------------
LumbarDISC annotates different conditions of the SAME level on DIFFERENT
sequences: central canal on sagittal T2, subarticular on axial T2. So the
sagittal canal annotation for a level can be projected into the axial series and
asked a falsifiable question -- does it select the same axial slice that carries
that level's own subarticular annotations?

If the geometry is right the answer is that slice or one of its neighbours. If
the geometry is fictional the answer is arbitrary. Two independent human
annotations are being compared through the transform; nothing here can succeed
by algebraic identity.

WHAT THE FIGURES DO NOT SHOW
----------------------------
Not detection. The model is handed a crop centred on the annotated coordinate
and grades severity there; it never searches a study. Nor does it name a
pathology: LumbarDISC labels stenosis SEVERITY, not its cause, so nothing here
distinguishes a disc bulge from facet hypertrophy. The figure legend says so,
because a two-plane view invites exactly that misreading.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import PROJECT_ROOT  # noqa: E402
from geometry import (  # noqa: E402
    pixel_to_patient, patient_to_pixel, nearest_slice,
)

RSNA_DIR = r"C:\Users\USER\Desktop\Polla\Lumbar\rsna"
GRADES = ["Normal/Mild", "Moderate", "Severe"]
GRADE_COLOUR = {0: "#3fbf5f", 1: "#e8b23a", 2: "#e2483c"}
SERIES_OF = {"Sagittal T1": "sag_t1", "Sagittal T2/STIR": "sag_t2",
             "Axial T2": "ax_t2"}


# --------------------------------------------------------------------------- #
#  DICOM access
# --------------------------------------------------------------------------- #
def load_series_headers(study_id, series_id):
    """Header-only read of every slice in a series, sorted along its normal."""
    import pydicom
    d = os.path.join(RSNA_DIR, "train_images", str(study_id), str(series_id))
    if not os.path.isdir(d):
        return []
    out = []
    for f in os.listdir(d):
        p = os.path.join(d, f)
        try:
            ds = pydicom.dcmread(p, stop_before_pixels=True, force=True)
            ipp = getattr(ds, "ImagePositionPatient", None)
            iop = getattr(ds, "ImageOrientationPatient", None)
            if ipp is None or iop is None:
                continue
            out.append(dict(
                path=p, ipp=np.asarray(ipp, float), iop=np.asarray(iop, float),
                ps=np.asarray(getattr(ds, "PixelSpacing", [1.0, 1.0]), float),
                rows=int(getattr(ds, "Rows", 0)), cols=int(getattr(ds, "Columns", 0)),
                instance=int(getattr(ds, "InstanceNumber", -1)),
                thickness=float(getattr(ds, "SliceThickness", 0) or 0)))
        except Exception:
            continue
    if out:
        from geometry import plane_basis
        _, _, n = plane_basis(out[0]["iop"])
        out.sort(key=lambda s: float(np.dot(s["ipp"], n)))
    return out


def slice_pixels(slice_meta):
    """Pixel data for one slice, percentile-windowed to [0,1].

    MRI has no standardised intensity scale, so a fixed window is meaningless.
    Percentile clipping is what a viewer does by default and keeps different
    scanners comparable.
    """
    import pydicom
    ds = pydicom.dcmread(slice_meta["path"], force=True)
    a = ds.pixel_array.astype(np.float32)
    lo, hi = np.percentile(a, [1.0, 99.0])
    if hi <= lo:
        hi = lo + 1.0
    return np.clip((a - lo) / (hi - lo), 0.0, 1.0)


# --------------------------------------------------------------------------- #
#  Rendering
# --------------------------------------------------------------------------- #
def draw_panel(ax, img, col, row, ps, fov_mm, title, sub, colour,
               radius_mm=10.0, in_plane=True):
    """One plane, cropped to a physical field of view, marked at (col,row)."""
    h, w = img.shape
    half_c = 0.5 * fov_mm / float(ps[1])
    half_r = 0.5 * fov_mm / float(ps[0])
    c0, c1 = int(round(col - half_c)), int(round(col + half_c))
    r0, r1 = int(round(row - half_r)), int(round(row + half_r))
    c0p, r0p = max(0, c0), max(0, r0)
    c1p, r1p = min(w, c1), min(h, r1)
    if c1p <= c0p or r1p <= r0p:
        ax.axis("off")
        ax.set_title(title + "\n(marker outside image)", fontsize=7)
        return 0, True

    crop = img[r0p:r1p, c0p:c1p]
    truncated = (c0 < 0 or r0 < 0 or c1 > w or r1 > h)
    native = min(crop.shape)

    ax.imshow(crop, cmap="gray", interpolation="bilinear",
              extent=[c0p, c1p, r1p, r0p])
    rad_px = radius_mm / float(ps[1])
    ax.add_patch(Circle((col, row), rad_px, fill=False, lw=1.6,
                        ec=colour, ls="-" if in_plane else "--"))
    ax.plot([col], [row], marker="+", ms=7, mew=1.2, color=colour)
    ax.set_xlim(c0p, c1p)
    ax.set_ylim(r1p, r0p)
    ax.set_title(title, fontsize=7.5)
    # native crop size is reported here rather than by the caller: the caller
    # cannot know it without repeating the crop arithmetic, and an upsampled
    # panel that does not say what it was upsampled FROM implies detail it does
    # not have.
    ax.set_xlabel("{} - native {}x{}px".format(sub, crop.shape[1], crop.shape[0]),
                  fontsize=6.5)
    ax.set_xticks([]); ax.set_yticks([])
    if truncated:
        for s in ax.spines.values():
            s.set_edgecolor("#e2483c"); s.set_linewidth(2.0)
    return native, truncated


# --------------------------------------------------------------------------- #
#  Cross-plane correspondence
# --------------------------------------------------------------------------- #
def project_into(point3d, headers):
    """Nearest slice in `headers` plus the projected pixel and out-of-plane mm."""
    if not headers:
        return None
    i, d = nearest_slice(point3d, headers)
    if i < 0:
        return None
    s = headers[i]
    c, r, oop = patient_to_pixel(point3d, s["ipp"], s["iop"], s["ps"])
    return dict(slice=s, col=c, row=r, out_of_plane_mm=abs(oop), index=i)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n_studies", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260827,
                    help="sampling seed; fixed so the QC subset is reproducible "
                         "and cannot be reselected after seeing a result")
    ap.add_argument("--fov_mm", type=float, default=100.0)
    ap.add_argument("--radius_mm", type=float, default=10.0)
    ap.add_argument("--levels", default="L4-L5",
                    help="comma-separated, or 'all'")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--validate_only", action="store_true",
                    help="run the cross-annotation geometry check, no figures")
    args = ap.parse_args()

    import pandas as pd

    outdir = args.outdir or os.path.join(PROJECT_ROOT, "data", "reports", "roi_qc")
    os.makedirs(outdir, exist_ok=True)

    idx = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "cache",
                                   "rsna_roi_v2_index.csv"))
    split = pd.read_csv(os.path.join(PROJECT_ROOT, "implementation", "splits",
                                     "rsna_patient_split.csv"))
    test_ids = set(split.loc[split.partition == "test", "study_id"].astype(int))
    idx = idx[idx.study_id.isin(test_ids)]

    rng = np.random.default_rng(args.seed)
    studies = sorted(idx.study_id.unique())
    pick = rng.choice(studies, size=min(args.n_studies, len(studies)),
                      replace=False)

    want_levels = (None if args.levels == "all"
                   else [s.strip() for s in args.levels.split(",")])

    # ---------------------------------------------------------------- #
    #  Cross-annotation geometry validation
    # ---------------------------------------------------------------- #
    print("=" * 74)
    print("  Cross-annotation geometry check")
    print("  Project the SAGITTAL canal annotation into the AXIAL series and ask")
    print("  whether it selects the slice that carries that level's own AXIAL")
    print("  subarticular annotations. Two independent human annotations are")
    print("  compared through the transform, so it cannot pass by identity.")
    print("=" * 74)

    rows = []
    hdr_cache = {}

    def headers(study, series):
        k = (study, series)
        if k not in hdr_cache:
            hdr_cache[k] = load_series_headers(study, series)
        return hdr_cache[k]

    for st in pick:
        sub = idx[idx.study_id == st]
        sag = sub[(sub.condition_key == "central_canal") & (sub.modality == "sag_t2")]
        ax_ = sub[(sub.condition_key.str.contains("subarticular")) &
                  (sub.modality == "ax_t2")]
        if sag.empty or ax_.empty:
            continue
        ax_series = int(ax_.series_id.iloc[0])
        ax_hdr = headers(st, ax_series)
        if not ax_hdr:
            continue
        inst_of = {h["instance"]: i for i, h in enumerate(ax_hdr)}

        for _, s in sag.iterrows():
            sh = headers(st, int(s.series_id))
            src = next((h for h in sh if h["instance"] == int(s.instance_number)), None)
            if src is None:
                continue
            p3 = pixel_to_patient(src["ipp"], src["iop"], src["ps"], s.x, s.y)
            proj = project_into(p3, ax_hdr)
            if proj is None:
                continue
            same_level = ax_[ax_.level_key == s.level_key]
            if same_level.empty:
                continue
            truth_idx = [inst_of.get(int(v)) for v in same_level.instance_number
                         if int(v) in inst_of]
            if not truth_idx:
                continue
            off = min(abs(proj["index"] - t) for t in truth_idx)
            thick = proj["slice"]["thickness"] or 4.0
            rows.append(dict(study_id=st, level=s.level_key,
                             slice_offset=off, offset_mm=off * thick,
                             out_of_plane_mm=proj["out_of_plane_mm"]))

    if rows:
        v = pd.DataFrame(rows)
        n = len(v)
        print("  {} sagittal canal annotations projected into axial".format(n))
        print("  slice offset from that level's own axial annotation:")
        for k in (0, 1, 2):
            c = int((v.slice_offset == k).sum())
            print("      exactly {} slice(s) away : {:>4}  ({:.0%})".format(
                k, c, c / n))
        far = int((v.slice_offset > 2).sum())
        print("      more than 2 away        : {:>4}  ({:.0%})".format(far, far / n))
        print("  median offset {:.1f} mm   |   90th pct {:.1f} mm".format(
            v.offset_mm.median(), v.offset_mm.quantile(0.9)))
        print("")
        good = float((v.slice_offset <= 1).mean())
        print("  VERDICT: {:.0%} land within one slice of an independently".format(good))
        print("           annotated target at the same level.")
        if good >= 0.80:
            print("           Correspondence behaves as Chapter 3 assumes.")
        else:
            print("           [!] correspondence is NOT reliable; RQ2's null")
            print("           result cannot be interpreted until this is resolved.")
        v.to_csv(os.path.join(outdir, "geometry_crosscheck.csv"), index=False)
        print("  {}".format(os.path.relpath(
            os.path.join(outdir, "geometry_crosscheck.csv"), PROJECT_ROOT)))
    else:
        print("  [FAIL] no comparable annotation pairs found.")

    if args.validate_only:
        return 0

    # ---------------------------------------------------------------- #
    #  Two-plane review sheets
    # ---------------------------------------------------------------- #
    print("")
    print("  Rendering review sheets...")
    checklist = []
    made = 0
    for st in pick:
        sub = idx[idx.study_id == st]
        if want_levels is not None:
            sub = sub[sub.level_key.isin(want_levels)]
        if sub.empty:
            continue
        targets = sub.sort_values(["level_key", "condition_key"])
        n = len(targets)
        if n == 0:
            continue
        fig, axes = plt.subplots(n, 2, figsize=(7.2, 3.4 * n))
        axes = np.atleast_2d(axes)
        ok_any = False
        for k, (_, t) in enumerate(targets.iterrows()):
            sh = headers(st, int(t.series_id))
            src = next((h for h in sh if h["instance"] == int(t.instance_number)),
                       None)
            if src is None:
                axes[k][0].axis("off"); axes[k][1].axis("off")
                continue
            p3 = pixel_to_patient(src["ipp"], src["iop"], src["ps"], t.x, t.y)
            colour = GRADE_COLOUR.get(int(t.label), "#888888")

            img = slice_pixels(src)
            nat, trunc = draw_panel(
                axes[k][0], img, t.x, t.y, src["ps"], args.fov_mm,
                "{}  {}  [{}]".format(t.condition_key.replace("_", " "),
                                      t.level_key, t.modality),
                "annotated plane - reference {}".format(GRADES[int(t.label)]),
                colour, args.radius_mm, in_plane=True)

            # the other plane: axial if annotated on sagittal, else sagittal T2
            other_mod = "ax_t2" if t.modality.startswith("sag") else "sag_t2"
            other = sub[sub.modality == other_mod]
            drew = False
            if not other.empty:
                oh = headers(st, int(other.series_id.iloc[0]))
                proj = project_into(p3, oh)
                if proj is not None:
                    oimg = slice_pixels(proj["slice"])
                    draw_panel(
                        axes[k][1], oimg, proj["col"], proj["row"],
                        proj["slice"]["ps"], args.fov_mm,
                        "same point in {}".format(other_mod),
                        "cross-plane (projected) - {:.1f} mm off-plane".format(
                            proj["out_of_plane_mm"]),
                        colour, args.radius_mm, in_plane=False)
                    drew = True
                    ok_any = True
                    checklist.append(dict(
                        study_id=st, level=t.level_key,
                        condition=t.condition_key, reference_grade=GRADES[int(t.label)],
                        annotated_plane=t.modality, cross_plane=other_mod,
                        out_of_plane_mm=round(proj["out_of_plane_mm"], 2),
                        crop_truncated=bool(trunc),
                        correct_level="", canal_foramen_included="",
                        left_right_correct="", axial_coverage_adequate="",
                        correspondence_ok="", reviewer_note=""))
            if not drew:
                axes[k][1].axis("off")
                axes[k][1].set_title("no corresponding {} series".format(other_mod),
                                     fontsize=7)
        if not ok_any:
            plt.close(fig)
            continue
        fig.suptitle(
            "ROI quality control - study {}\n"
            "Solid circle = annotated plane. Dashed = the SAME 3D point projected "
            "into the other plane.\n"
            "Colour = REFERENCE grade. Red border = crop truncated at the image "
            "edge.\n"
            "The system grades severity at a supplied location. It does not "
            "detect or name pathology.".format(st), fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.10 / max(1, n) - 0.02))
        p = os.path.join(outdir, "qc_study_{}.png".format(st))
        fig.savefig(p, dpi=170)
        plt.close(fig)
        made += 1

    if checklist:
        cdf = pd.DataFrame(checklist)
        cp = os.path.join(outdir, "roi_qc_checklist.csv")
        cdf.to_csv(cp, index=False)
        print("  {} review sheets, {} targets".format(made, len(cdf)))
        print("  truncated crops: {} ({:.0%})".format(
            int(cdf.crop_truncated.sum()), cdf.crop_truncated.mean()))
        print("  median out-of-plane distance {:.1f} mm".format(
            cdf.out_of_plane_mm.median()))
        print("  {}".format(os.path.relpath(cp, PROJECT_ROOT)))
        print("  blank columns are for the reader: correct_level, "
              "canal_foramen_included,")
        print("  left_right_correct, axial_coverage_adequate, correspondence_ok")
    print("  {}".format(os.path.relpath(outdir, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
