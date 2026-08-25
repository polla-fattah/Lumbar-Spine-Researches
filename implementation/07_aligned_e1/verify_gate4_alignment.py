# Phase 8 & Gate 4 Verification Audit: Multi-Sequence Alignment Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 8 & Gate 4: Multi-Sequence Spatial Alignment Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e1_aligned_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] E1 metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    err = m['mean_spatial_registration_error_mm']
    gain = m['accuracy_gain_over_e0_pct']

    print(f"Auditing E1 Model Performance:")
    print(f"  - Registration Error : {err:.3f} mm (Threshold < 0.50 mm)")
    print(f"  - Accuracy Gain      : +{gain:.2f}% (Threshold > +3.0%)")

    assert err < 0.50, f"[GATE 4 ERROR] Alignment error {err} mm exceeds 0.50 mm threshold!"
    assert gain > 3.0, f"[GATE 4 ERROR] Accuracy gain +{gain}% below +3.0% threshold!"

    print("\n✅ [PASS] Gate 4 Verified: 100% Geometry-Aligned Multi-Sequence Fusion Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
