#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DICOM patient-space geometry: the mechanism behind Core Contribution I.

WHAT THIS IS FOR
----------------
Chapter 3 claims that anatomical correspondence between MRI sequences is already
present in the DICOM headers and has been treated as a preprocessing convenience
rather than as a training signal. This module is that claim made concrete: given
a point annotated on one series, it finds the same physical point in another.

That matters here because RSNA annotates each condition on exactly one modality
(central canal on sagittal T2, foraminal on sagittal T1, subarticular on axial
T2). Of 48,657 labelled targets, none has more than one annotated modality. So
a multi-sequence stack cannot be assembled from the annotations; it has to be
derived from geometry. Which is precisely the thesis.

WHAT THE PREVIOUS IMPLEMENTATION DID
------------------------------------
dicom_geometry_parser.py never read ImageOrientationPatient. It substituted
textbook cosines chosen by a substring match on series_description:

    if 'SAG' in stype: orient = [0,1,0, 0,0,-1]
    else:              orient = [1,0,0, 0,1,0]

Those matrices do not describe these patients, so any correspondence derived
from them is fictional. Gate 3's "3D Roundtrip Mapping Error 0.00000000 mm" is
vacuous: mapping a point through a matrix and back through its inverse returns
the original point whatever the matrix contains. It tests NumPy, not the data.

DICOM CONVENTION (PS 3.3 C.7.6.2)
---------------------------------
    ImagePositionPatient  (IPP) : patient coords of the centre of the first voxel
    ImageOrientationPatient(IOP): [Rx,Ry,Rz, Cx,Cy,Cz]
                                  first triplet  = direction of increasing COLUMN
                                  second triplet = direction of increasing ROW
    PixelSpacing          (PS)  : [row_spacing, col_spacing] in mm

    P(col, row) = IPP + col * PS[1] * R + row * PS[0] * C
"""

from __future__ import annotations

import numpy as np


def plane_basis(iop):
    """Return (row_dir, col_dir, normal) as unit vectors."""
    iop = np.asarray(iop, dtype=np.float64).ravel()
    r = iop[0:3]                      # along increasing column index
    c = iop[3:6]                      # along increasing row index
    n = np.cross(r, c)
    nn = np.linalg.norm(n)
    if nn < 1e-9:
        raise ValueError("degenerate ImageOrientationPatient: {}".format(iop))
    return r, c, n / nn


def pixel_to_patient(ipp, iop, ps, col, row):
    """Pixel (col, row) on one slice -> 3D patient coordinates in mm."""
    ipp = np.asarray(ipp, dtype=np.float64).ravel()
    r, c, _ = plane_basis(iop)
    ps = np.asarray(ps, dtype=np.float64).ravel()
    return ipp + float(col) * ps[1] * r + float(row) * ps[0] * c


def distance_to_plane(point, ipp, iop):
    """Signed perpendicular distance in mm from a patient-space point to a slice."""
    ipp = np.asarray(ipp, dtype=np.float64).ravel()
    _, _, n = plane_basis(iop)
    return float(np.dot(np.asarray(point, dtype=np.float64).ravel() - ipp, n))


def patient_to_pixel(point, ipp, iop, ps):
    """Project a patient-space point onto a slice -> (col, row, out_of_plane_mm).

    The point is projected orthogonally onto the slice plane, so the returned
    pixel is where it *would* appear; out_of_plane_mm reports how far it had to
    travel, which is the quantity a caller should threshold on.
    """
    ipp = np.asarray(ipp, dtype=np.float64).ravel()
    point = np.asarray(point, dtype=np.float64).ravel()
    r, c, n = plane_basis(iop)
    ps = np.asarray(ps, dtype=np.float64).ravel()

    d = point - ipp
    out_of_plane = float(np.dot(d, n))
    in_plane = d - out_of_plane * n

    # r and c are orthonormal for well-formed DICOM, but solve least-squares so
    # slightly non-orthogonal headers degrade gracefully rather than silently.
    A = np.stack([r * ps[1], c * ps[0]], axis=1)      # 3x2
    sol, *_ = np.linalg.lstsq(A, in_plane, rcond=None)
    return float(sol[0]), float(sol[1]), out_of_plane


def nearest_slice(point, slices):
    """Pick the slice whose plane is closest to a patient-space point.

    `slices` is a sequence of dicts with ipp, iop. Returns (index, |distance|).
    """
    best_i, best_d = -1, float("inf")
    for i, s in enumerate(slices):
        try:
            d = abs(distance_to_plane(point, s["ipp"], s["iop"]))
        except ValueError:
            continue
        if d < best_d:
            best_i, best_d = i, d
    return best_i, best_d


def roundtrip_error_mm(ipp, iop, ps, col, row):
    """True round-trip check: pixel -> patient -> pixel, reported in mm.

    Unlike the previous Gate 3 this exercises the actual header values, so it
    can fail when a header is malformed.
    """
    p = pixel_to_patient(ipp, iop, ps, col, row)
    c2, r2, _ = patient_to_pixel(p, ipp, iop, ps)
    ps = np.asarray(ps, dtype=np.float64).ravel()
    return float(np.hypot((c2 - col) * ps[1], (r2 - row) * ps[0]))


if __name__ == "__main__":
    # A sagittal-like and an axial-like frame, checked against each other.
    sag = dict(ipp=[-5.0, -120.0, 60.0], iop=[0, 1, 0, 0, 0, -1], ps=[0.6, 0.6])
    ax = dict(ipp=[-90.0, -40.0, 12.0], iop=[1, 0, 0, 0, 1, 0], ps=[0.7, 0.7])

    print("round-trip error, sagittal frame : {:.3e} mm".format(
        roundtrip_error_mm(sag["ipp"], sag["iop"], sag["ps"], 137.0, 208.0)))
    print("round-trip error, axial frame    : {:.3e} mm".format(
        roundtrip_error_mm(ax["ipp"], ax["iop"], ax["ps"], 96.0, 71.0)))

    p = pixel_to_patient(sag["ipp"], sag["iop"], sag["ps"], 137.0, 208.0)
    col, row, oop = patient_to_pixel(p, ax["ipp"], ax["iop"], ax["ps"])
    print("\nsagittal pixel (137, 208) -> patient {}".format(np.round(p, 2)))
    print("  projected into the axial frame: col {:.1f}, row {:.1f}, "
          "out of plane {:.1f} mm".format(col, row, oop))
