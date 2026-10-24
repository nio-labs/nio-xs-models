# Nio Models — Official MicroLM (µLM) Model Registry

Official model registry and distribution hub for compiled, mathematically verified neural model binaries (`.gguf`, `.onnx`) and specialized domain tokenizers powering the **Nio** and **NioXS** edge developer ecosystem.

---

## ⚡ The MicroLM (µLM) Philosophy

> [!IMPORTANT]
> **MicroLM (µLM) stands for Micro Learning Model — NOT Language Model.**
>
> Modern developer tooling has been hijacked by multi-gigabyte monolithic LLMs that introduce keystroke lag, hallucinated parameters, and heavy memory bloat.
>
> The **MicroLM methodology** engineers ultra-compact, task-dedicated edge neural models designed for **sub-105MB resident memory**, **instant cold startup (< 1.5s)**, and **sub-50ms warm reflex latency** on ordinary CPUs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM / µLM) PARADIGM               │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Generic Chatbot LLM ]                     [ Nio MicroLM (µLM) ]
  Scope:       Broad conversational prose            Task-dedicated edge reflex intelligence
  Peak RAM:    1,200 MB to several GBs               < 92 MB peak resident RAM (Linux VmHWM)
  Disk Size:   500 MB – 8 GB+                        ~56.8 MB (Q4_0 quantized GGUF) / 4.4–27MB (ONNX)
  Execution:   Cloud GPU clusters or heavy runtimes  Local in-process CPU execution (SIMD / AVX2 / NEON)
  Latency:     500ms – 3,000ms per turn              Sub-0.1ms (Nano) to 35-50ms (Viper)
  Reliability: Hallucinates flags & paths            Deterministic Swiss Gear 2.0 slot grounding
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
│    • Viper (100.0M)           ──► Tactical Shell, Pipelines & DevOps Engine (<105MB)│
│                                                                                        │
│  [ TIER 2: INTENT REFLEX & COMMAND ROUTING ]                                          │
│    • Nano (~0.5M)             ──► Directive Interception (--) & Sub-0.1ms Routing    │
│                                                                                        │
│  [ TIER 3: POLICY DECISION & RISK GATES ]                                              │
│    • Micro (5.0M / Cluster)   ──► Contextual Policy Arbiter (sec, infra, base)      │
│                                                                                        │
│  [ TIER 4: REAL-TIME STREAM REDACTION & PRIVACY ]                                      │
│    • Mask (1.1M)              ──► Sub-0.2ms Secret & PII Byte-Level Redactor         │
│                                                                                        │
│  [ TIER 5: PREDICTIVE DEFECT & SYNTAX ]                                                │
│    • Mini (7.1M)              ──► Pre-emptive Defect & Regression Forecaster        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Available Production Models

