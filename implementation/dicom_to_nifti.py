#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert an RSNA DICOM series to NIfTI, preserving patient-space geometry.

TotalSpineSeg accepts NIfTI only, so a converter is needed before its disc
landmarks can be compared with RSNA's annotated coordinates. The comparison is
only meaningful if the affine is right, so this is written against the DICOM
standard rather than by trial and error.

THE PART THAT IS EASY TO GET WRONG
----------------------------------
DICOM patient space is LPS (+x left, +y posterior, +z superior). NIfTI world
space is RAS (+x right, +y anterior, +z superior). The first two axes therefore
change sign. Getting this wrong produces a volume that segments perfectly well
and whose landmarks are mirrored -- which, for a lumbar spine, is close to
undetectable by eye and fatal for a left/right claim.

Slice order is taken from geometry, not from InstanceNumber. Instance numbers
are not guaranteed monotonic in acquisition space, and a series stored in
reverse would otherwise yield a volume flipped head-to-foot.

The reverse mapping is exposed as `world_to_voxel` so that a landmark found in
the NIfTI can be brought back to the original DICOM (series, instance, col, row)
that RSNA annotated.

DELIBERATELY NOT VALIDATED BY ROUND-TRIP
----------------------------------------
geometry.py records that the previous pipeline "validated" its transforms by
mapping a point through a matrix and back through its inverse, obtaining
0.00000000 mm error. That tests NumPy, not the data: an inverse returns the
original point whatever the matrix contains. The validation for this converter
is external -- compare TotalSpineSeg's landmarks against RSNA's independently
annotated coordinates (see compare_totalspineseg.py).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def read_series(series_dir):
    """Read a DICOM series, sorted along its own slice normal."""
    import pydicom

    files = [os.path.join(series_dir, f) for f in os.listdir(series_dir)
             if f.lower().endswith(".dcm")]
    if not files:
        raise RuntimeError("no DICOM files in {}".format(series_dir))

    slices = []
    for f in files:
        ds = pydicom.dcmread(f)
        iop = getattr(ds, "ImageOrientationPatient", None)
        ipp = getattr(ds, "ImagePositionPatient", None)
        if iop is None or ipp is None:
            continue
        slices.append((f, ds, np.asarray(ipp, dtype=np.float64),
                       np.asarray(iop, dtype=np.float64)))
    if not slices:
        raise RuntimeError("no slice in {} carries IPP/IOP".format(series_dir))

    iop0 = slices[0][3]
    r = iop0[:3] / np.linalg.norm(iop0[:3])       # increasing column
    c = iop0[3:] / np.linalg.norm(iop0[3:])       # increasing row
    n = np.cross(r, c)                            # slice normal

    # sort by position ALONG THE NORMAL, not by InstanceNumber
    slices.sort(key=lambda s: float(np.dot(s[2], n)))
    return slices, r, c, n


def series_to_nifti(series_dir, out_path):
    """Write a NIfTI with an affine derived from IPP/IOP. Returns metadata."""
    import nibabel as nib

    slices, r, c, n = read_series(series_dir)
    ds0 = slices[0][1]
    ps = [float(v) for v in getattr(ds0, "PixelSpacing", [1.0, 1.0])]
    row_sp, col_sp = ps[0], ps[1]

    vol = np.stack([s[1].pixel_array.astype(np.float32) for s in slices], axis=-1)
    # pixel_array is (rows, cols); NIfTI is built as (cols, rows, slices)
    vol = np.transpose(vol, (1, 0, 2))

    ipp0 = slices[0][2]
    if len(slices) > 1:
        slice_vec = slices[1][2] - slices[0][2]
        slice_sp = float(np.linalg.norm(slice_vec))
        if slice_sp > 0:
            n_use = slice_vec / slice_sp
        else:
            n_use, slice_sp = n, float(getattr(ds0, "SliceThickness", 1.0) or 1.0)
    else:
        n_use, slice_sp = n, float(getattr(ds0, "SliceThickness", 1.0) or 1.0)

    aff_lps = np.eye(4, dtype=np.float64)
    aff_lps[:3, 0] = r * col_sp        # +i  -> increasing column
    aff_lps[:3, 1] = c * row_sp        # +j  -> increasing row
    aff_lps[:3, 2] = n_use * slice_sp  # +k  -> next slice
    aff_lps[:3, 3] = ipp0

    # LPS -> RAS: negate the first two world axes
    lps_to_ras = np.diag([-1.0, -1.0, 1.0, 1.0])
    aff_ras = lps_to_ras @ aff_lps

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    nib.save(nib.Nifti1Image(vol, aff_ras), out_path)

    return dict(path=out_path, shape=list(vol.shape), affine=aff_ras.tolist(),
                n_slices=len(slices), row_spacing=row_sp, col_spacing=col_sp,
                slice_spacing=slice_sp,
                instance_order=[int(getattr(s[1], "InstanceNumber", -1))
                                for s in slices],
                series_dir=series_dir)


def world_to_voxel(affine, point_ras):
    """RAS world point -> (i, j, k) voxel index, unrounded."""
    inv = np.linalg.inv(np.asarray(affine, dtype=np.float64))
    h = np.array([point_ras[0], point_ras[1], point_ras[2], 1.0])
    return (inv @ h)[:3]


def dicom_point_to_ras(ipp, iop, ps, col, row):
    """RSNA annotates (x=col, y=row) on one DICOM slice. Return its RAS point."""
    iop = np.asarray(iop, dtype=np.float64).ravel()
    r = iop[:3] / np.linalg.norm(iop[:3])
    c = iop[3:] / np.linalg.norm(iop[3:])
    lps = np.asarray(ipp, dtype=np.float64) + col * float(ps[1]) * r \
        + row * float(ps[0]) * c
    return np.array([-lps[0], -lps[1], lps[2]])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("series_dir")
    ap.add_argument("out_path")
    args = ap.parse_args()
    meta = series_to_nifti(args.series_dir, args.out_path)
    print("  {}  shape {}  {} slices  spacing {:.3f}/{:.3f}/{:.3f} mm".format(
        os.path.basename(args.out_path), meta["shape"], meta["n_slices"],
        meta["col_spacing"], meta["row_spacing"], meta["slice_spacing"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
