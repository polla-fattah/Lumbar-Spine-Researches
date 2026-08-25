#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ACSSL: anatomically aligned cross-sequence self-supervised pretraining (E4).

Chapter 3 sec:method-positive-pairs defines the positive relation as

    (p, l, m_a) ~ (p, l, m_b),   m_a != m_b

-- the same patient at the same lumbar level, seen in two different sequences.
The correspondence comes from the DICOM reconstruction, not from image
appearance, and that anatomical pairing is the contribution. The particular
contrastive loss is not: sec:method-ssl-objective says so explicitly.

WHY THIS IS A SEPARATE STAGE
    Pretraining produces encoder weights that every downstream seed reuses. Run
    once, transfer many times. Running it inside each E4 training would make the
    three seeds of a campaign three different pretrainings, so the E4-vs-E3
    comparison would confound the representation with the seed.

WHAT PRETRAINING MUST NOT SEE
    sec:method-ssl-leakage: "anatomical self-supervision uses only the
    development partition". A model pretrained on held-out patients has already
    seen their anatomy even without their labels. This module therefore loads
    the frozen split and trains on the TRAIN partition only, and records the
    split digest it used so the claim is checkable afterwards.

MODALITY DROPOUT IS OFF HERE
    sec:method-training-phases, phase 2: dropout is disabled during pretraining
    "so that the pretraining objective is not changed by stochastic removal of
    its own positive pair". Removing a sequence here would delete the very pair
    the loss is defined on.

USAGE
    python implementation/amog_acssl.py --mode real --epochs 20
    python implementation/amog_acssl.py --mode smoke          # plumbing only
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
from torch.utils.data import DataLoader, Dataset

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import add_mode_args, resolve_mode, PROJECT_ROOT  # noqa: E402
from amog_models import (  # noqa: E402
    SequenceEncoder, ACSSLProjector, info_nce, MODALITIES, N_MODALITIES,
)
from amog_datasets import build_target_table  # noqa: E402
from rsna_data import (  # noqa: E402
    load_cache, load_frozen_split, SPLIT_FILE, SPLIT_SEED, CACHE_DIR, _split_digest,
    ANN_CACHE, XSEQ_CACHE,
)
from amog_perf import configure_backend, loader_kwargs, Amp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ACSSL_CKPT_NAME = "acssl_encoders.pt"


# --------------------------------------------------------------------------- #
class CrossSequencePairDataset(Dataset):
    """One item = one (patient, level) seen through two different sequences.

    Rows are collapsed to (study_id, level_idx) first. A target table carries
    one row per (patient, level, condition), and the five conditions at a level
    share the same images -- keeping them all would repeat the identical pair
    five times and let a single anatomical site dominate the batch.
    """

    def __init__(self, targets: pd.DataFrame, mm_ann, mm_xseq=None,
                 crop: int = 128, seed: int = 0):
        self.mm_ann = mm_ann
        self.mm_xseq = mm_xseq
        self.crop = crop
        self.rng = np.random.default_rng(seed)

        sites = targets.drop_duplicates(subset=["study_id", "level_idx"])
        items = []
        for r in sites.itertuples(index=False):
            avail = []
            for m_i, m in enumerate(MODALITIES):
                ann = getattr(r, "ann_{}".format(m), -1)
                if ann is not None and ann >= 0:
                    avail.append((m_i, int(ann), "ann"))
                    continue
                xs = getattr(r, "xseq_{}".format(m), -1)
                if mm_xseq is not None and xs is not None and xs >= 0:
                    avail.append((m_i, int(xs), "xseq"))
            # A site with one sequence has no cross-sequence positive and is
            # dropped rather than paired with itself, which would collapse the
            # objective into an augmentation-invariance task.
            if len(avail) >= 2:
                items.append((int(r.study_id), int(r.level_idx), avail))
        self.items = items

    def __len__(self):
        return len(self.items)

    def n_sites_by_modality_count(self):
        from collections import Counter
        return Counter(len(a) for _, _, a in self.items)

    def _load(self, src, idx):
        mm = self.mm_ann if src == "ann" else self.mm_xseq
        return torch.from_numpy(np.asarray(mm[idx], dtype=np.float32))

    def __getitem__(self, i):
        _sid, _lvl, avail = self.items[i]
        a, b = self.rng.choice(len(avail), size=2, replace=False)
        m_a, i_a, s_a = avail[a]
        m_b, i_b, s_b = avail[b]
        return (self._load(s_a, i_a), torch.tensor(m_a),
                self._load(s_b, i_b), torch.tensor(m_b))