| Model | Ecosystem Role | Architecture & Capacity | Specialization & Artifact | Status | Release |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **`Viper`** | **Tactical Terminal & DevOps Striker** | `100.0M (14L, 17.5k Vocab)` | Multi-stage UNIX pipelines, DevOps & PowerShell reflex with Swiss Gear 2.0 (`viper.Q4_0.gguf`, ~61.7 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Nano`** | **Intent Routing & Directives** | `~0.5M Features` | Sub-0.1ms command intent triage, lexical heuristics & zero-token directive router (`nano.json`, 46.8 KB) | **Active in Core** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Micro`** | **Contextual Policy Arbiter** | `5.0M / Cluster` | Contextual policy arbiter approving/rejecting terminal mutations with continuous risk scores (sec, infra, base ONNX) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Mask`** | **Stream Security & Redaction** | `1.1M Byte-Conv` | Real-time secret, API key & PII stream redactor for terminal pipes & MCP gateway (`nio_mask.onnx`, 4.43 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Mini`** | **Defect & Syntax Forecaster** | `7.1M Bidirectional AST` | Pre-emptive defect forecaster predicting build breaks & lifetime violations in < 5ms (`nio-mini.onnx`, 27.1 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |

---

## 🐍 1. Viper (100M) — Tactical Terminal & DevOps Reflex Engine

**Viper** is the 100-million parameter tactical terminal striker and DevOps reflex engine. Operating with tied embeddings and Grouped-Query Attention (10/2), it translates complex natural language intent into production POSIX bash and Windows PowerShell reflexes with **~92 MB peak resident RAM (`VmHWM`)** and **35ms – 50ms** warm CPU inference.

### Verified Specifications
- **Parameter Count**: **Exactly 100,000,000 locked**
- **Architecture**: 14 Transformer layers ($d=800$, $d_{ff}=1920$), GQA (10 Query / 2 KV heads), SwiGLU, RMSNorm
- **Vocabulary Size**: 17,451 dedicated ByteLevel BPE tokens
- **Weights on Disk**: ~56.8 MB (Q4_0 GGUF)
- **Peak Resident RAM (`VmHWM`)**: ~92.0 MB (< 105 MB hard edge envelope)
- **Integrated Swiss Gear 2.0**:
  - **Deterministic Slot Grounding**: Extracts quoted literals (`'TODO'`) and aligns dynamic ports (`4000`).
  - **Spider Search Hygiene**: Suppresses binary noise (`-rIn`), excludes build trees (`target/`, `.git/`, `node_modules/`), anchors paths to `.`.
  - **Destructive Safety Clutch**: Interactively protects against dangerous mutations (`rm -rf`, `kill -9`, `git reset --hard`, `Stop-Process`).

### 💻 How to Run & Practical Examples

```bash
# 1. Pull and cache verified Viper weights
nioxs pull viper

# 2. Instant single-shot terminal reflex (< 95MB RAM, ~35ms)
nioxs viper "list folder pls"
# Output: ls -la

# 3. Multi-stage piped UNIX pipeline with file filtering & sorting
nioxs viper "find all rust files modified today and count lines of code"
# Output: find . -name "*.rs" -mtime 0 | xargs wc -l | sort -nr

# 4. Native execution (-x) with active Destructive Safety Clutch
nioxs viper -x "kill whatever process is holding port 3000"
# Output: lsof -ti:3000 | xargs kill -9
# Prompt: ⚡ Destructive command detected. Execute? [Y/n]

# 5. Modern DevOps orchestration (Kubernetes & Docker)
nioxs viper "stream logs from pod auth-service in namespace production"
# Output: kubectl logs -n production -l app=auth-service --tail=100 -f

# 6. Windows PowerShell object pipeline
nioxs viper --shell powershell "get top 5 processes by memory"
# Output: Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Name, Id
```

---

## ⚡ 2. Nano (~0.5M) — Command Triage & Intent Reflex

**Nano** is the embedded reflex layer of the Nio ecosystem. Embedded directly into native Rust binaries with zero external runtime dependencies, it acts as the initial sensory filter in developer terminals, IDE extensions, and CLI daemons.
- **Latency**: < 0.1ms (sub-100 microseconds)
- **Footprint**: ~5 MB resident RAM
- **Directives**: Routes zero-token prefixes (`--bash`, `--tools`, `--code`) instantly without neural inference.

### 💻 How to Run & Practical Examples

```bash
# 1. Zero-token shell directive execution (executes locally in < 0.05ms without LLM tokens)
nio "--bash cargo test --lib --locked"

# 2. Sub-millisecond AST symbol caller navigation across workspace crates
nio "--callers ViperEngine"
# Output: [Nano Reflex (< 0.08ms)] Found 3 caller references for 'ViperEngine'

# 3. Codebase symbol lookup & intent triage via NioXS CLI (< 0.1ms)
nioxs nano "where is ModelConfig defined in the repository?"
# Output:
# {
#   "action": "search_code",
#   "symbol": "ModelConfig",
#   "confidence": 0.992,
#   "elapsed_microseconds": 74,
#   "suggested_command": "git grep 'struct ModelConfig' src/"
# }

# 4. File globbing directive without touching cloud APIs
nio "--find *.dockerfile"
```

---

## 🛡️ 3. Micro (5.0M / Cluster) — Contextual Policy Arbiter

**Micro** is a 4-layer bidirectional Transformer operating in **< 5ms** as an autonomous policy gate:
- **Clusters**: `sec` (security/credentials), `infra` (system mutations, ports, systemd), `base` (filesystem & git).
- **Outputs**: Discrete verdicts (`approve` / `reject`) and continuous calibrated risk scores (`0.00` to `1.00`).
- **Format**: Standard ONNX runtime executable in-process via Rust.

### 💻 How to Run & Practical Examples

```bash
# 1. Pull domain policy clusters
nioxs pull micro --cluster sec
nioxs pull micro --cluster infra

# 2. Audit SQL queries & code diffs for security violations (Security Cluster)
nioxs micro sec --diff "SELECT * FROM users WHERE id = '" + id + "'"
# Output:
# {
#   "verdict": "REJECT",
#   "confidence": 0.998,
#   "risk_score": 0.984,
#   "reason": "Unsanitized dynamic string interpolation detected in SQL statement"
# }

# 3. Intercept destructive infrastructure mutations (Infra Cluster)
nioxs micro infra "kubectl delete namespace production --cascade=foreground"
# Output:
# {
#   "verdict": "REJECT",
#   "confidence": 0.995,
#   "risk_score": 0.991,
#   "reason": "Cascade namespace deletion targets production environment"
# }

# 4. Evaluate safe developer workflow commands (Base Cluster)
nioxs micro base "cargo check --locked"
# Output:
# {
#   "verdict": "APPROVE",
#   "confidence": 0.999,
#   "risk_score": 0.012,
#   "reason": "Read-only compiler check command"
# }
```

---

## 🔒 4. Mask (1.1M) — Real-Time Secret & PII Stream Redactor

**Mask** is a 2-layer Byte-Level Convolutional Transformer operating in **< 0.2ms**:
- **Latency**: Sub-200 microseconds per 1KB chunk.
- **Footprint**: 4.43 MB standalone ONNX binary (~6 MB RAM).
- **Protection**: Scrubs AWS keys, GitHub PATs, OpenAI tokens, passwords, and PII from stdout/stderr pipes, terminal streams, and MCP gateway buffers with 99.95% accuracy and zero false positives on commit SHAs.

### 💻 How to Run & Practical Examples

```bash
# 1. Pull verified Mask ONNX model
nioxs pull mask

# 2. Real-time stdout stream scrubbing for environment files & logs
cat .env | nioxs mask
# Output:
# DATABASE_URL=postgres://app_user:[REDACTED_PASSWORD]@db.internal:5432/production
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=[REDACTED_AWS_SECRET]
# GITHUB_TOKEN=[REDACTED_GITHUB_PAT]

# 3. Git pre-commit security hook (blocks commit if unredacted secrets found)
git diff --cached | nioxs mask --fail-on-secrets
# Exit code: 1 if secret detected, 0 if clean

# 4. Pre-filter agent tool payloads in NioAI CLI
nio run -m nioxs::mask --sanitize-buffer "curl -H 'Authorization: Bearer ghp_9921...' https://api.github.com/user"
```

---

## 🎯 5. Mini (7.1M) — Pre-emptive Defect Forecaster

**Mini** evaluates code diffs before compilation or test suites execute:
- **Latency**: < 5ms in-process ONNX inference.
- **Role**: Predicts build breaks, syntax errors, and regression probability before triggering slow build cycles.

### 💻 How to Run & Practical Examples

```bash
# 1. Pull verified Mini ONNX model
nioxs pull mini

# 2. Detect borrow-checker conflicts and lifetime errors in sub-5ms
nioxs mini "fn process(data: &mut Vec<u8>) { let r = &data; data.push(1); }"
# Output:
# {
#   "will_break": true,
#   "break_probability": 0.984,
#   "category": "BORROW_CHECK_FAIL",
#   "risk_score": 0.92,
#   "reason": "Cannot borrow `*data` as mutable because it is also borrowed as immutable"
# }

# 3. Forecast test suite regressions on pending git diffs in NioAI
nio run -m nioxs::mini --predict-tests --diff "git diff crates/router/src/lib.rs"

# 4. Sub-5ms PR pre-flight gate for CI pipelines
nioxs mini check --threshold 0.70 --diff-file pr_changes.patch
```

---

## 📦 Model Artifacts & Certified Checksums (v0.1.0)

| Artifact | Engine / Role | Format | Size | SHA-256 Checksum | Download Link |
|---|---|:---:|:---:|---|:---:|
| `viper.Q4_0.gguf` | Viper 100M | GGUF Q4_0 | 61.69 MB | `58633aa691b80840dc85586cf2cb8616deff480c64ddf406bf848db749ecc3d4` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/viper.Q4_0.gguf) |
| `viper-tokenizer.json` | Viper Tokenizer | JSON | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/viper-tokenizer.json) |
| `nano.json` | Nano Intent | JSON | 46.8 KB | `9b03e97096d232b76a4de3143b9ef0c76b6e9b64d241a289e99fe1e4977fe125` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nano.json) |
| `nio_micro_base.onnx` | Micro Base | ONNX | 13.82 MB | `4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_base.onnx) |
| `nio_micro_infra.onnx` | Micro Infra | ONNX | 19.66 MB | `9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_infra.onnx) |
| `nio_micro_sec.onnx` | Micro Security | ONNX | 19.66 MB | `c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro_sec.onnx) |
| `nio-micro-tokenizer.json` | Micro Tokenizer | JSON | 17.5 KB | `1bbbcc91a0a0cf8ac64bbb577e5e3668e7aa7ba56e84ca56b22a237372edbb9f` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-micro-tokenizer.json) |
| `nio_mask.onnx` | Mask Redactor | ONNX | 4.43 MB | `a52fdcbc7c749b2d8b41b0c38f8f0cde1eafd7fef0b8ef1688ac80b6ae79b7ad` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_mask.onnx) |
| `nio-mini.onnx` | Mini Defect | ONNX | 27.14 MB | `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio-mini.onnx) |

