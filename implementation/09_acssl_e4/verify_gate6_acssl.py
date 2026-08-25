# Phase 10 & Gate 6 Verification Audit: ACSSL Representation Quality Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 10 & Gate 6: ACSSL Representation Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e4_acssl_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] ACSSL metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    gain = m['accuracy_gain_over_scratch_pct']

    print(f"Auditing ACSSL Pretraining Representation Quality:")
    print(f"  - Accuracy Gain over Scratch : +{gain:.2f}% (Threshold > +4.00%)")

    assert gain > 4.0, f"[GATE 6 ERROR] Accuracy gain +{gain}% below +4.00% threshold!"

    print("\n✅ [PASS] Gate 6 Verified: ACSSL Contrastive Representation Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
