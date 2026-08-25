# Phase 6 Verification Audit: 2.5D ROI Extraction Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 6: 2.5D Compartment ROI Slice Extraction Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_path = os.path.join(base_dir, "data", "derived", "lumbar_roi_manifest.csv")

    if not os.path.exists(csv_path):
        print(f"[FAIL] ROI Manifest CSV not found at {csv_path}.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    total_rois = len(df)

    invalid_dims = df[(df['crop_width'] != 128) | (df['crop_height'] != 128) | (df['channels'] != 3)]

    print(f"Audited {total_rois} 2.5D ROI Crops...")
    print(f"  - Invalid Tensor Dimension Crops : {len(invalid_dims)}")

    assert total_rois == 500, f"[ERROR] Expected 500 ROIs (100 patients x 5 discs), got {total_rois}!"
    assert len(invalid_dims) == 0, f"[ERROR] Found {len(invalid_dims)} crops with invalid dimensions!"

    print("\n✅ [PASS] Phase 6 2.5D ROI Extraction Verified!")
    print("   100% of disc ROI crops conform to 128x128x3 multi-channel tensor specification.")
    print("=" * 65)

if __name__ == "__main__":
    main()
