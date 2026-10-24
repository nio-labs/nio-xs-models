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
  Disk Size:   500 MB – 8 GB+                        26.9 MB (Q4_0 quantized GGUF)
  Execution:   Cloud GPU clusters or heavy runtimes  Local in-process CPU execution (SIMD / AVX2 / NEON)
  Latency:     500ms – 3,000ms per turn              15ms – 35ms warm reflex
  Reliability: Hallucinates flags & paths            Deterministic Swiss Gear slot grounding
  Safety:      Blind command execution               Interactive Destructive Safety Clutch
```

---

## 🐍 Active Production Model: NioViper 50M (v0.1.0)

**NioViper** is the 50-million parameter tactical terminal striker and DevOps reflex engine. Designed from scratch for edge developers, it converts natural language developer intent into precise, production-grade POSIX bash/sh and Windows PowerShell commands.

### 📊 Verified Specifications

| Metric | Measured Value | Standard / Hard Envelope | Status |
|---|:---:|:---:|:---:|
| **Parameter Count** | **50,000,000** | Strict 50M Budget | ✅ Verified |
| **Model Weights (Q4_0 GGUF)** | **26.9 MB** | $< 35\text{ MB}$ | ✅ Verified |
| **Peak Resident RAM (`VmHWM`)** | **53.1 MB** | $< 55\text{ MB}$ | ✅ Verified |
| **Average Resident RAM (`VmRSS`)** | **51.8 MB** | $< 55\text{ MB}$ | ✅ Verified |
| **Cold Startup + Inference** | **1.2s – 1.7s** | $< 2.5\text{ s}$ | ✅ Verified |
| **Warm Forward Pass Latency** | **15ms – 35ms** | $< 50\text{ ms}$ | ✅ Verified |
| **Vocabulary Size** | **14,744** | Dedicated BPE Tokenizer | ✅ Verified |
| **Context Window** | **512 tokens** | SwiGLU + GQA (10/2) | ✅ Verified |

---

## 🛠️ Integrated Swiss Gear Capabilities

NioViper operates with the native **NioXS Swiss Gear** runtime engine, providing capabilities that raw LLMs cannot match:

1. **Deterministic Slot Grounding**:
   - Automatically aligns quoted literal terms (e.g. `'TODO'`, `'BUG'`, `'secret'`) directly into search flags (`-e 'TODO'`, `-Pattern 'TODO'`).
   - Grounding custom ports (e.g. `kill port 4000` $\rightarrow$ `lsof -ti:4000 | xargs kill -9`).
2. **Safe Scope Fallback & Path Anchoring**:
   - Automatically guards against unprompted system path scans (redirects unintended `/var/log` searches to `.`).
3. **Code & Spider Search Hygiene**:
   - Injects `-rIn` binary suppression so `.rmeta`, `.rlib`, and `.so` files never spam the terminal.
   - Automatically excludes `.git`, `target/`, and `node_modules/` build trees.
4. **Destructive Safety Clutch**:
   - Interactively intercepts dangerous mutations (`rm -rf`, `kill -9`, `git reset --hard`, `Stop-Process`) before native execution.
5. **Isolated Python Sandbox**:
   - Dedicated environment at `~/.nioxs/plugins/venv` for data analysis and DevOps plugins.

---

## 📦 Model Artifacts & Downloads (v0.1.0)

| Artifact | Format | Size | SHA-256 Checksum | Download Link |
|---|:---:|:---:|---|:---:|
| `nio-viper.Q4_0.gguf` | GGUF (Q4_0) | 26.9 MB | *(Verified on Release)* | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-viper.Q4_0.gguf) |
| `nio-viper-tokenizer.json` | HuggingFace JSON | 923 KB | *(Verified on Release)* | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-viper-tokenizer.json) |

### Automatic Installation via NioXS CLI

```bash
# Pull and verify NioViper weights automatically
nioxs pull viper

# Run an instant terminal reflex
nioxs viper "list folder pls"

# Execute natively with safety clutch
nioxs viper -x "spider search .rs files for 'fn main'"
```

---

## 🗺️ The Nio Fleet Roadmap

While **NioViper 50M** leads the edge reflex frontier, the full-brain predator fleet is in active rollout:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE NIO FULL-BRAIN FLEET                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  • NioViper  (50M)   ──► Tactical Terminal & DevOps Striker      [v0.1.0 ACTIVE]       │
│  • NioRay    (1.54B) ──► Full-Brain Code Synthesizer & Architect [Roadmap Q4 2026]     │
│  • NioApex   (3.2B)  ──► Swarm Reasoning Engine & Planner        [Roadmap Q1 2027]     │
│  • NioHydra  (8.0B)  ──► Polyglot Speculative MoE Engine         [Roadmap Q2 2027]     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 License

All model weights and tokenizer configurations in this registry are distributed under the **Apache 2.0 / MIT Dual License**.
