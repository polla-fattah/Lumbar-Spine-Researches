#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Render Grad-CAM attribution as figures.

`amog_attribution.py` reduces attribution to one number per target -- the
fraction of Grad-CAM mass inside a central disc. This script draws the maps that
number summarises, for the results chapter and for reader inspection.

WHAT THESE FIGURES DO AND DO NOT SHOW
-------------------------------------
They do NOT show lesion detection. The model is handed a crop already centred on
the annotated coordinate; it never searches a study for pathology. Nor does it
name a pathology: LumbarDISC labels the SEVERITY of stenosis at a condition and
level, not its cause, so nothing here distinguishes a disc bulge from facet
hypertrophy or ligamentum flavum thickening.

What they show is where, WITHIN that crop, the evidence for the assigned grade
comes from. That is a real and measurable question -- the crop is 60 mm across
and the graded structure occupies a small part of it -- and the answer is not
guaranteed: an untrained network of the same architecture puts only 0.204 of its
mass in the central disc against the 0.197 a uniform map would score, while the
trained models reach 0.46-0.58.

TWO KINDS OF FIGURE
-------------------
Per-target panels are illustrative and are chosen to include failures, not only
successes. A panel is one target: the annotated sequence, the Grad-CAM overlay,
the true and predicted grade.

The per-condition mean map is the quantitative one. Averaging every test target
of a condition cancels the anatomy of any individual patient and leaves the
systematic attention pattern, so it cannot be cherry-picked. It is the figure
that belongs in the chapter.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, LUMBAR_LEVELS, PROJECT_ROOT, resolve_mode  # noqa: E402
from amog_models import MODALITIES  # noqa: E402
from amog_train import (  # noqa: E402
    AMOGNet, make_datasets, suggest_batch, loader_kwargs, configure_backend,
)
from amog_attribution import (  # noqa: E402
    CROP, cam_layer, central_disc, dataset_args, gradcam_batch,
)

GRADES = ["Normal/Mild", "Moderate", "Severe"]