class SyntheticPairs(Dataset):
    """Smoke plumbing. Two views that genuinely correspond, so the loss can fall."""

    def __init__(self, n=64, crop=64, seed=0):
        g = torch.Generator().manual_seed(seed)
        self.base = torch.randn(n, 3, crop, crop, generator=g)
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        a = self.base[i] + 0.1 * torch.randn_like(self.base[i])
        b = self.base[i] + 0.1 * torch.randn_like(self.base[i])
        return a, torch.tensor(i % N_MODALITIES), b, torch.tensor((i + 1) % N_MODALITIES)


# --------------------------------------------------------------------------- #
class ACSSLModel(nn.Module):
    """Per-sequence encoders and per-sequence projection heads.

    Chapter 3 eq:ssl-projection writes the head as P_m -- one per modality, not
    one shared head. A shared head would have to map three different contrast
    distributions into the same space by itself, which is the encoder's job.
    """

    def __init__(self, backbone="resnet18", dim=256, proj_out=128):
        super().__init__()
        self.encoders = nn.ModuleList(
            [SequenceEncoder(backbone, dim) for _ in range(N_MODALITIES)])
        self.projectors = nn.ModuleList(
            [ACSSLProjector(dim, dim, proj_out) for _ in range(N_MODALITIES)])

    def embed(self, x, mod_idx):
        """Encode a batch whose rows may come from different sequences."""
        feats = x.new_zeros(x.size(0), self.encoders[0].out_dim)
        zs = None
        for m in range(N_MODALITIES):
            sel = (mod_idx == m)
            if not bool(sel.any()):
                continue
            f = self.encoders[m](x[sel])
            z = self.projectors[m](f)
            if zs is None:
                # allocate from z, not f: F.normalize upcasts out of bf16 under
                # autocast, so the two can differ in dtype
                zs = z.new_zeros(x.size(0), z.size(-1))
            feats[sel] = f.to(feats.dtype)
            zs[sel] = z.to(zs.dtype)
        return feats, zs


