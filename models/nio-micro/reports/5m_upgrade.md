# Exact 5M upgrade: first candidate

Historical binary candidate. See [the contextual fix report](contextual_accuracy_fix.md)
for the subsequent three-way candidate and its current limitations.

Implemented and trained a binary developer-classification candidate with exactly
**5,000,000 trainable parameters**. The 50-domain catalog and broader three-way
decision redesign are deferred. Existing root-level 3.5M artifacts were not
overwritten by this upgrade.

## Architecture

Four bidirectional encoder layers, hidden dimension 224, four attention heads,
feed-forward dimension 1,304, 8,000 embedding entries, and score hidden dimension
238 with no final output bias. Decision and sentiment heads remain binary.

| Component | Parameters |
|---|---:|
| Embedding | 1,792,000 |
| Encoder | 3,152,864 |
| Final normalization | 448 |
| Decision and sentiment heads | 900 |
| Score head | 53,788 |
| Total | 5,000,000 |

## Data and training

The existing 17,500 source rows contain 1,563 distinct texts from 180 base snippets.
Preparation deduplicates texts, averages duplicate score labels, and groups known
contextual wrappers with their underlying snippet before splitting:

| Split | Texts | Base-snippet groups |
|---|---:|---:|
| Train | 1,095 | 126 |
| Validation | 230 | 27 |
| Test | 238 | 27 |

No texts or base-snippet groups overlap between splits. Broader semantic similarity
is not audited, so these are not guaranteed independent semantic scenarios.
The new tokenizer is trained only on the training split and has 1,434 tokens;
the embedding retains 8,000 entries. Sentiment remains coupled to decision in
these source labels. No new finance, banking, or general workflow dataset was
introduced in this first architecture upgrade.

Training ran three epochs with seed 42 and selected epoch 2 using validation loss.
Training time was 32.1 seconds on this CPU. This small deduplicated run is not the
previously proposed 50,000-example training experiment.

## Results

- Held-out developer test: **163/238 correct (68.49%)**.
- False approvals: **44 of 99 reject-labeled examples**.
- False rejections: **31 of 139 approve-labeled examples**.
- Held-out score MAE: **0.253**.
- Previous developer regression prompts: **14/20** matched expected decisions.
- Previous workflow regression prompts: **11/20** matched expected decisions.

The regression prompts were previously inspected, and some developer prompts are
in the new training split. They are not an unseen benchmark. Training data and
tokenizer changed alongside architecture, so these results do not isolate the
effect of parameter count or prove improvement over the 3.5M model.

Confidence is uncalibrated. The high false-approval rate makes this an experimental
candidate rather than a production policy gate.

## Artifacts and verification

Candidate artifacts are in `models/5m/`: `nio_micro.pt`, `nio_micro.onnx`,
`tokenizer.json`, `metadata.json`, `training_report.json`, `export_report.json`,
and `regression_report.json`. Original data files remain unchanged; derived
splits are in `data/5m/` and are ignored by git.

Five automated tests pass, covering exact parameter count, forward/backward
behavior, scenario separation, reproducible preparation, conflicting labels,
and checkpoint architecture restoration. Export passes ONNX checker and numerical
agreement with PyTorch at lengths 1, 16, 64, 128, and 256, including padding and
batch sizes one and two. The inference CLI was exercised and rejects overlong
candidate inputs instead of silently truncating them.

Warm ONNX inference averaged **5.54 ms** over 200 runs at batch size one and
sequence length 64 with four CPU threads. This excludes tokenizer and startup
time. The ONNX artifact is approximately 19.67 MiB. The existing Rust CLI is a
keyword-based placeholder and does not run this ONNX model.

```bash
python scripts/infer.py --models-dir models/5m "git status"
```

The next quality improvement is diverse reviewed examples and independent labels,
followed by calibration and a comparison against a baseline trained on the same
repaired split. The larger parameter count alone has not resolved the failures.
