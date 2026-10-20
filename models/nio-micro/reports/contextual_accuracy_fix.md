# Contextual training and routing fix

Implemented, trained, and exported a separate **5,000,000-parameter** contextual
developer classifier in `models/5m-context/`. Earlier models remain in place.
The 50-domain catalog remains on hold.

## What changed

- Added a versioned policy and input contract: action, environment, authorization,
  target status, and optional feedback. Context must come from trusted application
  state; the model does not verify user permissions.
- Added a third decision, `needs_review`, while retaining exactly 5M parameters.
- Added permission/environment counterfactuals and independently varied tone.
  Neutral sentiment and unsupported score labels are excluded from their losses.
- Split complete action families into train, validation, calibration, and test.
  Tokenizer training uses training texts only. Text and family overlap are checked.
- Added class-balanced decision loss, early stopping on validation macro F1,
  temperature scaling, and a calibration-only approval-cutoff selection step.
- Added application guards for explicit denial and missing target/environment.
  Raw inputs without context return review. Raw model predictions, threshold-based
  routing, and application guards remain distinguishable in outputs and reports.
- Added transparent failure reasons and nullable confidence for routing decisions.
  A policy guard or review route does not invent a model-confidence value.

## Dataset and training

There are **8,640 rule-generated examples across 60 action families**:

| Split | Examples | Families |
|---|---:|---:|
| Train | 5,040 | 35 |
| Validation | 1,440 | 10 |
| Calibration | 720 | 5 |
| Test | 1,440 | 10 |

These are contextual and tone variants, not 8,640 independent workflows. Labels
come from auditable synthetic rules, not independent human review. Held-out
families share the same policy and input grammar. This does not establish broad
developer, arbitrary-policy, banking, or financial decision competence.

Training used seed 73, up to 12 epochs, and stopped after epoch 9. Epoch 6 had the
best validation macro F1 and was selected before calibration and test evaluation.
Training, calibration, and testing took approximately 33.2 minutes on this CPU.
The tokenizer has 1,004 actual entries against an 8,000-entry embedding capacity.

## Results on identical contextual test inputs

| Metric | Earlier binary 5M | New raw classifier | Configured application router |
|---|---:|---:|---:|
| Accuracy | 63.33% | 90.49% | 82.78% |
| Macro F1 | 0.259 | 0.866 | 0.565 |
| False approvals, including missing-information cases | 0 | 46 | 0 |
| Approvals of reject-labeled cases | 0 | 24 | 0 |
| Rejections of approve-labeled cases | 132 | 2 | 0 |
| Review rate | 0% | 31.46% | 44.72% |

The earlier binary model rejected every input and cannot represent review.
This is a matched-input comparison for the new fixed policy, not a comparison to
the earlier 68.5% result on a different dataset.

The new raw model correctly approved 115 of its 161 predicted approvals: only
**71.4% approval precision**. Overall accuracy hides this weakness.

## Important operational restriction

**Automatic approvals are disabled in this candidate.** Temperature scaling fit
T = 3.4613. No cutoff met the preconfigured requirement of at least 20 supported
approvals and no calibration false approvals, so the saved approval threshold is
1.000001. Every model approval is routed to review.

The router's zero false approvals is therefore a consequence of abstaining from
approval, not proof that the classifier can approve reliably. It automatically
rejected 796 test examples and sent 644 to review, including all 132 true approval
cases. Those 796 rejections matched the synthetic labels; this is not a real-world
safety guarantee. Do not lower the cutoff using test results to manufacture a
better accuracy or automation figure.

## Additional stress cases

Twenty hand-authored cases were written before the training run completed. They
include known action families and are a regression/stress set, not an independent
benchmark. The raw classifier matched **13/20** labels; the application router
matched **9/20**, partly because expected approvals were sent to review.

Raw failures included a production directory deletion and paraphrases of public
API-secret exposure. Routing prevented approvals in these examples but did not
repair their underlying classification. These failures are retained in
`models/5m-context/comparison_report.json`; they are not silently relabeled or
added to training to improve the reported test score.

Tone invariance across the controlled test variants was 98.75% for raw decisions.
Sentiment classification matched the two fixed feedback phrases in the generator;
that is not an independent sentiment benchmark.

## Verification and artifacts

The exact parameter count and class dimensions are tested. Tests cover missing
labels, family separation, independent tone labels, policy counterfactuals,
explicit-denial guards, raw-input review, and fail-closed approval routing.
ONNX checker and numerical comparisons against PyTorch passed for sequence
lengths 1, 16, 64, 128, and 256 with multiple batch sizes and padding.

Warm ONNX inference averaged **6.62 ms** over 200 runs at batch one, length 64,
and four CPU threads. This excludes tokenization and session startup.

Files in `models/5m-context/` include weights, ONNX, tokenizer, metadata,
training report, export report, and comparison report. The original binary and
3.5M artifacts were not overwritten. The Rust CLI remains a keyword placeholder;
it does not run this model or implement its version-2 schema.

```bash
python scripts/infer.py "git status" --context '{"environment":"sandbox","authorization":"granted","target":"known"}'
```

This currently returns review when the approval gate applies. Consumers must
handle `needs_review` and null confidence/score/sentiment values.

## What remains before automatic approval

The training/evaluation defects and conservative routing are addressed, but
reliable automatic approval is **not achieved**. The next requirement is a
broader, independently reviewed corpus of actual deployment workflows, with
new wording and policies represented in separately frozen evaluations. Explicit
permissions and executable policy conditions should continue to be enforced in
code. Model output should assist interpretation, not override those constraints.
