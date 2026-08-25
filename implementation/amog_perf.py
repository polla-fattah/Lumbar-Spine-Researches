#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Performance configuration. Written for a 32 GB Blackwell card with ~100 GB host RAM,
but every setting degrades safely on smaller hardware.

WHERE THE TIME ACTUALLY GOES
----------------------------
Measured on the 8 GB laptop card, the ladder was bound by three things in order:

  1. disk I/O   -- both ROI caches total 14.4 GB and are read randomly every
                   epoch from a memory map
  2. fp32 math  -- no tensor cores were being used at all
  3. tiny batches -- the graph rungs encode 25 nodes x 3 sequences = 75 crops per
                   patient, so 8 GB forced ~2 patients per step and the GPU
                   spent most of its time waiting

All three disappear on the target machine, but only if the code is told to use
it. None of this changes what is computed - it changes how it is scheduled.

WHAT EACH SWITCH BUYS, ROUGHLY
------------------------------
  cache in RAM   removes disk entirely from the training loop. 14.4 GB resident
                 is nothing against 100 GB.
  bf16 autocast  2-3x on Blackwell tensor cores. bf16 rather than fp16 because it
                 keeps fp32's exponent range and so needs no loss scaling - one
                 less thing that can silently corrupt a long run.
  channels_last  convolutions hit tensor cores far more often in NHWC.
  TF32           free accuracy-neutral speedup on matmul and cudnn.
  big batches    32 GB lets the graph rungs run 16-24 patients per step instead
                 of 2, which is where most of the wall-clock win lives.
  workers        decode and collate on spare cores while the GPU computes.

