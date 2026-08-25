# Phase 17 & Gate 12 Verification Audit
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 17 & Gate 12: LoRA Adaptation Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(base_dir, "data", "derived", "lora_adaptation_metrics.json")

    if not os.path.exists(json_path):
        print(f"[FAIL] LoRA metrics JSON not found at {json_path}.")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        m = json.load(f)

    acc = m['adapted_accuracy']
    print(f"LoRA Adapted Accuracy on Rizgary Cohort: {acc * 100:.2f}% (Threshold > 88.00%)")
    assert acc > 0.88, f"[GATE 12 ERROR] LoRA adapted accuracy {acc} below 0.8800 threshold!"

    print("\n✅ [PASS] Gate 12 Verified: LoRA Clinical Domain Adaptation Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
