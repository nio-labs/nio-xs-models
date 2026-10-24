# 🚀 Training NioMini on Google Colab

This directory provides Google Colab integration for training the **NioMini** (`7,100,000` parameter) pre-emptive defect forecaster.

---

## ⚡ Quick Start: 1-Click Google Colab Training

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nio-labs/nio-xs-models/blob/main/models/nio-mini/colab/NioMini_Training.ipynb)

1. Open the notebook in Google Colab using the button above or upload [`NioMini_Training.ipynb`](./NioMini_Training.ipynb).
2. Ensure hardware accelerator is set to GPU:
   - **Runtime** -> **Change runtime type** -> select **T4 GPU** (available on free tier).
3. Run all cells (`Ctrl+F9` or **Runtime** -> **Run all**).
4. The notebook will:
   - Verify GPU acceleration.
   - Clone the monorepo and verify exact 7.1M parameter budget.
   - Synthesize AST-annotated code samples across all 5 defect categories:
     - `CLEAN`
     - `SYNTAX_ERROR`
     - `TYPE_MISMATCH`
     - `BORROW_CHECK_FAIL`
     - `TEST_REGRESSION`
   - Train for 5 epochs with AdamW + Cosine Annealing.
   - Validate classification and break prediction accuracy.
   - Export optimized `nio-mini.onnx` with dynamic axes.
   - Trigger direct browser download of `nio-mini.onnx`.

---

## 🛠 Command-Line Training Options

If executing via terminal / SSH inside a Colab instance:

```bash
python scripts/train.py \
    --samples 15000 \
    --epochs 5 \
    --batch-size 64 \
    --lr 3e-4 \
    --onnx-out /content/nio-mini.onnx
```

### Options:
- `--samples`: Number of synthetic and AST diff samples to generate (default: `10000`).
- `--epochs`: Number of training epochs (default: `5`).
- `--batch-size`: Batch size for DataLoader (default: `64`).
- `--lr`: Learning rate (default: `3e-4`).
- `--onnx-out`: Output path for the exported ONNX model.
- `--device`: Target device (`cuda` or `cpu`).
