# Nio Models v0.4.0 — NioRay Standard and Dev

NioRay is fine-tuned from `Qwen/Qwen2.5-Coder-0.5B-Instruct` and exported as Q4_K_M GGUF for local inference.

## Corrected specifications and tokenizer packaging

| Variant | Parameters | Vocabulary | File size | External tokenizer |
| --- | ---: | ---: | ---: | --- |
| Standard | 494,032,768 | 151,936 | 397,807,552 bytes (379.38 MiB) | `tokenizer.json` |
| Dev | 386,570,112 | 32,000 | 278,780,480 bytes (265.87 MiB) | `nio-ray-dev-tokenizer.json` |

Dev removes 107,462,656 parameters and reduces artifact size by about 30%. It retains the first 31,978 BPE tokens by original ID and remaps 22 special tokens. The vocabulary was not selected using a developer corpus. Coding quality and token inflation have not yet been benchmarked.

**Packaging correction (2026-10-21):** `nio-ray-dev-tokenizer.json` is added for external-tokenizer runtimes, including the NioXS Candle loader. Do not pair Dev with Standard's `tokenizer.json`. Their ChatML end-token IDs differ: 31980 (Dev) versus 151645 (Standard). GGUF-native runtimes can use the tokenizer embedded in each model. Existing model weights and the Standard tokenizer are unchanged.

## Performance and integration status

Previous claims of ~320M Dev parameters, sub-5ms CPU TTFT, 180–220+ tok/s CPU throughput, under-160MB resident RAM, and whole-model L3-cache residency are corrected or withdrawn. Latency, throughput, and resident memory require reproducible measurements with named hardware, prompt lengths, warm/cold conditions, and runtime settings. File size is not resident memory. No measured daily-task coverage or cloud-token-savings percentage is available.

Training examples use `<nio_db>` and `<nio_js>` delegation tags. The host must implement interception, execution, and result feedback; standalone Candle generation does not execute these tags. Tool use does not guarantee generated-code syntax, types, or correctness.

## Installation for the corrected NioXS Candle loader

```bash
mkdir -p models
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.4.0/nio-ray-dev.Q4_K_M.gguf -o models/nio-ray-dev.Q4_K_M.gguf
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.4.0/nio-ray-dev-tokenizer.json -o models/nio-ray-dev-tokenizer.json
export NIOXS_RAY_MODEL="$PWD/models/nio-ray-dev.Q4_K_M.gguf"
export NIOXS_TOKENIZER="$PWD/models/nio-ray-dev-tokenizer.json"
```

Use a NioXS build that validates model/tokenizer compatibility. These environment variables select the pair; they do not add variant support to older CLI commands or configure NioAI automatically.

Prompt format: ChatML (`<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n`).

## SHA-256 verification

- `nio-ray.Q4_K_M.gguf` (397,807,552 bytes): `f52f5bc4f933eb6455d852b1de6316c9086c03fe676cbb1432dde939365494e1`
- `nio-ray-dev.Q4_K_M.gguf` (278,780,480 bytes): `e207e6a72807628d9034e800ace5180170e56a3bf54580170e2124aed146aa04`
- `tokenizer.json` (7,031,645 bytes): `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`
- `nio-ray-dev-tokenizer.json` (1,297,635 bytes): `c8a034fb2f7ad2484fc3010a73152fade6d48372ae322745fbf2c71e064effb1`

## Validation

The local files were matched to the published model and Standard-tokenizer SHA-256 hashes. The new Dev tokenizer was checked against every GGUF vocabulary entry and ordered BPE merge, with ChatML special-token checks and Unicode round trips. This verifies packaging compatibility; it is not an inference-quality or performance benchmark.
