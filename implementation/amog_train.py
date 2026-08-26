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
from rsna_data import (  # noqa: E402
    load_cache, load_frozen_split, SPLIT_FILE, SPLIT_SEED, CACHE_DIR,
    ANN_CACHE, XSEQ_CACHE,
)
from amog_acssl import ACSSL_CKPT_NAME  # noqa: E402
from amog_augment import MRIAugment, describe  # noqa: E402
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
                 shuffled=False, ungated=False, seed=0, pretrained=True):
        super().__init__()
        self.stage = stage
        self.dim = dim
        self._backbone_name = backbone
        self.use_multiseq = stage in MULTISEQ_STAGES
        self.use_router = stage in ROUTER_STAGES
        self.use_graph = stage in GRAPH_STAGES
        self.use_ordinal = stage == "E7"

        n_enc = N_MODALITIES if self.use_multiseq else 1
        # ImageNet initialisation. Chapter 3 sec:method-backbone-control treats
        # the backbone as a controlled feature extractor held fixed across the
        # ladder; training 24M parameters from scratch on 34k crops is a
        # different experiment, and a much weaker one.
        self.encoders = nn.ModuleList(
            [SequenceEncoder(backbone, dim, pretrained=pretrained)
             for _ in range(n_enc)])

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

        # No projector here. Chapter 3 sec:method-ssl-projection: "The projection
        # head is discarded or decoupled after the pretraining stage." It lived
        # in this model until now, received no gradient, and inflated the
        # reported parameter count of E4 while contributing nothing -- which is
        # what made E4 indistinguishable from E3.
        self.acssl_loaded_from = None

    def load_acssl(self, path: str) -> dict:
        """Transfer ACSSL-pretrained sequence encoders into this model.

        This is what makes E4 differ from E3. Chapter 3 sec:method-training-phases
        phase 3: encoders are fine-tuned from the anatomical pretraining, so the
        weights must actually arrive before supervised training starts.
        """
        ck = torch.load(path, map_location="cpu", weights_only=False)

        # A backbone or width mismatch would surface as a raw size-mismatch
        # stack trace from load_state_dict, or -- worse, with strict=False --
        # as a partial load that silently leaves most of the encoder random.
        # Both are checked here so the message names the actual problem.
        want_bb, want_dim = ck.get("backbone"), ck.get("dim")
        have_bb = getattr(self, "_backbone_name", None)
        if want_bb is not None and have_bb is not None and want_bb != have_bb:
            raise RuntimeError(
                "ACSSL checkpoint was pretrained with backbone '{}' but this run "
                "uses '{}'. Pretrain with --backbone {}, or train with "
                "--backbone {}.".format(want_bb, have_bb, have_bb, want_bb))
        if want_dim is not None and want_dim != self.dim:
            raise RuntimeError(
                "ACSSL checkpoint has feature dim {} but this run uses {}."
                .format(want_dim, self.dim))

        sd = ck["encoders_state_dict"]
        before = {k: v.detach().clone() for k, v in self.encoders.state_dict().items()}
        missing, unexpected = self.encoders.load_state_dict(sd, strict=False)
        after = self.encoders.state_dict()

        changed = sum(1 for k in before if not torch.equal(before[k], after[k]))
        if changed == 0:
            raise RuntimeError(
                "loading {} changed no encoder weight. E4 would be identical to "
                "E3 and the ACSSL comparison would measure nothing."
                .format(os.path.basename(path)))
        self.acssl_loaded_from = path
        return {"tensors_changed": changed,
                "tensors_total": len(before),
                "missing_keys": len(missing),
                "unexpected_keys": len(unexpected),
                "pretrain_val_infonce": ck.get("best_val_infonce"),
                "pretrain_chance_infonce": ck.get("chance_infonce"),
                "pretrain_mode": ck.get("mode")}

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

    def forward_target(self, imgs, mask, cond_idx, level_idx, ann_slot=None):
        feats = self.encode(imgs, mask)
        if self.use_router:
            fused, g = self.router(feats, mask, cond_idx, level_idx)
        elif self.use_multiseq:
            fused, g = self.fusion(feats, mask)
        else:
            # E0 grades a target from ITS annotated ROI. Chapter 3 sec:method-e0:
            # "Each target is graded from its anatomically localised input."
            # Taking slot 0 unconditionally fed 59.5% of targets a sagittal T1
            # crop when the radiologist had marked sagittal T2 or axial T2.
            if ann_slot is None:
                fused = feats[:, 0]
            else:
                fused = feats[torch.arange(feats.size(0), device=feats.device),
                              ann_slot.long()]
            g = None
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

        # Nodes without usable image evidence are zeroed so they cannot inject
        # unsupported "ghost" representations into their neighbours. The mask is
        # also passed INTO the GNN and re-applied after every layer: each layer
        # ends in a LayerNorm, and LayerNorm(0) = beta, so masking only here
        # would let an evidence-free node re-acquire a state at layer 1 and
        # broadcast it thereafter.
        nodes = nodes * evidence.unsqueeze(-1)
        h = self.gnn(nodes, self.edge_index, self.edge_type, evidence=evidence)
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
    mm_ann, valid, ann_idx, meta = load_cache(ANN_CACHE, in_ram=ram)
    ann_idx = ann_idx[valid].reset_index(drop=True)

    mm_x, xseq_idx = None, None
    xp = os.path.join(CACHE_DIR, XSEQ_CACHE + ".npy")
    if os.path.exists(xp):
        mm_x, xvalid, xseq_idx, _ = load_cache(XSEQ_CACHE, in_ram=ram)
        xseq_idx = xseq_idx[xvalid].reset_index(drop=True)
    elif stage != "E0":
        print("  NOTE cross-sequence cache absent; targets will carry only their")
        print("       annotated sequence, so fusion and routing have little to do.")

    xseq_for_stage = None if stage == "E0" else xseq_idx
    tt = build_target_table(ann_idx, xseq_for_stage)
    if args.max_targets:
        # Subsample with the SPLIT seed, not the training seed. A partial run
        # must look at the same subset of the cohort whichever seed is training,
        # or the seeds are not repeat measurements of one experiment.
        tt = tt.sample(n=min(args.max_targets, len(tt)), random_state=SPLIT_SEED)

    # Chapter 3 sec:method-patient-split: one frozen, version-controlled split,
    # consumed as a fixed list. Independent of args.seed by construction, so the
    # three seeds of a campaign are three trainings on ONE cohort partition.
    tr, va, te = load_frozen_split(tt)
    print("  split: {} train / {} val / {} test patients  (frozen: {})".format(
        len(tr), len(va), len(te), os.path.relpath(SPLIT_FILE, PROJECT_ROOT)))

    if getattr(args, "shuffle_labels", False):
        # NEGATIVE CONTROL. Permute labels WITHIN each partition, so the class
        # distribution is untouched and only the image-to-label correspondence
        # is destroyed. A pipeline that leaks information -- through the split,
        # the cache index, or the target table -- still scores well here. A
        # sound one collapses to QWK ~0. Chapter 3 sec:method-patient-split
        # motivates this: leakage of exactly this kind is among the commonest
        # causes of irreproducible results in applied machine learning.
        rng = np.random.default_rng(args.seed + 9973)
        tt = tt.copy()
        for part in (tr, va, te):
            m = tt.study_id.isin(part).values
            lab = tt.loc[m, "label"].values.copy()
            rng.shuffle(lab)
            tt.loc[m, "label"] = lab
        print("  *** NEGATIVE CONTROL: labels permuted within each partition ***")
        print("  *** a sound pipeline must now score QWK ~0.00              ***")

    # Chapter 3 sec:method-augmentation: train only. Validation and test see the
    # images unmodified, or model selection and the held-out score would be
    # measured on a distribution the deployed model never encounters.
    aug = None if getattr(args, "no_augment", False) else MRIAugment(
        intensity=args.aug_intensity, gamma=args.aug_gamma, noise=args.aug_noise,
        bias=args.aug_bias, translate=args.aug_translate,
        rotate_deg=args.aug_rotate, p=args.aug_prob)

    Cls = PatientGraphDataset if stage in GRAPH_STAGES else MultiSequenceDataset
    sel = lambda s, a=None: Cls(tt[tt.study_id.isin(s)], mm_ann, mm_x, augment=a)
    return (sel(tr, aug), sel(va), sel(te),
            {"targets": len(tt), "patients": tt.study_id.nunique(),
             "augmentation": describe(aug) if aug else None})


