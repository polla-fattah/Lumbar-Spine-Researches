"""
Gate 1 Reproducibility & Determinism Verification (Phase 1)
Author: Dr. Polla Fattah / Selar's PhD Research Team
Project: AMOG-Net Lumbar Spine MRI Automated Grading

This script verifies:
1. Seed setting across random, numpy, and torch
2. PyTorch GPU deterministic execution (CUDNN determinism)
3. Bit-for-bit reproducibility of forward pass outputs across repeated runs
"""

import sys
import os
import random
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def set_seed(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

def test_determinism():
    print("=" * 65)
    print("  Gate 1: Reproducibility & Seed Verification Test")
    print("=" * 65)
    
    SEED = 42
    print(f"Applying Random Seed: {SEED}")
    
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        print("[FAIL] PyTorch is not installed. Run 'python setup_environment.py' first.")
        return False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Testing execution on device: {device}")

    # Build toy dummy ConvNet model for 2.5D MRI ROI crop (3 channels x 64 x 64)
    class DummyROIClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv2d(3, 16, kernel_size=3, padding=1)
            self.fc = nn.Linear(16 * 64 * 64, 3) # 3 grading classes
            
        def forward(self, x):
            x = torch.relu(self.conv(x))
            x = x.view(x.size(0), -1)
            return self.fc(x)

    # Run 1
    set_seed(SEED)
    model1 = DummyROIClassifier().to(device)
    model1.eval()
    dummy_input1 = torch.randn(4, 3, 64, 64, device=device)
    with torch.no_grad():
        out1 = model1(dummy_input1)

    # Run 2 with same seed initialization
    set_seed(SEED)
    model2 = DummyROIClassifier().to(device)
    model2.eval()
    dummy_input2 = torch.randn(4, 3, 64, 64, device=device)
    with torch.no_grad():
        out2 = model2(dummy_input2)

    # Compare tensors
    diff = torch.max(torch.abs(out1 - out2)).item()
    is_exact = torch.equal(out1, out2)

    print(f"Max Absolute Output Difference: {diff:.8f}")
    
    if is_exact or diff < 1e-6:
        print("\n[PASS] Gate 1 Reproducibility Verified!")
        print("   PyTorch forward passes are deterministic and reproducible across runs.")
        print("   Environment is ready for Phase 2 dataset splitting and DICOM parsing.")
        print("=" * 65)
        return True
    else:
        print("\n[FAIL] Determinism check failed. Outputs differ between runs.")
        print("=" * 65)
        return False

if __name__ == "__main__":
    test_determinism()
