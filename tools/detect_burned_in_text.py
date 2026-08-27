#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Detect burned-in text in DICOM pixel data, without trusting the header.

WHY A PIXEL CHECK IS NECESSARY
------------------------------
Header-based detection does not work on this cohort, and believing it does is
worse than having no check at all. `tools/deidentify_dicom.py` flags a study
when `BurnedInAnnotation` is "YES" or the modality is Secondary Capture. On a
379-file sample of the Rizgary studies:

    BurnedInAnnotation present   0 / 379   (the tag is absent entirely)
    Modality SC or OT            0 / 379   (all are MR Image Storage)

So that flag can never fire here. An absent tag means the scanner declared
nothing; it is not a statement that the pixels are clean. Tag-stripping
de-identification will happily pass through a patient name rendered into the
image itself, and that is a disclosure regardless of how clean the header is.

WHAT THIS LOOKS FOR
-------------------
An earlier version of this screen thresholded bright pixels in a border band and
flagged 75% of a 535-image sample. Inspecting the flagged images showed it was
firing on anatomy and background noise, not text: in sagittal lumbar MRI the
spine fills the frame, so a border band contains spinous processes, fat and
cerebrospinal fluid, and none of the inspected images carried any text at all.
A screen with a 75% flag rate is not a screen.

The discriminator used instead exploits a property text has and anatomy does
not: **a scanner overlay is burned at the same pixel position in every slice of
a series, while anatomy changes from slice to slice.** Taking the pixel-wise
MINIMUM across all slices of a series therefore preserves burned-in text and
suppresses anatomy, because any pixel that is dark in even one slice collapses
to dark.

The minimum image is then searched for bright, small, text-sized components. A
series with no overlay yields a near-black minimum; a series with a corner
annotation yields exactly that annotation.

This also fixes a second problem. The header-based flag in
`tools/deidentify_dicom.py` fires on `BurnedInAnnotation == "YES"` or modality
Secondary Capture. On this cohort the tag is absent from every file and every
object is MR Image Storage, so that flag can never fire. An absent tag means
the scanner declared nothing; it is not a statement that the pixels are clean.

THIS IS A SCREEN, NOT A GUARANTEE
---------------------------------
It reports candidates for human inspection. A clean result is evidence that no
obvious overlay is present, not proof that no study anywhere carries text. Any
study flagged here must be looked at before the cohort leaves the institution,
and a sample of unflagged studies should be looked at too, because a screen
whose false-negative rate is unmeasured is not yet a control.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np


def norm01(a, lo_pct=1.0, hi_pct=99.5):
    """Percentile-window an array to [0,1]. MRI has no standard scale."""
    a = a.astype(np.float32)
    lo, hi = np.percentile(a, [lo_pct, hi_pct])
    if hi <= lo:
        return None
    return np.clip((a - lo) / (hi - lo), 0.0, 1.0)


def series_minimum(paths, max_slices=40):
    """Pixel-wise minimum over a series, after per-slice normalisation.

    Burned-in text occupies the same pixels in every slice and survives the
    minimum. Anatomy moves between slices, so any pixel that is dark in even one
    slice collapses to dark. Slices of differing size are skipped rather than
    resized, because resizing would blur exactly the small features being
    looked for.
    """
    import pydicom
    stack, shape, skipped = [], None, 0
    for q in paths[:max_slices]:
        try:
            arr = pydicom.dcmread(q, force=True).pixel_array
        except Exception:
            skipped += 1
            continue
        if arr is None or arr.ndim != 2:
            skipped += 1
            continue
        if shape is None:
            shape = arr.shape
        elif arr.shape != shape:
            skipped += 1
            continue
        n = norm01(arr)
        if n is not None:
            stack.append(n)
    if len(stack) < 3:
        return None, skipped, len(stack)
    return np.min(np.stack(stack, axis=0), axis=0), skipped, len(stack)


def text_like(minimg, bright=0.55, min_comp=4, max_comp_frac=0.0025):
    """Count small bright components in a series-minimum image."""
    import cv2
    mask = (minimg > bright).astype(np.uint8)
    n_bright = int(mask.sum())
    if n_bright == 0:
        return 0.0, dict(bright_px=0, n_components=0, n_small_components=0,
                         largest_component_frac=0.0)
    lab_n, _lab, stats, _cent = cv2.connectedComponentsWithStats(
        mask, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA] if lab_n > 1 else np.array([])
    if areas.size == 0:
        return 0.0, dict(bright_px=n_bright, n_components=0,
                         n_small_components=0, largest_component_frac=0.0)
    h, w = minimg.shape
    cap = max(6, int(max_comp_frac * h * w))
    small = areas[(areas >= min_comp) & (areas <= cap)]
    biggest = float(areas.max()) / float(h * w)
    return float(small.size), dict(
        bright_px=n_bright, n_components=int(areas.size),
        n_small_components=int(small.size),
        largest_component_frac=round(biggest, 6))


