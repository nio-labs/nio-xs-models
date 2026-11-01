# 🦈 Manta (494M) — Systems Guru & DAG Task Architect (`v-µLM Vector`)

**Manta** is Nio's production-certified systems architect, trade-off analyzer, and execution DAG planner. Operating within **< 85 MB post-turn idle resident RAM** (146.7 MB peak startup), Manta powers all 21 NioGuru personas and generates verified `<manta_plan>` orchestration graphs with strict Zero-Code invariants.

Manta forms **Tier 2** of the **Nio Companion Trinity**:
1. **Tier 1 (Ambient Desk-mate)**: Skate (135M, < 35 MB RAM, low latency, daily conversational companion)
2. **Tier 2 (Systems Architect & DAG Planner)**: Manta (494M, < 85 MB RAM, system trade-offs, RFCs, `<manta_plan>` DAGs)
3. **Tier 3 (Flagship Companion)**: 1.5B (DeepSeek-R1 / Mistral Large 2 / Phi-4 distilled, < 260 MB ultra-low / < 680 MB desktop, deep reasoning)

---

## 🏛️ Architectural Specifications

| Specification | Value | Technical Detail |
|---|:---:|---|
| **Parameter Count** | **`494,032,768` (~494M)** | Qwen2.5-0.5B backbone |
| **Transformer Layers ($L$)** | **24** | RMSNorm + Attention + SwiGLU MLP |
| **Hidden Dimension ($d$)** | **896** | Clean AVX2 / SIMD alignment |
| **Intermediate Dimension ($d_{ff}$)** | **4,864** | SwiGLU feedforward expansion |
| **Attention Configuration** | **GQA 14/2** | 14 Query heads, 2 Key/Value heads |
| **Vocabulary Size ($V$)** | **151,643** | Unpadded clean Byte-Level BPE |
| **Quantization Scheme** | **`IQ3_XXS` Vector Codebooks** | 32-chunk `llama-imatrix` importance matrix |
| **Binary Disk Footprint** | **317.92 MB** (`333,360,320 bytes`) | Single unified `manta.vmicrolm-vector.gguf` |
| **Tokenizer Footprint** | **13.89 MB** (`14,569,356 bytes`) | Single unified `manta-tokenizer.json` |
| **Post-Turn Idle RAM** | **76.03 MB – 78.14 MB** | Measured post-generation VmRSS (< 85 MB ceiling) |
| **Startup Peak RAM** | **146.74 MB** | Peak VmHWM during initialization (< 200 MB budget) |

---

## 🎯 Key Invariants & Features

1. **Production Gold Fine-Tuning**: Trained on `manta_production_gold_corpus.jsonl` (2,449 turns, 100% tag-balanced `<manta_plan id="...">` XML DAGs, 50x weighted production architecture exemplars).
2. **Zero Markdown Badge Glitches**: Broken markdown image badges (`[![...](...)]`) and cyclic bracket loops are completely eradicated.
3. **Strict Zero-Code Systems Architect Invariant**: Declares and strictly holds an architectural persona; cleanly defers raw code generation to downstream coding models (Cuda/Fin) while emitting comprehensive system trade-offs and plans.
4. **Natural EOS Termination**: 100% natural termination (`tok_id=151645`) across frontend rendering, code delegation, and distributed consensus scenarios.
5. **Structured DAG Orchestration**: Generates machine-parseable `<manta_plan id="...">` XML blocks with `<step id="..." priority="...">` and `<risk level="...">` tags parsed natively by `nio-manta-runtime`.

---

## 📦 Certified Binary Assets

| Asset Name | Format | Size | SHA-256 Checksum |
|---|:---:|:---:|---|
| `manta.vmicrolm-vector.gguf` | GGUF IQ3_XXS | 317.92 MB | `fa981bab81c7cb32a7072dfd193f1e03f988eb800d7e6773a03b69c861d452a5` |
| `manta-tokenizer.json` | JSON | 13.89 MB | `ade71ec5118be2cdd8aef3a7dcd417c51fa7e76b3e164adb339f446b42e97bc8` |

> Note: Large binary assets (`*.gguf`) are distributed via [GitHub Releases](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.2.7) and are not checked directly into git tree tracking.

---

## 💻 Quickstart & CLI Usage

### Download Assets via CLI
```bash
# Pull and cache verified Manta weights
nioxs pull manta
```

### Systems Architecture Triage
```bash
nioxs manta --persona architect "Design an event-driven CQRS pipeline with Raft consensus in Rust"
```

### DAG Task Planning
```bash
nioxs manta "Plan migration of our SQLite backend to high-throughput WAL mode with automated backups"
```

### Native Execution via ast-micro-engine
```bash
ast-micro-engine \
  models/nio-manta/manta.vmicrolm-vector.gguf \
  models/nio-manta/manta-tokenizer.json \
  --prompt "Compare SSR vs SSG for high-frequency financial dashboards"
```
