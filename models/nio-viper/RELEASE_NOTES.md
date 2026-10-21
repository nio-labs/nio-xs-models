# NioViper v0.5.0 — Tactical Terminal Runtime (AST-µLM)

NioViper has 8 transformer layers and 32,000 vocabulary rows. The 96.31 MiB GGUF stores Q4_0 main matrices, a Q8_0 embedding, and F32 norms/biases. The runtime shares `nio-ray-runtime::AstMicroEngine` and provides tactical candidate selection and output-tag parsing.

## Measured footprint — Intel Core i7-8650U

2026-10-21, Linux/WSL2, four Rayon threads, CPU release build with `-C target-cpu=native`. One process handled 20 independent prompts with KV reset between prompts, a retained engine/mmap/mask cache, the fixed 129-token tactical candidate pool, natural EOS/EOT and up to 32 new tokens per prompt. The tested runtime uses a 4,096-token RoPE window, releases unused embedded GGUF tokenizer metadata, and trims the heap after initialization and each layer.

| Measurement on Intel Core i7-8650U | Observed value |
| --- | ---: |
| Initial process RSS | 17.39 MiB |
| Peak process RSS (`VmHWM`) across 20 prompts | **44.98 MiB** |
| Process RSS after prompt 20 | 28.11 MiB |
| Input length | 17–29 tokens |
| Generated tokens / nonempty outputs | 198 / 9 of 20 |
| Median prefill (excludes loading and sampling) | 846.8 ms |
| Aggregate decode decisions after first token | 5.62 tok/s |

Eleven prompts generated no tokens; the other nine generated 198 tokens in total. These are workload-specific i7-8650U observations. They supersede earlier memory figures for this runtime configuration; they do not revalidate the earlier Intel Core Ultra 5 measurements. Prefill is not TTFT. Nonempty output is not command correctness or structured-tag adherence. The session did not execute generated commands or test for memory leaks.

[Raw records, hashes and per-prompt memory](../nio-ray/benchmarks/2026-10-21-ast-session/REPORT.md) · [Reproduce](../nio-ray/benchmark/ast-session/README.md).

---

### 📦 Release Assets & Cryptographic Checksums

| File | Size | Format | SHA-256 Checksum |
| :--- | :---: | :---: | :--- |
| **`nio-viper-ast.Q4_0.gguf`** | **96.31 MiB** (100,984,640 bytes) | GGUF (`Q4_0`) | `2e7df31bbe90a39e33b363d24085c2d04d7df6519909f27387e8b55b6d36ed32` |
| **`nio-viper-tokenizer.json`** | **1.24 MiB** (1,297,635 bytes) | JSON (BPE 32k) | `c8a034fb2f7ad2484fc3010a73152fade6d48372ae322745fbf2c71e064effb1` |

---

## Quickstart

```bash
RUSTFLAGS='-C target-cpu=native' cargo run --release --package nio-viper-runtime -- \
  --model nio-viper-ast.Q4_0.gguf \
  --tokenizer nio-viper-tokenizer.json \
  --prompt "Kill whatever process is listening on port 3000" --ast
```