# --------------------------------------------------------------------------- #
def run_epoch(model, loader, ctx, stage, args, optimizer=None, cost=None):
    """One pass. optimizer=None means evaluation."""
    train = optimizer is not None
    amp = getattr(args, "_amp", None)
    model.train() if train else model.eval()
    graph = stage in GRAPH_STAGES

    tot_loss, n = 0.0, 0
    preds, targets, probs, entropies, pids = [], [], [], [], []
    logits_all = []

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
            imgs, mask, cond, lvl, yy, batch_pid, ann_slot = [
                b.to(ctx.device) for b in batch]
            if stage in DROPOUT_STAGES and train:
                mask = apply_modality_dropout(mask, args.p_drop, True)
            with torch.set_grad_enabled(train), (
                    amp.autocast() if amp else torch.autocast("cpu", enabled=False)):
                fused, g = model.forward_target(imgs, mask, cond, lvl, ann_slot)
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
        logits_all.append(lg.detach().float().cpu().numpy())
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
                             y_true=yt, y_pred=yp, y_prob=pr,
                             logits=np.concatenate(logits_all))
    return m


def probs_from_logits(model, logits, temperature: float = 1.0):
    """Class probabilities under a calibration temperature.

    Applied to the LOGITS, before the ordinal head's cumulative transform, so a
    single scalar has the same meaning for E7 as for the categorical rungs.
    """
    z = logits / max(temperature, 1e-6)
    if model.use_ordinal:
        return OrdinalCORNHead.to_probs(z)
    return torch.softmax(z, dim=1)


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
    # Chapter 3 sec:method-optimiser: warm-up + cosine decay, or a plateau
    # scheduler. The chapter requires the thesis to REPORT the schedule, so it
    # is an explicit flag and is written into the run's result JSON.
    #
    # EARLY STOPPING IS DELIBERATELY ABSENT. Every rung runs the full configured
    # schedule so that the training budget is identical across the ladder. With
    # early stopping the budget becomes data-dependent -- E6 might run 50 epochs
    # while E5 stops at 20 -- and part of every ladder comparison would then be
    # training length rather than architecture. Cosine annealing also never
    # completes when a run is cut short, so different rungs would receive
    # different amounts of decay. Model selection still happens: the best
    # validation macro-F1 checkpoint is tracked and restored before the held-out
    # test. Selection and stopping are separate mechanisms and only the latter
    # is removed. Do not reintroduce a patience counter without also deciding
    # how the ladder stays budget-comparable.
    ap.add_argument("--scheduler", choices=["cosine", "plateau", "none"],
                    default="cosine",
                    help="LR schedule; 'none' only for a deliberate control")
    ap.add_argument("--warmup_frac", type=float, default=0.05,
                    help="fraction of total epochs spent warming up from lr/100")
    ap.add_argument("--plateau_patience", type=int, default=5,
                    help="epochs without val macro-F1 improvement before "
                         "ReduceLROnPlateau lowers the LR. This decays the "
                         "learning rate; it never stops training.")
    ap.add_argument("--calibrate", dest="calibrate", action="store_true", default=True,
                    help="fit temperature scaling on the validation split after "
                         "model selection (Chapter 3 phase 4)")
    ap.add_argument("--no_calibrate", dest="calibrate", action="store_false")
    ap.add_argument("--acssl_ckpt", type=str, default=None,
                    help="ACSSL-pretrained encoders for E4 (default: the run "
                         "mode's checkpoint dir). Produced by amog_acssl.py.")
    ap.add_argument("--allow_untrained_e4", action="store_true",
                    help="run E4 WITHOUT the ACSSL weights. Not a valid E4: the "
                         "result is E3 under a different name and must not be "
                         "reported as anatomical self-supervision.")
    ap.add_argument("--pretrained", dest="pretrained", action="store_true", default=True,
                    help="ImageNet-initialised backbones (default)")
    ap.add_argument("--from_scratch", dest="pretrained", action="store_false",
                    help="random initialisation; a separate experiment, not the ladder")
    ap.add_argument("--no_augment", action="store_true",
                    help="disable training augmentation; a deliberate control, "
                         "not the default")
    ap.add_argument("--aug_intensity", type=float, default=0.15)
    ap.add_argument("--aug_gamma", type=float, default=0.20)
    ap.add_argument("--aug_noise", type=float, default=0.02)
    ap.add_argument("--aug_bias", type=float, default=0.15)
    ap.add_argument("--aug_translate", type=float, default=0.05)
    ap.add_argument("--aug_rotate", type=float, default=7.0)
    ap.add_argument("--aug_prob", type=float, default=0.8)
    ap.add_argument("--shuffle_labels", action="store_true",
                    help="NEGATIVE CONTROL: permute labels inside each partition. "
                         "A sound pipeline collapses to QWK ~0; anything else "
                         "means information is leaking.")
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

    tag = (stage + ("_shuffled" if args.shuffled else "")
           + ("_ungated" if args.ungated else "")
           + ("_LABELSHUF" if args.shuffle_labels else ""))
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

    model = AMOGNet(stage, backbone, args.dim, args.shuffled, args.ungated,
                    args.seed, pretrained=args.pretrained).to(ctx.device)
    if args.channels_last and str(ctx.device).startswith("cuda"):
        model = model.to(memory_format=torch.channels_last)
    n_params = sum(p.numel() for p in model.parameters())
    print("  model: {:.2f}M parameters (counted)".format(n_params / 1e6))

    # E4 IS the ACSSL transfer. Without the pretrained encoders it is E3 with a
    # different label, which is precisely the defect this wiring exists to fix,
    # so refuse rather than run something that will be reported as CC I.
    acssl_info = None
    if stage == "E4":
        ck = args.acssl_ckpt or os.path.join(ctx.checkpoint_dir, ACSSL_CKPT_NAME)
        if os.path.exists(ck):
            acssl_info = model.load_acssl(ck)
            print("  ACSSL: loaded {} of {} encoder tensors from {}".format(
                acssl_info["tensors_changed"], acssl_info["tensors_total"],
                os.path.relpath(ck, PROJECT_ROOT)))
            vi = acssl_info.get("pretrain_val_infonce")
            ci = acssl_info.get("pretrain_chance_infonce")
            if vi is not None and ci is not None:
                print("         pretrain val InfoNCE {:.4f} vs chance {:.4f}{}".format(
                    vi, ci, "  [!] AT OR ABOVE CHANCE" if vi >= ci else ""))
            if acssl_info.get("pretrain_mode") != ctx.mode:
                print("         [!] pretrained in '{}' mode but training in '{}'"
                      .format(acssl_info.get("pretrain_mode"), ctx.mode))
        elif args.allow_untrained_e4:
            print("  ACSSL: [!] NO pretrained encoders. This run is E3 wearing "
                  "E4's name and must not be reported as CC I.")
        else:
            print("")
            print("[FAIL] E4 needs ACSSL-pretrained encoders and none were found at")
            print("       {}".format(ck))
            print("")
            print("       E4 minus the pretraining is exactly E3, so running it")
            print("       would produce a CC I number that measures nothing.")
            print("       Pretrain first:")
            print("         python implementation/amog_acssl.py --mode {}".format(ctx.mode))
            print("       or pass --allow_untrained_e4 to run it as a labelled "
                  "control.")
            return 2

    amp = Amp(args.amp, str(ctx.device))
    print("  precision: {}".format(amp.label()))
    model = maybe_compile(model, args.compile)
    args._amp = amp
    args._channels_last = args.channels_last

    optimizer = torch.optim.AdamW(model.parameters(), lr=ctx.lr)
    cost = clinical_cost_matrix(device=ctx.device) if args.cost_weight > 0 else None

    # Chapter 3 sec:method-optimiser. Stepped once per epoch, so the schedule is
    # independent of dataset size and identical across every rung of the ladder
    # -- a schedule that varied with the loader length would make E5-E7 (graph
    # rungs, far fewer batches) decay on a different curve from E0-E4 and
    # confound the comparison with an optimisation difference.
    warmup_epochs = max(0, int(round(args.warmup_frac * ctx.epochs)))
    if args.scheduler == "cosine":
        cosine = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max(1, ctx.epochs - warmup_epochs))
        if warmup_epochs:
            scheduler = torch.optim.lr_scheduler.SequentialLR(
                optimizer,
                schedulers=[torch.optim.lr_scheduler.LinearLR(
                    optimizer, start_factor=0.01, total_iters=warmup_epochs), cosine],
                milestones=[warmup_epochs])
        else:
            scheduler = cosine
    elif args.scheduler == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=args.plateau_patience)
    else:
        scheduler = None
    print("  schedule: {}{}  |  {} epochs, no early stopping".format(
        args.scheduler,
        " (warmup {} ep)".format(warmup_epochs) if warmup_epochs and
        args.scheduler == "cosine" else "",
        ctx.epochs))

    hist = os.path.join(ctx.log_dir, "{}_{}_seed{}_history.csv".format(tag, ctx.mode, args.seed))
    best, best_path = -1.0, os.path.join(
        ctx.checkpoint_dir, "{}_{}_seed{}_best.pt".format(tag, ctx.mode, args.seed))

    print("\n[STAGE 1] training")
    with open(hist, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["mode", "stage", "seed", "epoch", "lr", "train_loss", "val_loss",
                    "val_acc", "val_macro_f1", "val_qwk", "val_ece",
                    "gate_entropy", "seconds"])
        best_epoch = 0
        for ep in range(1, ctx.epochs + 1):
            t0 = time.time()
            lr_now = optimizer.param_groups[0]["lr"]
            tm = run_epoch(model, train_loader, ctx, stage, args, optimizer, cost)
            tm.pop("_predictions", None)
            vm = run_epoch(model, val_loader, ctx, stage, args, None, cost)
            vm.pop("_predictions", None)
            secs = time.time() - t0
            w.writerow([ctx.mode, stage, args.seed, ep, "{:.3e}".format(lr_now),
                        round(tm["loss"], 6),
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
            # Model selection. This is NOT early stopping: training always runs
            # the full schedule, and this only records which epoch to test.
            if vm["macro_f1"] > best:
                best = vm["macro_f1"]
                best_epoch = ep
                torch.save({"model_state_dict": model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(),
                            "epoch": ep, "val_macro_f1": best, "stage": stage,
                            "backbone": backbone, "provenance": ctx.stamp()}, best_path)

            if scheduler is not None:
                # ReduceLROnPlateau is driven by the metric; the others are not.
                if args.scheduler == "plateau":
                    scheduler.step(vm["macro_f1"])
                else:
                    scheduler.step()

    # Restore the selected weights. Chapter 3 sec:method-model-selection makes
    # validation the basis of selection, so the held-out test must run on the
    # checkpoint that selection chose -- not on whatever the last epoch left in
    # memory. Loading the file and asserting it is non-empty is not restoring it.
    rl = torch.load(best_path, map_location="cpu", weights_only=False)
    assert rl["model_state_dict"], "checkpoint did not round-trip"
    model.load_state_dict(rl["model_state_dict"])
    print("  restored epoch {} (val macro-F1 {:.4f}) for the held-out test".format(
        rl["epoch"], rl["val_macro_f1"]))

    # Chapter 3 sec:method-training-phases phase 4 and sec:method-calibration:
    # "Temperature/uncertainty parameters are fitted on validation data AFTER
    # model selection." Fitted here, on the restored checkpoint, using the
    # validation split only -- fitting on test would be selecting on test.
    calib = None
    if args.calibrate:
        vres = run_epoch(model, val_loader, ctx, stage, args, None, cost)
        vlog = torch.from_numpy(vres["_predictions"]["logits"])
        vy = torch.from_numpy(vres["_predictions"]["y_true"]).long()
        scaler = TemperatureScaler()
        # head-aware: E7 emits cumulative logits, the other rungs emit class
        # logits, and one scalar must mean the same thing for both
        temperature = scaler.fit_probs(
            vlog, vy, lambda z: OrdinalCORNHead.to_probs(z) if model.use_ordinal
            else torch.softmax(z, dim=1))
        v_before = compute_metrics(
            vy.numpy(),
            probs_from_logits(model, vlog).argmax(1).numpy(),
            probs_from_logits(model, vlog).numpy())["ece"]
        v_after = compute_metrics(
            vy.numpy(),
            probs_from_logits(model, vlog, temperature).argmax(1).numpy(),
            probs_from_logits(model, vlog, temperature).numpy())["ece"]
        calib = {"temperature": float(temperature),
                 "val_ece_before": float(v_before),
                 "val_ece_after": float(v_after),
                 "fitted_on": "validation"}
        print("  calibration: T = {:.4f}   val ECE {:.4f} -> {:.4f}".format(
            temperature, v_before, v_after))
        if v_after > v_before + 1e-6:
            print("               [!] calibration did not improve validation ECE")

    print("\n[STAGE 2] held-out test")
    tmet = run_epoch(model, test_loader, ctx, stage, args, None, cost)

    if calib is not None:
        # Report uncalibrated AND calibrated on the test set. Only the
        # temperature came from validation; the test numbers are still measured.
        tl = torch.from_numpy(tmet["_predictions"]["logits"])
        ty = tmet["_predictions"]["y_true"]
        pc = probs_from_logits(model, tl, calib["temperature"]).numpy()
        cm = compute_metrics(ty, pc.argmax(1), pc)
        tmet["ece_uncalibrated"] = tmet["ece"]
        tmet["calibrated"] = {k: cm[k] for k in
                              ("accuracy", "macro_f1", "qwk", "ece", "brier")
                              if k in cm}
        print("  test ECE {:.4f} uncalibrated -> {:.4f} calibrated (T = {:.4f})".format(
            tmet["ece"], cm["ece"], calib["temperature"]))
    tmet.update({"stage": stage, "tag": tag, "backbone": backbone,
                 "n_parameters": int(n_params), "seed": args.seed,
                 "shuffled_control": bool(args.shuffled), "ungated": bool(args.ungated),
                 # Chapter 3 sec:method-optimiser requires the schedule and the
                 # selection point to be reported. epochs_run is recorded even
                 # though it always equals epochs_configured, so that a future
                 # run which does stop early cannot be mistaken for one that did
                 # not.
                 # Fingerprint of everything that changes what a number MEANS.
                 # run_ladder compares this before reusing a completed run, so a
                 # result produced under a different configuration can never be
                 # silently mixed into a campaign.
                 "run_config": {
                     "stage": stage, "backbone": backbone, "dim": args.dim,
                     "epochs": ctx.epochs, "mode": ctx.mode,
                     "augmented": bool(meta.get("augmentation")),
                     "pretrained_backbone": bool(args.pretrained),
                     "cache": ANN_CACHE,
                     "shuffled": bool(args.shuffled),
                     "ungated": bool(args.ungated),
                     "cost_weight": args.cost_weight,
                     "acssl": bool(acssl_info),
                 },
                 "augmentation": meta.get("augmentation"),
                 "calibration": calib,
                 "acssl": acssl_info,
                 "acssl_pretrained": acssl_info is not None,
                 "scheduler": args.scheduler,
                 "warmup_epochs": warmup_epochs,
                 "early_stopping": False,
                 "epochs_configured": ctx.epochs,
                 "epochs_run": ctx.epochs,
                 "selected_epoch": int(rl["epoch"]),
                 "selected_val_macro_f1": float(rl["val_macro_f1"])})
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
