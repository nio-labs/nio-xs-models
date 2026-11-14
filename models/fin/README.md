# ⚡ Nio Fin Models (Phase 0 Pilot)

This directory contains the compiled GGUF model binaries for **Fin** (Grand-Master Apex Triumvirate, Tentacle 7 of Kraken).

---

## 📦 Model Artifacts & Specifications

| Model | Foundation | Quantization | Disk Size | Resident RAM Target | SHA-256 Checksum | Specialization |
|---|---|:---:|:---:|:---:|---|---|
| **`fin-sql.q4km.gguf`** | Manta (0.5B) | `Q4_K_M` | 380 MB | `< 460 MB` | `a2c1bc36ec8ceef39381a7162cb781f49d1c6127b38a666d7388a620354a5458` | Zero-alloc SQL transpiler, dialect translation (PostgreSQL, ClickHouse, DuckDB) |
| **`fin-kernel.q4km.gguf`** | Cheetah (1.5B) | `Q4_K_M` | 941 MB | `< 850 MB` | `3a1b7bd1d7da3279feae7e5a7c12bd99d7b7d9d4f6573f89fb79028a2ed83460` | Lock-free concurrency, zero-copy buffer kernels, OS/memory invariant verification |

---

## 🚀 Training Provenance
- **Environment**: Distributed Parallel Kaggle Batch Sessions (Dual Tesla T4 GPUs)
- **Methodology**: QLoRA (Rank 16, Alpha 32, FP16 Tensor Cores) with strict prompt loss masking
- **Compiler**: `llama.cpp` zero-copy quantization (`Q4_K_M`)
- **Cost**: $0.00
