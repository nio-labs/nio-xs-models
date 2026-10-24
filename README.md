# Nio Models — Official MicroLM (µLM) Model Registry

Official model registry and distribution hub for compiled, mathematically verified neural model binaries (`.gguf`, `.onnx`) and specialized domain tokenizers powering the **Nio** and **NioXS** edge developer ecosystem.

---

## ⚡ The MicroLM (µLM) Philosophy

> [!IMPORTANT]
> **MicroLM (µLM) stands for Micro Learning Model — NOT Language Model.**
>
> Modern developer tooling has been hijacked by multi-gigabyte monolithic LLMs that introduce keystroke lag, hallucinated parameters, and heavy memory bloat.
>
> The **MicroLM methodology** engineers ultra-compact, task-dedicated edge neural models designed for **sub-55MB resident memory**, **instant cold startup (< 1.5s)**, and **sub-25ms warm reflex latency** on ordinary CPUs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM / µLM) PARADIGM               │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Generic Chatbot LLM ]                     [ Nio MicroLM (µLM) ]
  Scope:       Broad conversational prose            Task-dedicated edge reflex intelligence
  Peak RAM:    1,200 MB to several GBs               < 53.1 MB peak resident RAM (Linux VmHWM)
  Disk Size:   500 MB – 8 GB+                        26.9 MB (Q4_0 quantized GGUF) / 14-28MB (ONNX)
  Execution:   Cloud GPU clusters or heavy runtimes  Local in-process CPU execution (SIMD / AVX2 / NEON)
  Latency:     500ms – 3,000ms per turn              Sub-0.1ms (Nano) to 15-35ms (Viper)
  Reliability: Hallucinates flags & paths            Deterministic Swiss Gear slot grounding
  Safety:      Blind command execution               Interactive Destructive Safety Clutch
