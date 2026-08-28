#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""What does automating localisation cost, in QWK?

THE EXPERIMENT
--------------
Every result in this thesis grades targets at HUMAN-annotated coordinates. A
deployable system cannot: on a new cohort nobody has annotated anything. The
localisation feasibility study established that derived coordinates land inside
the model's field of view for 99-100% of targets, but containment is not
centring, and the attribution analysis shows the model concentrates its evidence
near the centre of the crop.

So the question is not whether the structure is in the crop. It is how much
grading accuracy is lost when the crop is centred ~6 mm off. That is measured
here directly: the same trained checkpoints, the same test patients, the same
labels, evaluated twice -- once on crops built from human coordinates and once on
crops built from coordinates derived by segmentation.

WHAT IS HELD FIXED
------------------
Everything except position. Same checkpoints, no retraining. Same labels, same
frozen split, same crop geometry and resolution. Targets are matched on
(study, level, condition) so the two runs score exactly the same set, and a
target missing from either side is dropped from BOTH rather than scored on one.

WHY NOT RETRAIN
---------------
Retraining on derived coordinates would measure something else -- whether a model
can adapt to a systematically offset crop -- and would confound it with this
question. A deployed system would use the released checkpoints, so the released
checkpoints are what is tested.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, PROJECT_ROOT, resolve_mode  # noqa: E402
from amog_models import MODALITIES  # noqa: E402
from amog_train import AMOGNet, configure_backend, compute_metrics  # noqa: E402
from rsna_data import cache_paths  # noqa: E402


class CacheTargets(Dataset):
    """Target-rung samples straight from a built cache, in index order."""

    def __init__(self, cache_name, keys):
        arr_p, valid_p, idx_p, _ = cache_paths(cache_name)
        import pandas as pd
        self.index = pd.read_csv(idx_p)
        self.arr = np.load(arr_p, mmap_mode="r")
        self.valid = np.load(valid_p)
        self.keys = keys
        pos = {}
        for i, r in enumerate(self.index.itertuples()):
            pos[(r.study_id, r.level_key, r.condition_key)] = i
        self.pos = pos

    def usable(self):
        return [k for k in self.keys
                if k in self.pos and self.valid[self.pos[k]]]

    def build(self, keys):
        self.use = keys

    def __len__(self):
        return len(self.use)

    def __getitem__(self, i):
        k = self.use[i]
        row = self.index.iloc[self.pos[k]]
        img = np.asarray(self.arr[self.pos[k]], dtype=np.float32)
        slot = MODALITIES.index(row.modality)
        # the model expects (M, C, H, W) with a mask; only the annotated
        # modality is populated, which is exactly how E0 is fed
        m = np.zeros((len(MODALITIES),) + img.shape, dtype=np.float32)
        m[slot] = img
        mask = np.zeros(len(MODALITIES), dtype=np.float32)
        mask[slot] = 1.0
        return (torch.from_numpy(m), torch.from_numpy(mask),
                torch.tensor(CONDITIONS.index(row.condition_key)),
                torch.tensor(int(str(row.level_key)[1]) - 1),
                torch.tensor(int(row.label)),
                torch.tensor(int(row.study_id)),
                torch.tensor(slot))


