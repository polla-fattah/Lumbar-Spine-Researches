#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Controlled input ablation for Core Contribution II.

Chapter 3 sec:method-router-interpretation commits to this experiment in as many
words:

    "The gate weights are model allocations, not causal estimates of sequence
    importance. A high axial T2 weight does not prove that axial T2 caused a
    correct decision. [...] Second, controlled input ablation tests whether
    removing the sequence with high routing weight causes a greater performance
    loss than removing a low-weight sequence. Agreement between learned
    allocation and intervention strengthens the interpretation; disagreement is
    reported rather than rationalised post hoc."

The campaign reported the FIRST of those two checks -- aggregate routing weights
by target, which replicated foraminal->sag_T1, canal->sag_T2 and
subarticular->ax_T2 in 15/15 runs -- and never ran the second. Without it,
Contribution II rests on a correlation that the chapter itself disclaims.

WHAT THIS DOES
--------------
Inference only, on the frozen test split, against checkpoints that already
exist. For each modality m the availability mask is forced to zero for m -- the
same channel the fusion and router already consult, so an ablated sequence is
*absent* rather than zeroed-but-present -- and the per-condition metric is
recompared against the unablated baseline.

The prediction under test is per condition, not global: ablating sag_T1 should
cost FORAMINAL targets more than it costs canal targets, and ablating ax_T2
should cost SUBARTICULAR targets most. A uniform drop across conditions would
mean the router allocates differently per condition but the network does not
actually depend on that allocation -- which is a real answer, and the chapter
requires it be reported as one.

Ablating every modality at once is not tested: with an all-zero mask a target
has no evidence at all, so the number would measure the head's class prior
rather than any sequence's contribution.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, PROJECT_ROOT, resolve_mode  # noqa: E402
from amog_models import MODALITIES  # noqa: E402
from amog_train import (  # noqa: E402
    AMOGNet, ROUTER_STAGES, GRAPH_STAGES, make_datasets, suggest_batch, loader_kwargs,
    configure_backend, compute_metrics,
)

# Chapter 3's stated expectation, used only for reporting agreement. It is never
# shown to the model.
EXPECTED = {
    "left_foraminal": "sag_t1",
    "right_foraminal": "sag_t1",
    "central_canal": "sag_t2",
    "left_subarticular": "ax_t2",
    "right_subarticular": "ax_t2",
}


@torch.no_grad()
def infer(model, loader, device, drop=None):
    """Test-set inference with modality `drop` withheld."""
    model.eval()
    yt, yp, cc, gw = [], [], [], []
    for batch in loader:
        imgs, mask, cond, lvl, yy, _pid, ann_slot = [b.to(device) for b in batch]
        if drop is not None:
            mask = mask.clone()
            mask[:, drop] = 0
            # A target whose ONLY sequence was the ablated one now has no
            # evidence. Those rows are dropped rather than scored: they measure
            # the class prior, and how many there are differs per modality, so
            # keeping them would confound the comparison with a change of
            # denominator.
            keep = mask.sum(dim=1) > 0
            if keep.sum() == 0:
                continue
            imgs, mask, cond = imgs[keep], mask[keep], cond[keep]
            lvl, yy, ann_slot = lvl[keep], yy[keep], ann_slot[keep]
        fused, g = model.forward_target(imgs, mask, cond, lvl, ann_slot)
        logits = model.head(fused)
        if logits.size(-1) == 2:      # ordinal head: cumulative -> class
            p = torch.sigmoid(logits.float())
            probs = torch.stack([1 - p[:, 0], p[:, 0] - p[:, 1], p[:, 1]],
                                dim=1).clamp(min=0)
        else:
            probs = torch.softmax(logits.float(), dim=1)
        yp.append(probs.argmax(1).cpu().numpy())
        yt.append(yy.cpu().numpy())
        cc.append(cond.cpu().numpy())
        if g is not None:
            gw.append(g.float().cpu().numpy())
    return (np.concatenate(yt), np.concatenate(yp), np.concatenate(cc),
            np.concatenate(gw) if gw else None)


