# Phase 16 & Gate 11 Verification Audit
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 16 & Gate 11: Zero-Shot Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(base_dir, "data", "derived", "zero_shot_metrics.json")

    if not os.path.exists(json_path):
        print(f"[FAIL] Zero-shot metrics JSON not found at {json_path}.")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        m = json.load(f)

    acc = m['zero_shot_accuracy']
    print(f"Zero-Shot Accuracy on Rizgary Cohort: {acc * 100:.2f}% (Threshold > 80.00%)")
    assert acc > 0.80, f"[GATE 11 ERROR] Zero-shot accuracy {acc} below 0.8000 threshold!"

    print("\n✅ [PASS] Gate 11 Verified: Zero-Shot Out-of-Domain Generalization Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