@torch.no_grad()
def run(model, loader, device):
    model.eval()
    yt, yp, cc = [], [], []
    for imgs, mask, cond, lvl, y, _pid, slot in loader:
        imgs, mask = imgs.to(device), mask.to(device)
        cond, lvl, slot = cond.to(device), lvl.to(device), slot.to(device)
        fused, _ = model.forward_target(imgs, mask, cond, lvl, slot)
        lg = model.head(fused)
        if lg.size(-1) == 2:
            p = torch.sigmoid(lg.float())
            probs = torch.stack([1 - p[:, 0], p[:, 0] - p[:, 1], p[:, 1]],
                                dim=1).clamp(min=0)
        else:
            probs = torch.softmax(lg.float(), dim=1)
        yp.append(probs.argmax(1).cpu().numpy())
        yt.append(y.numpy())
        cc.append(cond.cpu().numpy())
    return np.concatenate(yt), np.concatenate(yp), np.concatenate(cc)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--human_cache", default="rsna_roi_v2")
    ap.add_argument("--derived_cache", default="rsna_roi_derived")
    ap.add_argument("--stages", default="E0,E2,E4")
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--batch_size", type=int, default=64)
    args = ap.parse_args()

    import pandas as pd
    ctx = resolve_mode(argparse.Namespace(
        mode="real", seed=42, epochs=None, lr=None, device=None,
        max_samples=None, batch_size=None))
    configure_backend()

    # the target set is the intersection: a target must be usable in BOTH
    _, _, didx_p, _ = cache_paths(args.derived_cache)
    didx = pd.read_csv(didx_p)
    keys = [(r.study_id, r.level_key, r.condition_key)
            for r in didx.itertuples()]

    ds_h = CacheTargets(args.human_cache, keys)
    ds_d = CacheTargets(args.derived_cache, keys)
    common = sorted(set(ds_h.usable()) & set(ds_d.usable()))
    ds_h.build(common)
    ds_d.build(common)
    print("  scoring {} targets present and valid in BOTH caches".format(
        len(common)))
    print("  ({} studies)".format(len({k[0] for k in common})))

    rows = []
    for stage in [s.strip() for s in args.stages.split(",")]:
        for seed in [int(s) for s in args.seeds.split(",")]:
            ck = os.path.join(ctx.checkpoint_dir, "{}_real_seed{}_best.pt".format(
                stage, seed))
            if not os.path.exists(ck):
                continue
            sd = torch.load(ck, map_location=ctx.device, weights_only=False)
            model = AMOGNet(stage, sd.get("backbone") or args.backbone, args.dim,
                            False, False, seed, pretrained=False).to(ctx.device)
            model.load_state_dict(sd["model_state_dict"], strict=True)
            out = {}
            for tag, ds in (("human", ds_h), ("derived", ds_d)):
                dl = DataLoader(ds, batch_size=args.batch_size, shuffle=False,
                                num_workers=0)
                yt, yp, cc = run(model, dl, ctx.device)
                m = compute_metrics(yt, yp)
                out[tag] = (m, yt, yp, cc)
            h, d = out["human"][0], out["derived"][0]
            rows.append(dict(stage=stage, seed=seed,
                             qwk_human=h["qwk"], qwk_derived=d["qwk"],
                             f1_human=h["macro_f1"], f1_derived=d["macro_f1"]))
            print("  {} seed {}: QWK human {:.4f} -> derived {:.4f}  "
                  "({:+.4f})".format(stage, seed, h["qwk"], d["qwk"],
                                     d["qwk"] - h["qwk"]))
            if stage == "E0" and seed == 42:
                yt, yph, cch = out["human"][1], out["human"][2], out["human"][3]
                ypd = out["derived"][2]
                print("")
                print("    per condition, {} seed {}".format(stage, seed))
                for k, c in enumerate(CONDITIONS):
                    s = cch == k
                    if s.sum() < 10:
                        continue
                    qh = compute_metrics(yt[s], yph[s])["qwk"]
                    qd = compute_metrics(yt[s], ypd[s])["qwk"]
                    print("      {:<20} {:.4f} -> {:.4f}  ({:+.4f})".format(
                        c, qh, qd, qd - qh))
                print("")

    if not rows:
        print("[FAIL] no checkpoints evaluated.")
        return 1
    df = pd.DataFrame(rows)
    df["delta"] = df.qwk_derived - df.qwk_human

    print("")
    print("=" * 74)
    print("  COST OF AUTOMATING LOCALISATION")
    print("=" * 74)
    for stage, g in df.groupby("stage"):
        d = g.delta.to_numpy()
        print("  {:<6} human {:.4f}   derived {:.4f}   delta {:+.4f} +/- {:.4f}"
              "  ({}/{} seeds worse)".format(
                  stage, g.qwk_human.mean(), g.qwk_derived.mean(), d.mean(),
                  d.std(ddof=1) if len(d) > 1 else 0.0,
                  int((d < 0).sum()), len(d)))
    overall = df.delta.mean()
    base = df.qwk_human.mean()
    print("")
    print("  overall {:+.4f} QWK, i.e. {:.1f}% of the human-coordinate result"
          .format(overall, 100.0 * abs(overall) / base))

    out = os.path.join(PROJECT_ROOT, "data", "reports",
                       "derived_coordinate_cost.csv")
    df.to_csv(out, index=False)
    print("  {}".format(os.path.relpath(out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
