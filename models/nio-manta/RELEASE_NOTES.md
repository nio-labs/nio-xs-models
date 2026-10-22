# NioManta v0.5.1 — Mobile & Conversational Companion (AST-µLM)

`NioManta` (`nioxs::nio-manta`) is the mobile-friendly conversational companion and structured AST planner of the Nio MicroLM (µLM) fleet. Architected with 16 Transformer Layers and preserving the complete 151,936 multilingual vocabulary, NioManta is engineered specifically for natural pair-programming dialogues across multiple natural languages (English, Spanish, Chinese, Japanese, French, German) and deterministic multi-step AST plan generation (`<manta_plan>`, `<step>`) operating within `< 110 MB` peak RAM (69.32 MB working RAM on edge CPU).

---

## Technical Specifications

| Parameter | Specification |
| :--- | :--- |
| **Base Model Architecture** | **`Qwen/Qwen2.5-0.5B-Instruct`** (depth-sliced to 16 Transformer Layers) |
| **Active Parameters** | ~374.73 Million |
| **Hidden Dimension ($d$)** | 896 ($896 / 32 = 28$ blocks, 100% 32-byte SIMD clean block alignment) |
| **Vocabulary Size** | 151,936 tokens (Complete Multilingual Lexicon intact) |
| **Quantization Format** | GGUF `Q4_0` (`nio-manta-ast.Q4_0.gguf`) |
| **Engine Footprint** | Working RAM: ~69.32 MB \| Peak RAM: ~90.27 MB (< 110 MB budget) |
| **Target Runtime** | In-process native Rust Candle runtime (`crates/nio-manta-runtime`) |

---

## Output Protocols

### Multi-Step Structured AST Plan (`<manta_plan>`)
```xml
<manta_plan task="implement redis connection pooling in rust">
  <step order="1" action="add_dependency" crate="deadpool-redis" version="0.14" />
  <step order="2" action="create_module" path="src/pool.rs" />
  <step order="3" action="implement_helper" symbol="create_redis_pool" />
  <step order="4" action="verify" command="cargo check" />
</manta_plan>
```

---

## Release Assets & Cryptographic Checksums

| File | Size | Format | SHA-256 Checksum |
| :--- | :---: | :---: | :--- |
| **`nio-manta-ast.Q4_0.gguf`** | **271.76 MiB** (284,962,368 bytes) | GGUF (`Q4_0`) | `56be66f3628768f1f8a71e526da4e06e063554c8c8c50f7f205299d3671a91d2` |
| **`nio-manta-tokenizer.json`** | **6.71 MiB** (7,031,645 bytes) | JSON (BPE 151k) | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |

---

## Quickstart

```bash
cargo run --release --package nio-manta-runtime -- \
  --model models/nio-manta/nio-manta-ast.Q4_0.gguf \
  --tokenizer models/nio-manta/nio-manta-tokenizer.json \
  --prompt "Plan how to implement redis connection pooling in src/db.rs" --ast
```
