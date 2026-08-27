#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Grad-CAM attribution for the graph rungs E5-E7.

WHY THIS EXISTS SEPARATELY
--------------------------
`amog_attribution.py` covers E0-E4 only. The graph rungs reach `forward_target`
through `forward_graph`, whose batch is (B, N, M, 3, H, W) over 25 nodes per
patient rather than (B, M, 3, H, W) over one target, so the probe needs a
different entry point.

That gap mattered. Chapter 4's mechanism for the null results -- that the
convolutional encoder already localises, leaving structural priors little to
add -- was measured on E0-E4 and therefore **not on the final system**. It was
recorded as a limitation. This closes it.

CHOOSING THE ENCODER, AGAIN
---------------------------
The same trap as in the target-rung probe applies here and is easier to fall
into. `forward_graph` calls `forward_target` with `ann_slot=None`, so nothing in
the graph path knows which sequence a node's target was annotated on. Hooking
one encoder would measure the sagittal T1 encoder's attention on subarticular
nodes graded from axial T2, which in the target-rung case reversed the sign of
the headline comparison.

The mapping is recoverable because node index determines condition
(node % 5), and in LumbarDISC each condition is annotated on one sequence.
Verified against the index over all 48,657 targets:

    left/right foraminal   -> sagittal T1   19,689 of 19,689
    left/right subarticular-> axial T2      19,215 of 19,215
    central canal          -> sagittal T2    9,748 of 9,753

Five central-canal targets are annotated on sagittal T1 instead, 0.01% of the
cohort. They are absorbed into the canal mapping rather than special-cased; at
that rate the effect on a mean over thousands of nodes is below the reporting
precision.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, PROJECT_ROOT, resolve_mode  # noqa: E402
from amog_models import MODALITIES  # noqa: E402
from amog_train import (  # noqa: E402
    AMOGNet, GRAPH_STAGES, make_datasets, suggest_batch, loader_kwargs,
    configure_backend,
)
from amog_attribution import (  # noqa: E402
    CROP, RANDOM_INIT, cam_layer, central_disc, dataset_args,
)

# CONDITIONS is [left_foraminal, left_subarticular, central_canal,
#                right_subarticular, right_foraminal]
# MODALITIES is [sag_t1, sag_t2, ax_t2]
CONDITION_SLOT = [0, 2, 1, 2, 0]


@torch.no_grad()
def _noop():
    pass


def gradcam_graph(model, imgs, mask, ev, layers, device):
    """CAM per NODE, from the encoder that read that node's annotated sequence.

    Returns (cam (B*N, CROP, CROP), node_condition (B*N,)).
    """
    acts, grads, handles = {}, {}, []

    def mk(i):
        def fwd(_m, _i, o):
            acts[i] = o

        def bwd(_m, _gi, go):
            grads[i] = go[0]
        return fwd, bwd

    for i, lay in enumerate(layers):
        f, b = mk(i)
        handles.append(lay.register_forward_hook(f))
        handles.append(lay.register_full_backward_hook(b))
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits, _g = model.forward_graph(imgs, mask, ev)
            flat = logits.reshape(-1, logits.size(-1))
            sel = flat.argmax(dim=1)
            flat.gather(1, sel.unsqueeze(1)).sum().backward()

        maps = {}
        for i in acts:
            if i not in grads:
                continue
            a, g = acts[i], grads[i]
            w = g.mean(dim=(2, 3), keepdim=True)
            cam = F.relu((w * a).sum(dim=1, keepdim=True))
            maps[i] = F.interpolate(cam.float(), size=(CROP, CROP),
                                    mode="bilinear", align_corners=False)[:, 0]
        if not maps:
            raise RuntimeError("Grad-CAM hooks captured nothing")

        B, N = imgs.shape[:2]
        cond = torch.arange(N, device=imgs.device).remainder(5).repeat(B)
        slot = torch.tensor(CONDITION_SLOT, device=imgs.device)[cond]

        any_map = list(maps.values())[0]
        out = torch.zeros(any_map.shape[0], CROP, CROP, device=imgs.device)
        for i, m in maps.items():
            pick = (slot == i)
            if pick.any():
                out[pick] = m[pick]
        covered = torch.isin(slot, torch.tensor(sorted(maps), device=imgs.device))
        if (~covered).any():
            out[~covered] = any_map[~covered]

        f2 = out.reshape(out.shape[0], -1)
        tot = f2.sum(dim=1, keepdim=True)
        f2 = torch.where(tot > 0, f2 / tot, torch.full_like(f2, 1.0 / f2.size(1)))
        return (f2.reshape(-1, CROP, CROP).detach().cpu().numpy(),
                cond.detach().cpu().numpy())
    finally:
        for h in handles:
            h.remove()


