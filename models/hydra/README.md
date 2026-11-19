# 🐉 Nio Hydra Sovereign Dynasty & 0.5B + 14B Trinity Council

This directory contains the manifest, configuration, and architectural definitions for the **Nio Hydra** sovereign vMicroLM-Council dynasty powered by the **0.5B + 14B Trinity Architecture**.

---

## 🏛️ Sovereign 3-Chair Trinity Architecture

```
User Prompt
    │
    ▼
[Chair A: Sovereign Arbiter & Triage] (anchor-000-chair)
    │  Deliberates in <think> with invariant triage, emits:
    │  `@council(head=NNN)`
    ▼
[Chair B: Domain Specialist] (anchor-001 through anchor-041)
    │  ⚡ In-process LoRA head hot-swap (< 60 ms cold, < 1 ms warm LRU)
    │  Emits zero-allocation, compilable code
    ▼
[Chair C: Invariant Verifier & Auditor] (anchor-042-chair-c-critic)
    │  ⚡ Hot-swaps in < 50 ms
    │  Conducts formal audit on memory safety, concurrency, and data race invariants
    ▼
Client Response Stream
```

---

## 📦 Core Model Binaries

| Model Artifact | Base Arch | Quantization | Size | Purpose |
|---|---|:---:|:---:|---|
| **`hydra-anchor-0.5b.q4km.gguf`** | Qwen-Coder-0.5B (24L Unpruned) | `Q4_K_M` | 380 MB | Full 24-layer sovereign base anchor for triage & polymath synthesis |
| **`hydra-kernel-0.5b.q4km.gguf`** | Qwen-Coder-0.5B (24L Unpruned) | `Q4_K_M` | 380 MB | SFT-aligned kernel emitting `<think>` formal invariants & systems code |

---

## 🧠 Sovereign Anchor Fleet (43 Calibrated 24-Layer Adapters)

Each anchor is a calibrated 24-layer low-rank adapter (Rank 32 $\rightarrow$ 12 factored SVD + Scaled FP8 E4M3 + LZ4 compression) requiring **~6.33 MB** on disk, hot-swappable in-process in under **50 ms** while the 0.5B base anchor stays resident in RAM.

- **Chair A (#000):** `anchor-000-chair` — Meta-Coordination & Invariant Triage Arbiter
- **Chairs B (#001–#041):** 41 Specialist Anchors spanning Systems, Distributed, Web, ML, and Cloud
- **Chair C (#042):** `anchor-042-chair-c-critic` — Invariant Verifier & Formal Code Auditor

---

## ⚡ Execution & Router

Run Hydra directly with automatic 3-Chair routing and verification:

```bash
# Systems / Lock-free (routes to Chair B #001 / #004 with Chair C Invariant Verification)
nioxs hydra "Implement an SPSC ring buffer in Zig with comptime"

# Kernel / eBPF (routes to Chair B #005)
nioxs hydra "Write a Linux XDP packet filter in Rust aya"

# Vector SIMD (routes to Chair B #006)
nioxs hydra "Vectorize dot product using AVX2 SIMD intrinsics"
```
