# AMOG-Net Unified Experiment & Epoch History Logger
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: Automated Lumbar Spine MRI Grading & Clinical Transfer

import sys
import os
import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime

class AMOGExperimentLogger:
    """
    Unified Logger that automatically records epoch-by-epoch training metrics,
    confusion matrices, hyperparameter configurations, and dissertation tables
    into CSV, JSON, and Markdown formats for unambiguous thesis/paper analysis.
    """
    def __init__(self, experiment_name, base_project_dir=None):
        self.experiment_name = experiment_name
        
        if base_project_dir is None:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        else:
            self.base_dir = base_project_dir

        self.logs_dir = os.path.join(self.base_dir, "data", "logs")
        self.derived_dir = os.path.join(self.base_dir, "data", "derived")
        self.reports_dir = os.path.join(self.base_dir, "data", "reports")

        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.derived_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        self.csv_path = os.path.join(self.logs_dir, f"{experiment_name}_epoch_history.csv")
        self.json_path = os.path.join(self.derived_dir, f"{experiment_name}_metrics.json")
        self.md_path = os.path.join(self.reports_dir, f"{experiment_name}_summary.md")

        # Initialize CSV header if file does not exist
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "epoch", "train_loss", "train_accuracy",
                    "val_loss", "val_accuracy", "val_macro_f1",
                    "val_qwk_kappa", "val_ece_error", "learning_rate", "epoch_time_sec"
                ])

        self.history = []

    def log_epoch(self, epoch, train_loss, train_acc, val_loss, val_acc, val_f1, val_qwk, val_ece, lr, epoch_time):
        """Record a single training epoch into CSV log."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "timestamp": ts,
            "epoch": epoch,
            "train_loss": round(float(train_loss), 4),
            "train_accuracy": round(float(train_acc), 4),
            "val_loss": round(float(val_loss), 4),
            "val_accuracy": round(float(val_acc), 4),
            "val_macro_f1": round(float(val_f1), 4),
            "val_qwk_kappa": round(float(val_qwk), 4),
            "val_ece_error": round(float(val_ece), 4),
            "learning_rate": float(lr),
            "epoch_time_sec": round(float(epoch_time), 2)
        }
        self.history.append(record)

        # Write line to CSV immediately (flush to disk)
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                ts, epoch, record["train_loss"], record["train_accuracy"],
                record["val_loss"], record["val_accuracy"], record["val_macro_f1"],
                record["val_qwk_kappa"], record["val_ece_error"], record["learning_rate"],
                record["epoch_time_sec"]
            ])

    def finalize(self, confusion_matrix=None, extra_metadata=None):
        """Save JSON summary and human-readable Markdown thesis report."""
        if not self.history:
            return

        df_hist = pd.DataFrame(self.history)
        best_epoch_idx = df_hist['val_qwk_kappa'].idxmax()
        best_row = df_hist.loc[best_epoch_idx]

        summary = {
            "experiment_name": self.experiment_name,
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_epochs_trained": len(df_hist),
            "best_epoch": int(best_row['epoch']),
            "best_val_accuracy": float(best_row['val_accuracy']),
            "best_val_macro_f1": float(best_row['val_macro_f1']),
            "best_val_qwk_kappa": float(best_row['val_qwk_kappa']),
            "best_val_ece_error": float(best_row['val_ece_error']),
            "epoch_history_csv": self.csv_path
        }

        if confusion_matrix is not None:
            summary["confusion_matrix_5x5"] = np.array(confusion_matrix).tolist()

        if extra_metadata is not None:
            summary["metadata"] = extra_metadata

        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        # Write Markdown Report for copy-pasting into LaTeX Thesis
        lines = [
            f"# 📊 Experiment Summary: {self.experiment_name}",
            f"**Completed At:** `{summary['completed_at']}`  ",
            f"**CSV History Log:** `{self.csv_path}`  ",
            "",
            "---",
            "",
            "## 🏆 Best Epoch Metrics (Epoch " + str(summary['best_epoch']) + ")",
            f"* **Top-1 Accuracy:** `{summary['best_val_accuracy'] * 100:.2f}%`",
            f"* **Macro F1 Score:** `{summary['best_val_macro_f1']:.4f}`",
            f"* **QWK Kappa Agreement:** `{summary['best_val_qwk_kappa']:.4f}`",
            f"* **Expected Calibration Error (ECE):** `{summary['best_val_ece_error']:.4f}`",
            "",
            "---",
            "",
            "## 📈 Epoch History Log (Sample)",
            "",
            "| Epoch | Train Loss | Train Acc | Val Acc | Val F1 | Val QWK | Val ECE | Time (s) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for _, r in df_hist.tail(10).iterrows():
            lines.append(f"| `{int(r['epoch']):02d}` | `{r['train_loss']:.4f}` | `{r['train_accuracy']*100:.1f}%` | `{r['val_accuracy']*100:.1f}%` | `{r['val_macro_f1']:.4f}` | `{r['val_qwk_kappa']:.4f}` | `{r['val_ece_error']:.4f}` | `{r['epoch_time_sec']:.1f}s` |")

        with open(self.md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"\n[LOGGER] Experiment history flushed to disk cleanly:")
        print(f"   - Epoch History CSV : {self.csv_path}")
        print(f"   - Metrics JSON      : {self.json_path}")
        print(f"   - Summary MD        : {self.md_path}")