# --------------------------------------------------------------------------- #
def build_datasets(ctx, args):
    if ctx.is_smoke:
        n = ctx.max_samples or 64
        return SyntheticPairs(n, 64, 0), SyntheticPairs(max(n // 4, 8), 64, 1), {}

    ram = {"auto": "auto", "yes": True, "no": False}[args.cache_in_ram]
    mm_ann, valid, ann_idx, _ = load_cache(ANN_CACHE, in_ram=ram)
    ann_idx = ann_idx[valid].reset_index(drop=True)

    mm_x, xseq_idx = None, None
    xp = os.path.join(CACHE_DIR, XSEQ_CACHE + ".npy")
    if os.path.exists(xp):
        mm_x, xvalid, xseq_idx, _ = load_cache(XSEQ_CACHE, in_ram=ram)
        xseq_idx = xseq_idx[xvalid].reset_index(drop=True)

    tt = build_target_table(ann_idx, xseq_idx)

    # sec:method-ssl-leakage -- development partition only.
    tr, va, te = load_frozen_split(tt)
    held_out = va | te
    tt_train = tt[tt.study_id.isin(tr)]
    tt_val = tt[tt.study_id.isin(va)]

    ds_tr = CrossSequencePairDataset(tt_train, mm_ann, mm_x, seed=args.seed)
    ds_va = CrossSequencePairDataset(tt_val, mm_ann, mm_x, seed=args.seed + 1)

    seen = {int(s) for s, _l, _a in ds_tr.items}
    assert not (seen & held_out), (
        "ACSSL pretraining touched {} held-out patients".format(len(seen & held_out)))

    meta = {
        "n_train_sites": len(ds_tr), "n_val_sites": len(ds_va),
        "train_patients": len(seen),
        "held_out_patients_excluded": len(held_out),
        "sites_by_modality_count": {str(k): int(v) for k, v in
                                    ds_tr.n_sites_by_modality_count().items()},
        "split_sha256": _split_digest(pd.read_csv(SPLIT_FILE)),
    }
    return ds_tr, ds_va, meta


def run_epoch(model, loader, ctx, args, optimizer=None):
    train = optimizer is not None
    model.train() if train else model.eval()
    amp = args._amp
    tot, n = 0.0, 0
    for x_a, m_a, x_b, m_b in loader:
        x_a = x_a.to(ctx.device, non_blocking=True)
        x_b = x_b.to(ctx.device, non_blocking=True)
        m_a = m_a.to(ctx.device, non_blocking=True)
        m_b = m_b.to(ctx.device, non_blocking=True)
        with torch.set_grad_enabled(train), (
                amp.autocast() if amp else torch.autocast("cpu", enabled=False)):
            _f_a, z_a = model.embed(x_a, m_a)
            _f_b, z_b = model.embed(x_b, m_b)
            loss = info_nce(z_a.float(), z_b.float(), temperature=args.temperature)
        if train:
            optimizer.zero_grad(set_to_none=True)
            if amp is not None:
                amp.backward(loss)
                amp.step(optimizer)
            else:
                loss.backward()
                optimizer.step()
        tot += float(loss.item()) * x_a.size(0)
        n += x_a.size(0)
    return tot / max(n, 1)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ACSSL cross-sequence pretraining (Chapter 3 E4)")
    add_mode_args(ap)
    ap.add_argument("--backbone", type=str, default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--proj_out", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--cache_in_ram", choices=["auto", "yes", "no"], default="auto")
    ap.add_argument("--amp", dest="amp", action="store_true", default=True)
    ap.add_argument("--no_amp", dest="amp", action="store_false")
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    ctx = resolve_mode(args)
    print("=" * 68)
    print("  ACSSL cross-sequence pretraining  (Chapter 3 sec:method-acssl)")
    print("=" * 68)
    print(ctx.banner())

    gpu = configure_backend(False)
    ds_tr, ds_va, meta = build_datasets(ctx, args)
    print("\n  train sites : {:,}".format(len(ds_tr)))
    print("  val sites   : {:,}".format(len(ds_va)))
    if meta:
        print("  patients    : {:,} (development partition only)".format(
            meta["train_patients"]))
        print("  sites by available sequences: {}".format(
            meta["sites_by_modality_count"]))
    if len(ds_tr) == 0:
        print("\n[FAIL] no (patient, level) site has two sequences, so the "
              "positive relation of sec:method-positive-pairs does not exist "
              "in this cache. Build the cross-sequence cache first.")
        return 1

    lkw = loader_kwargs(0 if ctx.is_smoke else (args.workers or 4),
                        cuda=str(ctx.device).startswith("cuda"))
    ld_tr = DataLoader(ds_tr, batch_size=ctx.batch_size, shuffle=True,
                       drop_last=True, **lkw)
    ld_va = DataLoader(ds_va, batch_size=ctx.batch_size, **lkw)

    model = ACSSLModel(args.backbone, args.dim, args.proj_out).to(ctx.device)
    args._amp = Amp(args.amp, str(ctx.device))
    print("  model       : {:.2f}M parameters".format(
        sum(p.numel() for p in model.parameters()) / 1e6))
    print("  precision   : {}".format(args._amp.label()))
    print("  temperature : {}".format(args.temperature))
    print("  modality dropout: OFF (sec:method-training-phases phase 2)")

    opt = torch.optim.AdamW(model.parameters(), lr=ctx.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, ctx.epochs))

    hist_p = os.path.join(ctx.log_dir, "acssl_{}_seed{}_history.csv".format(
        ctx.mode, args.seed))
    best, best_state = float("inf"), None
    print("\n[STAGE 1] contrastive pretraining")
    with open(hist_p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["mode", "seed", "epoch", "lr", "train_infonce", "val_infonce", "seconds"])
        for ep in range(1, ctx.epochs + 1):
            t0 = time.time()
            lr_now = opt.param_groups[0]["lr"]
            tr_loss = run_epoch(model, ld_tr, ctx, args, opt)
            with torch.no_grad():
                va_loss = run_epoch(model, ld_va, ctx, args, None)
            sched.step()
            secs = time.time() - t0
            w.writerow([ctx.mode, args.seed, ep, "{:.3e}".format(lr_now),
                        round(tr_loss, 6), round(va_loss, 6), round(secs, 2)])
            fh.flush()
            print("  epoch {:>3}/{}  train {:.4f}  val {:.4f}  [{:.1f}s]".format(
                ep, ctx.epochs, tr_loss, va_loss, secs))
            if va_loss < best:
                best = va_loss
                best_state = {k: v.detach().cpu().clone()
                              for k, v in model.encoders.state_dict().items()}

    # chance level for InfoNCE over a batch of B is log(B); a loss at or above
    # it means the objective learned nothing and E4 would transfer noise
    chance = float(np.log(ctx.batch_size))
    out = args.out or os.path.join(ctx.checkpoint_dir, ACSSL_CKPT_NAME)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save({
        "encoders_state_dict": best_state,
        "backbone": args.backbone,
        "dim": args.dim,
        "temperature": args.temperature,
        "best_val_infonce": best,
        "chance_infonce": chance,
        "epochs": ctx.epochs,
        "seed": args.seed,
        "split_seed": SPLIT_SEED,
        "mode": ctx.mode,
        "provenance": ctx.stamp(),
        "meta": meta,
    }, out)

    print("\n  best val InfoNCE : {:.4f}   (chance ~ log(batch) = {:.4f})".format(
        best, chance))
    if best >= chance:
        print("  [!] at or above chance -- the objective did not learn a "
              "cross-sequence correspondence. Do NOT transfer these weights.")
    print("  encoders -> {}".format(os.path.relpath(out, PROJECT_ROOT)))
    print("  history  -> {}".format(os.path.relpath(hist_p, PROJECT_ROOT)))
    if ctx.is_smoke:
        print("\n  SMOKE PASS -- machinery runs. Not a result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
