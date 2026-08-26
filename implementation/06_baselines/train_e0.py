"""Phase 6 (Track A): E0 baseline -- a real backbone on real ROI crops.

This is the number every later experiment (E1..E7) must beat. It is deliberately
plain: one ImageNet-pretrained backbone, cross-entropy, no tricks.

Two things are non-negotiable here and are asserted at runtime:

  1. Splits are grouped by study_id. Two crops from the same patient must never
     land on opposite sides of a split, or the test score is leakage.
  2. Accuracy is reported next to the majority-class rate. On this dataset a
     model that predicts 'Normal/Mild' for everything scores 77.33% accuracy
     and QWK 0.0000. Accuracy alone cannot tell those apart.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M

GRADES = ["Normal/Mild", "Moderate", "Severe"]
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


def _stats_for(n_ch):
    """ImageNet statistics tiled to however many 2.5D slices the cache holds."""
    if n_ch == 3:
        return IMAGENET_MEAN, IMAGENET_STD
    reps = (n_ch + 2) // 3
    return (IMAGENET_MEAN.repeat(reps, 1, 1)[:n_ch],
            IMAGENET_STD.repeat(reps, 1, 1)[:n_ch])


def adapt_first_conv(model, n_ch):
    """Widen the stem to n_ch inputs, preserving the pretrained filters.

    The new channels are seeded with the mean of the RGB filters and the whole
    stem is rescaled by 3/n_ch, so the expected activation magnitude entering
    the network is unchanged. Re-initialising the stem randomly instead would
    make an r=2 variant look worse for a reason that has nothing to do with
    through-plane context.
    """
    if n_ch == 3:
        return model
    import torch.nn as nn
    for name, mod in model.named_modules():
        if isinstance(mod, nn.Conv2d) and mod.in_channels == 3:
            w = mod.weight.data
            new = w.mean(dim=1, keepdim=True).repeat(1, n_ch, 1, 1) * (3.0 / n_ch)
            new[:, :3] = w * (3.0 / n_ch)
            conv = nn.Conv2d(n_ch, mod.out_channels, mod.kernel_size,
                             mod.stride, mod.padding, bias=mod.bias is not None)
            conv.weight.data = new
            if mod.bias is not None:
                conv.bias.data = mod.bias.data.clone()
            parent = model
            parts = name.split(".")
            for q in parts[:-1]:
                parent = getattr(parent, q)
            setattr(parent, parts[-1], conv)
            return model
    return model


class ROIDataset(Dataset):
    def __init__(self, npy_path, indices, labels, train=False, n_ch=3):
        self.mean, self.std = _stats_for(n_ch)
        self.npy_path = npy_path
        self.arr = None                  # opened lazily, per worker
        self.indices = np.asarray(indices)
        self.labels = np.asarray(labels)
        self.train = train

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        if self.arr is None:
            self.arr = np.load(self.npy_path, mmap_mode="r")
        x = np.array(self.arr[self.indices[i]], dtype=np.float32) / 255.0
        x = torch.from_numpy(x)
        if self.train:
            # No horizontal flip. This harness pools all five conditions, and
            # most crops are SAGITTAL, where the in-plane axes are
            # anterior-posterior and superior-inferior -- left-right is through
            # plane. A horizontal flip there mirrors anterior against posterior,
            # putting the vertebral body behind the canal, which is anatomically
            # impossible rather than merely a label swap. The earlier version of
            # this line flipped every crop regardless of plane.
            if torch.rand(1).item() < 0.5:                 # mild intensity jitter
                x = torch.clamp(x * (0.9 + 0.2 * torch.rand(1)), 0, 1)
        x = (x - self.mean) / self.std
        return x, int(self.labels[i])


def build_model(name, n_classes=3):
    import torchvision.models as tvm
    if name == "resnet50":
        m = tvm.resnet50(weights=tvm.ResNet50_Weights.IMAGENET1K_V2)
        m.fc = nn.Linear(m.fc.in_features, n_classes)
    elif name == "convnext_tiny":
        m = tvm.convnext_tiny(weights=tvm.ConvNeXt_Tiny_Weights.IMAGENET1K_V1)
        m.classifier[2] = nn.Linear(m.classifier[2].in_features, n_classes)
    elif name == "densenet121":
        m = tvm.densenet121(weights=tvm.DenseNet121_Weights.IMAGENET1K_V1)
        m.classifier = nn.Linear(m.classifier.in_features, n_classes)
    else:
        raise ValueError(f"unknown backbone {name}")
    return m


def grouped_split(groups, fracs=(0.70, 0.15, 0.15), seed=42):
    """Split *by group*, so no study appears in more than one partition."""
    uniq = np.unique(groups)
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n = len(uniq)
    n_tr = int(round(fracs[0] * n))
    n_va = int(round(fracs[1] * n))
    sets = (set(uniq[:n_tr]), set(uniq[n_tr:n_tr + n_va]), set(uniq[n_tr + n_va:]))
    return [np.array([g in s for g in groups]) for s in sets]


@torch.no_grad()
def run_eval(model, loader, device, criterion):
    model.eval()
    logits_all, y_all, loss_sum, n = [], [], 0.0, 0
    for x, y in loader:
        x = x.to(device, non_blocking=True).to(memory_format=torch.channels_last)
        y = y.to(device, non_blocking=True)
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=device.type == "cuda"):
            out = model(x)
            loss = criterion(out, y)
        loss_sum += float(loss) * len(y)
        n += len(y)
        logits_all.append(out.float().cpu())
        y_all.append(y.cpu())
    logits = torch.cat(logits_all)
    y_true = torch.cat(y_all).numpy()
    probs = torch.softmax(logits, dim=1).numpy()
    y_pred = probs.argmax(1)
    res = M.summarise(y_true, y_pred, probs, k=3)
    res["loss"] = loss_sum / max(n, 1)
    return res, y_true, y_pred, probs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roi_npy", default="implementation/05_rsna_rois/rsna_rois.npy")
    ap.add_argument("--roi_index", default="implementation/05_rsna_rois/rsna_roi_index.csv")
    ap.add_argument("--backbone", default="resnet50")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch_size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--class_weighted", action="store_true",
                    help="inverse-frequency class weights in the loss")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--shuffle_labels", action="store_true",
                    help="NEGATIVE CONTROL: permute labels within each split. A "
                         "sound pipeline must collapse to QWK ~0 here. Anything "
                         "else means information is leaking through the split.")
    ap.add_argument("--out_dir", default="implementation/06_baselines/results")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)

    df = pd.read_csv(args.roi_index)
    n_total = len(df)
    df = df[df["ok"] == 1].reset_index(drop=True)
    print(f"ROIs available     : {len(df):,} / {n_total:,} extracted ok")

    groups = df["study_id"].values
    labels = df["label"].values
    idx = df["roi_index"].values

    m_tr, m_va, m_te = grouped_split(groups, seed=args.seed)

    # Leakage assertion: this is the check that makes the test score meaningful.
    s_tr, s_va, s_te = (set(groups[m]) for m in (m_tr, m_va, m_te))
    assert not (s_tr & s_va) and not (s_tr & s_te) and not (s_va & s_te), \
        "study_id leaked across splits"
    print(f"studies            : train {len(s_tr)}  val {len(s_va)}  test {len(s_te)}")
    print(f"crops              : train {m_tr.sum():,}  val {m_va.sum():,}  test {m_te.sum():,}")

    if args.shuffle_labels:
        # Permute within each split, so the class distribution is untouched and
        # only the image->label correspondence is destroyed.
        rng = np.random.default_rng(args.seed + 1)
        labels = labels.copy()
        for m in (m_tr, m_va, m_te):
            sub = labels[m].copy()
            rng.shuffle(sub)
            labels[m] = sub
        print("")
        print("*** NEGATIVE CONTROL: labels permuted within each split ***")
        print("*** a sound pipeline must now score QWK ~0.00          ***")

    maj = np.bincount(labels[m_te], minlength=3).max() / m_te.sum()
    print("")
    print(f"TEST majority-class accuracy: {maj * 100:.2f}%   <-- the bar")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu = torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu"
    print(f"device             : {device} ({gpu})")

    n_ch = int(np.load(args.roi_npy, mmap_mode="r").shape[1])
    print(f"channels           : {n_ch}  (2.5D radius {(n_ch - 1) // 2})")
    ds_tr = ROIDataset(args.roi_npy, idx[m_tr], labels[m_tr], train=True, n_ch=n_ch)
    ds_va = ROIDataset(args.roi_npy, idx[m_va], labels[m_va], n_ch=n_ch)
    ds_te = ROIDataset(args.roi_npy, idx[m_te], labels[m_te], n_ch=n_ch)
    dl = dict(num_workers=args.workers, pin_memory=True,
              persistent_workers=args.workers > 0)
    ld_tr = DataLoader(ds_tr, batch_size=args.batch_size, shuffle=True,
                       drop_last=True, **dl)
    ld_va = DataLoader(ds_va, batch_size=args.batch_size, **dl)
    ld_te = DataLoader(ds_te, batch_size=args.batch_size, **dl)

    model = adapt_first_conv(build_model(args.backbone), n_ch)
    model = model.to(device).to(memory_format=torch.channels_last)
    n_par = sum(p.numel() for p in model.parameters())
    print(f"backbone           : {args.backbone}  ({n_par / 1e6:.1f}M parameters)")

    if args.class_weighted:
        counts = np.bincount(labels[m_tr], minlength=3).astype(np.float64)
        w = counts.sum() / (3 * np.maximum(counts, 1))
        print(f"class weights      : {np.round(w, 3).tolist()}")
        criterion = nn.CrossEntropyLoss(
            weight=torch.tensor(w, dtype=torch.float32, device=device))
    else:
        criterion = nn.CrossEntropyLoss()

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=args.lr, epochs=args.epochs, steps_per_epoch=len(ld_tr))

    history, best_qwk, best_state, best_ep = [], -2.0, None, -1
    for ep in range(1, args.epochs + 1):
        model.train()
        t0, run_loss, seen = time.time(), 0.0, 0
        for x, y in ld_tr:
            x = x.to(device, non_blocking=True).to(memory_format=torch.channels_last)
            y = y.to(device, non_blocking=True)
            with torch.autocast("cuda", dtype=torch.bfloat16,
                                enabled=device.type == "cuda"):
                loss = criterion(model(x), y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            run_loss += float(loss) * len(y)
            seen += len(y)
        va, *_ = run_eval(model, ld_va, device, criterion)
        dt = time.time() - t0
        history.append(dict(epoch=ep, train_loss=run_loss / seen,
                            **{f"val_{k}": v for k, v in va.items()}, seconds=dt))
        print(f"  ep {ep:02d}/{args.epochs}  train_loss {run_loss / seen:.4f}  "
              f"val_acc {va['accuracy'] * 100:5.2f}%  "
              f"val_bal {va['balanced_accuracy'] * 100:5.2f}%  "
              f"val_f1 {va['macro_f1']:.4f}  val_QWK {va['qwk']:.4f}  ({dt:.0f}s)")
        if va["qwk"] > best_qwk:
            best_qwk, best_ep = va["qwk"], ep
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}

    print("")
    print(f"selecting epoch {best_ep} (best val QWK {best_qwk:.4f}) for the test set")
    model.load_state_dict(best_state)
    te, y_true, y_pred, probs = run_eval(model, ld_te, device, criterion)

    cm = M.confusion(y_true, y_pred, 3)
    print("")
    print("=" * 62)
    print("  HELD-OUT TEST SET  (studies never seen in training or selection)")
    print("=" * 62)
    print(f"  accuracy          {te['accuracy'] * 100:6.2f}%   "
          f"(majority-class {maj * 100:.2f}%)")
    print(f"  balanced accuracy {te['balanced_accuracy'] * 100:6.2f}%")
    print(f"  macro F1          {te['macro_f1']:.4f}")
    print(f"  QWK               {te['qwk']:.4f}")
    print(f"  ECE               {te['ece']:.4f}")
    print("")
    print("  confusion (rows = truth, cols = predicted)")
    print("               " + "".join(f"{g[:8]:>10s}" for g in GRADES))
    for i, g in enumerate(GRADES):
        print(f"    {g:<11s}" + "".join(f"{int(v):10d}" for v in cm[i]))

    if te["accuracy"] <= maj:
        print("")
        print("  [!] accuracy does not beat predicting the majority class.")
    if abs(te["qwk"]) < 1e-6:
        print("  [!] QWK is 0.0000 -- the model is not ordering severity at all.")

    tag = (f"{args.backbone}"
           f"{'_cw' if args.class_weighted else ''}"
           f"{'_SHUFFLED' if args.shuffle_labels else ''}")
    out = {
        "backbone": args.backbone,
        "class_weighted": args.class_weighted,
        "shuffled_labels_control": args.shuffle_labels,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "parameters": int(n_par),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "seed": args.seed,
        "selected_epoch": best_ep,
        "n_train_crops": int(m_tr.sum()), "n_val_crops": int(m_va.sum()),
        "n_test_crops": int(m_te.sum()),
        "n_train_studies": len(s_tr), "n_val_studies": len(s_va),
        "n_test_studies": len(s_te),
        "test_majority_class_accuracy": float(maj),
        "test": te,
        "test_confusion": cm.tolist(),
        "history": history,
    }
    p = os.path.join(args.out_dir, f"e0_{tag}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    torch.save(best_state, os.path.join(args.out_dir, f"e0_{tag}.pt"))
    print("")
    print(f"  results -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
