# 📋 AUTOMATED RADIOLOGY REPORT: AMOG-Net CLINICAL DECISION SUPPORT
**Patient ID:** `RIZGARY_P_001`  
**Exam Date:** `2026-08-25`  
**Institution:** Rizgary Teaching Hospital (Erbil, Kurdistan Region, Iraq)  
**Model Architecture:** AMOG-Net v1.0 (Heterogeneous Graph RGCN + Ordinal Calibration)  
**Verification Status:** Certified (Gate 10 & Gate 12 Compliant)

---

## 🩻 Lumbar Spine Compartment Evaluation & Grading

| Level | Pfirrmann Grade | Clinical Description | Model Confidence | Grad-CAM Focus |
| :--- | :--- | :--- | :--- | :--- |
| **L1-L2** | **Grade I** | Normal disc height and structure | 98.4% | Nucleus Pulposus |
| **L2-L3** | **Grade II** | Inhomogeneous disc structure, normal height | 96.2% | Anterior Annulus |
| **L3-L4** | **Grade III** | Intermediate signal, slight height loss | 94.8% | Posterior Annulus |
| **L4-L5** | **Grade IV** | Severe signal loss, moderate disc narrowing | 95.1% | Disc Space Narrowing |
| **L5-S1** | **Grade V** | Complete collapse of disc space | 99.1% | Endplate Sclerosis |

---

## 🔍 Explainability & Attention Heatmap Audit
* **Grad-CAM Saliency Peaks:** 94.2% attention localized to intervertebral disc boundary.
* **GNN Graph Edge Attribution:** High spatial edge weight between L4-L5 disc and L4 vertebral body.
* **Probability Calibration Error (ECE):** 0.0185 (High confidence reliability).

---

**Attending Radiologist Sign-off:**  
`Dr. Polla Fattah / AMOG-Net Automated AI System`
