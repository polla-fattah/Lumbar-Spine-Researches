# Phase 14 & Gate 10 Verification Audit: Master Model Freeze Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 14 & Gate 10: Master Model Freeze Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    results_json = os.path.join(base_dir, "data", "derived", "amog_public_test_results.json")

    if not os.path.exists(results_json):
        print(f"[FAIL] Master test results JSON not found at {results_json}.")
        sys.exit(1)

    with open(results_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    acc = m['test_top1_accuracy']
    qwk = m['test_qwk_kappa']

    print(f"Auditing Master Model Release {m['model_version']}:")
    print(f"  - Public Test Top-1 Accuracy : {acc * 100:.2f}% (Threshold > 90.00%)")
    print(f"  - Public Test QWK Agreement   : {qwk:.4f} (Threshold > 0.9300)")

    assert acc > 0.90, f"[GATE 10 ERROR] Test accuracy {acc} below 0.9000 threshold!"
    assert qwk > 0.93, f"[GATE 10 ERROR] Test QWK kappa {qwk} below 0.9300 threshold!"

    print("\n✅ [PASS] Gate 10 Verified: AMOG_PUBLIC_FROZEN_v1.0 Certified & Released!")
    print("   Track A Public Development Complete! Ready for Track B Clinical Validation.")
    print("=" * 65)

if __name__ == "__main__":
    main()
