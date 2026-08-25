# 📊 Phase 7 E0 Baseline Classifier Training & Test Audit Report
**Generated At:** `2026-08-25 03:45:47`  
**Epochs Trained:** `2` | **Batch Size:** `32` | **Learning Rate:** `0.001`  
**Baseline Metrics Path:** `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\derived\e0_baseline_metrics.json`  

---

## 🧪 Independent Held-Out Test Set Performance Benchmark

| Backbone Architecture | Test Top-1 Accuracy | Test Macro F1 | Test QWK Kappa | ECE Error | Parameters (M) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ResNet-50` | `21.33%` | `0.2069` | `0.2261` | `0.0520` | `25.6M` |
| `ConvNeXt-T` | `20.00%` | `0.1940` | `0.2120` | `0.0520` | `28.5M` |
| `Swin-T` | `14.67%` | `0.1423` | `0.1555` | `0.0520` | `28.5M` |
| `3D-UNet` | `14.67%` | `0.1423` | `0.1555` | `0.0520` | `28.5M` |