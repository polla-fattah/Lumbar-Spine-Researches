#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Grad-CAM attribution: does the model look where the pathology is?

WHY
---
The campaign established that anatomical graph topology does not beat a
degree-preserving shuffle (E6 vs E6_shuffled, +0.0051 QWK, 2/3 seeds) and that
the router's sequence preference is a property of the annotation rather than
something routing creates (see input_ablation.md). Both are null results about
*structure imposed on top of the encoder*. Neither says whether the encoder
itself attends to the right anatomy, and that is the question a reader will ask
next: if the CNN already localises the lesion, extra structural priors have
little left to add, and the nulls have an explanation rather than just a
p-value.

WHAT IS MEASURED
----------------
Every crop is centred, by construction, on the annotated coordinate of its
target -- `rsna_data.decode_roi` cuts a fixed physical field of view around it.
So the pathology sits at the middle of the image and "attends to the right
place" becomes measurable rather than impressionistic: the fraction of Grad-CAM
mass falling inside a central disc.

The number is meaningless on its own, because a disc covering p% of the frame
would collect p% of a uniform map, and convolutional networks are centre-biased
regardless of what they learned. Three references are therefore reported with it:

  * the AREA fraction of the disc -- what a uniform map would score;
  * RANDOM_INIT, the identical architecture with untrained weights, which is the
    architectural centre bias with no learning in it at all;
  * the same architecture trained on SHUFFLED LABELS (`E0_LABELSHUF`), which has
    seen this data distribution but cannot have learned lesion appearance.

RANDOM_INIT is the primary floor because it is always exactly matched. The
label-shuffled checkpoint is the stronger control in principle -- it also
controls for having trained on this data -- but only when it was trained with
the same backbone, and on this tree it was not (E0 is resnet18, E0_LABELSHUF is
resnet50), so its gap is reported and flagged rather than relied on.

A trained model that beats the floors is attending to the lesion. One that
matches them is merely looking at the middle of a crop that happens to be
centred on the lesion, which is a different and much weaker claim.

Grad-CAM is taken at the last convolutional block of the encoder that actually
read the target (layer4 for the resnets), with respect to the logit of the
PREDICTED class -- not the true class, since the goal is to explain what the
model did, not what it should have done.
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

CROP = 128

# A pseudo-stage: the same architecture with random weights, never trained.
# It costs nothing to evaluate and gives the architectural centre-bias floor
# exactly matched to the model under test, which a label-shuffled checkpoint
# only does if it was trained with the same backbone.
RANDOM_INIT = "RANDOM_INIT"


def dataset_args(stage, seed, workers, batch_size):
    """Namespace make_datasets needs, with augmentation off for inference."""
    return argparse.Namespace(
        stage=stage, seed=seed, shuffled=False, ungated=False,
        shuffle_labels=False, workers=workers, batch_size=batch_size,
        cache_in_ram="auto", subset=None, p_drop=0.0, max_targets=None,
        _augment=None, aug_intensity=0.0, aug_gamma=0.0, aug_noise=0.0,
        aug_bias=0.0, aug_translate=0.0, aug_rotate=0.0, aug_prob=0.0)


def cam_layer(encoder, which="layer3"):
    """The block Grad-CAM hooks.

    DEPTH MATTERS MORE HERE THAN IN THE USUAL GRAD-CAM SETTING. A resnet
    downsamples by 32, and these crops are 128 px, so layer4 is 4x4 -- sixteen
    cells to describe a 60 mm field of view. Concentration measured on a 4x4 map
    upsampled to 128x128 says almost nothing about where the model looked, since
    a single cell already spans 15 mm. layer3 is 8x8 and layer2 is 16x16.

    The default is therefore layer3, and --layer exposes the choice so the
    number can be shown to be stable across depths rather than an artefact of
    one.
    """
    bb = encoder.backbone
    if hasattr(bb, which):
        return getattr(bb, which)
    if hasattr(bb, "features"):          # convnext
        return bb.features
    convs = [m for m in bb.modules() if isinstance(m, torch.nn.Conv2d)]
    if not convs:
        raise RuntimeError("no convolutional layer to attribute to")
    return convs[-1]


def central_disc(radius_frac, size=CROP):
    """Boolean mask of a centred disc, plus the fraction of the frame it covers."""
    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2.0
    r = radius_frac * size / 2.0
    m = ((yy - c) ** 2 + (xx - c) ** 2) <= r * r
    return m, float(m.mean())


