# 🐉 Nio Hydra Sovereign Dynasty & vMicroLM-Council

This directory contains the manifest, configuration, and architectural definitions for the **Nio Hydra** sovereign vMicroLM-Council dynasty.

---

## 🏛️ Dynasty Tiers & Specifications

| Tier | Council Heads | Knowledge Surface | Target Storage | Target Hardware | Engine |
|---|:---:|:---:|:---:|:---:|:---:|
| **🐉 Hydra (Standard)** | 1,000 | **~320 Billion** | **~3.0 GB** | Raspberry Pi 5 / Jetson / CPU / GTX 1660 | `nioxs hydra` |
| **👑 Hydra Max (Enterprise)** | 6,000 | **~2.412 Trillion** | **~16.8 GB** | M-Series Mac / 16GB–32GB Workstation | `nioxs hydra-max` |
| **🌌 Hydra Ultra (Apex Sovereign)** | 25,000 | **~10.0 Trillion** | **~70.0 GB** (< 100 GB) | High-Density NVMe Storage Appliances | `nioxs hydra-ultra` |

---

## 📦 Core Model Binaries (Base Anchor & SFT Kernel)

| Model Artifact | Base Arch | Quantization | Size | SHA-256 Checksum | Purpose |
|---|---|:---:|:---:|---|---|
| **`hydra-anchor-180m.q4km.gguf`** | Qwen-Coder-180M (10L Sliced) | `Q4_K_M` | 242 MB | `cb5c0b050b4cb68712d54a8c47e65b8844bda868e8134c0c18bd86924337216e` | Base Council anchor weights for hot-swapping specialist heads |
| **`hydra-kernel-180m.q4km.gguf`** | Qwen-Coder-180M (10L Sliced) | `Q4_K_M` | 242 MB | `f177c73a75219c875dff160b8381e821cfb9565e714e9907e759d4469adf912d` | SFT-aligned kernel emitting `<think>` formal invariants & lock-free POSIX code |

---

## 🧠 Sovereign Specialist Heads (`vMicroLM-Council`)

Each specialist head is a focused LoRA adapter (Rank 16, Alpha 32, Target: all linear projections) requiring only **~28 MB** storage and hot-swappable in under **10ms**.

### Active Trained Heads

1. **`head-001-atomic-concurrency`**:
   - **Target**: Lock-free atomic data structures (SPSC/MPMC rings, hazard pointers, seq-locks)
   - **Languages**: Rust (`core::sync::atomic`), Zig (`std.atomic`), freestanding C
   - **Training**: Kaggle Tesla T4 GPU (Batch Phase 2)
   - **Adapter Package**: `head-001-atomic-concurrency.tar.gz` (26 MB compressed, SHA-256: `bafe0f7eb5d935bf17f135a869ee8efe029086090345d68c32809246d53fd1f5`)

2. **`head-002-backend-axum-tokio`**:
   - **Target**: High-throughput async web services with Axum, Tokio, zero-copy JSON/Bytes, connection pooling
   - **Languages**: Rust
   - **Training**: Google Colab CLI on Tesla T4 GPU (60 steps, 69.9s training time)
   - **Adapter Package**: `head-002-backend-axum-tokio.tar.gz` (26 MB compressed, SHA-256: `ebff46a9997572e56a914b3848078dfed6e9f3d80d42f3d9fc9d8021da0ce0ee`)

---

## ⚡ Execution

Run freestanding Hydra models directly using `nioxs`:

```bash
# Pull model artifacts
nioxs pull hydra
nioxs pull hydra-kernel

# Interactive generation
nioxs hydra-kernel -n 120 "Write a lock-free ring buffer in Rust"
```
