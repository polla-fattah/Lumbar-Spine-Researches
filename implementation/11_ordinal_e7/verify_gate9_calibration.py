# Phase 13 & Gate 9 Verification Audit: Ordinal Calibration Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 13 & Gate 9: Ordinal Calibration Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e7_ordinal_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] Ordinal metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    qwk = m['qwk_kappa']
    ece = m['ece_calibration']

    print(f"Auditing Ordinal Loss & Calibration Metrics:")
    print(f"  - QWK Kappa Agreement : {qwk:.4f} (Threshold > 0.9000)")
    print(f"  - ECE Calibration Error : {ece:.4f} (Threshold < 0.0500)")

    assert qwk > 0.90, f"[GATE 9 ERROR] QWK Kappa {qwk} below 0.9000 threshold!"
    assert ece < 0.05, f"[GATE 9 ERROR] ECE error {ece} exceeds 0.0500 threshold!"

    print("\n✅ [PASS] Gate 9 Verified: Ordinal Calibration Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
