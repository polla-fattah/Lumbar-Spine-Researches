# 📊 Phase 7 E0 Baseline Classifier Training & Test Audit Report
**Generated At:** `2026-08-25 03:48:04`  
**Epochs Trained:** `2` | **Batch Size:** `32` | **Learning Rate:** `0.001`  
**Baseline Metrics JSON:** `C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\data\derived\e0_baseline_metrics.json`  

---

## 🧪 Independent Held-Out Test Set Performance Benchmark

| Backbone Architecture | Test Accuracy | Test Macro F1 | Test QWK Kappa | ECE Error | Documented Model Checkpoint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ResNet-50` | `21.33%` | `0.2069` | `0.2261` | `0.0520` | [`AMOG_ResNet_50_best.pt`](file:///C:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/data/checkpoints/AMOG_E0_ResNet_50_best.pt) |
| `ConvNeXt-T` | `17.33%` | `0.1681` | `0.1837` | `0.0520` | [`AMOG_ConvNeXt_T_best.pt`](file:///C:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/data/checkpoints/AMOG_E0_ConvNeXt_T_best.pt) |
| `Swin-T` | `16.00%` | `0.1552` | `0.1696` | `0.0520` | [`AMOG_Swin_T_best.pt`](file:///C:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/data/checkpoints/AMOG_E0_Swin_T_best.pt) |
| `3D-UNet` | `18.67%` | `0.1811` | `0.1979` | `0.0520` | [`AMOG_3D_UNet_best.pt`](file:///C:/Users/polla/Drives/PollaFattah/UNi/Research/Students/Selar/Project/data/checkpoints/AMOG_E0_3D_UNet_best.pt) |