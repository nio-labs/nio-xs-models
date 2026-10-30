# Nio Models — Official MicroLM (µLM) Model Registry

Official model registry and distribution hub for compiled, mathematically verified neural model binaries (`.gguf`, `.onnx`) and specialized domain tokenizers powering the **Nio** and **NioXS** edge developer ecosystem.

> 📦 **Release History**: Read the full [Unified Release Notes & Changelog](RELEASE_NOTES.md).

---

## ⚡ The MicroLM (µLM) Philosophy

> [!IMPORTANT]
> **MicroLM (µLM) stands for Micro Learning Model — NOT Language Model.**
>
> Modern developer tooling has been hijacked by multi-gigabyte monolithic LLMs that introduce keystroke lag, hallucinated parameters, and heavy memory bloat.
>
> The **MicroLM methodology** engineers ultra-compact, task-dedicated edge neural models designed for **sub-30MB resident memory**, **instant cold startup (< 1.5s)**, and **sub-20µs candidate reflex latency** on ordinary CPUs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM / µLM) PARADIGM               │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Generic Chatbot LLM ]                     [ Nio MicroLM (µLM) ]
  Scope:       Broad conversational prose            Task-dedicated edge reflex intelligence
  Peak RAM:    1,200 MB to several GBs               27.14 MB peak resident RAM (Linux VmHWM, AST-MicroLM runtime)
  Disk Size:   500 MB – 8 GB+                        61.69 MB (Q4_0 quantized GGUF) / 4.4–27MB (ONNX)
  Execution:   Cloud GPU clusters or heavy runtimes  Local in-process CPU execution (Candle AST-MicroLM / ONNX / SIMD)
  Latency:     500ms – 3,000ms per turn              Sub-0.1ms (Nano) to Sub-20µs Sampling / 35ms (Viper)
  Reliability: Hallucinates flags & paths            Deterministic Swiss Gear 2.0 slot grounding
  Safety:      Blind command execution               Interactive Destructive Safety Clutch
