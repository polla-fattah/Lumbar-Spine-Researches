"""Are RSNA's left/right annotations themselves mirrored about the midline?

The Grad-CAM means showed left-subarticular attention 11.3 px left of centre and
right-subarticular only 0.9 px right -- a separation in the correct direction but
not a clean mirror. Two very different explanations:

  (a) the MODEL learned an asymmetric representation, or
  (b) the ANNOTATIONS are themselves asymmetric, and the model faithfully
      reproduces them.

This distinguishes them by measuring the annotations alone, with no model
involved. Positions are expressed relative to each slice's own horizontal
centre, in mm, so studies of different matrix size and pixel spacing are
comparable.

Axial targets only: left-right is in-plane on axial and through-plane on
sagittal, so only axial annotations carry in-plane laterality at all.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))

idx = pd.read_csv('data/cache/rsna_roi_v2_index.csv')
split = pd.read_csv('implementation/splits/rsna_patient_split.csv')
test = set(split.loc[split.partition == 'test', 'study_id'].astype(int))

ax = idx[(idx.modality == 'ax_t2') & (idx.study_id.isin(test))].copy()
print('axial annotations on test studies:', len(ax))

# image width per series, read once per series from any of its slices
import pydicom
RSNA = r'C:\Users\USER\Desktop\Polla\Lumbar\rsna\train_images'
meta = {}
for (st, se), _g in ax.groupby(['study_id', 'series_id']):
    d = os.path.join(RSNA, str(st), str(se))
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d)[:1]:
        try:
            ds = pydicom.dcmread(os.path.join(d, f), stop_before_pixels=True,
                                 force=True)
            meta[(st, se)] = (int(ds.Columns),
                              float(np.asarray(ds.PixelSpacing, float)[1]))
        except Exception:
            pass

ax['cols'] = [meta.get((s, e), (np.nan, np.nan))[0]
              for s, e in zip(ax.study_id, ax.series_id)]
ax['colsp'] = [meta.get((s, e), (np.nan, np.nan))[1]
               for s, e in zip(ax.study_id, ax.series_id)]
ax = ax.dropna(subset=['cols', 'colsp'])
ax['offset_mm'] = (ax.x - (ax.cols - 1) / 2.0) * ax.colsp

print('with geometry:', len(ax), 'across', ax.study_id.nunique(), 'studies')
print()
print('%-22s %6s %9s %9s' % ('condition', 'n', 'mean mm', 'median mm'))
res = {}
for c, g in ax.groupby('condition_key'):
    res[c] = g.offset_mm
    print('%-22s %6d %+9.2f %+9.2f' % (c, len(g), g.offset_mm.mean(),
                                       g.offset_mm.median()))

print()
print('Positive = right of image centre. Radiological convention renders')
print('patient-LEFT on the image RIGHT, so left_* should be POSITIVE.')
print()
for l, r in (('left_subarticular', 'right_subarticular'),):
    if l in res and r in res:
        a, b = res[l], res[r]
        print('%s  mean %+.2f mm' % (l, a.mean()))
        print('%s mean %+.2f mm' % (r, b.mean()))
        print('separation           %.2f mm' % abs(a.mean() - b.mean()))
        print('symmetry (|left+right|, 0 = perfect mirror)  %.2f mm'
              % abs(a.mean() + b.mean()))