```

---

## 🏛️ The Production MicroLM Hierarchy

Instead of relying on a single slow generalist model, Nio deploys a specialized hierarchy of 5 edge MicroLMs:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE NIO PRODUCTION FLEET                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ TIER 1: TACTICAL TERMINAL & DEVOPS REFLEX ]                                         │
│    • NioViper (50.0M)            ──► Tactical Shell & DevOps Reflex Engine (< 52MB RAM)│
│                                                                                        │
│  [ TIER 2: INTENT REFLEX & COMMAND ROUTING ]                                          │
│    • NioNano (~0.5M)             ──► Directive Interception (--) & Sub-0.1ms Routing    │
│                                                                                        │
│  [ TIER 3: POLICY DECISION & RISK GATES ]                                              │
│    • NioMicro (5.0M / Cluster)   ──► Contextual Policy Arbiter (sec, infra, base)      │
│                                                                                        │
│  [ TIER 4: REAL-TIME STREAM REDACTION & PRIVACY ]                                      │
│    • NioMask (1.1M)              ──► Sub-0.2ms Secret & PII Byte-Level Redactor         │
│                                                                                        │
│  [ TIER 5: PREDICTIVE DEFECT & SYNTAX ]                                                │
│    • NioMini (7.1M)              ──► Pre-emptive Defect & Regression Forecaster        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Available Production Models

| Model | Ecosystem Role | Architecture & Capacity | Specialization & Artifact | Status | Release |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **`NioViper`** | **Tactical Terminal Striker** | `50.0M (10L, 14.7k Vocab)` | Natural language to POSIX & PowerShell reflex with Swiss Gear Runner (`nio-viper.Q4_0.gguf`, 26.9 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`NioNano`** | **Intent Routing & Directives** | `~0.5M Features` | Sub-0.1ms command intent triage, lexical heuristics & zero-token directive router (`nano.json`, 46.8 KB) | **Active in Core** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`NioMicro`** | **Contextual Policy Arbiter** | `5.0M / Cluster` | Contextual policy arbiter approving/rejecting terminal mutations with continuous risk scores (sec, infra, base ONNX) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`NioMask`** | **Stream Security & Redaction** | `1.1M Byte-Conv` | Real-time secret, API key & PII stream redactor for terminal pipes & MCP gateway (`nio_mask.onnx`, 4.43 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`NioMini`** | **Defect & Syntax Forecaster** | `7.1M Bidirectional AST` | Pre-emptive defect forecaster predicting build breaks & lifetime violations in < 5ms (`nio-mini.onnx`, 27.1 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |

---

## 🐍 1. NioViper 50M — Tactical Terminal & DevOps Reflex Engine

**NioViper** is the 50-million parameter tactical terminal striker and DevOps reflex engine. Operating with tied embeddings and Grouped-Query Attention (10/2), it translates complex natural language intent into production POSIX bash and Windows PowerShell reflexes with **51.8 MB average / 53.1 MB peak resident RAM** and **15ms – 35ms** warm inference.

### Verified Specifications
- **Parameter Count**: 50,000,000 locked
- **Architecture**: 10 Transformer layers ($d=640$, $d_{ff}=1600$), GQA (10/2), SwiGLU, RMSNorm
- **Vocabulary Size**: 14,744 dedicated ByteLevel BPE tokens
- **Weights on Disk**: 26.9 MB (Q4_0 GGUF)
- **Peak Resident RAM (`VmHWM`)**: 53.1 MB (< 55 MB hard envelope)
- **Integrated Swiss Gear**:
  - **Deterministic Slot Grounding**: Extracts quoted literals (`'TODO'`) and aligns dynamic ports (`4000`).
  - **Spider Search Hygiene**: Suppresses binary noise (`-rIn`), excludes build trees (`target/`, `.git/`, `node_modules/`), anchors paths to `.`.
  - **Destructive Safety Clutch**: Interactively protects against dangerous mutations (`rm -rf`, `kill -9`, `git reset --hard`, `Stop-Process`).
  - **Python Sandbox**: Isolated venv at `~/.nioxs/plugins/venv` for data analysis tools (`duckdb`, `tree-sitter`).

---

## ⚡ 2. NioNano (~0.5M) — Command Triage & Intent Reflex

**NioNano** is the embedded reflex layer of the Nio ecosystem. Embedded directly into native Rust binaries with zero external runtime dependencies, it acts as the initial sensory filter in developer terminals, IDE extensions, and CLI daemons.
- **Latency**: < 0.1ms (sub-100 microseconds)
- **Footprint**: ~5 MB resident RAM
- **Directives**: Routes zero-token prefixes (`--bash`, `--tools`, `--code`) instantly without neural inference.

---

## 🛡️ 3. NioMicro (5.0M / Cluster) — Contextual Policy Arbiter

**NioMicro** is a 4-layer bidirectional Transformer operating in **< 5ms** as a mathematical gatekeeper:
- **Clusters**: `sec` (security/credentials), `infra` (system mutations, ports, systemd), `base` (filesystem & git).
- **Outputs**: Discrete verdicts (`approve` / `reject`) and continuous calibrated risk scores (`0.00` to `1.00`).
- **Format**: Standard ONNX runtime executable in-process via Rust.

---

## 🔒 4. NioMask (1.1M) — Real-Time Secret & PII Stream Redactor

**NioMask** is a 2-layer Byte-Level Convolutional Transformer operating in **< 0.2ms**:
- **Latency**: Sub-200 microseconds per 1KB chunk.
- **Footprint**: 4.43 MB standalone ONNX binary (~6 MB RAM).
- **Protection**: Scrubs AWS keys, GitHub PATs, OpenAI tokens, passwords, and PII from stdout/stderr pipes, terminal streams, and MCP gateway buffers with 99.95% accuracy and zero false positives on commit SHAs.

---

## 🎯 5. NioMini (7.1M) — Pre-emptive Defect Forecaster

**NioMini** evaluates code diffs before compilation or test suites execute:
- **Latency**: < 5ms in-process ONNX inference.
- **Role**: Predicts build breaks, syntax errors, and regression probability before triggering slow build cycles.

---

## 📦 Model Artifacts & Certified Checksums (v0.1.0)

| Artifact | Engine / Role | Format | Size | SHA-256 Checksum | Download Link |
|---|---|:---:|:---:|---|:---:|
| `nio-viper.Q4_0.gguf` | NioViper 50M | GGUF Q4_0 | 26.91 MB | `acaa8a21c8d37d12398a2e7ac67ad367d2e3786b261ce95195e6e0cc08363e9c` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-viper.Q4_0.gguf) |
| `nio-viper-tokenizer.json` | NioViper Tokenizer | JSON | 923 KB | `25e0b493570d3f1cd338033a685f69eb3fefd4f307424bca5709fa8bb1994806` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-viper-tokenizer.json) |
| `nano.json` | NioNano Intent | JSON | 46.8 KB | `9b03e97096d232b76a4de3143b9ef0c76b6e9b64d241a289e99fe1e4977fe125` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nano.json) |
| `nio_micro_base.onnx` | NioMicro Base | ONNX | 13.82 MB | `4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_base.onnx) |
| `nio_micro_infra.onnx` | NioMicro Infra | ONNX | 19.66 MB | `9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_infra.onnx) |
| `nio_micro_sec.onnx` | NioMicro Security | ONNX | 19.66 MB | `c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_sec.onnx) |
| `nio-micro-tokenizer.json` | NioMicro Tokenizer | JSON | 17.5 KB | `1bbbcc91a0a0cf8ac64bbb577e5e3668e7aa7ba56e84ca56b22a237372edbb9f` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-micro-tokenizer.json) |
| `nio_mask.onnx` | NioMask Redactor | ONNX | 4.43 MB | `a52fdcbc7c749b2d8b41b0c38f8f0cde1eafd7fef0b8ef1688ac80b6ae79b7ad` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_mask.onnx) |
| `nio-mini.onnx` | NioMini Defect | ONNX | 27.14 MB | `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-mini.onnx) |

---

### 💻 Quickstart via NioXS CLI

```bash
# Pull and verify NioViper weights
nioxs pull viper

# Natural language terminal reflex (< 52MB RAM)
nioxs viper "list folder pls"

# Execute natively with Destructive Safety Clutch
nioxs viper -x "spider search .rs files for 'fn main'"

# Real-time secret and PII scrubbing
cat .env | nioxs mask
```

---

## 📄 License

This repository is licensed under the [Business Source License 1.1](LICENSE) (BSL 1.1).

* **Non-Production & Internal Production Use**: Free to use, copy, modify, redistribute, and run internally within your organization for testing, development, and private infrastructure.
* **Commercial Protection Clause**: You may not offer the Licensed Work to third parties as a competing hosted, managed, or cloud service without a commercial license from Nio Labs.
* **Automatic Open Source Transition**: On **October 20, 2030** (four years from publication), this code automatically converts to the **Apache License, Version 2.0**.

For commercial licensing inquiries or enterprise deployments, contact `licensing@nio-labs.com`.
