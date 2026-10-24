# NioMicro compared with Jev and Laya

Reviewed 2026-10-15. This compares local evidence with primary documentation.
No Jev or Laya inference runs were performed for this report.

## Capability comparison

| Dimension | Current NioMicro | Jev | Laya English root checkpoint |
|---|---|---|---|
| Parameters | Exactly 3.5M; 5M is proposed | Not established in the sources reviewed | 421M reported |
| Interface | Text to fixed decision, sentiment, scalar score | State plus typed questions | State plus typed questions |
| Output flexibility | Labels fixed during training | Request-defined choice options and scoring rubrics | Request-defined options and typed questions |
| Deployment | Local ONNX; Python and Rust consumers | Hosted TypeSafe API | Downloadable Apache-2.0 weights and local SDK |
| Training foundation | Small encoder trained from scratch | Vendor describes a specialized architecture and RLCD | Pretrained ModernBERT-large plus a decision head |
| Calibration | Not fitted; wrong answers can have near-100% softmax confidence | Vendor describes calibrated decisions | Model card explicitly warns that shipped checkpoints need calibration |

Sources: [TypeSafe introduction](https://docs.typesafe.ai/introduction),
[TypeSafe launch article](https://typesafe.ai/blog/introducing-system-one-models-and-jev),
[Laya model card](https://huggingface.co/convaiinnovations/laya),
[Laya repository](https://github.com/NandhaKishorM/laya).
Laya has multiple checkpoints; the table identifies the English root checkpoint
rather than treating all versions as one model.

## What our measurements establish

NioMicro matched 14/20 manually labeled developer prompts and 8/20 loan/project
workflow prompts. The workflow test contained three false approvals and nine
false rejections. These small, selected sets do not estimate production accuracy.
The internal validation split is contaminated: every validation text also occurs
in training. The previous 100% result is not evidence of generalization.

Our exported model averaged about 3.93 ms over 200 warmed CPU inference runs at
batch size one and sequence length 64. That excludes tokenization, session startup,
and network time. It cannot be ranked against vendor GPU or hosted timings.

Jev and Laya have not been measured on these prompts. No accuracy winner is
established here. Typed output constraints also do not establish decision correctness.

## Implication for the proposed upgrade

The gap includes the training foundation and task interface, not just size.
Increasing from 3.5M to 5M with the current labels would still produce a classifier
with fixed labels. It would not implement arbitrary question answering or dynamic
choice scoring. A separate architecture and training experiment would be needed
for that goal.

The practical hypothesis to test is that NioMicro can be a compact local specialist
for a bounded, explicitly defined workflow. Broad general-purpose decision quality
is not demonstrated by our existing training or tests. Preserve the data repair
proposal and decide whether fixed-policy classification or dynamic typed questions
is the intended product before implementing the architecture upgrade.

## Proposed shared benchmark before retraining

1. Freeze 300 newly reviewed cases: 100 developer/security, 100 loan/credit workflow,
   and 100 project management. Include explicit policy, facts, and action, balanced
   approvals/rejections, and missing-information cases with a review outcome.
2. Give each backend the same substantive information and decision question. Pin
   versions and checkpoint revisions. Record formatting adapters and truncation.
3. Treat the current binary NioMicro model's inability to emit review as a measured
   limitation. Do not hide it by inventing a confidence threshold on the test set.
4. Report per-domain class metrics, false approvals, false rejections, review
   behavior, calibration, and complete disagreements against reviewed labels.
5. Measure local inference separately from end-to-end latency. Record warm/cold
   runs, hardware, input lengths, p50/p95, memory, and hosted cost where applicable.
6. Use our 40 previous prompts as a separate regression set, not the unseen test
   benchmark. Do not select training examples using the frozen test results.

Running the remaining backends requires a Jev API credential and a provisioned
Laya checkpoint/runtime. This report neither downloads weights nor calls a paid API.
