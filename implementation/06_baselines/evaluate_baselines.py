# Phase 7 Verification Audit: Baseline Benchmarks Audit Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 7: E0 Baseline Classifier Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e0_baseline_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] Baseline metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        metrics = json.load(f)

    print(f"Auditing Baseline Backbones ({len(metrics)} evaluated)...")
    for b_name, m in metrics.items():
        assert m['top1_accuracy'] > 0.65, f"[ERROR] {b_name} accuracy below minimum baseline threshold!"
        assert m['qwk_kappa'] > 0.60, f"[ERROR] {b_name} QWK below minimum threshold!"

    print("\n✅ [PASS] Phase 7 Baseline Benchmarks Verified!")
    print("   100% of baseline architectures evaluated with valid accuracy and QWK metrics.")
    print("=" * 65)

if __name__ == "__main__":
    main()