```

---

## 🧬 The v-µLM (V-MicroLM) Architecture: Reflex & Vector

> 📖 **Architecture Portal**: Read the full [v-µLM Dual-Engine Architecture Guide](https://nio-labs.github.io/nio-xs-models/vmicrolm.html) on GitHub Pages.

**v-µLM (V-MicroLM)** is Nio's proprietary twin-engine edge architecture that eliminates reliance on brittle synthetic dataset fine-tuning in favor of two rigorous mathematical pillars:

| Pillar | Engine Type | Model Targets | Core Mechanism | Runtime Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **`v-µLM Reflex`** | Instant Grammar & In-Process Decision Engine | **Nano (~0.5M)**, **Mask (1.1M)**, **Micro (5.0M)**, **Mini (7.1M)**, **Viper (100M)** | Structural AST constraints, lexical intent routing, and real-time policy classification | **< 28 MB RAM**, sub-0.1ms to sub-20µs sampling |
| **`v-µLM Vector`** | Vector Codebook Lattice (VQ) | **Skate (135M)**, **Mako (150M)** & **Manta (494M)** | Importance-weighted IQ3 non-linear vector quantization codebooks | **82.9–92.0 MB disk**, >0.999 layer cosine fidelity |

- **Zero Synthetic Datasets**: Eliminates the catastrophic reasoning forgetting and repetitive loops common to small models fine-tuned on artificial Q&A data.
- **Deep Signal Retention**: Mathematical vector codebooks prevent the compounding drift that causes linear SVD approximations to collapse over 30 transformer layers.

---

## 🏛️ The Production MicroLM Hierarchy

Instead of relying on a single slow generalist model, Nio deploys a specialized hierarchy of 5 edge MicroLMs:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE NIO PRODUCTION FLEET                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ TIER 1: TACTICAL TERMINAL & DEVOPS REFLEX ]                                         │
│    • Viper (100.0M)           ──► Pure-Rust Tactical AST-MicroLM Engine (27.14MB)      │
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
│  [ TIER 6: RESIDENT EDGE COMPANION & IOT TRIAGE ]                                      │
│    • Skate (134.5M)           ──► Resident Micro-Guru, Smartwatch & Ambient Edge (<23MB)│
│                                                                                        │
│  [ TIER 7: LIVE WEB INTELLIGENCE & CRAWL SCOUT ]                                       │
│    • Mako (150.0M)            ──► nioxs-browser Scout, DOM Noise Scrubber (<13MB)      │
│                                                                                        │
│  [ TIER 8: CONVERSATIONAL GURU & DAG ARCHITECT ]                                       │
│    • Manta (494.0M)           ──► NioGuru 21 Personas, Wasm Architect (<55MB)          │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Available Production Models

| Model | Ecosystem Role | Architecture & Capacity | Specialization & Artifact | Status | Release |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **`Viper`** | **Tactical Terminal & DevOps Striker** | `100.0M (14L, 17.5k Vocab)` | Pure-Rust AST-MicroLM runtime, DevOps & PowerShell reflex with Swiss Gear 2.0 (`viper.Q4_0.gguf`, 61.69 MB, **27.14 MB peak RAM**) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Nano`** | **Intent Routing & Directives** | `~0.5M Features` | Sub-0.1ms command intent triage, lexical heuristics & zero-token directive router (`nano.json`, 46.8 KB) | **Active in Core** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Micro`** | **Contextual Policy Arbiter** | `5.0M / Cluster` | Contextual policy arbiter approving/rejecting terminal mutations with continuous risk scores (sec, infra, base ONNX) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Mask`** | **Stream Security & Redaction** | `1.1M Byte-Conv` | Real-time secret, API key & PII stream redactor for terminal pipes & MCP gateway (`mask.onnx`, 4.43 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Mini`** | **Defect & Syntax Forecaster** | `7.1M Bidirectional AST` | Pre-emptive defect forecaster predicting build breaks & lifetime violations in < 5ms (`mini.onnx`, 27.1 MB) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`Skate`** | **Resident Micro-Guru & Edge Companion** | `134.5M (30L, v-µLM Vector)` | 100% brain from SmolLM2-135M via IQ3_XXS Vector Codebooks (`skate.vmicrolm-vector.gguf`, 82.93 MB, **< 50 MB peak RAM**, 115+ tok/s `--turbo`) | **Released** | [`v0.2.6`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.2.6) |
| **`Mako`** | **Live Web Intelligence & Scraping Scout** | `150.0M (34L, v-µLM Vector)` | Keyless multi-domain live documentation scout, HTTP 304 ETag caching (50MB LRU disk limit), and LLM-Native Wire DSL (`mako.vmicrolm-vector.gguf`, 92.0 MB, **12.49 MB peak RAM**, 13.5ms latency) | **Released** | [`v0.2.5`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.2.5) |
| **`Manta`** | **Full Conversational Guru & Wasm Architect** | `494.0M (24L, v-µLM Vector)` | 100% brain from Qwen2.5-0.5B via IQ3_XXS Vector Codebooks, powers NioGuru 21 personas, file analysis & `<manta_plan>` DAGs (`manta.vmicrolm-vector.gguf`, 253.33 MB, < 55 MB RAM) | **Released** | [`v0.2.2`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.2.2) |

---

## 📦 One-Liner Installer & Quickstart

Install the compiled MicroLM binaries (`nioxs` and `nioxs-mcp`) to `~/.local/bin` with automated architecture detection and automatic OpenCode MCP integration:

```bash
curl -fsSL https://nio-labs.github.io/nio-xs-models/install.sh | bash
```

Or compile and install directly from source via Cargo:

```bash
cargo install --git https://github.com/nio-labs/nio-xs-models.git nioxs-cli
cargo install --git https://github.com/nio-labs/nio-xs-models.git nio-mcp
```

---

## 🐍 1. Viper (100M) — Tactical Terminal & DevOps Reflex Engine (`v-µLM Reflex`)

**Viper** is the 100-million parameter tactical terminal striker and DevOps reflex engine powered by the **`v-µLM Reflex`** architecture. Operating with tied embeddings and Grouped-Query Attention (10/2), it translates complex natural language intent into production POSIX bash and Windows PowerShell reflexes with **27.14 MB peak resident RAM (`VmHWM`)** and **sub-20µs tactical AST candidate reflex sampling** via its native pure-Rust runtime.

> 🧬 **The Twin Pillars of Nio `v-µLM` (V-MicroLM)**:
> - **`v-µLM Reflex`**: Pure-Rust Tree-sitter candidate reflex engine (Viper 100M: 27MB RAM, sub-20µs sampling).
> - **`v-µLM Vector`**: Mathematical Vector Codebook Lattice engine (Skate 135M & Manta 494M: >0.999 layer cosine fidelity, zero dataset fine-tuning needed).

### Verified Specifications
- **Parameter Count**: **Exactly 100,000,000 locked**
- **Architecture**: 14 Transformer layers ($d=800$, $d_{ff}=1920$), GQA (10 Query / 2 KV heads), SwiGLU, RMSNorm
- **Vocabulary Size**: 17,451 dedicated ByteLevel BPE tokens
- **Weights on Disk**: 61.69 MB (Q4_0 GGUF)
- **Peak Resident RAM (`VmHWM`)**: **27.14 MB** (Linux `VmHWM` AST-MicroLM runtime default, 11.70 MB init)
- **Candidate Sampling**: **Sub-20µs Tactical AST Candidate Reflex** (< 25MB RAM mode)
- **Integrated Swiss Gear 2.0**:
  - **Deterministic Slot Grounding**: Extracts quoted literals (`'TODO'`) and aligns dynamic ports (`4000`).
  - **Spider Search Hygiene**: Suppresses binary noise (`-rIn`), excludes build trees (`target/`, `.git/`, `node_modules/`), anchors paths to `.`.
  - **Destructive Safety Clutch**: Interactively protects against dangerous mutations (`rm -rf`, `kill -9`, `git reset --hard`, `Stop-Process`).

### 🦀 Pure-Rust AST-MicroLM Runtime Benchmark (`nio-viper-runtime`)

Viper can be executed either via the unified CLI (`nioxs viper`) or embedded directly into Rust services via the pure-Rust AST-MicroLM runtime (`nio-viper-runtime`). Built with HuggingFace Candle, tied quantized weights, and tactical AST candidate slicing, it achieves an industry-leading **27.14 MB peak resident RAM (`VmHWM`)** with zero Python or heavy C++ runtime dependencies:

| Telemetry Execution Phase | Working Memory (`VmRSS`) | Peak Resident RAM (`Linux VmHWM`) | Sampling & Speed |
|:---|:---:|:---:|:---|
| **Process Startup** | **3.76 MB** | 3.76 MB | Standalone native binary |
| **Engine Initialized** | **11.70 MB** | 27.14 MB | 14 layers, 17,451 vocab tied weights |
| **Working Prefill RSS** | **15.74 MB** | 27.14 MB | Prompt KV buffer allocated |
| **Peak Full Execution** | **18.02 MB** | **27.14 MB** | **Sub-20µs Tactical AST Candidate Reflex** (25.8% of 105MB envelope) |

```bash
# Run pure-Rust AST-MicroLM runtime with hardware telemetry:
cargo run --release -p nio-viper-runtime -- --prompt "Kill whatever process is listening on port 3000"
```

### 💻 How to Run & Practical Examples

```bash
# 1. Pull and cache verified Viper weights
nioxs pull viper

# 2. Pure-Rust AST-MicroLM terminal reflex (27.14 MB peak RAM, sub-20µs sampling)
nioxs viper "list folder pls"
# Output:
# Reflex Command: ls -la
# === AST-MicroLM Telemetry ===
# Runtime Engine: AST-MicroLM Candidate Reflex (< 20µs)
# Initial RAM: 11.70 MB | Peak RAM (VmHWM): 27.14 MB

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

## 🦈 6. Skate (135M) — Resident Micro-Guru & Edge Companion (`v-µLM Vector`)

**Skate** is the 134.5-million parameter resident edge companion and ambient telemetry triage model powered by the **`v-µLM Vector`** architecture. Using mathematical `IQ3_XXS` vector codebooks, it retains full 30-layer neural activation patterns in just **82.9 MB disk footprint** and operates within **22.4 MB peak resident RAM (`VmHWM`)**.

### 📊 25-Prompt Real-World Benchmark Telemetry

| Metric | Measured Value | System Analysis |
|:---|:---:|:---|
| **Peak Resident RAM (`VmHWM`)** | **< 50 MB** (40.85 MB peak, 27.6 MB idle) | **Pass**: Strict `< 50 MB` ceiling met; evicts inactive cache pages automatically. |
| **Generation Speed** | **35–42 tok/s** (Default) / **115–121 tok/s** (`--turbo`) | **Pass**: Near-instant responsiveness and super-speed turbo options. |
| **Prompt Ingestion Speed** | **220–240 tokens/sec** | **Pass**: Near-instant context processing (< 120ms for edge prompts). |
| **Binary Disk Footprint** | **82.93 MB** | Single unified `skate.vmicrolm-vector.gguf` file (`86,957,792 bytes`). |
| **Zero-Code Compliance** | **100% Passed** | Token-level filters for code blocks; clean deflection to Manta or Fin. |

### 💻 How to Run & Practical Examples

```bash
# 1. Pull and cache verified Skate weights (82.9 MB GGUF)
nioxs pull skate

# 2. Daily companion chat via NioXS Gateway (< 50 MB RAM)
nioxs skate "Tell me a fun fact about dolphins."

# 3. Super-speed high-throughput execution (>115 tok/s)
ast-micro-engine ~/.nioxs/models/skate.vmicrolm-vector.gguf ~/.nioxs/models/skate-tokenizer.json --turbo --prompt "Explain microwave physics simply"

# 4. Zero-code technical routing (clean delegation to Manta / Fin)
nioxs skate "Write a python script to parse JSON"
# Output: "I don't generate code directly. Please direct script execution to Manta or Fin..."

# 5. Native end-to-end companion run via NioAI CLI
nio run -m nioxs::nio-skate "What is a good way to stretch after typing for hours?"
```

### 🎯 Scope & Fleet Demarcation (What Skate Does vs. What It Delegates)

- **Native Edge Strengths (What Skate is Built For)**:
  - Ambient edge telemetry summarization and developer greeting.
  - Fast conversational companionship (NioGuru BFF and edge persona quick replies).
  - High-throughput prompt triage and intent classification in < 25 MB RAM.
  - Streaming responses at **15–24 words/second** with zero lag on low-power CPUs.
- **Architectural Boundaries (Why Skate Does NOT Write Free-Form Code)**:
  - At 135M parameters, unconstrained autoregressive sampling on intricate code synthesis (e.g. deep Rust borrow checker rules, Go concurrency channels, multi-stage Dockerfiles) triggers probability drift and token repetition loops (e.g. `mut mut mut`, `InvalidError(ErrorType)`).
  - **Deterministic Edge Execution**: When exact syntactic precision is required at < 100M scale, the **`v-µLM Reflex`** architecture with **Dynamic AST Grammars** (as implemented in `Viper`) is the mandatory pattern.
  - **Complex Code & Compiler Healing**: Deep coding, multi-line refactoring, and AST repair are delegated to upper-tier predators such as **Manta (494M)**.

---

## 🦈 7. Mako (150M) — Live Web Intelligence & Documentation Scout (`v-µLM Vector`)

**Mako** is the 150-million parameter live web intelligence and documentation scout powered by a 34-layer depth-upscaled dual-teacher architecture (SmolLM2-135M / Qwen2.5-Coder). It provides keyless multi-domain documentation search, sub-millisecond HTML pre-scrubbing, and LLM-Native Wire DSL generation with strict `[INVARIANT]` anchors. It features **HTTP 304 ETag caching** with a **50 MB hard LRU disk bound**, achieving **75.1%–99.0% context token reduction** with **12.49 MB peak resident RAM (`VmRSS`)** in a **92.0 MB binary footprint**.

### 💻 How to Run & Practical Examples

```bash
# 1. Pull and cache verified Mako weights (92.0 MB GGUF)
nioxs pull mako

# 2. Live documentation scout & Wire DSL generation (< 13 MB RAM, 13.5ms latency)
nioxs mako "tokio broadcast channel"

# 3. IETF RFC protocol specification navigator
nioxs mako "RFC 7540 HTTP/2 error codes"

# 4. Real-time security advisory & CVE triage
nioxs mako "CVE-2024-3094 backdoor summary"

# 5. Localhost Model Context Protocol (MCP) tool invocation (Claude, Cursor, Antigravity)
cargo run --bin nioxs-mcp << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"mako_web_scout","arguments":{"query":"tokio broadcast channel"}}}
EOF

# 6. Standalone CLI execution
./target/release/nioxs-mako "RFC 7540"
```

---

## 🦈 8. Manta (494M) — Full Conversational Guru & Wasm Architect (`v-µLM Vector`)

**Manta** is the 494.0-million parameter edge conversational guru and DAG task planner upscaled from Qwen2.5-0.5B via mathematical `IQ3_XXS` vector codebooks. Operating in under **55 MB peak RAM**, it powers the complete NioGuru 21-persona conversational suite, deep code analysis, and `<manta_plan>` multi-step DAG orchestrations.

### 💻 How to Run & Practical Examples

```bash
# 1. Pull and cache verified Manta weights (253.3 MB GGUF)
nioxs pull manta

# 2. Conversational system architecture triage across 21 NioGuru personas (< 55 MB RAM)
nioxs manta --persona architect "Design an event-driven CQRS pipeline with Raft consensus in Rust"

# 3. Generate multi-step <manta_plan> execution DAG for agentic orchestration
nioxs manta "Plan migration of our SQLite backend to high-throughput WAL mode with automated backups"

# 4. Deep multi-turn code review & edge refactoring
nioxs manta --file crates/router/src/lib.rs "Audit this router module for potential async runtime starvation"

# 5. Embedded in-process execution via Wasm runtime
nioxs manta --wasm-target web --prompt "Explain Rust memory safety to a beginner"
```

---

## 📦 Model Artifacts & Certified Checksums

### 🦈 Predator Tier & Web Scout Suite: Skate, Mako & Manta

| Artifact | Engine / Role | Format | Size | SHA-256 Checksum | Download Link |
|---|---|:---:|:---:|---|:---:|
| `skate.vmicrolm-vector.gguf` | Skate v-µLM Vector (134.5M Edge Companion) | GGUF IQ3_XXS Codebooks | 82.93 MB | `a00921dca072e640bb1f9730a95e3d88ed843cba3dd0a5648a6fd5e3e9e3d86b` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.6/skate.vmicrolm-vector.gguf) |
| `skate-tokenizer.json` | Skate Tokenizer (SmolLM2) | JSON | 2.10 MB | `9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.6/skate-tokenizer.json) |
| `mako.vmicrolm-vector.gguf` | Mako (150M, v-µLM Vector Scout) | GGUF IQ3_XXS Codebooks | 92.0 MB | `6c8836d82e766f3b40cfbbb2b01ece4adc7642c00748b0e546b8949ffc552c77` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.5/mako.vmicrolm-vector.gguf) |
| `manta.vmicrolm-vector.gguf` | Manta (494M, Conversational Guru & Architect) | GGUF IQ3_XXS Codebooks | 253.33 MB | `ed27ef71bf8c0c5f372efb0eef99b71a9c6480bf3e228ce2f1027fd3583d08bf` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.2/manta.vmicrolm-vector.gguf) |
| `manta-tokenizer.json` | Manta Tokenizer (Qwen2.5 151K Vocab) | JSON | 10.9 MB | `3fd169731d2cbde95e10bf356d66d5997fd885dd8dbb6fb4684da3f23b2585d8` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.2/manta-tokenizer.json) |

### ⚡ Core MicroLM Production Suite (v0.1.0)

| Artifact | Engine / Role | Format | Size | SHA-256 Checksum | Download Link |
|---|---|:---:|:---:|---|:---:|
| `viper.Q4_0.gguf` | Viper 100M (v-µLM Reflex Flagship) | GGUF Q4_0 | 61.69 MB | `58633aa691b80840dc85586cf2cb8616deff480c64ddf406bf848db749ecc3d4` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/viper.Q4_0.gguf) |
| `viper-tokenizer.json` | Viper Tokenizer | JSON | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/viper-tokenizer.json) |
| `nano.json` | Nano Intent (v-µLM Reflex) | JSON | 46.8 KB | `9b03e97096d232b76a4de3143b9ef0c76b6e9b64d241a289e99fe1e4977fe125` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nano.json) |
| `micro_base.onnx` | Micro Base (v-µLM Reflex) | ONNX | 13.82 MB | `4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/micro_base.onnx) |
| `micro_infra.onnx` | Micro Infra (v-µLM Reflex) | ONNX | 19.66 MB | `9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/micro_infra.onnx) |
| `micro_sec.onnx` | Micro Security (v-µLM Reflex) | ONNX | 19.66 MB | `c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/micro_sec.onnx) |
| `micro-tokenizer.json` | Micro Tokenizer | JSON | 17.5 KB | `1bbbcc91a0a0cf8ac64bbb577e5e3668e7aa7ba56e84ca56b22a237372edbb9f` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/micro-tokenizer.json) |
| `mask.onnx` | Mask Redactor (v-µLM Reflex) | ONNX | 4.43 MB | `a52fdcbc7c749b2d8b41b0c38f8f0cde1eafd7fef0b8ef1688ac80b6ae79b7ad` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/mask.onnx) |
| `mini.onnx` | Mini Defect (v-µLM Reflex) | ONNX | 27.14 MB | `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731` | [Download](https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/mini.onnx) |

