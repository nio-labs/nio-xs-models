# 🐍 Viper 2.0 (100M) — Google Colab Training Guide

This directory contains the training pipeline for **Viper 2.0 (Exact 100,000,000 Parameters)** on Google Colab with a free **T4 GPU** runtime.

---

### Step-by-Step Training Instructions

1. Open [Google Colab](https://colab.research.google.com).
2. Click **File** -> **Upload notebook** and upload [`Viper2_Training.ipynb`](Viper2_Training.ipynb).
3. Ensure GPU acceleration is enabled:
   * **Runtime** -> **Change runtime type** -> Select **T4 GPU** -> Click **Save**.
4. Run all cells sequentially (**Runtime** -> **Run all** or `Ctrl + F9`):
   * Verifies GPU availability (`nvidia-smi`).
   * Clones `nio-xs-models` repository and validates the **exact 100M parameter invariant**.
   * Generates 250,000 synthetic curriculum samples covering multi-stage UNIX pipelines, DevOps tools (`kubectl`, `docker compose`, `terraform`), and Windows PowerShell cmdlets.
   * Trains the dedicated 17,451 vocabulary BPE tokenizer.
   * Trains Viper 2.0 across 3 epochs using mixed-precision AdamW.
   * Quantizes the final model to `viper-2.Q4_0.gguf` (~56.8 MB).
   * Automatically triggers browser download of `viper-2.Q4_0.gguf` and `viper-2-tokenizer.json`.