def gradcam_batch(model, imgs, mask, cond, lvl, ann_slot, layers, device):
    """Grad-CAM for the predicted class, from the encoder that read the target.

    WHICH ENCODER IS HOOKED IS NOT A DETAIL. E0 selects its annotated sequence
    inside forward_target, so encoders[0] genuinely sees the graded image. The
    multi-sequence rungs run one encoder PER MODALITY, so encoders[0] is always
    sagittal T1 -- and hooking only that one measured the T1 encoder's attention
    on subarticular targets that are graded from axial T2. That silently
    penalised every rung above E0 and made "no rung improves on E0" an artefact
    of the probe rather than a result.

    All encoders are therefore hooked, and each sample takes the map from the
    encoder matching its own annotated slot.
    """
    acts, grads = {}, {}
    handles = []

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
            fused, _ = model.forward_target(imgs, mask, cond, lvl, ann_slot)
            logits = model.head(fused)
            # explain the decision the model actually made
            sel = logits.argmax(dim=1)
            logits.gather(1, sel.unsqueeze(1)).sum().backward()

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

        B = imgs.size(0)
        slot = (torch.zeros(B, dtype=torch.long, device=imgs.device)
                if ann_slot is None else ann_slot.long())
        if len(maps) == 1:
            # E0: one encoder, and it already read the annotated sequence
            out = list(maps.values())[0]
        else:
            out = torch.zeros(B, CROP, CROP, device=imgs.device)
            for i, m in maps.items():
                pick = (slot == i)
                if pick.any():
                    out[pick] = m[pick]
            # a slot with no hooked encoder would leave zeros; fall back so the
            # normalisation below cannot silently invent a uniform map
            missing = ~torch.isin(slot, torch.tensor(sorted(maps), device=imgs.device))
            if missing.any():
                out[missing] = list(maps.values())[0][missing]

        flat = out.reshape(B, -1)
        tot = flat.sum(dim=1, keepdim=True)
        flat = torch.where(tot > 0, flat / tot,
                           torch.full_like(flat, 1.0 / flat.size(1)))
        return (flat.reshape(-1, CROP, CROP).detach().cpu().numpy(),
                logits.argmax(1).detach().cpu().numpy())
    finally:
        for h in handles:
            h.remove()


