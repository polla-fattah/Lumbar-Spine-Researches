"""Positive control: does the screen detect text it is known to contain?

A screen that flags nothing may be reassuring or may be broken, and the two are
indistinguishable without a case that MUST be caught. This burns realistic
scanner-style text into every slice of a real, unflagged series and re-runs the
detector on it.
"""
import os, sys
import numpy as np
import cv2
sys.path.insert(0, os.path.join(os.getcwd(), 'tools'))
from detect_burned_in_text import find_series, series_minimum, text_like, norm01
import pydicom

root = os.path.join('data', 'rizgary_unpacked')
groups = find_series(root)
key = sorted(groups)[0]
paths = groups[key]

m, skipped, used = series_minimum(paths)
base_score, base_detail = text_like(m)
print('clean series : %s' % os.path.relpath(key, root))
print('  slices used %d, score %.1f, bright px %d'
      % (used, base_score, base_detail['bright_px']))

# rebuild the same series with text burned into every slice, same position
stack = []
for q in paths[:40]:
    try:
        a = pydicom.dcmread(q, force=True).pixel_array
    except Exception:
        continue
    if a is None or a.ndim != 2:
        continue
    n = norm01(a)
    if n is None:
        continue
    if stack and n.shape != stack[0].shape:
        continue
    img = (n * 255).astype(np.uint8)
    for txt, y in (('PATIENT NAME', 18), ('DOB 01/01/1970', 34)):
        cv2.putText(img, txt, (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.32,
                    255, 1, cv2.LINE_AA)
    stack.append(img.astype(np.float32) / 255.0)

mt = np.min(np.stack(stack, axis=0), axis=0)
t_score, t_detail = text_like(mt)
print('same series with burned-in text:')
print('  score %.1f, bright px %d, small comps %d'
      % (t_score, t_detail['bright_px'], t_detail['n_small_components']))
print()
ok = t_score >= 3.0 and base_score < 3.0
print('POSITIVE CONTROL %s' % ('PASSED' if ok else 'FAILED'))
if not ok:
    print('  the screen cannot detect text it is known to contain;')
    print('  a clean result from it means nothing.')

os.makedirs('data/governance', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(8, 4.2))
ax[0].imshow(m, cmap='gray', vmin=0, vmax=1)
ax[0].set_title('clean series minimum\nscore %.1f' % base_score, fontsize=9)
ax[1].imshow(mt, cmap='gray', vmin=0, vmax=1)
ax[1].set_title('with burned-in text\nscore %.1f' % t_score, fontsize=9)
for a_ in ax: a_.set_xticks([]); a_.set_yticks([])
fig.suptitle('Positive control for the burned-in text screen', fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig('data/governance/burnin_positive_control.png', dpi=140)
print('  data/governance/burnin_positive_control.png')