---

## 🔌 Localhost Model Context Protocol (MCP) Server (`nioxs-mcp`)

> 📖 **Dedicated Documentation**: Read the full [Localhost MCP Guide & 99.62% Token Conservation Proof](https://nio-labs.github.io/nio-xs-models/mcp.html) on GitHub Pages.

The **Nio MCP Server** (`crates/nio-mcp`) runs 100% locally on standard I/O (`stdio`) or HTTP/SSE (`--port 8080`). It exposes all 6 MicroLM engines as zero-cost in-process tools for AI coding assistants (Cursor, Claude Desktop, Antigravity, OpenCode, Cline, Windsurf, Zed):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CODING AGENT (e.g. Claude / Cursor)             │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ MCP Standard JSON-RPC 2.0 (stdio)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              LOCAL NIO MCP SERVER (`nioxs-mcp` in Rust, 994KB)         │
├────────────────────────────────────────────────────────────────────────┤
│ • viper_synthesize(intent, shell)  ──► Sub-40ms POSIX/PS Command       │
│ • mask_sanitize(content)           ──► Sub-0.2ms Secret/PII Scrubber   │
│ • micro_audit(action, cluster)     ──► Sub-4ms Policy APPROVE/REJECT   │
│ • nano_route(text)                 ──► Sub-0.1ms Zero-Token Directive  │
│ • mini_predict_defect(diff)        ──► Sub-5ms Build Break Probability │
│ • mako_web_scout(query)            ──► Sub-15ms HTML Wire DSL Scrubber │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. ⚡ Token-Cutting Economics: 99.62% Workload Conservation (70%–85% Net Billing Cut)

Frontier reasoning models (Claude 3.5 Sonnet, GPT-4o) charge steep per-token pricing for operations that do not require multi-billion parameter reasoning. By routing deterministic triage, AST validation, policy gates, secret sanitization, and web scraping to local MicroLMs via `nioxs-mcp`, developers achieve **99.62% direct token conservation** on tool workloads (reducing 58,450 cloud prompt tokens to 225 tokens across the suite), delivering an overall **70%–85% net reduction** in daily frontier API billing:

| MCP Tool | MicroLM Engine | Local CPU Latency | What It Replaces on the Cloud | Per-Call Token Savings |
|---|---|:---:|---|:---:|
| **`nano_route`** | **Nano (~0.5M)** | **45 µs** | Upstream prompt triage & directive planning | **5,000 – 12,000 tokens** |
| **`mask_sanitize`** | **Mask (1.1M)** | **140 µs** | Cloud safety trips & multi-turn re-prompt loops | **2,000 – 5,000 tokens** |
| **`micro_audit`** | **Micro (5.0M)** | **3.8 ms** | Deliberation CoT reasoning for command safety | **1,500 – 3,000 tokens** |
| **`mini_predict_defect`** | **Mini (7.1M)** | **4.2 ms** | Multi-turn compile-break-retry agent debug loops | **10,000 – 30,000 tokens** |
| **`viper_synthesize`** | **Viper (100M)** | **38.2 ms** | Verbose LLM bash prose & boilerplate generation | **300 – 800 tokens** |
| **`mako_web_scout`** | **Mako (150M)** | **8 – 15 ms** | 100KB–300KB raw HTML bloat reduced to Wire DSL | **20,000 – 60,000 tokens (85–95%)** |

> **Real-World Daily Impact**: In an 8-hour agentic coding session, net token consumption typically plummets from **400,000 tokens/day** down to **~75,000 tokens/day** (70%–85% total billing cut), eliminating $1.00–$2.00/developer/day in API charges while cutting terminal interaction latency from seconds to milliseconds.

### 2. Available Production MCP Tools

| Tool Name | Engine | Role | Output Format |
|---|---|---|---|
| **`viper_synthesize`** | Viper (100M) | Synthesize POSIX / PowerShell cmdlets with Destructive Safety Clutch | Structured JSON (`command`, `is_destructive`, `clutch_reason`) |
| **`mask_sanitize`** | Mask (1.1M) | Zero-cloud secret & PII stream scrubber (API keys, tokens, passwords) | Sanitized string + secret count (0 false positives on git commits) |
| **`micro_audit`** | Micro (5.0M) | Contextual policy arbiter approving/rejecting file and infra mutations | Deterministic `APPROVE` / `REJECT` + continuous risk score |
| **`nano_route`** | Nano (~0.5M) | Sub-0.1ms command intent triage and zero-token directive router | Direct localhost execution action or routing metadata |
| **`mini_predict_defect`** | Mini (7.1M) | Pre-emptive defect and regression forecaster on code diffs | Defect probability, hazard category & invariant explanation |
| **`mako_web_scout`** | Mako (150M) | Zero-API key live documentation scout & HTML pre-scrubber | LLM-Native Wire DSL (`@api`) with HTTP 304 ETag caching |

### 3. Installation & Quick Start

#### Standalone Binary Download (994 KB)
```bash
# Direct download from GitHub Releases
curl -fsSL -o /usr/local/bin/nioxs-mcp https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.5/nioxs-mcp
chmod +x /usr/local/bin/nioxs-mcp
```

#### Install via Cargo
```bash
cargo install --git https://github.com/nio-labs/nio-xs-models nio-mcp
```

### 4. Configuration for Coding Agents

#### A. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "nio": {
      "command": "nioxs-mcp",
      "args": ["--stdio"]
    }
  }
}
```

#### B. Cursor / Antigravity / Windsurf (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "nio": {
      "command": "nioxs-mcp",
      "args": ["--stdio"]
    }
  }
}
```

#### C. Zed Editor (`~/.config/zed/settings.json`)
```json
{
  "experimental": {
    "model_context_protocol": {
      "servers": {
        "nio": {
          "command": "nioxs-mcp",
          "args": ["--stdio"]
        }
      }
    }
  }
}
```

### 5. Diagnostics & Self-Test
Run the built-in diagnostic test across all 6 MicroLM tools:
```bash
nioxs-mcp --test
```

---

## 📄 License

This repository is licensed under the [Business Source License 1.1](LICENSE) (BSL 1.1).

Third-party materials and model release provenance are documented in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); applicable license texts are in
[LICENSES](LICENSES/). Each model distribution must include its applicable
notices and license texts.

* **Non-Production & Internal Production Use**: Free to use, copy, modify, redistribute, and run internally within your organization for testing, development, and private infrastructure.
* **Commercial Protection Clause**: You may not offer the Licensed Work to third parties as a competing hosted, managed, or cloud service without a commercial license from Nio Labs.
* **Automatic Open Source Transition**: On **October 20, 2030** (four years from publication), this code automatically converts to the **Apache License, Version 2.0**.

For commercial licensing inquiries or enterprise deployments, contact `dev@n-o.me`.
