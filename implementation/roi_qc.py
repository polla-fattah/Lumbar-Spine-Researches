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

# Overridable, because a hardcoded absolute path makes every figure in this
# chapter unreproducible on any other machine. Order: --rsna_dir, then the
# RSNA_DIR environment variable, then the location on the development machine.
RSNA_DIR = os.environ.get(
    "RSNA_DIR", r"C:\Users\USER\Desktop\Polla\Lumbar\rsna")


def file_digest(path, n=16):
    """Short SHA-256 of a file, for recording which data version was used."""
    import hashlib
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def provenance(args, index_path, split_path):
    """Everything a second researcher needs to reproduce this figure set.

    Two audiences need different halves of this. A computer-vision reader needs
    the commit, the seed, the library versions and the digest of the exact
    index and split files, because a different cache build changes which
    targets exist and therefore which studies a seed selects. A radiologist
    needs the DICOM provenance recorded per panel (see the checklist), because
    a figure that cannot be traced back to a study, series and instance cannot
    be looked up and cannot be disputed.
    """
    import subprocess
    import platform
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
            capture_output=True, text=True).stdout.strip() or None
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
            capture_output=True, text=True).stdout.strip())
    except Exception:
        commit, dirty = None, None

    vers = {}
    for m in ("numpy", "pandas", "matplotlib", "pydicom"):
        try:
            vers[m] = __import__(m).__version__
        except Exception:
            vers[m] = None

    return dict(
        generated=__import__("datetime").datetime.now().isoformat(timespec="seconds"),
        git_commit=commit, git_dirty=dirty,
        python=platform.python_version(), platform=platform.platform(),
        libraries=vers,
        rsna_dir_basename=os.path.basename(os.path.normpath(RSNA_DIR)),
        index_sha256_16=file_digest(index_path),
        split_sha256_16=file_digest(split_path),
        args={k: v for k, v in vars(args).items()})


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
                series_id=int(series_id),
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
def fname_for(study_id, level):
    """Sheet filename. Shared so checklist and manifest cannot disagree."""
    return "qc_{}_{}.png".format(study_id, str(level).replace("/", "-"))


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
    ap.add_argument("--rsna_dir", default=None,
                    help="root of the RSNA download; also settable via the "
                         "RSNA_DIR environment variable. Required for anyone "
                         "reproducing these figures on another machine.")
    ap.add_argument("--validate_only", action="store_true",
                    help="run the cross-annotation geometry check, no figures")
    ap.add_argument("--partition", default="test",
                    choices=["test", "train", "val", "dev", "all"],
                    help="'dev' is train+val, the partition ACSSL pretrained on "
                         "and therefore the one whose correspondence Contribution "
                         "I actually depended on. 'test' is what the review "
                         "sheets should show.")
    args = ap.parse_args()

    global RSNA_DIR
    if args.rsna_dir:
        RSNA_DIR = args.rsna_dir
    if not os.path.isdir(os.path.join(RSNA_DIR, "train_images")):
        print("[FAIL] no train_images under {}".format(RSNA_DIR))
        print("       pass --rsna_dir or set the RSNA_DIR environment variable")
        return 1

    import pandas as pd

    outdir = args.outdir or os.path.join(PROJECT_ROOT, "data", "reports", "roi_qc")
    os.makedirs(outdir, exist_ok=True)

    index_path = os.path.join(PROJECT_ROOT, "data", "cache",
                              "rsna_roi_v2_index.csv")
    split_path = os.path.join(PROJECT_ROOT, "implementation", "splits",
                              "rsna_patient_split.csv")
    if not os.path.exists(index_path):
        print("[FAIL] ROI index not found: {}".format(index_path))
        print("       It is generated by the cache builder and is gitignored")
        print("       because of its size. Rebuild it before running this.")
        return 1
    idx = pd.read_csv(index_path)
    split = pd.read_csv(split_path)
    if args.partition == "all":
        keep = set(split.study_id.astype(int))
    elif args.partition == "dev":
        keep = set(split.loc[split.partition.isin(["train", "val"]),
                             "study_id"].astype(int))
    else:
        keep = set(split.loc[split.partition == args.partition,
                             "study_id"].astype(int))
    idx = idx[idx.study_id.isin(keep)]
    print("  partition '{}': {} studies available".format(
        args.partition, idx.study_id.nunique()))

    # Sample from the TRACKED split, not from the index. The index is a build
    # artefact of the cache and is gitignored; keying the sample on it means a
    # different cache build silently yields a different figure set for the same
    # seed. The split file is in version control and is what a second
    # researcher will actually have.
    rng = np.random.default_rng(args.seed)
    studies = sorted(keep)
    pick = rng.choice(studies, size=min(args.n_studies, len(studies)),
                      replace=False)
    have = set(idx.study_id.unique())
    missing = [int(s) for s in pick if s not in have]
    pick = [int(s) for s in pick if s in have]
    if missing:
        print("  [note] {} sampled studies absent from the index, skipped: {}"
              .format(len(missing), missing[:5]))

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
        v.to_csv(os.path.join(outdir, "geometry_crosscheck_{}.csv".format(args.partition)), index=False)
        print("  {}".format(os.path.relpath(
            os.path.join(outdir, "geometry_crosscheck_{}.csv".format(args.partition)), PROJECT_ROOT)))
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
    manifest = []
    made = 0
    # One sheet per (study, level). A whole study at all five levels is 25
    # targets, which as a single figure is 25 rows tall and unreadable; per
    # level it is five condition rows, which is what a reader actually reviews
    # at one sitting.
    jobs = []
    for st in pick:
        sub_all = idx[idx.study_id == st]
        if want_levels is not None:
            sub_all = sub_all[sub_all.level_key.isin(want_levels)]
        for lv in sorted(sub_all.level_key.unique()):
            jobs.append((st, lv))

    for st, lv in jobs:
        sub = idx[idx.study_id == st]
        sub_lv = sub[sub.level_key == lv]
        if sub_lv.empty:
            continue
        targets = sub_lv.sort_values("condition_key")
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
                        sheet=fname_for(st, lv),
                        study_id=st, level=t.level_key,
                        condition=t.condition_key, reference_grade=GRADES[int(t.label)],
                        # DICOM provenance for BOTH panels. A radiologist who
                        # disputes a figure must be able to pull the exact slice
                        # up in a viewer; a figure that cannot be traced back to
                        # a study, series and instance cannot be checked.
                        annotated_plane=t.modality,
                        annotated_series=int(t.series_id),
                        annotated_instance=int(t.instance_number),
                        annotated_col=round(float(t.x), 2),
                        annotated_row=round(float(t.y), 2),
                        cross_plane=other_mod,
                        cross_series=int(proj["slice"].get("series_id", -1)),
                        cross_instance=int(proj["slice"]["instance"]),
                        cross_col=round(float(proj["col"]), 2),
                        cross_row=round(float(proj["row"]), 2),
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
            "ROI quality control - study {}, level {}\n"
            "Solid circle = annotated plane. Dashed = the SAME 3D point projected "
            "into the other plane.\n"
            "Colour = REFERENCE grade. Red border = crop truncated at the image "
            "edge.\n"
            "The system grades severity at a supplied location. It does not "
            "detect or name pathology.".format(st, lv), fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.10 / max(1, n) - 0.02))
        fname = fname_for(st, lv)
        p = os.path.join(outdir, fname)
        fig.savefig(p, dpi=170)
        plt.close(fig)
        made += 1
        manifest.append(dict(
            sheet=fname, study_id=st, level=lv, n_targets=n,
            partition=args.partition, seed=args.seed,
            fov_mm=args.fov_mm, radius_mm=args.radius_mm))

    if manifest:
        mdf = pd.DataFrame(manifest)
        mp = os.path.join(outdir, "roi_qc_manifest.csv")
        mdf.to_csv(mp, index=False)
        # the exact command that produced this set, so the figure set in the
        # thesis is regenerable rather than a one-off artefact
        import json as _json
        prov = provenance(args, index_path, split_path)
        with open(os.path.join(outdir, "provenance.json"), "w",
                  encoding="utf-8") as fh:
            _json.dump(prov, fh, indent=2)
        with open(os.path.join(outdir, "REPRODUCE.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write("python implementation/roi_qc.py --n_studies {} "
                     "--partition {} --seed {} --levels {} --fov_mm {} "
                     "--radius_mm {}\n".format(
                         args.n_studies, args.partition, args.seed,
                         args.levels, args.fov_mm, args.radius_mm))
            fh.write("\n{} sheets, {} studies, levels {}\n".format(
                len(mdf), mdf.study_id.nunique(),
                ", ".join(sorted(mdf.level.unique()))))
            fh.write("commit {}{}\n".format(
                prov["git_commit"],
                "  (WORKING TREE DIRTY)" if prov["git_dirty"] else ""))
            fh.write("index sha256[:16] {}\n".format(prov["index_sha256_16"]))
            fh.write("split sha256[:16] {}\n".format(prov["split_sha256_16"]))
            fh.write("Set RSNA_DIR to your own RSNA download first.\n")

        # data/ is gitignored for size, so the PROVENANCE (not the
        # PNGs) is mirrored somewhere tracked. Without this the
        # record of how the thesis figures were produced does not
        # survive a clone.
        import shutil
        tracked = os.path.join(PROJECT_ROOT, "thesis", "chapter4",
                               "roi_qc")
        os.makedirs(tracked, exist_ok=True)
        for f in ("roi_qc_manifest.csv", "provenance.json",
                  "REPRODUCE.txt"):
            src = os.path.join(outdir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(tracked, f))

    if checklist:
        cdf = pd.DataFrame(checklist)
        cp = os.path.join(outdir, "roi_qc_checklist.csv")
        cdf.to_csv(cp, index=False)
        import shutil as _sh
        _tracked = os.path.join(PROJECT_ROOT, "thesis", "chapter4", "roi_qc")
        os.makedirs(_tracked, exist_ok=True)
        _sh.copy2(cp, os.path.join(_tracked, "roi_qc_checklist.csv"))
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