def run_stage(stage, seed, ctx, gpu, args, disc):
    """One model's CAM concentration. `stage` may be RANDOM_INIT (see below)."""
    random_init = (stage == RANDOM_INIT)
    ck = os.path.join(ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(
        stage, ctx.mode, seed))
    if not random_init and not os.path.exists(ck):
        print("  [skip] no checkpoint: {}".format(os.path.basename(ck)))
        return None

    torch.manual_seed(seed)
    np.random.seed(seed)
    base_stage = "E0" if random_init else stage.replace("_LABELSHUF", "")
    _, _, test_ds, _ = make_datasets(
        ctx, base_stage, dataset_args(base_stage, seed, args.workers, args.batch_size))
    bs = min(64, suggest_batch(False, gpu["vram_gb"], args.batch_size))
    lkw = loader_kwargs(args.workers, cuda=str(ctx.device).startswith("cuda"))
    loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **lkw)

    # The backbone must come from the checkpoint, never from a flag. E0 was
    # trained as resnet18 and E0_LABELSHUF as resnet50; building both from
    # --backbone silently loaded one into the other and raised 40 shape errors.
    # Worse, had the shapes happened to match, the comparison would have run and
    # been meaningless.
    bb = args.backbone if random_init else (
        torch.load(ck, map_location="cpu", weights_only=False).get("backbone")
        or args.backbone)
    model = AMOGNet(base_stage, bb, args.dim, False, False, seed,
                    pretrained=False).to(ctx.device)
    if not random_init:
        sd = torch.load(ck, map_location=ctx.device, weights_only=False)
        model.load_state_dict(sd["model_state_dict"], strict=True)
    model.eval()

    layers = [cam_layer(e, args.layer) for e in model.encoders]
    dm = torch.from_numpy(disc.astype(np.float32)).to(ctx.device)

    frac, conds, n = [], [], 0
    for batch in loader:
        imgs, mask, cond, lvl, yy, _pid, ann_slot = [b.to(ctx.device) for b in batch]
        cam, _pred = gradcam_batch(model, imgs, mask, cond, lvl, ann_slot,
                                   layers, ctx.device)
        c = torch.from_numpy(cam).to(ctx.device)
        frac.append(((c * dm).sum(dim=(1, 2))).detach().cpu().numpy())
        conds.append(cond.detach().cpu().numpy())
        n += cam.shape[0]
        if args.max_samples and n >= args.max_samples:
            break
    return np.concatenate(frac), np.concatenate(conds), bb


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", default="E0")
    ap.add_argument("--control", default="E0_LABELSHUF",
                    help="label-shuffled model; its concentration is the "
                         "centre-bias floor. Pass '' to skip.")
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--mode", default="real", choices=["real", "smoke"])
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--batch_size", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--layer", default="layer3",
                    choices=["layer1", "layer2", "layer3", "layer4"],
                    help="resnet block to attribute at. layer4 is 4x4 at this "
                         "crop size and too coarse to localise; default layer3.")
    ap.add_argument("--radius_frac", type=float, default=0.5,
                    help="disc diameter as a fraction of the crop; 0.5 is a "
                         "15 mm radius at the 60 mm field of view")
    ap.add_argument("--max_samples", type=int, default=4000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.stage in GRAPH_STAGES:
        print("[FAIL] {} is a graph rung; attribute on a target rung "
              "(E0-E4).".format(args.stage))
        return 2

    ctx = resolve_mode(argparse.Namespace(
        mode=args.mode, seed=42, epochs=None, lr=None, device=None,
        max_samples=None, batch_size=args.batch_size or None))
    gpu = configure_backend()
    disc, area = central_disc(args.radius_frac)
    seeds = [int(s) for s in args.seeds.split(",")]

    print("  central disc covers {:.1%} of the crop -- a uniform map scores "
          "exactly that".format(area))

    results, bb_of = {}, {}
    tags = [args.stage, RANDOM_INIT] + ([args.control] if args.control else [])
    for tag in tags:
        per_seed = []
        for seed in seeds:
            r = run_stage(tag, seed, ctx, gpu, args, disc)
            if r is None:
                continue
            f, c, bb = r
            bb_of[tag] = bb
            per_seed.append(dict(seed=seed, mean=float(f.mean()),
                                 n=int(f.size),
                                 by_condition={CONDITIONS[k]: float(f[c == k].mean())
                                               for k in range(len(CONDITIONS))
                                               if (c == k).any()}))
            print("  {} seed {}: CAM mass in disc {:.3f}  (n={}, {})".format(
                tag, seed, f.mean(), f.size, bb_of.get(tag, "?")))
        if per_seed:
            results[tag] = per_seed

    if not results:
        print("[FAIL] no checkpoints found.")
        return 1

    print("")
    print("=" * 74)
    print("  Grad-CAM concentration on the annotated centre")
    print("=" * 74)
    print("  uniform map (disc area)        {:.3f}".format(area))
    for tag, rows in results.items():
        m = np.mean([r["mean"] for r in rows])
        s = np.std([r["mean"] for r in rows], ddof=1) if len(rows) > 1 else 0.0
        print("  {:<30} {:.3f} +/- {:.3f}".format(tag, m, s))
    if args.stage in results:
        a = np.mean([r["mean"] for r in results[args.stage]])
        print("")
        for ref in (RANDOM_INIT, args.control):
            if ref and ref in results:
                b = np.mean([r["mean"] for r in results[ref]])
                note = ""
                if ref == args.control and bb_of.get(ref) != bb_of.get(args.stage):
                    note = ("   [!] backbone {} vs {}; NOT a matched control, "
                            "gap not interpretable".format(
                                bb_of.get(args.stage), bb_of.get(ref)))
                print("  {:<28} {:+.3f}{}".format(
                    "minus " + ref, a - b, note))
        print("  A positive gap over RANDOM_INIT is the evidence: concentration")
        print("  the labels bought, beyond the centre bias the architecture has.")
    print("=" * 74)

    out = args.out or os.path.join(PROJECT_ROOT, "data", "reports",
                                   "attribution_{}_{}.json".format(
                                       args.stage, args.layer))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(stage=args.stage, control=args.control, seeds=seeds,
                       radius_frac=args.radius_frac, disc_area=area,
                       layer=args.layer,
                       results=results, modalities=MODALITIES), fh, indent=2)
    print("  {}".format(os.path.relpath(out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
