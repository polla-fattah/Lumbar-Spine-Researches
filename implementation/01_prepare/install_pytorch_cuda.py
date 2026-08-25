#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Install the CUDA build of PyTorch into this environment, and prove it works.

THE PROBLEM THIS FIXES
----------------------
requirements.txt asks for `torch>=2.0.0`. On Windows, plain PyPI resolves that
to the CPU-ONLY wheel. Everything installs cleanly, nothing errors, and the GPU
is simply never used. On this machine that produced torch 2.13.0+cpu alongside
an idle RTX 4060.

auto_setup_and_verify.py detected the situation and printed a suggestion to
install the cu118 wheel, but only printed it -- and cu118 predates the Ada
architecture this card uses. A hint that is never acted on and points at the
wrong wheel is why the CPU build survived setup.

CUDA wheels are not on PyPI. They are served from a separate index and must be
requested explicitly with --index-url. That is the whole fix.

SAFETY
------
Defaults to a dry run: it prints the exact command and changes nothing. Pass
--yes to perform the install (roughly 2-3 GB of download).

USAGE
-----
    python install_pytorch_cuda.py             # inspect, change nothing
    python install_pytorch_cuda.py --yes       # install
    python install_pytorch_cuda.py --verify    # only check the current state
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Driver CUDA version -> preferred PyTorch wheel index, best first.
# A driver reports the HIGHEST CUDA it supports; wheels built for lower CUDA
# versions run fine on it, so we try newest-first and fall back.
WHEEL_PREFERENCE = [
    (12.8, "cu128"),
    (12.6, "cu126"),
    (12.4, "cu124"),
    (12.1, "cu121"),
    (11.8, "cu118"),
]

INDEX = "https://download.pytorch.org/whl/{}"


def detect_gpu():
    """Return (gpu_name, driver_cuda_version) or (None, None)."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi"], stderr=subprocess.STDOUT, timeout=30).decode("utf-8", "replace")
    except Exception:
        return None, None

    cuda = None
    m = re.search(r"CUDA Version:\s*([0-9]+\.[0-9]+)", out)
    if m:
        cuda = float(m.group(1))

    name = None
    m = re.search(r"\|\s+\d+\s+(NVIDIA[^|]*?)\s{2,}", out)
    if m:
        name = m.group(1).strip()
    return name, cuda


def choose_wheel(driver_cuda: float | None) -> str:
    if driver_cuda is None:
        return "cu126"
    for need, tag in WHEEL_PREFERENCE:
        if driver_cuda >= need:
            return tag
    return "cu118"


def torch_state():
    """(installed, version, cuda_available, device_name)."""
    try:
        import torch
    except ImportError:
        return False, None, False, None
    ok = False
    dev = None
    try:
        ok = torch.cuda.is_available()
        if ok:
            dev = torch.cuda.get_device_name(0)
    except Exception:
        ok = False
    return True, torch.__version__, ok, dev


def verify(strict_gpu_present: bool) -> int:
    installed, version, cuda_ok, dev = torch_state()
    print("\n" + "-" * 70)
    print("VERIFICATION")
    print("-" * 70)
    if not installed:
        print("  [FAIL] torch is not installed in this environment.")
        return 1

    print("  torch version      : {}".format(version))
    print("  cuda available     : {}".format(cuda_ok))
    if cuda_ok:
        import torch
        print("  device             : {}".format(dev))
        print("  torch CUDA runtime : {}".format(torch.version.cuda))
        vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print("  VRAM               : {:.1f} GB".format(vram))
        try:
            a = torch.randn(512, 512, device="cuda")
            b = (a @ a).sum().item()
            print("  matmul on GPU      : OK ({:.3e})".format(b))
        except Exception as exc:
            print("  [FAIL] GPU matmul failed: {}".format(exc))
            return 1
        print("\n  [PASS] CUDA acceleration is active.")
        return 0

    if "+cpu" in str(version):
        print("\n  [FAIL] this is a CPU-ONLY build ('+cpu' in the version string).")
    else:
        print("\n  [FAIL] torch cannot see a CUDA device.")
    if strict_gpu_present:
        print("         An NVIDIA GPU IS present on this machine, so this is a")
        print("         wheel problem, not a hardware one. Re-run with --yes.")
    return 1


def main():
    ap = argparse.ArgumentParser(description="Install CUDA-enabled PyTorch")
    ap.add_argument("--yes", action="store_true", help="actually perform the install")
    ap.add_argument("--verify", action="store_true", help="only verify current state")
    ap.add_argument("--wheel", type=str, default=None,
                    help="force a wheel tag, e.g. cu126")
    args = ap.parse_args()

    print("=" * 70)
    print("  PyTorch CUDA Installer")
    print("=" * 70)

    gpu, driver_cuda = detect_gpu()
    if gpu:
        print("  GPU detected       : {}".format(gpu))
        print("  driver supports    : CUDA {}".format(driver_cuda))
    else:
        print("  GPU detected       : none (nvidia-smi unavailable)")

    installed, version, cuda_ok, dev = torch_state()
    print("  torch installed    : {}".format(version if installed else "no"))
    print("  cuda available now : {}".format(cuda_ok))

    if args.verify:
        return verify(strict_gpu_present=bool(gpu))

    if cuda_ok:
        print("\n  Nothing to do: CUDA is already working.")
        return verify(strict_gpu_present=bool(gpu))

    if not gpu:
        print("\n  No NVIDIA GPU visible. Install the CPU build deliberately, or")
        print("  check that the driver is installed and nvidia-smi is on PATH.")
        return 1

    tag = args.wheel or choose_wheel(driver_cuda)
    index = INDEX.format(tag)
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           "--index-url", index, "torch", "torchvision"]

    print("\n  Chosen wheel       : {}  (for driver CUDA {})".format(tag, driver_cuda))
    print("  Target interpreter : {}".format(sys.executable))
    print("\n  Command:")
    print("    " + " ".join(cmd))

    if not args.yes:
        print("\n  DRY RUN -- nothing installed. Re-run with --yes to proceed.")
        print("  Download is roughly 2-3 GB.")
        return 0

    print("\n  Installing (this takes several minutes)...\n")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        print("\n  [FAIL] pip exited {}.".format(exc.returncode))
        print("  If the index has no wheel for this Python version, try an")
        print("  older tag: --wheel cu126")
        return 1

    # torch was replaced underneath us; re-verify in a clean interpreter
    print("\n  Re-checking in a fresh interpreter...")
    probe = (
        "import torch;"
        "print('version', torch.__version__);"
        "print('cuda', torch.cuda.is_available());"
        "print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"
    )
    subprocess.call([sys.executable, "-c", probe])
    return 0


if __name__ == "__main__":
    sys.exit(main())
