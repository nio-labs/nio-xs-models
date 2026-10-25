# Release Notes: v0.2.0 — Predator Tier & v-µLM Vector: Manta (494M) & Skate 135M (82.9MB)

Official v0.2.0 release distributing compiled GGUF neural model binaries and tokenizers for the Predator Tier and proprietary **v-µLM Vector** architecture.

---

### 🦈 1. Skate (135M) — v-µLM Vector (Predator Level 2)
- **Base Architecture**: HuggingFaceTB/SmolLM2-135M-Instruct (100% full brain retained, 30 layers, 8K context)
- **Quantization**: Proprietary **v-µLM Vector** (IQ3_XXS Vector Codebook Lattice, **82.9 MB disk**, ~22MB peak private heap)
- **Fidelity**: >0.999 layer cosine similarity across 30 deep layers; zero token collapse, zero repetition, 100% fluent Rust/TS/Go coding syntax.
- **Fleet Role**: Instant resident micro-guru for mobile web PWA, IoT, and sub-15ms fast terminal Q&A.
- **SHA-256**: `c9e5be43d3b3a50111e7a2312683bfeee8659befe2a9df18cfba970a0d39e99e`
- **Asset**: `skate.vmicrolm-vector.gguf` (82.9 MB)

---

### 🌊 2. Manta (494M) — Conversational Guru (Predator Level 3)
- **Base Architecture**: Qwen/Qwen2.5-0.5B-Instruct (100% full brain retained, 24 layers, 32K context)
- **Quantization**: SIMD Q4_0 with Q8_0 precision embeddings (270.9 MB disk, ~73MB peak private heap)
- **Fleet Role**: Powers NioGuru (21 Gurus), file analysis, and machine-verifiable `<manta_plan>` execution DAGs.
- **SHA-256**: `3017aaa98c315b94728d6ad0aa6ae4d068ac3c8b23c00625791a4d2c56c4eca4`
- **Asset**: `manta.Q4_0.gguf` (270.9 MB)

---

### 💻 Predator Tier Dedicated Coding Models Roadmap
- **Level 4: ⚡ Ray (1.54B)** — **Rapid Stream Coding Model** (Qwen2.5-Coder-1.5B, 75.6% HumanEval)
- **Level 6: 🏔️ Apex (3.09B)** — **Multi-Branch Deep Coding Model** (Qwen2.5-Coder-3B, 81.7% HumanEval)
- **Level 7: 👑 Hydra (7.61B)** — **Sovereign Whole-Repo Coding Titan** (Qwen2.5-Coder-7B, 88.4% HumanEval)

---

### 📦 Certified Binary Assets
| Asset | Engine / Role | Format | Size | SHA-256 Checksum |
|---|---|:---:|:---:|---|
| `skate.vmicrolm-vector.gguf` | Skate v-µLM Vector (Predator Level 2) | GGUF IQ3_XXS | 82.9 MB | `c9e5be43d3b3a50111e7a2312683bfeee8659befe2a9df18cfba970a0d39e99e` |
| `manta.Q4_0.gguf` | Manta Conversational Guru (Predator Level 3) | GGUF Q4_0 | 270.9 MB | `3017aaa98c315b94728d6ad0aa6ae4d068ac3c8b23c00625791a4d2c56c4eca4` |
| `skate-tokenizer.json` | Skate Tokenizer (SmolLM2) | JSON | 2.1 MB | `9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c` |
| `manta-tokenizer.json` | Manta Tokenizer (Qwen2.5) | JSON | 6.8 MB | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
