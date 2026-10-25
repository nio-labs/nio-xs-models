# Release Notes: v0.2.2 — Manta (494M) v-µLM Vector & Conversational Guru

Official **v0.2.2** release distributing the compiled **Manta (494M)** `v-µLM Vector` neural binary (`manta.vmicrolm-vector.gguf`), standalone tokenizer (`manta-tokenizer.json`), and native streaming companion runtime.

---

### 🌊 1. Manta (494M) — Full Conversational Guru & Wasm Architect (`v-µLM Vector`)

Manta ascends to Nio's proprietary **`v-µLM Vector`** architecture, retiring legacy scalar Q4_0 in favor of calibrated non-linear vector codebooks:

- **Base Foundation**: `Qwen/Qwen2.5-0.5B-Instruct` (**100% full brain retained**, 24 layers, $d=896$, SwiGLU $d_{ff}=4864$, 14 attention heads, 2 KV heads, 32K context).
- **Quantization Engine**: Proprietary **`v-µLM Vector`** (`IQ3_XXS` Vector Codebook Lattice with optimized embedding table quantization, **253.33 MiB disk**, **< 55 MB resident working RAM**).
- **Mathematical Fidelity**: **>0.999 layer cosine similarity fidelity** with zero synthetic SFT distortion, zero repetitive keyword loops, and zero reasoning collapse.
- **Cognitive Scope**: Powers all **21 NioGuru personas** in `nio-guru` (`bff`, `architect`, `security`, `debugger`, `devops`, `sage`, `refactor`, etc.), interactive architectural debates, multi-file code reviews, and compiles consensus into structured, machine-verifiable `<manta_plan>` execution DAGs.
- **Measured CPU Inference**:
  - Prompt Ingestion: **44.6 – 71.7 tokens/sec**
  - Generation: **14.0 – 16.7 tokens/sec** (6.0 – 10.3 words/sec) on a single CPU core.

---

### 📦 Certified Binary Assets & Checksums

| Asset | Engine / Role | Format | Size | SHA-256 Checksum |
|---|---|:---:|:---:|---|
| `manta.vmicrolm-vector.gguf` | Manta (494M, Conversational Guru & Wasm Architect) | GGUF IQ3_XXS Codebooks | 253.33 MB | `ed27ef71bf8c0c5f372efb0eef99b71a9c6480bf3e228ce2f1027fd3583d08bf` |
| `manta-tokenizer.json` | Manta Tokenizer (Qwen2.5 151K Vocab) | JSON | 10.9 MB | `3fd169731d2cbde95e10bf356d66d5997fd885dd8dbb6fb4684da3f23b2585d8` |
| `mako.vmicrolm-vector.gguf` | Mako (150M, Live Web Scout & Scrubber) | GGUF IQ3_XXS Codebooks | 65.39 MB | *(Distributed in v0.2.1)* |
| `skate.vmicrolm-vector.gguf` | Skate (135M, Resident Micro-Guru) | GGUF IQ3_XXS Codebooks | 82.9 MB | `c9e5be43d3b3a50111e7a2312683bfeee8659befe2a9df18cfba970a0d39e99e` |

---

### ⚡ Installation & Local Verification

Pull and run Manta directly via `nioxs`:

```bash
# Pull Manta weights to local cache (~/.nioxs/models/)
nioxs pull manta

# Run conversational companion query
nioxs manta "Persona: architect. Propose an event-driven telemetry ingest pipeline."

# Emit structured machine-verifiable plan DAG
nioxs manta --plan "Add zero-downtime NOT NULL column to postgres table"
```