def per_condition(yt, yp, cc, metric="qwk"):
    out = {}
    for c in range(len(CONDITIONS)):
        s = cc == c
        if s.sum() < 10 or len(np.unique(yt[s])) < 2:
            continue
        out[CONDITIONS[c]] = float(compute_metrics(yt[s], yp[s])[metric])
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # E1 is deliberately allowed. It fuses the three sequences with FIXED
    # weights and has no router at all, so it is the control this experiment
    # needs: in RSNA a condition is ANNOTATED on one particular sequence
    # (foraminal on sagittal T1, canal on sagittal T2, subarticular on axial
    # T2), which is the same pattern the router learns. Ablating the annotated
    # sequence removes the only crop actually centred on the pathology, so a
    # router-free model should suffer too. Agreement at E2 only counts as
    # evidence FOR the router to the extent it exceeds E1.
    ap.add_argument("--stage", default="E2",
                    choices=sorted(ROUTER_STAGES | {"E1"}))
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--mode", default="real", choices=["real", "smoke"])
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--batch_size", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--metric", default="qwk", choices=["qwk", "macro_f1"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.stage in GRAPH_STAGES:
        # forward_target is reached through forward_graph for these, with a
        # different batch layout. The routing claim is introduced at E2 and is
        # cleanest to test there, with the graph out of the path.
        print("[FAIL] {} is a graph rung. Test the routing claim on a target "
              "rung (E2, E3 or E4).".format(args.stage))
        return 2

    ctx = resolve_mode(argparse.Namespace(
        mode=args.mode, seed=42, epochs=None, lr=None, device=None,
        max_samples=None, batch_size=args.batch_size or None))
    gpu = configure_backend()
    seeds = [int(s) for s in args.seeds.split(",")]

    rows, gates_by_seed = [], []
    for seed in seeds:
        ck = os.path.join(ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(
            args.stage, ctx.mode, seed))
        if not os.path.exists(ck):
            print("  [skip] seed {}: no checkpoint at {}".format(seed, ck))
            continue

        torch.manual_seed(seed)
        np.random.seed(seed)
        # make_datasets reads the augmentation knobs to build the TRAIN set.
        # This is inference on the frozen test split, so augmentation is off --
        # an augmented test set would move the baseline and the ablated score by
        # different random amounts and make the drop meaningless.
        da = argparse.Namespace(
            stage=args.stage, seed=seed, shuffled=False, ungated=False,
            shuffle_labels=False, workers=args.workers,
            batch_size=args.batch_size, cache_in_ram="auto", subset=None,
            p_drop=0.0, max_targets=None, _augment=None,
            aug_intensity=0.0, aug_gamma=0.0, aug_noise=0.0, aug_bias=0.0,
            aug_translate=0.0, aug_rotate=0.0, aug_prob=0.0)
        _, _, test_ds, _ = make_datasets(ctx, args.stage, da)
        bs = suggest_batch(False, gpu["vram_gb"], args.batch_size)
        lkw = loader_kwargs(args.workers, cuda=str(ctx.device).startswith("cuda"))
        loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **lkw)

        model = AMOGNet(args.stage, args.backbone, args.dim, False, False,
                        seed, pretrained=False).to(ctx.device)
        sd = torch.load(ck, map_location=ctx.device, weights_only=False)
        model.load_state_dict(sd["model_state_dict"], strict=True)
        print("  seed {}: loaded {}  (val macro-F1 {:.4f}, epoch {})".format(
            seed, os.path.basename(ck), sd.get("val_macro_f1", float("nan")),
            sd.get("epoch", -1)))

        yt, yp, cc, gw = infer(model, loader, ctx.device, drop=None)
        base = per_condition(yt, yp, cc, args.metric)
        if gw is not None:
            gates_by_seed.append({
                CONDITIONS[c]: [round(float(v), 4)
                                for v in gw[cc == c].mean(axis=0)]
                for c in range(len(CONDITIONS)) if (cc == c).any()})

        for mi, mname in enumerate(MODALITIES):
            yt2, yp2, cc2, _ = infer(model, loader, ctx.device, drop=mi)
            abl = per_condition(yt2, yp2, cc2, args.metric)
            for cond in base:
                if cond in abl:
                    rows.append(dict(seed=seed, condition=cond, ablated=mname,
                                     base=base[cond], ablated_score=abl[cond],
                                     drop=base[cond] - abl[cond]))

    if not rows:
        print("[FAIL] nothing to report -- no checkpoints found.")
        return 1

    import pandas as pd
    df = pd.DataFrame(rows)
    agg = (df.groupby(["condition", "ablated"])["drop"]
             .agg(["mean", "std", "count"]).reset_index())

    print("")
    print("=" * 74)
    print("  Controlled input ablation -- {} on the frozen test split".format(
        args.metric))
    print("  drop = baseline - ablated. Larger drop = greater dependence.")
    print("=" * 74)
    hits = 0
    conds = [c for c in CONDITIONS if c in set(agg.condition)]
    for cond in conds:
        sub = agg[agg.condition == cond].set_index("ablated")
        worst = sub["mean"].idxmax()
        exp = EXPECTED.get(cond)
        ok = (worst == exp)
        hits += int(ok)
        print("")
        print("  {}   expected {}   most damaging {}   {}".format(
            cond, exp, worst, "AGREES" if ok else "DISAGREES"))
        for m in MODALITIES:
            if m in sub.index:
                r = sub.loc[m]
                star = " <--" if m == worst else ""
                sd_ = 0.0 if np.isnan(r["std"]) else r["std"]
                print("      drop without {:<8} {:+.4f} +/- {:.4f}{}".format(
                    m, r["mean"], sd_, star))
    print("")
    print("  agreement with the Chapter 3 expectation: {}/{} conditions".format(
        hits, len(conds)))
    print("=" * 74)

    out = args.out or os.path.join(PROJECT_ROOT, "data", "reports",
                                   "input_ablation_{}.json".format(args.stage))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(stage=args.stage, metric=args.metric, seeds=seeds,
                       expected=EXPECTED, agreement=hits, n_conditions=len(conds),
                       per_seed=rows, aggregate=agg.to_dict(orient="records"),
                       gate_weights_by_seed=gates_by_seed,
                       modalities=MODALITIES), fh, indent=2)
    df.to_csv(out.replace(".json", ".csv"), index=False)
    print("  {}".format(os.path.relpath(out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
