# 📦 Nio Models — Unified Release Notes & Changelog

Official release history and distribution registry for compiled neural binaries (`.gguf`, `.onnx`), tokenizers, and MCP runtime packages across the **Nio** and **NioXS** ecosystem.

---

## 📑 Table of Contents

- [v0.2.4 — Skate Ambient Conversational Companion & v-µLM Vector GGUF](#v024--skate-ambient-conversational-companion--v-µlm-vector-gguf)
- [v0.2.3 — Viper (100M) Multi-Dialect Neural Reflex & 61.69MB Q4_0 GGUF](#v023--viper-100m-multi-dialect-neural-reflex--6169mb-q4_0-gguf)
- [v0.2.2 — Manta (494M) v-µLM Vector & Conversational Guru](#v022--manta-494m-v-µlm-vector--conversational-guru)
- [v0.2.1 — Mako (150M) Live Web Scout & MCP Token Scrubber](#v021--mako-150m-live-web-scout--mcp-token-scrubber)
- [v0.2.0 — Predator Tier & v-µLM Vector: Manta (494M) & Skate (135M)](#v020--predator-tier--v-µlm-vector-manta-494m--skate-135m)
- [v0.1.0 — MicroLM (µLM) Core Production Suite & Localhost MCP Server](#v010--microlm-µlm-core-production-suite--localhost-mcp-server)

---

## v0.2.4 — Skate Ambient Conversational Companion & v-µLM Vector GGUF

Official **v0.2.4** release distributing the certified **Skate** ambient conversational companion engine (`skate.vmicrolm-vector.gguf`), dedicated conversational tokenizer (`skate-tokenizer.json`), and production companion runner harness.

### 🦈 1. Skate — Ambient Conversational Companion MicroLM (v-µLM Vector)

Skate provides dedicated, ultra-low latency conversational companionship, active listening, friendly banter, and daily check-ins with zero code bloat:

- **Target Footprint**: Quantized **`IQ3_XXS` Vector Codebooks GGUF** takes exactly **82.93 MB** on disk (< 100 MB ceiling met).
- **Peak RAM Envelope**: Resident peak memory under continuous multi-turn generation stays strictly within **< 28 MB** (`VmRSS`), suitable for always-on background daemons and mobile browser PWAs.
- **Inference Speed**: **215–235 tokens/sec** prompt evaluation, **40–43 tokens/sec** continuous streaming generation on standard CPU.
- **Zero-Code Deflection Invariant**: 100% clean deflection handoffs for compiler, AST, and coding queries directly to **Viper (100M)** and **Manta (494M)**.
- **Anti-Looping Stability**: **0.0% repetition loop rate** across 20-turn continuous conversational stress testing (`mut mut mut` and phrase echo loops completely eliminated).
- **Wellness & Safety Boundaries**: Validated empathetic perspective on burnout and work stress; warmly defers clinical and medical diagnoses to healthcare professionals.

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | SHA-256 Checksum | Target Hardware Peak RAM |
|---|---|:---:|:---:|---|:---:|
| `skate.vmicrolm-vector.gguf` | Skate (Ambient Conversational Companion) | GGUF IQ3_XXS | 82.93 MB | `cedbd01bce0a83882ac23d6c77e500b65a194286fea5ac62f416889c8f818588` | **< 28 MB** |
| `skate-tokenizer.json` | Skate Conversational Tokenizer | JSON | 2.10 MB | `9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c` | N/A |

### 🔬 20-Turn Multi-Turn Stress Benchmark Verification

Certified report archived at `scripts/skate_20turn_anti_loop_report.json`:
- **Total Turns Evaluated:** 20 sequential turns
- **Repetition Loop Rate:** **0.0%** (0 / 20 loops detected)
- **Code Bloat Violations:** **0.0%** (0 / 20 code emissions on technical queries)
- **Medical Safety Boundary:** **100% Passed** (Graceful healthcare deferral)
- **Production 1.0 Certification:** **VERIFIED & CERTIFIED**

---

## v0.2.3 — Viper (100M) Multi-Dialect Neural Reflex & 61.69MB Q4_0 GGUF

Official **v0.2.3** release distributing the retrained **Viper (100M)** tactical reflex engine (`viper.Q4_0.gguf`), dedicated trimmed developer vocabulary tokenizer (`viper-tokenizer.json`), and native multi-shell runtime.

### 🐍 1. Viper (100M) — Pure-Rust Multi-Shell Neural Dialect Reflex Engine

Viper achieves full zero-shot cross-platform terminal precision across POSIX, Windows, and modern shells:

- **Architecture Invariant**: Exactly **100,000,000 parameters** ($L=14$ layers, $d=800$, SwiGLU $d_{ff}=1,920$, GQA 10/2, tied embeddings).
- **Dedicated 17,451 Lexicon**: Pruned and trimmed developer-only Byte-Level BPE vocabulary (`viper-tokenizer.json`, **3.17 MB**), discarding extraneous multilingual tokens.
- **Physical Footprint**: Quantized **`Q4_0` GGUF** takes exactly **61.69 MB** on disk.
- **Peak RAM Envelope**: Resident peak memory under active query decoding stays strictly within **36 – 41 MB** (`VmHWM`), beating the < 50MB ceiling with margin to spare.
- **Multi-Dialect Prompt Conditioning**:
  - `[bash]`: POSIX pipelines, `lsof`, `fuser`, `xargs`, `systemd`, `awk`, `find`, `git`, `docker`, `kubectl`, `terraform`.
  - `[powershell]`: Native Windows object pipelines (`Get-Process`, `Stop-Process`, `Get-Service`, `Where-Object`, `Select-Object`, `Get-NetTCPConnection`).
  - `[fish]`: Fish subshells `(...)`, native command substitution, pattern searching.
  - `[zsh]`: Zsh glob qualifiers `**/*(...)`, recursive pattern matching.
- **Spider Search Hygiene**: Automatic noise filtering that appends clean build exclusions (`--exclude-dir={target,.git,node_modules,dist,.venv}`) to `grep` and path pruning to `find` / `Get-ChildItem`.
- **Destructive Clutch Guard**: Structured `<viper_alert level='warn'>` interception for high-impact filesystem operations (`rm -rf`, disk formatting, service kills).

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | SHA-256 Checksum | Target Hardware Peak RAM |
|---|---|:---:|:---:|---|:---:|
| `viper.Q4_0.gguf` | Viper (100M, Multi-Dialect Tactical Terminal Reflex) | GGUF Q4_0 | 61.69 MB | `45d9796b27728544af66c11d294b07e5a0fb241a310b3a93f54e26fb1ff1766e` | **40.32 MB** (< 50 MB) |
| `viper-tokenizer.json` | Viper Dedicated Developer Tokenizer (17,451 Vocab) | JSON | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` | N/A |

---

## v0.2.2 — Manta (494M) v-µLM Vector & Conversational Guru

Official **v0.2.2** release distributing the compiled **Manta (494M)** `v-µLM Vector` neural binary (`manta.vmicrolm-vector.gguf`), standalone tokenizer (`manta-tokenizer.json`), and native streaming companion runtime.

### 🌊 1. Manta (494M) — Full Conversational Guru & Wasm Architect (`v-µLM Vector`)

Manta ascends to Nio's proprietary **`v-µLM Vector`** architecture, retiring legacy scalar Q4_0 in favor of calibrated non-linear vector codebooks:

- **Base Foundation**: `Qwen/Qwen2.5-0.5B-Instruct` (**100% full brain retained**, 24 layers, $d=896$, SwiGLU $d_{ff}=4864$, 14 attention heads, 2 KV heads, 32K context).
- **Quantization Engine**: Proprietary **`v-µLM Vector`** (`IQ3_XXS` Vector Codebook Lattice with optimized embedding table quantization, **253.33 MiB disk**, **< 55 MB resident working RAM**).
- **Mathematical Fidelity**: **>0.999 layer cosine similarity fidelity** with zero synthetic SFT distortion, zero repetitive keyword loops, and zero reasoning collapse.
- **Cognitive Scope**: Powers all **21 NioGuru personas** in `nio-guru` (`bff`, `architect`, `security`, `debugger`, `devops`, `sage`, `refactor`, etc.), interactive architectural debates, multi-file code reviews, and compiles consensus into structured, machine-verifiable `<manta_plan>` execution DAGs.
- **Measured CPU Inference**:
  - Prompt Ingestion: **44.6 – 71.7 tokens/sec**
  - Generation: **14.0 – 16.7 tokens/sec** (6.0 – 10.3 words/sec) on a single CPU core.

### 📦 Certified Binary Assets & Checksums

| Asset | Engine / Role | Format | Size | SHA-256 Checksum |
|---|---|:---:|:---:|---|
| `manta.vmicrolm-vector.gguf` | Manta (494M, Conversational Guru & Wasm Architect) | GGUF IQ3_XXS Codebooks | 253.33 MB | `ed27ef71bf8c0c5f372efb0eef99b71a9c6480bf3e228ce2f1027fd3583d08bf` |
| `manta-tokenizer.json` | Manta Tokenizer (Qwen2.5 151K Vocab) | JSON | 10.9 MB | `3fd169731d2cbde95e10bf356d66d5997fd885dd8dbb6fb4684da3f23b2585d8` |

---

## v0.2.1 — Mako (150M) Live Web Scout & MCP Token Scrubber

Official **v0.2.1** release distributing the compiled **Mako (150M)** neural binary (`mako.vmicrolm-vector.gguf`), standalone tokenizer, and the first-class **MCP Web Scout** integration in `nioxs-mcp`.

### 🦈 1. Mako (150M) — Live Web Intelligence & Scraping Scout (`v-µLM Vector`)

- **Base Architecture**: `OuteAI/Lite-Mistral-150M-v2-Instruct` (100% full brain retained, 12 layers, $d=768$, 32K vocab, Apache 2.0).
- **Quantization Engine**: Proprietary **v-µLM Vector** (`IQ3_XXS` Vector Codebook Lattice, **65.39 MiB disk**, **~21.8 MB resident RAM**).
- **Throughput**: **207.4 – 227.6 tokens/sec** prompt ingestion; **17.7 – 30.7 tokens/sec** generation on single-core CPU.
- **Core Role**: Powers live web research in `nioxs-browser`, synthesizing surgical search operator queries and stripping 90%–99.6% of raw DOM noise before context injection.

### 🔌 2. Localhost Model Context Protocol (MCP) Web Scout Integration

Exposed directly via `nioxs mcp` over standard JSON-RPC 2.0:
- **`web_fetch` (DOM Noise Scrubber & Surgical Focus Extractor)**: Strips HTML overhead down to clean Markdown with optional surgical `focus` extraction (99.6% token reduction).
- **`mako_search` (Keyless Live Documentation Search)**: Generates surgical search operators and queries DuckDuckGo HTML endpoints with zero API keys required.

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | Target RAM |
|---|---|:---:|:---:|:---:|
| `mako.vmicrolm-vector.gguf` | Mako 150M (Live Web Scout & Scrubber) | GGUF IQ3_XXS Codebooks | 65.39 MB | < 22 MB |
| `mako-tokenizer.json` | Mako Tokenizer (Mistral 32K) | JSON | 1.8 MB | < 2 MB |

---

## v0.2.0 — Predator Tier & v-µLM Vector: Manta (494M) & Skate (135M)

Official **v0.2.0** release distributing compiled GGUF neural model binaries and tokenizers for the Predator Tier and proprietary **v-µLM Vector** architecture.

### 🦈 1. Skate (135M) — v-µLM Vector (Predator Level 2)
- **Base Architecture**: `HuggingFaceTB/SmolLM2-135M-Instruct` (100% full brain retained, 30 layers, 8K context).
- **Quantization**: Proprietary **v-µLM Vector** (`IQ3_XXS` Vector Codebook Lattice, **82.9 MB disk**, ~22MB peak private heap).
- **Fidelity**: >0.999 layer cosine similarity across 30 deep layers.

### 🌊 2. Manta (494M) — Conversational Guru (Predator Level 3)
- **Base Architecture**: `Qwen/Qwen2.5-0.5B-Instruct` (100% full brain retained, 24 layers, 32K context).
- **Quantization**: SIMD `Q4_0` with `Q8_0` precision embeddings (270.9 MB disk, ~73MB peak private heap).

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | SHA-256 Checksum |
|---|---|:---:|:---:|---|
| `skate.vmicrolm-vector.gguf` | Skate v-µLM Vector | GGUF IQ3_XXS | 82.9 MB | `c9e5be43d3b3a50111e7a2312683bfeee8659befe2a9df18cfba970a0d39e99e` |
| `manta.Q4_0.gguf` | Manta Conversational Guru | GGUF Q4_0 | 270.9 MB | `3017aaa98c315b94728d6ad0aa6ae4d068ac3c8b23c00625791a4d2c56c4eca4` |
| `skate-tokenizer.json` | Skate Tokenizer (SmolLM2) | JSON | 2.1 MB | `9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c` |
| `manta-tokenizer.json` | Manta Tokenizer (Qwen2.5) | JSON | 6.8 MB | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |

---

## v0.1.0 — MicroLM (µLM) Core Production Suite & Localhost MCP Server

Official **v0.1.0** release of the unified Micro Learning Model (µLM) production family and Localhost MCP Server.

```bash
# Instant One-Liner Installer
curl -fsSL https://nio-labs.github.io/nio-xs-models/install.sh | bash
```

### 🏛️ The Production MicroLM Fleet

1. **Viper (100M Tactical Terminal & DevOps Striker)**:
   - **100,000,000 parameter** locked pure-Rust AST-MicroLM tactical terminal striker.
   - **27.14 MB peak resident RAM (`VmHWM`)** on Linux.
   - **Sub-20µs Tactical AST Candidate Reflex** sampling.
   - 61.69 MB quantized `Q4_0` GGUF with dedicated 17,451 ByteLevel BPE vocabulary (`viper.Q4_0.gguf`).
   - Integrated Swiss Gear 2.0 with Destructive Safety Clutch and spider search hygiene.

2. **Nano (~0.5M Intent & Directive Router)**:
   - In-process Rust feature engine operating in **< 0.1ms**.
   - Intercepts zero-token directives (`--bash`, `--tools`, `--code`) and performs instant intent routing.

3. **Micro (5.0M Contextual Policy Arbiter)**:
   - 4-layer bidirectional Transformer operating in **< 5ms** as an autonomous policy gate.
   - Partitioned into independent 5M clusters (`sec`, `infra`, `base`) approving/rejecting terminal mutations.

4. **Mask (1.1M Real-Time Stream Redactor)**:
   - 2-layer Byte-Level Convolutional Transformer operating in **< 0.2ms**.
   - Real-time secret, API key, and sensitive PII redactor embedded directly in terminal streams and MCP gateways.

5. **Mini (7.1M Pre-Emptive Defect Forecaster)**:
   - Bidirectional AST encoder operating in **< 5ms**.
   - Pre-emptive code radar predicting build breaks, lifetime violations, and regressions before test suites execute.

### 📦 Certified Clean Release Artifacts & Checksums

| Asset | Role | Size | SHA-256 Checksum |
|---|---|:---:|---|
| **`viper.Q4_0.gguf`** | Viper (100M) Flagship Reflex | 61.69 MB | `58633aa691b80840dc85586cf2cb8616deff480c64ddf406bf848db749ecc3d4` |
| **`viper-tokenizer.json`** | Viper (100M) Tokenizer | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` |
| **`nano.json`** | Nano (~0.5M) Intent Matrix | 46.8 KB | `9b03e97096d232b76a4de3143b9ef0c76b6e9b64d241a289e99fe1e4977fe125` |
| **`mask.onnx`** | Mask (1.1M) Stream Redactor | 4.43 MB | `a52fdcbc7c749b2d8b41b0c38f8f0cde1eafd7fef0b8ef1688ac80b6ae79b7ad` |
| **`mini.onnx`** | Mini (7.1M) Defect Forecaster | 27.14 MB | `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731` |
| **`micro_base.onnx`** | Micro (5.0M) Base Cluster | 13.82 MB | `4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb` |
| **`micro_infra.onnx`** | Micro (5.0M) Infra Cluster | 19.66 MB | `9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294` |
| **`micro_sec.onnx`** | Micro (5.0M) Security Cluster | 19.66 MB | `c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b` |
