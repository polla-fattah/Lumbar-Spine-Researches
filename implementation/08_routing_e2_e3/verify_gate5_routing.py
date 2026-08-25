# Phase 9 & Gate 5 Verification Audit: Routing & Dropout Robustness Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 9 & Gate 5: Disease Routing & Modality Dropout Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e2_e3_routing_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] E2/E3 metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    drop_pct = m['accuracy_drop_1_seq_pct']

    print(f"Auditing E2/E3 Routing Robustness:")
    print(f"  - Accuracy Drop (1-Sequence Dropped) : {drop_pct:.2f}% (Threshold < 2.50%)")

    assert drop_pct < 2.50, f"[GATE 5 ERROR] Accuracy drop {drop_pct}% exceeds 2.50% threshold!"

    print("\n✅ [PASS] Gate 5 Verified: Modality Dropout & Routing Resilience Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
