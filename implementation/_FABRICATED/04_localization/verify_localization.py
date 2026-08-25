# Phase 5 Verification Audit: SPIDER Landmark Sanity & Distance Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 5: SPIDER Landmark Localization Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(base_dir, "data", "derived", "spider_localization_landmarks.json")

    if not os.path.exists(json_path):
        print(f"[FAIL] Landmark JSON not found at {json_path}.")
        print("       Run 'python spider_locator.py' first.")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    total_patients = len(registry)
    missing_landmarks = 0
    distance_violations = 0

    for p_id, lms in registry.items():
        if len(lms) != 10:
            missing_landmarks += 1
            
        c1 = np.array(lms["disc_L1-L2"]["centroid_mm"])
        c2 = np.array(lms["disc_L2-L3"]["centroid_mm"])
        dist = np.linalg.norm(c2 - c1)
        
        if dist < 10.0 or dist > 80.0:
            distance_violations += 1

    print(f"Audited 3D Landmarks for {total_patients} Patients...")
    print(f"  - Patients with Missing Landmarks : {missing_landmarks}")
    print(f"  - Inter-Disc Distance Violations   : {distance_violations}")

    assert missing_landmarks == 0, f"[ERROR] Found {missing_landmarks} patients with incomplete landmarks!"
    assert distance_violations == 0, f"[ERROR] Found {distance_violations} inter-disc distance violations!"

    print("\n✅ [PASS] Phase 5 SPIDER Localization Verified!")
    print("   100% of patients possess complete 3D centroids with valid anatomical spacing.")
    print("=" * 65)

if __name__ == "__main__":
    main()
