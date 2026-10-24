# Proposal: NioMicro training repair and exact 5M parameter experiment

Status: the binary 5M upgrade and a subsequent contextual three-way candidate
are implemented; see [the contextual fix report](contextual_accuracy_fix.md).
The reviewed 50,000-example dataset and matched retrained 3.5M baseline below
remain proposed. The new contextual data is rule-generated and approval routing
remains disabled because calibration did not support a reliable cutoff.
Existing root-level 3.5M artifacts are preserved.

## Problem and evidence

- Current training data: 10,000 rows, only 308 unique texts.
- Current validation data: 1,500 rows; every validation text occurs in training.
- Decision and sentiment labels match in every training and validation row.
- The tokenizer has 1,193 tokens; the model reserves 8,000 embedding entries.
- Developer prompt smoke test: 14/20 expected decisions matched.
- Loan/credit and project management smoke test: 8/20 matched, including three
  false approvals and nine false rejections.

These smoke tests use manually assigned labels and are not independent benchmarks.
The previous 100% validation decision accuracy does not establish generalization.

## Intended behavior

Evaluate a proposed action against explicit policy and supplied facts. Return
`approve`, `reject`, or `needs_review`. Missing facts, missing policy, contradictory
evidence, and cases requiring human judgment should have explicit review examples.
For lending, assess an action against the supplied policy rather than infer a
universal lending policy from a sentence.

Separate decision, sentiment, and score labels. Polite wording must not turn a
policy violation into an approval. Negative sentiment must not imply rejection.
The score is a separately annotated policy-satisfaction score under a documented
rubric, not a probability of correctness. Omit its training loss where evidence
cannot support a score. Retain binary sentiment for this iteration, annotate it
independently, and mask its loss for neutral or inapplicable examples.

## Architecture experiment

Both proposed variants use three decision classes, two sentiment classes,
sinusoidal position buffers, an 8,000-entry vocabulary, and a score head with
GELU, a biased output linear layer, and sigmoid. All parameters are used by the
forward computation; no unused parameter tensors are added to meet the count.

| Setting | Revised baseline | Candidate |
|---|---:|---:|
| Trainable parameters | 3,500,000 | 5,000,000 |
| Encoder layers | 4 | 4 |
| Hidden dimension | 192 | 224 |
| Attention heads | 4 | 4 |
| Feed-forward dimension | 844 | 1,304 |
| Score hidden dimension | 341 | 237 |
| Decision classes | 3 | 3 |
| Maximum sequence length | 256 | 256 |

These counts were verified by constructing the proposed modules in PyTorch.
The revised baseline differs from the current binary-decision checkpoint and
also requires retraining.

Candidate parameter breakdown:

| Component | Parameters |
|---|---:|
| Embedding | 1,792,000 |
| Encoder | 3,152,864 |
| Final normalization | 448 |
| Decision head | 675 |
| Sentiment head | 450 |
| Score head | 53,563 |
| Total | 5,000,000 |

## Dataset changes

Start with a target of 50,000 reviewed examples across developer/security,
loan/credit workflows, and project management. This is a starting experiment,
not a claim that this quantity guarantees adequate performance.

Each example records: domain, policy, facts, proposed action, decision label,
decision rationale, independent sentiment label when applicable, optional score,
source, scenario family, and paraphrase group. Serialize policy, facts, and action
consistently as model input. Retain rationale as annotation; the classifier does
not generate explanations.

Include ordinary approvals, violations, requests for clarification, negation,
mixed evidence, and paired cases whose outcomes change when one material fact
changes. Review labels against the supplied policy, including generated examples.
Do not enlarge the dataset by repeatedly sampling the existing snippets.

Assign scenario families to train/validation/test before generating paraphrases,
using an approximately 70/15/15 split. Keep all paraphrases, counterfactual pairs,
and related source examples together. Detect exact duplicates, conflicting
labels, and near duplicates across splits. Maintain coverage by domain and class.

Keep the existing 40 smoke-test prompts as a regression set and exclude their
scenario families from new training data. Create a separate unseen test set;
the 40 prompts have already influenced this proposal.

Retrain the tokenizer on training texts only, with broad natural language and code
coverage and an 8,000-token target. Check actual vocabulary size and token lengths.
Keep 8,000 embedding entries to preserve both exact model parameter budgets.

## Implementation sequence

1. Update `scripts/dataset_generator.py` and add dataset auditing and split tools.
   Produce a split report with class/domain counts, overlap checks, and token
   lengths before starting a training run.
2. Add explicit baseline/candidate configurations to `scripts/model.py` and test
   exact counts, output shapes, masking, and finite gradients.
3. Update `scripts/train_tokenizer.py` and `scripts/train.py` for the input schema,
   three decision classes, optional-label loss masks, fixed seeds, early stopping,
   and machine-readable training metrics.
4. Save weights, architecture, tokenizer identity, class mapping, seed, and training
   configuration together. Keep baseline and candidate artifacts in separate
   directories so the current checkpoint is preserved.
5. Train both sizes on the same repaired dataset and split with comparable training
   budgets. Measure training time rather than assume the old runtime still applies.
6. Fit confidence calibration on validation data, then evaluate the test set once.
   Report confidence calibration separately from classification performance.
7. Update `scripts/infer.py`, `scripts/export_onnx.py`, and the Rust consumer for
   the third decision class and matching input serialization. Never interpret
   `needs_review` as an approval. Use the same tokenizer truncation policy and
   sequence limit in training, evaluation, Python inference, and Rust inference;
   flag overlong inputs rather than silently discarding material policy facts.
8. Export each model and verify PyTorch/ONNX numerical agreement across batch
   sizes, padding patterns, and sequence lengths through 256. Run the regression
   prompts and publish both successes and failures.

## Evaluation and promotion

Report per-domain and per-class precision/recall, macro F1, confusion matrices,
false approvals among labeled violations, false rejections among labeled approvals,
and review frequency. Report score error only where score labels exist. Include
model memory and CPU latency under the same benchmark conditions.

Inspect the three workflow false approvals explicitly: hiding loan fees,
threatening staff into unpaid weekend work, and falsely reporting overdue
milestones as on track. Passing those examples alone is not sufficient.

Promote the 5M candidate only if it improves unseen-test results over the revised
3.5M baseline, does not increase false approvals, and meets the chosen CPU latency
budget. Define domain-specific acceptance thresholds before examining test
results. Otherwise retain the stronger baseline and investigate the failure cases.

## Compatibility

Three decision logits change the current inference contract. Version the new
artifact/schema and update Python and Rust label mapping together. Existing
checkpoints cannot be loaded as the proposed models without retraining. The
existing trained checkpoint, ONNX artifact, and validation reports remain useful
historical baselines but are not the repaired model.