def run_stage(stage, seed, ctx, gpu, args, disc):
    random_init = (stage == RANDOM_INIT)
    base = args.stage if random_init else stage
    ck = os.path.join(ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(
        stage, ctx.mode, seed))
    if not random_init and not os.path.exists(ck):
        print("  [skip] no checkpoint: {}".format(os.path.basename(ck)))
        return None

    torch.manual_seed(seed)
    np.random.seed(seed)
    _, _, test_ds, _ = make_datasets(
        ctx, base, dataset_args(base, seed, args.workers, args.batch_size))
    bs = max(1, min(8, suggest_batch(True, gpu["vram_gb"], args.batch_size)))
    lkw = loader_kwargs(args.workers, cuda=str(ctx.device).startswith("cuda"))
    loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **lkw)

    bb = args.backbone if random_init else (
        torch.load(ck, map_location="cpu", weights_only=False).get("backbone")
        or args.backbone)
    model = AMOGNet(base, bb, args.dim, False, False, seed,
                    pretrained=False).to(ctx.device)
    if not random_init:
        sd = torch.load(ck, map_location=ctx.device, weights_only=False)
        model.load_state_dict(sd["model_state_dict"], strict=True)
    model.eval()
    layers = [cam_layer(e, args.layer) for e in model.encoders]
    dm = torch.from_numpy(disc.astype(np.float32)).to(ctx.device)

    frac, conds, n = [], [], 0
    for batch in loader:
        imgs, mask, y, lmask, ev, _pid = [b.to(ctx.device) for b in batch]
        cam, cond = gradcam_graph(model, imgs, mask, ev, layers, ctx.device)
        keep = lmask.reshape(-1).detach().cpu().numpy() > 0
        if keep.sum() == 0:
            continue
        c = torch.from_numpy(cam[keep]).to(ctx.device)
        frac.append(((c * dm).sum(dim=(1, 2))).detach().cpu().numpy())
        conds.append(cond[keep])
        n += int(keep.sum())
        if args.max_samples and n >= args.max_samples:
            break
    if not frac:
        return None
    return np.concatenate(frac), np.concatenate(conds), bb


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", default="E6", choices=sorted(GRAPH_STAGES))
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--mode", default="real", choices=["real", "smoke"])
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--layer", default="layer3")
    ap.add_argument("--batch_size", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--radius_frac", type=float, default=0.5)
    ap.add_argument("--max_samples", type=int, default=3000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ctx = resolve_mode(argparse.Namespace(
        mode=args.mode, seed=42, epochs=None, lr=None, device=None,
        max_samples=None, batch_size=args.batch_size or None))
    gpu = configure_backend()
    disc, area = central_disc(args.radius_frac)
    seeds = [int(s) for s in args.seeds.split(",")]

    print("  central disc covers {:.1%} of the crop".format(area))
    results, bb_of = {}, {}
    for tag in (args.stage, RANDOM_INIT):
        rows = []
        for seed in seeds:
            r = run_stage(tag, seed, ctx, gpu, args, disc)
            if r is None:
                continue
            f, c, bb = r
            bb_of[tag] = bb
            rows.append(dict(seed=seed, mean=float(f.mean()), n=int(f.size),
                             by_condition={CONDITIONS[k]: float(f[c == k].mean())
                                           for k in range(len(CONDITIONS))
                                           if (c == k).any()}))
            print("  {} seed {}: CAM mass in disc {:.3f}  (n={})".format(
                tag, seed, f.mean(), f.size))
        if rows:
            results[tag] = rows

    if not results:
        print("[FAIL] no checkpoints found.")
        return 1

    print("")
    print("=" * 74)
    print("  Grad-CAM concentration, graph rung {}".format(args.stage))
    print("=" * 74)
    print("  uniform map (disc area)        {:.3f}".format(area))
    for tag, rows in results.items():
        m = np.mean([r["mean"] for r in rows])
        s = np.std([r["mean"] for r in rows], ddof=1) if len(rows) > 1 else 0.0
        print("  {:<30} {:.3f} +/- {:.3f}".format(tag, m, s))
    if args.stage in results and RANDOM_INIT in results:
        a = np.mean([r["mean"] for r in results[args.stage]])
        b = np.mean([r["mean"] for r in results[RANDOM_INIT]])
        print("")
        print("  minus RANDOM_INIT              {:+.3f}".format(a - b))
    print("=" * 74)

    out = args.out or os.path.join(PROJECT_ROOT, "data", "reports",
                                   "attribution_{}_{}.json".format(
                                       args.stage, args.layer))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(stage=args.stage, seeds=seeds, layer=args.layer,
                       radius_frac=args.radius_frac, disc_area=area,
                       condition_slot=CONDITION_SLOT, modalities=MODALITIES,
                       results=results), fh, indent=2)
    print("  {}".format(os.path.relpath(out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
