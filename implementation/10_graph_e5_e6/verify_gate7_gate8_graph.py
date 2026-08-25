# Phase 11 & 12 Verification Audit: Gates 7 & 8 Test
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("  Phase 11 & 12 & Gates 7 & 8: Heterogeneous Graph Verification Audit")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    metrics_json = os.path.join(base_dir, "data", "derived", "e5_e6_graph_metrics.json")

    if not os.path.exists(metrics_json):
        print(f"[FAIL] Graph metrics JSON not found at {metrics_json}.")
        sys.exit(1)

    with open(metrics_json, 'r', encoding='utf-8') as f:
        m = json.load(f)

    f1_gain = m['macro_f1_gain_over_e1_pct']

    print(f"Auditing Heterogeneous Graph & GNN Performance:")
    print(f"  - Gate 7 Schema Nodes/Edges : {m['total_graph_nodes']} / {m['total_graph_edges']}")
    print(f"  - Gate 8 Macro F1 Gain      : +{f1_gain:.2f}% (Threshold > +5.00%)")

    assert m['total_graph_nodes'] == 1000, f"[GATE 7 ERROR] Graph node count mismatch!"
    assert f1_gain > 5.0, f"[GATE 8 ERROR] Macro F1 gain +{f1_gain}% below +5.00% threshold!"

    print("\n✅ [PASS] Gates 7 & 8 Verified: Heterogeneous Graph Engine Certified!")
    print("=" * 65)

if __name__ == "__main__":
    main()
