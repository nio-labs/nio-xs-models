# NioMini — Pre-emptive Defect Forecaster (7.1M)

`NioMini` is a pre-execution quality and defect prediction MicroLM (µLM). It evaluates code diffs and AST feature projections to forecast build breakages, syntax errors, borrow checker conflicts, and test regressions before running full CI suites.

---

## Model Specifications

- **Parameters:** Exactly **7,100,000**
- **Architecture:** 6-Layer Transformer Encoder with Graph AST Projection
- **Inputs:**
  - `input_ids: int64[batch_size, seq_len]`
  - `ast_features: float32[batch_size, seq_len, 32]`
- **Outputs:**
  - `will_break: float32[batch_size, 1]` (Binary break verdict)
  - `defect_category: float32[batch_size, 5]` (5 defect classes)
  - `risk_score: float32[batch_size, 1]` (Calibrated continuous risk)
- **Defect Categories:**
  1. `CLEAN`
  2. `SYNTAX_ERROR`
  3. `TYPE_MISMATCH`
  4. `BORROW_CHECK_FAIL`
  5. `TEST_REGRESSION`

---

## Google Colab Training

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nio-labs/nio-xs-models/blob/main/models/nio-mini/colab/NioMini_Training.ipynb)

To train on a free GPU using Google Colab:
1. Open [`colab/NioMini_Training.ipynb`](colab/NioMini_Training.ipynb) in Colab.
2. Select **T4 GPU** runtime.
3. Run all cells to synthesize AST samples, train the 7.1M model, export to ONNX, and download.

Or run directly via command-line in Colab:
```bash
python scripts/train.py --samples 15000 --epochs 5 --batch-size 64 --onnx-out /content/nio-mini.onnx
```

---

## Inference

Run Python reference inference via ONNX:
```bash
python scripts/infer.py --model nio-mini.onnx --input "pub fn add(a: i32, b: i32) -> i32 { a + b }"
```

Or execute via the native Rust runtime:
```bash
cargo run -p nio-mini-runtime --bin nio-mini-cli "pub fn bad() { let a = &mut x; let b = &mut x; }"
```
