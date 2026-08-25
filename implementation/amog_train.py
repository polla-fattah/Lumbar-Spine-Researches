#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified stage trainer for the E0-E7 ablation ladder.

One engine rather than eight near-identical scripts, because the ladder's whole
logic is that consecutive rungs differ by ONE assumption. Keeping them in one
file makes the difference between rungs visible and auditable; eight copies
invite silent divergence in the parts that are supposed to be held constant.

    E0  single annotated ROI                       baseline
    E1  + geometry-derived multi-sequence, fixed fusion
    E2  + disease-conditioned routing              (vs E1's fixed fusion)
    E3  + modality dropout                         (robustness to absence)
    E4  + ACSSL cross-sequence pretraining         (label efficiency)
    E5  + homogeneous target graph                 (control for E6)
    E6  + typed heterogeneous graph, gated         (the CC III claim)
    E7  + ordinal head, clinical cost, calibration

CONTROLS, WHICH ARE NOT OPTIONAL
    --shuffled   E6 with permuted edges, identical node and edge counts. If the
                 shuffled graph matches the anatomical one, the result is that
                 extra capacity helps, not that anatomy matters.
    --ungated    E6 without the residual gate, so any gain can be attributed.

Both modes call the same step. Smoke uses synthetic tensors; real uses the
memory-mapped ROI caches. Metrics are always computed, never assigned.

USAGE
    python amog_train.py --stage E1 --mode smoke
    python amog_train.py --stage E6 --mode real --epochs 30
    python amog_train.py --stage E6 --mode real --shuffled     # the control
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import (  # noqa: E402
    add_mode_args, resolve_mode, compute_metrics, PROJECT_ROOT, N_CLASSES,
)
from amog_models import (  # noqa: E402
    SequenceEncoder, FixedFusion, DiseaseConditionedRouter, apply_modality_dropout,
    ACSSLProjector, info_nce, HomogeneousGNN, HeterogeneousRGCN, build_edges,
    OrdinalCORNHead, clinical_cost_matrix, expected_cost_loss, TemperatureScaler,
    MODALITIES, N_MODALITIES, N_TARGETS,
)
from amog_datasets import (  # noqa: E402
    ROIDataset, MultiSequenceDataset, PatientGraphDataset,
    SyntheticMultiSequence, SyntheticPatientGraph, build_target_table,
)
from rsna_data import load_cache, patient_split, CACHE_DIR  # noqa: E402
from amog_perf import (  # noqa: E402
    configure_backend, suggest_batch, loader_kwargs, Amp, maybe_compile,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STAGES = ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"]
GRAPH_STAGES = {"E5", "E6", "E7"}
MULTISEQ_STAGES = {"E1", "E2", "E3", "E4", "E5", "E6", "E7"}
ROUTER_STAGES = {"E2", "E3", "E4", "E5", "E6", "E7"}
DROPOUT_STAGES = {"E3", "E4", "E5", "E6", "E7"}


# --------------------------------------------------------------------------- #
class AMOGNet(nn.Module):
    """Assembles exactly the components the requested rung calls for."""

    def __init__(self, stage: str, backbone="resnet18", dim=256,
                 shuffled=False, ungated=False, seed=0):
        super().__init__()
        self.stage = stage
        self.dim = dim
        self.use_multiseq = stage in MULTISEQ_STAGES
        self.use_router = stage in ROUTER_STAGES
        self.use_graph = stage in GRAPH_STAGES
        self.use_ordinal = stage == "E7"

        n_enc = N_MODALITIES if self.use_multiseq else 1
        self.encoders = nn.ModuleList(
            [SequenceEncoder(backbone, dim) for _ in range(n_enc)])

        if self.use_multiseq and not self.use_router:
            self.fusion = FixedFusion(dim, mode="mean")
        elif self.use_router:
            self.router = DiseaseConditionedRouter(dim)

        if self.use_graph:
            ei, et = build_edges(shuffled=shuffled, seed=seed)
            self.register_buffer("edge_index", ei)
            self.register_buffer("edge_type", et)
            if stage == "E5":
                self.gnn = HomogeneousGNN(dim, dim, layers=2)
            else:
                self.gnn = HeterogeneousRGCN(dim, dim, layers=2, gated=not ungated)
            head_in = self.gnn.out_dim
        else:
            head_in = dim

        if self.use_ordinal:
            self.head = OrdinalCORNHead(head_in, N_CLASSES)
        else:
            self.head = nn.Linear(head_in, N_CLASSES)

        self.projector = ACSSLProjector(dim) if stage == "E4" else None

    def encode(self, imgs, mask):
        """imgs (B, M, 3, H, W) -> (B, M, D), zeroed where a sequence is absent.

        The batch is encoded densely and masked afterwards. Selecting present
        rows first looks cheaper but forces a host synchronisation per modality,
        and 95.3% of targets carry all three sequences anyway, so the skipped
        work is small next to the stalls it costs.
        """
        outs = []
        for m in range(imgs.shape[1]):
            enc = self.encoders[m if len(self.encoders) > 1 else 0]
            x = imgs[:, m]
            if x.is_cuda:
                # rank 4 here, so channels_last is well defined and lets the
                # convolutions reach tensor cores
                x = x.contiguous(memory_format=torch.channels_last)
            outs.append(enc(x))
        feats = torch.stack(outs, dim=1)
        return feats * mask.unsqueeze(-1).to(feats.dtype)

    def forward_target(self, imgs, mask, cond_idx, level_idx):
        feats = self.encode(imgs, mask)
        if self.use_router:
            fused, g = self.router(feats, mask, cond_idx, level_idx)
        elif self.use_multiseq:
            fused, g = self.fusion(feats, mask)
        else:
            fused, g = feats[:, 0], None
        return fused, g

    def forward_graph(self, imgs, mask, evidence):
        """imgs (B, N, M, 3, H, W) -> node logits (B, N, C)."""
        B, N = imgs.shape[:2]
        flat_i = imgs.reshape(B * N, *imgs.shape[2:])
        flat_m = mask.reshape(B * N, N_MODALITIES)
        cond = torch.arange(N, device=imgs.device).remainder(5).repeat(B)
        lvl = torch.arange(N, device=imgs.device).div(5, rounding_mode="floor").repeat(B)

        fused, g = self.forward_target(flat_i, flat_m, cond, lvl)
        nodes = fused.reshape(B, N, -1)

        # nodes without usable image evidence are zeroed so they cannot inject
        # unsupported "ghost" representations into their neighbours
        nodes = nodes * evidence.unsqueeze(-1)
        h = self.gnn(nodes, self.edge_index, self.edge_type)
        return self.head(h), g


# --------------------------------------------------------------------------- #
def make_datasets(ctx, stage, args):
    """Returns (train, val, test, meta) for the requested stage and mode."""
    if ctx.is_smoke:
        crop = 64
        n = ctx.max_samples or 64
        if stage in GRAPH_STAGES:
            mk = lambda k, s: SyntheticPatientGraph(max(k, 4), crop=crop, seed=s)
            return mk(n // 8, 0), mk(n // 16, 1), mk(n // 16, 2), {"crop": crop}
        mk = lambda k, s: SyntheticMultiSequence(max(k, 8), crop=crop, seed=s)
        return mk(n, 0), mk(n // 4, 1), mk(n // 4, 2), {"crop": crop}

    ram = {"auto": "auto", "yes": True, "no": False}[getattr(args, "cache_in_ram", "auto")]
    mm_ann, valid, ann_idx, meta = load_cache("rsna_roi_v1", in_ram=ram)
    ann_idx = ann_idx[valid].reset_index(drop=True)

    mm_x, xseq_idx = None, None
    xp = os.path.join(CACHE_DIR, "rsna_xseq_v1.npy")
    if os.path.exists(xp):
        mm_x, xvalid, xseq_idx, _ = load_cache("rsna_xseq_v1", in_ram=ram)
        xseq_idx = xseq_idx[xvalid].reset_index(drop=True)
    elif stage != "E0":
        print("  NOTE cross-sequence cache absent; targets will carry only their")
        print("       annotated sequence, so fusion and routing have little to do.")

    if stage == "E0":
        tr, va, te = patient_split(ann_idx, seed=args.seed)
        ann_idx = ann_idx.assign(cache_idx=np.arange(len(ann_idx)))
        sel = lambda s: ROIDataset(mm_ann, ann_idx[ann_idx.study_id.isin(s)])
        return sel(tr), sel(va), sel(te), meta

    tt = build_target_table(ann_idx, xseq_idx)
    if args.max_targets:
        tt = tt.sample(n=min(args.max_targets, len(tt)), random_state=args.seed)
    tr, va, te = patient_split(tt, seed=args.seed)

    if stage in GRAPH_STAGES:
        sel = lambda s: PatientGraphDataset(tt[tt.study_id.isin(s)], mm_ann, mm_x)
    else:
        sel = lambda s: MultiSequenceDataset(tt[tt.study_id.isin(s)], mm_ann, mm_x)
    return sel(tr), sel(va), sel(te), {"targets": len(tt), "patients": tt.study_id.nunique()}


# --------------------------------------------------------------------------- #
def run_epoch(model, loader, ctx, stage, args, optimizer=None, cost=None):
    """One pass. optimizer=None means evaluation."""
    train = optimizer is not None
    amp = getattr(args, "_amp", None)
    model.train() if train else model.eval()
    graph = stage in GRAPH_STAGES

    tot_loss, n = 0.0, 0
    preds, targets, probs, entropies, pids = [], [], [], [], []

    for batch in loader:
        if graph:
            imgs, mask, y, lmask, ev, pid = [b.to(ctx.device) for b in batch]
            if stage in DROPOUT_STAGES and train:
                B, N, M = mask.shape
                mask = apply_modality_dropout(
                    mask.reshape(B * N, M), args.p_drop, True).reshape(B, N, M)
            with torch.set_grad_enabled(train), (
                    amp.autocast() if amp else torch.autocast("cpu", enabled=False)):
                logits, g = model.forward_graph(imgs, mask, ev)
                sel = lmask.reshape(-1) > 0
                lg = logits.reshape(-1, logits.size(-1))[sel]
                yy = y.reshape(-1)[sel]
                if lg.numel() == 0:
                    continue
                loss, p = _loss_and_probs(model, lg, yy, cost, args)
                # one patient contributes many nodes; keep them attributable
                batch_pid = pid.unsqueeze(1).expand(-1, logits.size(1)).reshape(-1)[sel]
        else:
            imgs, mask, cond, lvl, yy, batch_pid = [b.to(ctx.device) for b in batch]
            if stage in DROPOUT_STAGES and train:
                mask = apply_modality_dropout(mask, args.p_drop, True)
            with torch.set_grad_enabled(train), (
                    amp.autocast() if amp else torch.autocast("cpu", enabled=False)):
                fused, g = model.forward_target(imgs, mask, cond, lvl)
                lg = model.head(fused)
                loss, p = _loss_and_probs(model, lg, yy, cost, args)

        if train:
            if g is not None and args.balance_weight > 0:
                m2 = mask.reshape(-1, N_MODALITIES) if graph else mask
                loss = loss + args.balance_weight * \
                    DiseaseConditionedRouter.load_balance_loss(g, m2)
            optimizer.zero_grad(set_to_none=True)
            if amp is not None:
                amp.backward(loss)
                amp.step(optimizer)
            else:
                loss.backward()
                optimizer.step()

        bs = yy.size(0)
        tot_loss += float(loss.item()) * bs
        n += bs
        p = p.float()
        preds.append(p.argmax(1).detach().cpu().numpy())
        targets.append(yy.detach().cpu().numpy())
        probs.append(p.detach().cpu().numpy())
        pids.append(batch_pid.detach().cpu().numpy())
        if g is not None:
            m2 = mask.reshape(-1, N_MODALITIES) if graph else mask
            entropies.append(float(DiseaseConditionedRouter.gate_entropy(g, m2)))

    if n == 0:
        raise RuntimeError("no labelled samples in this split")
    yt, yp, pr = (np.concatenate(targets), np.concatenate(preds),
                  np.concatenate(probs))
    m = compute_metrics(yt, yp, pr)
    m["loss"] = tot_loss / n
    m["gate_entropy"] = float(np.mean(entropies)) if entropies else None
    m["_predictions"] = dict(patient_id=np.concatenate(pids),
                             y_true=yt, y_pred=yp, y_prob=pr)
    return m


def _loss_and_probs(model, logits, y, cost, args):
    if model.use_ordinal:
        loss = OrdinalCORNHead.loss(logits, y)
        p = OrdinalCORNHead.to_probs(logits)
        if cost is not None and args.cost_weight > 0:
            loss = loss + args.cost_weight * expected_cost_loss(p, y, cost)
    else:
        loss = F.cross_entropy(logits, y)
        p = torch.softmax(logits, dim=1)
        if cost is not None and args.cost_weight > 0:
            loss = loss + args.cost_weight * expected_cost_loss(p, y, cost)
    return loss, p


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="AMOG-Net stage trainer (E0-E7)")
    add_mode_args(ap)
    ap.add_argument("--stage", choices=STAGES, required=True)
    ap.add_argument("--backbone", type=str, default=None)
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--p_drop", type=float, default=0.2)
    ap.add_argument("--balance_weight", type=float, default=0.01)
    ap.add_argument("--cost_weight", type=float, default=0.0)
    ap.add_argument("--shuffled", action="store_true", help="E6 control")
    ap.add_argument("--ungated", action="store_true", help="E6 ablation")
    ap.add_argument("--max_targets", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--amp", dest="amp", action="store_true", default=True,
                    help="bf16 autocast (default on for CUDA)")
    ap.add_argument("--no_amp", dest="amp", action="store_false")
    ap.add_argument("--channels_last", action="store_true", default=True)
    ap.add_argument("--compile", action="store_true",
                    help="torch.compile the model (slow first step, faster after)")
    ap.add_argument("--cache_in_ram", choices=["auto", "yes", "no"], default="auto")
    ap.add_argument("--deterministic", action="store_true",
                    help="disable TF32/cudnn autotune for a reproducibility check")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    ctx = resolve_mode(args)
    gpu = configure_backend(deterministic=args.deterministic)
    stage = args.stage
    backbone = args.backbone or ("smallcnn" if ctx.is_smoke else "resnet18")

    tag = stage + ("_shuffled" if args.shuffled else "") + ("_ungated" if args.ungated else "")
    print("Stage {}  backbone {}  seed {}".format(tag, backbone, args.seed))
    if args.shuffled:
        print("  CONTROL: edges permuted, node and edge counts preserved.")

    train_ds, val_ds, test_ds, meta = make_datasets(ctx, stage, args)
    print("  data: train {}  val {}  test {}".format(
        len(train_ds), len(val_ds), len(test_ds)))
    if "targets" in meta:
        print("        {:,} targets over {:,} patients".format(
            meta["targets"], meta["patients"]))

    is_graph = stage in GRAPH_STAGES
    if ctx.is_smoke:
        bs = max(1, ctx.batch_size // 16) if is_graph else ctx.batch_size
    else:
        bs = suggest_batch(is_graph, gpu["vram_gb"], args.batch_size)
    # Smoke datasets are a handful of in-memory tensors; spawning a dozen
    # persistent workers for them costs far more than it saves.
    lkw = loader_kwargs(0 if ctx.is_smoke else args.workers,
                        cuda=str(ctx.device).startswith("cuda"))
    print("  batch {}  ({} rung, {:.1f} GB VRAM)  workers {}".format(
        bs, "graph" if is_graph else "target", gpu["vram_gb"], lkw["num_workers"]))
    dl = lambda d, s: DataLoader(d, batch_size=bs, shuffle=s, **lkw)
    train_loader, val_loader, test_loader = dl(train_ds, True), dl(val_ds, False), dl(test_ds, False)

    model = AMOGNet(stage, backbone, args.dim, args.shuffled, args.ungated, args.seed).to(ctx.device)
    if args.channels_last and str(ctx.device).startswith("cuda"):
        model = model.to(memory_format=torch.channels_last)
    n_params = sum(p.numel() for p in model.parameters())
    print("  model: {:.2f}M parameters (counted)".format(n_params / 1e6))

    amp = Amp(args.amp, str(ctx.device))
    print("  precision: {}".format(amp.label()))
    model = maybe_compile(model, args.compile)
    args._amp = amp
    args._channels_last = args.channels_last

    optimizer = torch.optim.AdamW(model.parameters(), lr=ctx.lr)
    cost = clinical_cost_matrix(device=ctx.device) if args.cost_weight > 0 else None

    hist = os.path.join(ctx.log_dir, "{}_{}_seed{}_history.csv".format(tag, ctx.mode, args.seed))
    best, best_path = -1.0, os.path.join(
        ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(tag, ctx.mode, args.seed))

    print("\n[STAGE 1] training")
    with open(hist, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["mode", "stage", "seed", "epoch", "train_loss", "val_loss",
                    "val_acc", "val_macro_f1", "val_qwk", "val_ece",
                    "gate_entropy", "seconds"])
        for ep in range(1, ctx.epochs + 1):
            t0 = time.time()
            tm = run_epoch(model, train_loader, ctx, stage, args, optimizer, cost)
            tm.pop("_predictions", None)
            vm = run_epoch(model, val_loader, ctx, stage, args, None, cost)
            vm.pop("_predictions", None)
            secs = time.time() - t0
            w.writerow([ctx.mode, stage, args.seed, ep, round(tm["loss"], 6),
                        round(vm["loss"], 6), round(vm["accuracy"], 6),
                        round(vm["macro_f1"], 6), round(vm["qwk"], 6),
                        round(vm["ece"], 6),
                        round(vm["gate_entropy"], 4) if vm["gate_entropy"] else "",
                        round(secs, 2)])
            fh.flush()
            ge = "  gate-H {:.3f}".format(vm["gate_entropy"]) if vm["gate_entropy"] else ""
            print("  epoch {:>3}/{}  train {:.4f}  val {:.4f}  acc {:.3f}  F1 {:.3f}"
                  "  QWK {:.3f}{}  [{:.1f}s]".format(
                      ep, ctx.epochs, tm["loss"], vm["loss"], vm["accuracy"],
                      vm["macro_f1"], vm["qwk"], ge, secs))
            if vm["macro_f1"] > best:
                best = vm["macro_f1"]
                torch.save({"model_state_dict": model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(),
                            "epoch": ep, "val_macro_f1": best, "stage": stage,
                            "backbone": backbone, "provenance": ctx.stamp()}, best_path)

    rl = torch.load(best_path, map_location="cpu", weights_only=False)
    assert rl["model_state_dict"], "checkpoint did not round-trip"

    print("\n[STAGE 2] held-out test")
    tmet = run_epoch(model, test_loader, ctx, stage, args, None, cost)
    tmet.update({"stage": stage, "tag": tag, "backbone": backbone,
                 "n_parameters": int(n_params), "seed": args.seed,
                 "shuffled_control": bool(args.shuffled), "ungated": bool(args.ungated)})
    print("  loss {:.4f}  acc {:.4f}  macro-F1 {:.4f}  QWK {:.4f}  ECE {:.4f}".format(
        tmet["loss"], tmet["accuracy"], tmet["macro_f1"], tmet["qwk"], tmet["ece"]))
    print("  grade distance  d0 {:.3f}  d1 {:.3f}  d>=2 {:.3f}".format(
        tmet["grade_distance"]["d0"], tmet["grade_distance"]["d1"],
        tmet["grade_distance"]["d2_or_more"]))
    if tmet["severe_recall"] is not None:
        print("  severe recall {:.3f}   Severe->Normal/Mild {:.3f}".format(
            tmet["severe_recall"], tmet["severe_to_normal_rate"]))

    preds = tmet.pop("_predictions")
    npz = os.path.join(ctx.report_dir,
                       "{}_{}_seed{}_predictions.npz".format(tag, ctx.mode, args.seed))
    np.savez_compressed(npz, **preds)

    out = ctx.write_json("{}_{}_seed{}_test.json".format(tag, ctx.mode, args.seed), tmet)
    print("  -> {}".format(os.path.relpath(out, PROJECT_ROOT)))
    print("  -> {}  ({:,} predictions over {:,} patients)".format(
        os.path.relpath(npz, PROJECT_ROOT), len(preds["y_true"]),
        len(np.unique(preds["patient_id"]))))

    if ctx.is_smoke:
        print("\n  SMOKE PASS for {} -- machinery runs. Not a result.".format(tag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