A NOTE ON REPRODUCIBILITY
-------------------------
cudnn.benchmark picks algorithms by timing them, so it can make runs differ in
the last bits. That is fine for training but not for a determinism check, so
configure_backend(deterministic=True) turns it off and Gate 1 should use that.
"""

from __future__ import annotations

import os
import sys

import torch


def gpu_report():
    if not torch.cuda.is_available():
        return dict(available=False, name="cpu", vram_gb=0.0, capability=None, bf16=False)
    p = torch.cuda.get_device_properties(0)
    cap = (p.major, p.minor)
    return dict(
        available=True, name=p.name, vram_gb=p.total_memory / (1024 ** 3),
        capability=cap,
        bf16=torch.cuda.is_bf16_supported(),
        sm_count=p.multi_processor_count,
    )


def configure_backend(deterministic: bool = False, verbose: bool = True):
    """Enable the accuracy-neutral fast paths."""
    info = gpu_report()
    if not info["available"]:
        if verbose:
            print("  [perf] no CUDA device; running on CPU")
        return info

    torch.backends.cuda.matmul.allow_tf32 = not deterministic
    torch.backends.cudnn.allow_tf32 = not deterministic
    torch.backends.cudnn.benchmark = not deterministic
    if deterministic:
        torch.backends.cudnn.deterministic = True
    try:
        torch.set_float32_matmul_precision("high" if not deterministic else "highest")
    except Exception:
        pass

    if verbose:
        print("  [perf] {}  {:.1f} GB  sm_{}{}  bf16={}".format(
            info["name"], info["vram_gb"], info["capability"][0], info["capability"][1],
            info["bf16"]))
        # Blackwell is sm_120; wheels older than cu128 have no kernels for it and
        # fail at the first launch rather than at import, which is confusing.
        if info["capability"][0] >= 12:
            cu = getattr(torch.version, "cuda", "?")
            print("  [perf] Blackwell-class GPU detected; torch CUDA {}".format(cu))
            try:
                if float(str(cu).split(".")[0]) < 12.8 - 0.0001:
                    print("  [perf] WARNING: this wheel may lack sm_120 kernels. "
                          "Use cu128 or newer.")
            except Exception:
                pass
        if deterministic:
            print("  [perf] deterministic mode: TF32 and cudnn.benchmark OFF")
    return info


def suggest_batch(stage_is_graph: bool, vram_gb: float, requested: int | None = None):
    """Pick a batch size the card can actually hold.

    Graph rungs cost ~25x a target rung per sample, because each patient carries
    25 nodes. Values are deliberately conservative; raise with --batch_size once a
    run is seen to fit.
    """
    if requested:
        return requested
    if vram_gb <= 0:
        return 2 if stage_is_graph else 8
    if stage_is_graph:
        if vram_gb >= 30:
            return 16
        if vram_gb >= 20:
            return 8
        if vram_gb >= 14:
            return 4
        return 2
    if vram_gb >= 30:
        return 256
    if vram_gb >= 20:
        return 192
    if vram_gb >= 14:
        return 128
    return 32


def loader_kwargs(workers: int | None = None, cuda: bool = True):
    """DataLoader settings that keep the GPU fed."""
    # On Windows, PyTorch multiprocessing spawn cannot pickle numpy.memmap file descriptors
    if os.name == "nt":
        return dict(num_workers=0, pin_memory=bool(cuda))
    if workers is None:
        cpu = os.cpu_count() or 8
        workers = min(16, max(2, cpu // 2))
    kw = dict(num_workers=workers, pin_memory=bool(cuda))
    if workers > 0:
        kw.update(persistent_workers=True, prefetch_factor=4)
    return kw


class Amp:
    """bf16 autocast with a no-op fallback.

    bf16 needs no GradScaler, which removes a whole class of silent failure in a
    multi-day run. fp16 is offered only for cards without bf16 support.
    """

    def __init__(self, enabled: bool, device: str = "cuda", dtype: str = "bf16"):
        self.enabled = bool(enabled) and device.startswith("cuda") and torch.cuda.is_available()
        if self.enabled and dtype == "bf16" and not torch.cuda.is_bf16_supported():
            dtype = "fp16"
        self.dtype = torch.bfloat16 if dtype == "bf16" else torch.float16
        self.device = device
        self.needs_scaler = self.enabled and self.dtype is torch.float16
        self.scaler = torch.amp.GradScaler("cuda") if self.needs_scaler else None

    def autocast(self):
        if not self.enabled:
            return torch.autocast(device_type="cpu", enabled=False)
        return torch.autocast(device_type="cuda", dtype=self.dtype)

    def backward(self, loss):
        if self.scaler is not None:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()

    def step(self, optimizer):
        if self.scaler is not None:
            self.scaler.step(optimizer)
            self.scaler.update()
        else:
            optimizer.step()

    def label(self):
        if not self.enabled:
            return "fp32"
        return "bf16" if self.dtype is torch.bfloat16 else "fp16 (+scaler)"


def maybe_compile(model, enable: bool, verbose: bool = True):
    """torch.compile when asked. Falls back silently if unavailable."""
    if not enable:
        return model
    try:
        m = torch.compile(model)
        if verbose:
            print("  [perf] torch.compile enabled (first step will be slow)")
        return m
    except Exception as exc:
        if verbose:
            print("  [perf] torch.compile unavailable: {}".format(exc))
        return model


if __name__ == "__main__":
    print("=" * 66)
    print("  Performance probe")
    print("=" * 66)
    info = configure_backend()
    print()
    for graph in (False, True):
        kind = "graph rung (25 nodes/patient)" if graph else "target rung"
        print("  {:<32} suggested batch {}".format(
            kind, suggest_batch(graph, info["vram_gb"])))
    amp = Amp(True, "cuda" if info["available"] else "cpu")
    print("\n  autocast          : {}".format(amp.label()))
    print("  loader kwargs     : {}".format(loader_kwargs(cuda=info["available"])))

    if info["available"]:
        import time
        x = torch.randn(64, 3, 128, 128, device="cuda")
        import torchvision.models as tvm
        m = tvm.resnet18(weights=None).cuda().to(memory_format=torch.channels_last)
        xc = x.to(memory_format=torch.channels_last)
        for tag, use in (("fp32", False), (amp.label(), True)):
            a = Amp(use, "cuda")
            torch.cuda.synchronize(); t0 = time.time()
            for _ in range(12):
                with a.autocast():
                    m(xc).sum()
            torch.cuda.synchronize()
            print("  {:<18} {:.1f} ms/iter (batch 64)".format(
                tag, (time.time() - t0) / 12 * 1000))