def find_series(root):
    """Group files by their containing directory, which is one series here."""
    groups = {}
    for dirpath, _dirs, names in os.walk(root):
        files = [os.path.join(dirpath, n) for n in sorted(names)]
        if len(files) >= 3:
            groups[dirpath] = files
    return groups


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join("data", "rizgary_unpacked"))
    ap.add_argument("--sample", type=int, default=80,
                    help="series to examine; 0 for all")
    ap.add_argument("--seed", type=int, default=20260827)
    ap.add_argument("--min_score", type=float, default=3.0,
                    help="small persistent components needed to flag a series")
    ap.add_argument("--save_flagged", type=int, default=8,
                    help="write this many flagged minimum-images for inspection")
    ap.add_argument("--out", default=os.path.join("data", "governance",
                                                  "burned_in_screen.csv"))
    args = ap.parse_args()

    try:
        import cv2  # noqa: F401
    except ImportError:
        print("[FAIL] opencv is required: pip install opencv-python")
        return 2
    import pandas as pd

    groups = find_series(args.root)
    if not groups:
        print("[FAIL] no multi-file series under {}".format(args.root))
        return 1
    keys = sorted(groups)
    if args.sample and args.sample < len(keys):
        rng = np.random.default_rng(args.seed)
        keys = [keys[i] for i in
                sorted(rng.choice(len(keys), args.sample, replace=False))]

    rows, mins = [], {}
    for k in keys:
        m, skipped, used = series_minimum(groups[k])
        if m is None:
            rows.append(dict(series=os.path.relpath(k, args.root), score=np.nan,
                             slices_used=used, slices_skipped=skipped,
                             note="too few comparable slices"))
            continue
        score, detail = text_like(m)
        rows.append(dict(series=os.path.relpath(k, args.root), score=score,
                         slices_used=used, slices_skipped=skipped, note="",
                         **detail))
        mins[k] = m

    df = pd.DataFrame(rows)
    ok = df[df.score.notna()]
    flagged = ok[ok.score >= args.min_score].sort_values("score", ascending=False)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)

    print("=" * 74)
    print("  Burned-in text screen -- per-series minimum projection")
    print("=" * 74)
    print("  series examined            : {}".format(len(ok)))
    print("  series with too few slices : {}".format(int(df.score.isna().sum())))
    print("  median bright pixels in the series minimum : {:.0f}".format(
        ok.bright_px.median() if len(ok) else float("nan")))
    print("  FLAGGED (score >= {})       : {}  ({:.1%})".format(
        args.min_score, len(flagged), len(flagged) / max(len(ok), 1)))
    for _, r in flagged.head(10).iterrows():
        print("     score {:5.1f}   {} small comps   {}".format(
            r.score, int(r.n_small_components), r.series))

    if args.save_flagged and len(flagged):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        sel = list(flagged.series.head(args.save_flagged))
        picks = [k for k in mins
                 if os.path.relpath(k, args.root) in sel][:args.save_flagged]
        if picks:
            n = len(picks)
            fig, axes = plt.subplots(1, n, figsize=(3.0 * n, 3.4))
            axes = np.atleast_1d(axes)
            for i, k in enumerate(picks):
                axes[i].imshow(mins[k], cmap="gray", vmin=0, vmax=1)
                axes[i].set_title(os.path.basename(k)[:22], fontsize=7)
                axes[i].set_xticks([]); axes[i].set_yticks([])
            fig.suptitle("Series-minimum images for flagged series. Burned-in "
                         "text would appear as legible characters; anatomy "
                         "should be suppressed.", fontsize=8)
            fig.tight_layout(rect=(0, 0, 1, 0.90))
            fp = os.path.join(os.path.dirname(args.out), "burned_in_flagged.png")
            fig.savefig(fp, dpi=150)
            plt.close(fig)
            print("  {}".format(fp))

    print("  {}".format(args.out))
    print("  A clean result is evidence, not proof. Inspect flagged series, and")
    print("  a sample of unflagged ones, before the cohort leaves the site.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
