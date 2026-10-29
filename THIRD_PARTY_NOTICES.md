# Third-party notices

This file records known third-party materials relevant to Nio model development.
The repository's own license is in [LICENSE](LICENSE); the licenses of third-party
materials remain applicable to those materials. Entries below do not assert that a
particular third-party model is included in every Nio release.

## Skate experiments

The following sources were used in the experimental Skate work recorded in the
`nio-ideas` workspace. The resulting experimental datasets are machine-screened
and unreviewed; this list does not establish the provenance of existing releases.

| Material | Role in the experiment | Declared license | Source |
| --- | --- | --- | --- |
| SmolLM2-135M-Instruct | Student base for an earlier Skate experiment | Apache 2.0 | [HuggingFaceTB/SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) |
| Qwen2.5-7B-Instruct | Teacher used to generate training examples | Apache 2.0 | [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) |
| Mistral-7B-Instruct-v0.3 | Teacher used to generate and rewrite training examples | Apache 2.0 | [mistralai/Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) |
| Vertex 0.6 200M Base | Student base for the current experimental Skate checkpoint | Apache 2.0 | [VertexResearch/Vertex-0.6-200M-Base](https://huggingface.co/VertexResearch/Vertex-0.6-200M-Base) |

| Granite 3.3 8B Instruct | Replacement teacher for the 2026-10-29 Skate experiment; revision `51dd4bc2ade4059a6bd87649d68aa11e4fb2529b` | Apache 2.0 | [IBM Granite model card](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct/tree/51dd4bc2ade4059a6bd87649d68aa11e4fb2529b) |

The [Apache License 2.0 text](LICENSES/Apache-2.0.txt) is included for reference.
Retain applicable upstream copyright and attribution notices and any relevant
upstream NOTICE content when distributing materials derived from these sources.

The Vertex checkpoint is experimental and has not been approved for a release.

## Model releases

This is not a complete inventory of the base models, datasets, tools, or other
dependencies used by Skate, Manta, Fin, Nemo, or other Nio models. Before a model
is distributed, its release maintainer must identify the actual inputs and their
licenses, retain applicable upstream notices, and include this file, the relevant
license texts, and a model-specific provenance and notices file in the distributed
package. Record the base model and revision, training datasets and provenance,
teachers where applicable, Nio's changes, and the resulting artifact hash. Review
upstream data licenses and terms separately; an Apache-labeled model does not by
itself establish the license status of every source used to train it.