def overlay(ax, img, cam, title, sub=None):
    ax.imshow(img, cmap="gray", interpolation="bilinear")
    if cam is not None:
        # percentile clip so one hot cell does not flatten the rest
        v = np.percentile(cam, 99.5) or cam.max() or 1.0
        ax.imshow(np.clip(cam / v, 0, 1), cmap="inferno", alpha=0.45,
                  interpolation="bilinear")
    ax.set_title(title, fontsize=8)
    if sub:
        # inside the axes, not as an xlabel: at four columns the xlabels of
        # adjacent panels overlap and become unreadable
        ax.text(0.5, -0.03, sub, transform=ax.transAxes, ha="center",
                va="top", fontsize=6.5)
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", default="E2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mode", default="real", choices=["real", "smoke"])
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--layer", default="layer3")
    ap.add_argument("--batch_size", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--max_batches", type=int, default=40)
    ap.add_argument("--panels", type=int, default=12)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    ctx = resolve_mode(argparse.Namespace(
        mode=args.mode, seed=args.seed, epochs=None, lr=None, device=None,
        max_samples=None, batch_size=args.batch_size or None))
    gpu = configure_backend()
    outdir = args.outdir or os.path.join(PROJECT_ROOT, "data", "reports", "figures")
    os.makedirs(outdir, exist_ok=True)

    ck = os.path.join(ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(
        args.stage, ctx.mode, args.seed))
    if not os.path.exists(ck):
        print("[FAIL] no checkpoint at {}".format(ck))
        return 1

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    _, _, test_ds, _ = make_datasets(
        ctx, args.stage, dataset_args(args.stage, args.seed, args.workers,
                                      args.batch_size))
    bs = min(64, suggest_batch(False, gpu["vram_gb"], args.batch_size))
    lkw = loader_kwargs(args.workers, cuda=str(ctx.device).startswith("cuda"))
    loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **lkw)

    sd = torch.load(ck, map_location=ctx.device, weights_only=False)
    bb = sd.get("backbone") or args.backbone
    model = AMOGNet(args.stage, bb, args.dim, False, False, args.seed,
                    pretrained=False).to(ctx.device)
    model.load_state_dict(sd["model_state_dict"], strict=True)
    model.eval()
    layers = [cam_layer(e, args.layer) for e in model.encoders]
    disc, area = central_disc(0.5)

    # accumulate per-condition mean maps, and keep a pool of candidate panels
    acc = {c: np.zeros((CROP, CROP), dtype=np.float64) for c in range(len(CONDITIONS))}
    cnt = {c: 0 for c in range(len(CONDITIONS))}
    pool = []

    for bi, batch in enumerate(loader):
        if bi >= args.max_batches:
            break
        imgs, mask, cond, lvl, yy, _pid, ann_slot = [b.to(ctx.device) for b in batch]
        cam, pred = gradcam_batch(model, imgs, mask, cond, lvl, ann_slot,
                                  layers, ctx.device)
        c_np = cond.cpu().numpy()
        y_np = yy.cpu().numpy()
        l_np = lvl.cpu().numpy()
        s_np = (ann_slot.cpu().numpy() if ann_slot is not None
                else np.zeros_like(c_np))
        im_np = imgs.detach().cpu().numpy()
        for i in range(cam.shape[0]):
            acc[int(c_np[i])] += cam[i]
            cnt[int(c_np[i])] += 1
            conc = float((cam[i] * disc).sum())
            pool.append((float(im_np[i, s_np[i], 1].mean()), bi, i,
                         im_np[i, s_np[i], 1], cam[i], int(c_np[i]), int(l_np[i]),
                         int(y_np[i]), int(pred[i]), int(s_np[i]), conc))

    if not pool:
        print("[FAIL] no targets processed.")
        return 1

    # ---- Figure 1: per-condition mean attention -------------------------- #
    fig, axes = plt.subplots(1, len(CONDITIONS), figsize=(3.0 * len(CONDITIONS), 3.6))
    for k, c in enumerate(range(len(CONDITIONS))):
        m = acc[c] / max(cnt[c], 1)
        ax = axes[k]
        im = ax.imshow(m, cmap="inferno", interpolation="bilinear")
        ax.contour(disc.astype(float), levels=[0.5], colors="cyan", linewidths=1.0)
        inside = float((m * disc).sum() / max(m.sum(), 1e-12))
        ax.set_title("{}\nn={}, {:.0%} in disc".format(
            CONDITIONS[c].replace("_", " "), cnt[c], inside), fontsize=8)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Mean Grad-CAM per condition, {} seed {} ({}). Cyan = 15 mm disc "
                 "({:.1%} of frame); uniform would score {:.1%}."
                 .format(args.stage, args.seed, args.layer, area, area),
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    p1 = os.path.join(outdir, "cam_mean_by_condition_{}_seed{}.png".format(
        args.stage, args.seed))
    fig.savefig(p1, dpi=170)
    plt.close(fig)

    # ---- Figure 2: example panels, deliberately including failures -------- #
    # Sort so the selection spans correct-severe, correct-normal and errors
    correct = [r for r in pool if r[7] == r[8]]
    wrong = [r for r in pool if r[7] != r[8]]
    sev = [r for r in correct if r[7] == 2]
    mod = [r for r in correct if r[7] == 1]
    nor = [r for r in correct if r[7] == 0]
    n = args.panels
    take = (sev[:max(1, n // 4)] + mod[:max(1, n // 4)] + nor[:max(1, n // 4)]
            + wrong[:n - 3 * max(1, n // 4)])
    take = take[:n]

    rows = int(np.ceil(len(take) / 4.0))
    fig, axes = plt.subplots(rows, 4, figsize=(12.5, 3.3 * rows))
    axes = np.atleast_2d(axes)
    for k, r in enumerate(take):
        ax = axes[k // 4][k % 4]
        _, _, _, img, cam, c, lv, yt, yp, slot, conc = r
        ok = "correct" if yt == yp else "MISS"
        overlay(ax, img, cam,
                "{} {}".format(CONDITIONS[c].replace("_", " "),
                               LUMBAR_LEVELS[lv] if lv < len(LUMBAR_LEVELS) else lv),
                "true {} / pred {} ({}) - {} - {:.0%} in disc".format(
                    GRADES[yt], GRADES[yp], ok, MODALITIES[slot], conc))
    for k in range(len(take), rows * 4):
        axes[k // 4][k % 4].axis("off")
    fig.suptitle("Grad-CAM on individual targets, {} seed {}. Failures included "
                 "deliberately. The model grades severity at a given location; it "
                 "does not detect or name pathology.".format(args.stage, args.seed),
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    p2 = os.path.join(outdir, "cam_panels_{}_seed{}.png".format(args.stage, args.seed))
    fig.savefig(p2, dpi=160)
    plt.close(fig)

    print("  targets processed: {}".format(len(pool)))
    for c in range(len(CONDITIONS)):
        if cnt[c]:
            m = acc[c] / cnt[c]
            print("    {:<20} n={:<5} {:.1%} of mean CAM mass in disc".format(
                CONDITIONS[c], cnt[c], float((m * disc).sum() / max(m.sum(), 1e-12))))

    # ---- Laterality ------------------------------------------------------ #
    # The mean maps appear to place left- and right-subarticular attention on
    # opposite sides of the midline. That is checkable, and the check has a
    # built-in negative control, because the prediction differs by condition:
    #
    #   SUBARTICULAR is graded on AXIAL T2, where left-right is IN-PLANE, so a
    #   left/right pair should separate horizontally.
    #   FORAMINAL is graded on SAGITTAL T1, where left-right is THROUGH-plane --
    #   the two sides are different slices, not different in-plane positions --
    #   so the pair should NOT separate.
    #
    # A model that separated the foraminal pair too would be showing an artefact
    # rather than laterality, so the foraminal row is what makes the axial row
    # interpretable.
    xs = np.arange(CROP)
    mid = (CROP - 1) / 2.0
    off = {}
    for c in range(len(CONDITIONS)):
        if cnt[c]:
            m = acc[c] / cnt[c]
            off[CONDITIONS[c]] = float((m.sum(axis=0) * xs).sum() / m.sum()) - mid
    print("")
    print("  Horizontal centroid offset from midline (px; +ve = right of centre)")
    for k, v in off.items():
        print("    {:<20} {:+.2f}".format(k, v))
    for lab, l, r, expect in (
            ("subarticular (axial T2, L-R in-plane)",
             "left_subarticular", "right_subarticular", "separated"),
            ("foraminal (sagittal T1, L-R through-plane)",
             "left_foraminal", "right_foraminal", "NOT separated")):
        if l in off and r in off:
            print("    {:<42} separation {:5.2f} px   (expected {})".format(
                lab, abs(off[l] - off[r]), expect))
    print("  {}".format(os.path.relpath(p1, PROJECT_ROOT)))
    print("  {}".format(os.path.relpath(p2, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