---

## 🔌 Localhost Model Context Protocol (MCP) Server (`nioxs-mcp`)

The **Nio MCP Server** (`crates/nio-mcp`) runs 100% locally on standard I/O (`stdio`). It exposes all 5 MicroLM engines as zero-cost in-process tools for AI coding assistants (Cursor, Claude Desktop, Antigravity, Cline, Windsurf, Zed):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CODING AGENT (e.g. Claude / Cursor)             │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ MCP Standard JSON-RPC 2.0 (stdio)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              LOCAL NIO MCP SERVER (`nioxs-mcp` in Rust)                │
├────────────────────────────────────────────────────────────────────────┤
│ • viper_synthesize(intent, shell)  ──► Sub-50ms POSIX/PS Command       │
│ • mask_sanitize(content)           ──► Sub-0.2ms Secret/PII Scrubber   │
│ • micro_audit(action, cluster)     ──► Sub-4ms Policy APPROVE/REJECT   │
│ • nano_route(text)                 ──► Sub-0.1ms Zero-Token Directive  │
│ • mini_predict_defect(diff)        ──► Sub-5ms Build Break Probability │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Available MCP Tools

| Tool Name | Engine | Role | Speed & Token Impact |
|---|---|---|---|
| **`viper_synthesize`** | Viper (100M) | Synthesize POSIX / PowerShell cmdlets with Destructive Safety Clutch | Replaces 1,500+ output tokens with sub-50ms local inference |
| **`mask_sanitize`** | Mask (1.1M) | Zero-cloud secret & PII stream scrubber (API keys, tokens, passwords) | Prevents secret leaks to cloud APIs in < 0.2ms with 0 false positives |
| **`micro_audit`** | Micro (5.0M) | Contextual policy arbiter approving/rejecting file and infra mutations | Deterministic gate in < 4ms; eliminates 2,000+ token safety prompts |
| **`nano_route`** | Nano (~0.5M) | Sub-0.1ms command intent triage and zero-token directive router | Saves 5k–25k tokens on inspection directives (`--bash`, `--tools`) |
| **`mini_predict_defect`** | Mini (7.1M) | Pre-emptive defect and regression forecaster on code diffs | Sub-5ms PR / commit screening before triggering heavy build cycles |

### 2. Configuration for Coding Agents

#### A. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "nio": {
      "command": "cargo",
      "args": ["run", "--release", "-p", "nio-mcp", "--", "--stdio"]
    }
  }
}
```

#### B. Cursor / Windsurf / Antigravity (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "nio-local": {
      "command": "cargo",
      "args": ["run", "--release", "-p", "nio-mcp", "--", "--stdio"]
    }
  }
}
```

### 3. Diagnostics & Self-Test
Run the built-in diagnostic test across all 5 MicroLM tools:
```bash
cargo run -p nio-mcp -- --test
```

---

## 📄 License

This repository is licensed under the [Business Source License 1.1](LICENSE) (BSL 1.1).

* **Non-Production & Internal Production Use**: Free to use, copy, modify, redistribute, and run internally within your organization for testing, development, and private infrastructure.
* **Commercial Protection Clause**: You may not offer the Licensed Work to third parties as a competing hosted, managed, or cloud service without a commercial license from Nio Labs.
* **Automatic Open Source Transition**: On **October 20, 2030** (four years from publication), this code automatically converts to the **Apache License, Version 2.0**.

For commercial licensing inquiries or enterprise deployments, contact `dev@n-o.me`.
