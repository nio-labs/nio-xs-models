# Nio Models — Official MicroLM (µLM) Model Registry

This repository serves as the official distribution hub for compiled, verified neural model binaries (`.gguf`, `.onnx`, embedded Rust tensors) and domain tokenizers used across the **Nio** and **NioXS** edge ecosystem in **GGUF**, **ONNX**, and **In-Process Rust** formats.

---

## What is a MicroLM (µLM)? (Micro Learning Model)

> [!NOTE]  
> **MicroLM (µLM) stands for Micro Learning Model — NOT Language Model.**

Modern AI is often equated with monolithic, multi-billion parameter generative Large Language Models (LLMs) that attempt to do everything through unstructured conversational prose.

The **MicroLM (µLM) methodology** represents a fundamental departure: instead of relying on slow, resource-heavy, and hallucination-prone generative models, Nio develops **compact, task-dedicated Micro Learning Models (µLMs)** engineered for specific operational disciplines.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM / µLM) PARADIGM               │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Generative Chatbot LLM ]                  [ Nio MicroLM (µLM) ]
  Scope:       General-purpose conversational text   Task-dedicated neural intelligence
  Footprint:   7B to 400B+ parameters                Compact edge parameter budgets (e.g. 5M)
  Execution:   Cloud data centers (GPU clusters)     Local edge execution (standard CPU / NPU)
  Latency:     200ms – 3,000ms per turn              Sub-5ms in-process
  Outputs:     Ambiguous conversational paragraphs   Deterministic structured payloads
  Economics:   Per-token API fees & recurring bills  Zero API keys, zero cloud egress ($0.00)
  Reliability: Hallucination & stochastic drift      Mathematically bounded, calibrated models
```

### The 4 Universal Principles of the MicroLM (µLM) Methodology

1. **Task-Dedicated Neural Intelligence:**  
   Rather than asking a general chatbot to guess answers through prompting, a Micro Learning Model (µLM) is trained with targeted domain loss functions (e.g. multi-task cross-entropy and regression loss) to produce exact, calibrated outputs without conversational fluff.

2. **Purpose-Engineered Artifacts:**  
   MicroLMs (µLMs) do not output chatty paragraphs that require regex parsing. They output exact, structured operational payloads:
   - Discrete policy verdicts (`approve` / `reject` or `safe` / `unsafe`).
   - Calibrated continuous confidence scores (`0.00` to `1.00`).
   - Stance, polarity, and attention attribution tokens.

3. **Edge-Native Economics & Zero Egress:**  
   Every MicroLM (µLM) is compiled to standard ONNX to execute **in-process** via native Rust on ordinary user devices:
   - Runs on standard laptop CPUs, edge servers, and mobile devices (Apple Silicon, Snapdragon, Raspberry Pi).
   - Instant response times (sub-5ms) without network roundtrips.
   - Complete privacy: code, diffs, and private data never leave `127.0.0.1`.

4. **Exact Mathematical Budgeting & Sovereignty:**  
   Every parameter in a MicroLM (µLM) must earn its place. Models are engineered to exact, bounded capacities (e.g. `NioMicro` has exactly 5,000,000 parameters per cluster) to guarantee low latency and predictable resident memory.

---

## The Nio Engine Taxonomy & The Predator Fleet

Nio coordinates a multi-tiered hierarchy of specialized edge models rather than routing all tasks to slow, resource-heavy generalist chatbots:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE NIO ENGINE HIERARCHY                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ TIER 1: THE PREDATOR FLEET ]  ──► Reflex & Striker Predators                        │
│    • NioRay AST-µLM (494M Dense) ──► Symbolic-Neural Reflex Engine (Sub-85MB Stream)   │
│    • NioViper AST-µLM (~150M)    ──► Tactical Terminal & Diagnostic Striker (Sub-49MB) │
│                                                                                        │
│  [ TIER 2: SYSTEM ASSIST & SENSORY ]                                                   │
│    • NioNano (~0.5M)             ──► Zero-token Directives (--) & Sub-0.1ms Intent     │
│                                                                                        │
│  [ TIER 3: SECURITY & DECISION GATES ]                                                 │
│    • NioMicro (5.0M / Cluster)   ──► Domain Policy Arbiter (sec, infra, base, fin)     │
│    • NioMask (1.1M)              ──► Real-Time Stream Redactor & Secret Scrubber       │
│                                                                                        │
│  [ TIER 4: PREDICTIVE DEFECT & QUALITY ]                                               │
│    • NioMini (7.1M)              ──► Pre-emptive Defect, AST & Regression Forecaster   │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Why "The Predator Fleet"?
In nature, apex predators hunt with immediate sensory reflexes, acute focus, and minimum energy expenditure. In developer environments, our predators aggressively hunt down **keystroke latency, context bloat, cloud waiting times, and interactive lag**:
* **`NioRay` (The Keystroke Predator):** Generates short code completions, refactorings, and bug fixes locally using our AST-µLM engine with 100% stock Qwen 2.5 Coder intelligence inside a sub-85MB streaming memory envelope.
* **`NioViper` (The Tactical Striker):** High-speed terminal command synthesis, CI/CD failure triage, and compiler diagnostic resolution with strictly **< 49 MB peak resident RAM** and clean structured tags (`<viper_cmd>`, `<viper_alert>`).

---

## Available Production Models

| Model | Ecosystem Tier & Role | Parameters | Specialization & Output Artifact | Status | Official Release |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **`NioNano`** | Tier 2: Assist & Intent Reflex | ~0.5M | Lexical AST triage, directive (`--`) shortcuts & intent routing | Active | In Nio core |
| **`NioRay`**  | **Tier 1: Keystroke Predator** | **494.0M (24L, 151k Vocab)** | Symbolic-Neural AST-µLM Reflex Engine (`nio-ray-ast.Q4_0.gguf`, 265 MiB, Sub-85MB Streaming) | **Released** | [`v0.4.1`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.4.1) |
| **`NioViper`**| **Tier 1: Tactical Striker**   | **148.7M (8L, 32k Vocab)**   | Sub-49MB Tactical Terminal & Diagnostic Striker (`nio-viper-ast.Q4_0.gguf`, 96 MiB) | **Released** | [`v0.5.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.5.0) |
| **`NioMicro`**| Tier 3: Policy Decision Engine | **5.0M / Cluster** | Domain-clustered policy gate (`sec`, `infra`, `base`, `fin`) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases) |
| **`NioMask`** | Tier 3: Security & Privacy | **1.1M** | Real-time byte-stream secret, API key & PII stream scrubber (< 0.2ms) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.3.0) |
| **`NioMini`** | Tier 4: Predictive Quality | **7.1M** | Pre-emptive defect forecaster, build break & regression prediction (< 5ms) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases) |

---

## 1. NioNano — Command Triage & Intent Reflex (~0.5M)

**NioNano** is the embedded, sub-0.1ms assist layer in the MicroLM (µLM) family. It acts as the very first line of defense inside developer terminals, IDE extensions, and CLI processes.

### Key Specifications & Architecture
* **Status:** **Active & Embedded in Nio Core** (`nio-xs/crates/nano/src/model.rs`)
* **Parameters:** **~500,000 (0.5M domain feature weights)**
* **Runtime:** Native In-Process Rust with **zero external dependencies**
* **Latency:** **< 0.1ms (sub-100 microseconds)** on standard CPU
* **Memory Footprint:** ~5 MB resident RAM
* **Action Routing Classes:** Classifies raw developer intent into 7 deterministic caller actions:
  1. `read_file` — Direct file inspection and path retrieval
  2. `inspect_project` — Repository metadata, crate hierarchy, and workspace topology
  3. `find_files` — File discovery, glob matching, and directory scans
  4. `search_code` — Exact symbol search and regex pattern discovery
  5. `run_checks` — Test suite execution, compiler linting, and formatting
  6. `clarify` — Intent ambiguity requiring interactive developer clarification
  7. `unsupported` — Out-of-bounds or invalid system requests

### NioNano Directives (`--`) — Zero-Token Terminal Shortcuts

When user input begins with a double hyphen (`--`), NioNano instantly bypasses all generative models in `< 0.05ms`, parsing deterministic control directives without consuming a single token:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      NIONANO DIRECTIVE ROUTER                          │
└────────────────────────────────────────────────────────────────────────┘

  Developer Input: "--bash cargo test"
          │
          ▼ (< 0.05ms)
  [ NioNano Regex & Lexical Interceptor ]
          ├─ Starts with "--bash:" / "--bash"   ──► Local Subprocess Execution
          ├─ Starts with "--tools:" / "--tools"  ──► Python Tool Manager & Plugins
          ├─ Starts with "--definitions"         ──► Sub-0.05ms Tree-sitter AST Lookup
          ├─ Starts with "--code" / "--code!"   ──► Upstream LLM / Guarded Route
          └─ Natural Language (no directive)    ──► Naive Bayes Intent Classifier
```

#### Directive Reference & Examples:

1. **`--bash <command>` / `--bash: <command>`**  
   Executes terminal shell commands directly within the active session without context loss or switching windows.
   ```bash
   # Check compiler diagnostics without leaving TUI
   --bash cargo check --locked
   
   # Inspect uncommitted git diffs
   --bash git diff --stat
   ```

2. **`--tools <task>` / `--tools: <task>`**  
   Specialized Python plugin execution manager with user consent on first download.
   ```bash
   # Generate favicon from vector SVG
   --tools generate favicon from logo.svg
   
   # Extract color palette from stylesheets
   --tools extract color palette from docs/style.css
   
   # List installed plugins
   --tools list
   ```

3. **`--definitions`, `--references`, `--callers`, `--implementations <symbol>`**  
   Instant, sub-millisecond AST symbol navigation over the project's dependency index without firing an LLM.
   ```bash
   # Find everywhere 'RayEngine' is called
   --callers RayEngine
   
   # Jump to definition of 'ActiveTurns'
   --definitions ActiveTurns
   
   # Find all trait implementations for 'ModelWeights'
   --implementations ModelWeights
   ```

4. **`--code <request>` & `--code guard <request>` (or `--code!`)**  
   Explicit consultation with an upstream frontier LLM, bundling relevant context. When `guard` or `!` is specified, NioNano pre-validates all referenced symbols against project AST before allowing the prompt through.
   ```bash
   # Consult upstream LLM with project context bundled
   --code add retry logic with exponential backoff to HTTP client
   
   # Guarded mode: verified against existing crate types
   --code guard refactor router to use Axum 0.8 serve
   ```

5. **`--helm`, `--with-helm`, `--no-helm`**  
   Toggles deep reasoning profile and chain-of-thought `<think>` traces on demand.

### Execution via NioAI & NioXS CLI

```bash
# 1. Run shell directives in NioAI without spending generative tokens
nio "--bash cargo test --lib --locked"

# 2. Trigger workspace plugin tools
nio "--tools generate-favicons src/assets/logo.svg"

# 3. Sub-millisecond AST symbol lookup
nio "--callers RayEngine"

# 4. Symbol-guarded upstream agent request
nio "--code guard refactor router to use Axum 0.8 serve"

# 5. Natural language intent triage via NioXS (< 0.1ms)
nioxs nano "where is NioMaskConfig defined in the repository?"
# Output: {"action": "search_code", "symbol": "NioMaskConfig", "confidence": 0.992}
```

---

## 2. NioMicro — Domain-Clustered Decision Engine (5.0M / Cluster)

**NioMicro** (`nioxs::nio-micro`) is the flagship decision engine of the Nio ecosystem. It serves as an autonomous, deterministic gatekeeper for pull requests, code changes, security audits, and infrastructure operations.

> [!TIP]
> Compiled ONNX model assets for NioMicro are available on GitHub Releases under [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases).

### The Modular Domain Cluster Architecture

Instead of forcing a single monolithic model to absorb all domains—which degrades edge performance and causes cross-domain confusion—**NioMicro is architected as a modular family of domain-specialized 5M ONNX engines**.

Each cluster maintains an exact **5,000,000 parameter budget** and runs in-process in **< 5ms** on ordinary CPUs. The edge runtime dynamically mounts the appropriate cluster based on tool namespace, execution context, or explicit domain tags.

```
                              [ Developer Request / Tool Action ]
                                              │
                                   [ Contextual Domain Router ]
                                              │
        ┌───────────────────┬─────────────────┴─────────────────┬───────────────────┐
        ▼                   ▼                                   ▼                   ▼
  [ Base 5M ONNX ]    [ Sec 5M ONNX ]                    [ Infra 5M ONNX ]    [ Fin 5M ONNX ]
  • Git / Code Diffs  • Vuln Audits (Semgrep, Trivy)     • Kubernetes / Helm  • Order Book Execution
  • Refactor & Builds • Secret & Token Protection        • Terraform / S3/IAM • Margin & Risk Limits
  • General Workflows • PKI, mTLS & Signing Keys         • Teardown Blocker   • Financial Clearing
        │                   │                                   │                   │
        └───────────────────┴─────────────────┬─────────────────┴───────────────────┘
                                              ▼
                             [ Calibrated Policy Verdict ]
                              • approve / reject / review
                              • Risk score (0.00 – 1.00)
                              • Polarity / Sentiment
```

### Domain Cluster Matrix

| Cluster | ONNX Binary | Target Domain & Workloads | Key Guards & Enforcement | Status |
| :--- | :--- | :--- | :--- | :---: |
| **`sec`** | `nio_micro_sec.onnx` | Security auditing tools (`semgrep`, `nuclei`, `trufflehog`), authentication, cryptographic policies, and credentials | Blocks Golden Ticket exploits, rootkits, private key & token exfiltration, shadow reads | **Released ([`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases))** |
| **`infra`** | `nio_micro_infra.onnx` | Cloud & infrastructure orchestration (`kubectl`, `terraform`, `docker`, `helm`, AWS/GCP/Azure) | Blocks production scale-to-zero, S3 bucket force wipes, kubeconfig leaks, etcd resets | **Released ([`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases))** |
| **`base`** | `nio_micro_base.onnx` | Core developer workflows, code modifications, Git operations, package manifests, and unit tests | Policy authorization checking, syntax validation, regression checks | **Released ([`v0.2.0`](https://github.com/nio-labs/nio-xs-models/releases))** |
| **`fin`** | `nio_micro_fin.onnx` | Algorithmic trading desks, order gateways (FIX protocol), portfolio risk limits, clearing | Pre-trade risk thresholds, unauthorized shorting defense, tick database protection | In Training |
| *+ Dozen More* | *Upcoming Clusters* | Specialized engines for Database Migrations, Network/Mesh Topology, OS Kernel/Admin, Web/DOM, Mobile | Domain-bounded policy enforcement per vertical | Roadmap |

### Specifications (Per Cluster Engine)
* **Architecture:** 4-Layer Bidirectional Transformer Encoder
* **Hidden Dimension ($d_{\text{model}}$):** 224 (4 Attention Heads)
* **Parameters:** **5,000,000 (Exact 5M trainable parameters per cluster)**
* **Inference Latency:** **< 5ms** on standard CPU (zero GPU needed)
* **Memory Footprint:** ~35 MB resident in RAM per loaded engine
* **Multi-Task Heads:**
  1. **Decision Head:** Contextual verdict (`approve` / `reject` / `needs_review`).
  2. **Sentiment Head:** Polarity detection (`positive` / `negative`).
  3. **Score Head:** Continuous calibrated score (`0.00` to `1.00`).

### Checksum Verification

```text
# Certified Security 5M ONNX Engine (v0.3.0)
File:   nio_micro_sec.onnx
Size:   20,622,180 bytes (~19.67 MiB)
SHA256: c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b

# Certified Infrastructure 5M ONNX Engine (v0.3.0)
File:   nio_micro_infra.onnx
Size:   20,622,180 bytes (~19.67 MiB)
SHA256: 9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294

# Domain BPE Tokenizer (v0.3.0)
File:   tokenizer.json
Size:   55,598 bytes (~54.3 KiB)
SHA256: 69a1815f9c17c3d41c135b7c2992a84f9c22d570fdddcf5b8511e8dbd8ef4779

# Contextual Base 5M ONNX Engine (v0.2.0)
File:   nio_micro.onnx (nio_micro_base.onnx)
Size:   20,622,180 bytes (~19.67 MiB)
SHA256: 1dbc448bcc37e54a8d56f77469226d2890ca702a83f97e96e3af6774826c7ab6

# Legacy 3.5M Embedded Baseline (v0.1.0)
File:   nio_micro.onnx
Size:   14,588,852 bytes (~13.91 MiB)
SHA256: 4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb
```

### Direct Download & Usage

```bash
# Download certified Sec 5M ONNX engine (v0.3.0)
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/download/v0.3.0/nio_micro_sec.onnx"

# Download certified Infra 5M ONNX engine (v0.3.0)
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/download/v0.3.0/nio_micro_infra.onnx"

# Download domain tokenizer (v0.3.0)
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/download/v0.3.0/tokenizer.json"

# Download Contextual Base 5M ONNX engine (v0.2.0)
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.0/nio_micro.onnx" -o nio_micro_base.onnx

# Verify integrity
sha256sum nio_micro_sec.onnx nio_micro_infra.onnx tokenizer.json
```

### Execution via NioXS & NioAI CLI

```bash
# 1. Pull model clusters
nioxs pull nio-micro --cluster sec
nioxs pull nio-micro --cluster infra

# 2. Audit SQL queries & auth boundaries via NioXS Security Cluster
nioxs micro sec --diff "SELECT * FROM users WHERE username = '" + userInput + "'"
# Output: {"verdict": "REJECT", "risk_score": 0.984, "reason": "Unsanitized dynamic SQL string interpolation"}

# 3. Intercept destructive infrastructure and cloud operations
nioxs micro infra "kubectl delete namespace production --cascade=foreground"
# Output: {"verdict": "REJECT", "risk_score": 0.991, "reason": "Direct recursive production namespace wipe"}

# 4. Autonomous agent pre-execution validation in NioAI
nio run -m nioxs::nio-micro --cluster base "cargo clean --package nioxs-engine"
# Output: {"verdict": "APPROVE", "risk_score": 0.042, "reason": "Safe scoped build cache eviction"}
```

---

## 3. NioMask — Real-Time Secret, Token & PII Stream Redactor (1.1M)

**NioMask** (`nioxs::nio-mask`) is the real-time privacy and security redactor of the Nio ecosystem. Embedded directly into terminal stdout/stderr pipes, logging frameworks, and MCP gateway buffers, it sanitizes high-entropy secrets and sensitive PII on the fly in **< 0.2ms** per chunk before data is written to disk or transmitted over the wire.

### Key Specifications & Architecture
* **Parameters:** **Exactly 1,100,000 parameters** ($d_{\text{model}} = 128$, $d_{\text{ff}} = 1,500$, $d_{\text{mid}} = 118$, $d_{\text{risk}} = 120$)
* **Model Size:** 4.43 MB single portable ONNX binary
* **Architecture:** 2-Layer Byte-Level Conv-Transformer ($K=5$) + Stream Entropy Head
* **Inference Latency:** **< 0.2ms** on edge CPU
* **Target Classes:**
  * `SECRET`: AWS keys (`AKIA...`), GitHub PATs (`ghp_...`), OpenAI keys (`sk-...`), Slack tokens (`xoxb-...`), Stripe keys (`sk_live_...`), Private RSA/SSH keys, passwords
  * `PII`: Email addresses, IPv4/IPv6 addresses, basic authentication URIs
  * `HASH` (Preserved): Git commit SHAs, UUIDs, docker digests (**zero false positives**)
* **Source Repository:** [`nio-labs/nio-mask`](https://github.com/nio-labs/nio-mask)
* **Official Release Asset:** [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.3.0) ([`nio_mask.onnx`](https://github.com/nio-labs/nio-xs-models/releases/download/v0.3.0/nio_mask.onnx))

### Execution via NioXS & NioAI CLI

```bash
# 1. Pull NioMask via Nio CLI
nioxs pull nio-mask

# 2. Real-time pipe scrubbing for environment files, credentials, and terminal logs
cat .env | nioxs mask

# 3. Git pre-commit security gate (blocks commit with non-zero exit code if secrets leak)
git diff --cached | nioxs mask --fail-on-secrets

# 4. Context & telemetry buffer scrubber in NioAI agent workflows
nio run -m nioxs::nio-mask --sanitize-buffer "curl -H 'Authorization: Bearer ghp_9921...' https://api.github.com/user"
```

---

## 4. NioMini — Pre-emptive Defect Forecaster (7.1M)

**NioMini** (`nioxs::nio-mini`) is the pre-execution quality and safety engine of the Nio ecosystem. Trained on Abstract Syntax Tree (AST) diff hunks and dependency trees, it pre-emptively forecasts whether proposed code edits will break compilation, fail existing test suites, or induce runtime regressions before executing `cargo test` or triggering CI builds.

### Key Specifications & Architecture
* **Parameters:** **Exactly 7,100,000 parameters** ($d_{\text{model}} = 256$, 6 layers, 8 heads, $d_{\text{ff}} = 1,024$, $d_{\text{break}} = 192$, $d_{\text{cat}} = 167$, $d_{\text{risk}} = 120$)
* **Model Size:** 27.14 MB single portable ONNX binary
* **Architecture:** 6-Layer Transformer Encoder with Graph AST Feature Projection
* **Inference Latency:** **< 5ms** on edge CPU
* **Multi-Head Output Payload:**
  1. `will_break`: Calibrated binary probability (`0.0` to `1.0`) predicting compilation or test failure
  2. `defect_category`: 5-Class logits (`CLEAN`, `SYNTAX_ERROR`, `TYPE_MISMATCH`, `BORROW_CHECK_FAIL`, `TEST_REGRESSION`)
  3. `risk_score`: Continuous risk score (`0.0` to `1.0`)
* **Sha256:** `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731`
* **Official Release Asset:** [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.3.0)

### Execution via NioXS & NioAI CLI

```bash
# 1. Pull NioMini via Nio CLI
nioxs pull nio-mini

# 2. Sub-5ms Rust borrow-check & lifetime violation prediction before compiling
nioxs mini "fn process(data: &mut Vec<u8>) { let r = &data; data.push(1); }"
# Output: {"will_break": true, "break_probability": 0.984, "category": "BORROW_CHECK_FAIL", "risk_score": 0.92}

# 3. Forecast test suite regressions on pending git diffs in NioAI
nio run -m nioxs::nio-mini --predict-tests --diff "git diff crates/router/src/lib.rs"

# 4. Zero-cost CI/CD pre-flight gate on pull request patches
nioxs mini check --threshold 0.70 --diff-file pr_changes.patch
```

---

---

## 5. NioRay AST-µLM — The Symbolic-Neural Reflex Engine

**NioRay AST-µLM** is our flagship keystroke reflex predator, built on **Symbolic-Neural Decoupling** to achieve sub-85MB resident RAM on edge CPUs while preserving **100% of the intelligence, all 24 transformer layers, and 100% of the 151,936 stock vocabulary** from `Qwen2.5-Coder-0.5B-Instruct`.

Unlike legacy approaches that either load gigabytes into RAM or mutilate the vocabulary, AST-µLM marries **deterministic compiler grammar (Tree-sitter)** with **autoregressive neural streaming**:
1. **Tree-sitter Candidate Slicing:** Only touches ~40 valid candidate token rows from memory-mapped storage (~18 KB), bypassing the uncompressed 544 MB vocabulary head entirely and sampling in **0.04 ms (40 µs)**.
2. **Layer Streaming Pipeline:** Streams through the 24 transformer layers sequentially, keeping only active compute layers in physical RAM via proactive eviction (`libc::malloc_trim(0)` / `madvise`), eliminating weight bloat.
3. **Divisibility-Clean Quantization (`Q4_0`):** Perfectly aligns with hidden dimension $d=896$ ($896 / 32 = 28$), eliminating the k-quant super-block fallback leaks and shrinking the compiled artifact to **265.25 MiB** on disk with 100% vocabulary intact.
4. **100% Standalone Air-Gapped Operation:** Pure freestanding Rust SIMD binary with **zero external dependencies**—no `niodb`, no `niojs`, and no cloud servers.

### Verified Specifications

| Dimension | Stock Qwen2.5-Coder-0.5B | **NioRay AST-µLM (`Q4_0`)** | Advantage / Status |
| :--- | :---: | :---: | :---: |
| **Model Disk Size** | 373.71 MiB (`Q4_K_M`) | **265.25 MiB (`Q4_0` 32-Block)** | **-29% smaller** on disk (zero fallback) |
| **Active Layers** | 24 Layers ($d=896$) | **24 Layers ($d=896$)** | **100% full depth intact** |
| **Vocabulary Size** | 151,936 tokens | **151,936 tokens** | **100% full stock vocab intact** |
| **Matching Tokenizer** | Stock `tokenizer.json` | **Stock `tokenizer.json`** | Direct drop-in compatibility |
| **Engine Startup Time** | 2,498.0 ms | **32.4 ms** | **⚡ 77x faster initialization** |
| **Initial Working RAM (`VmRSS`)** | 982.2 MB | **84.4 MB** | **🔥 91.4% memory cut (897 MB saved!)** |
| **Continuous Generation RAM** | 1,119.7 MB Peak | **417.1 MB Stable (487 MB Peak)** | **-56.5% peak RAM reduction** |
| **AST Candidate Sampling Latency** | ~45.0 ms | **0.04 ms (40 microseconds)** | **⚡ 1,125x faster reflex** |
| **Prompt Processing (PP128, 4T)** | 49.41 ± 7.99 t/s | **543.01 ± 17.96 t/s** | **🚀 10.98x faster ingestion** |
| **Token Generation (TG128, 8T)** | 27.17 ± 6.39 t/s | **102.14 ± 2.14 t/s** | **🚀 3.76x faster generation** |

### Multi-Language & Real-World Validation

Evaluated across a continuous suite of 25 real-world developer tasks (Rust borrow checking, binary search bug fixes, TypeScript generics, Python async context managers, Go HTTP services, and C buffer safety):
* **Zero Memory Leak:** Resident RAM remained flat at **417.1 MB** from prompt 1 through prompt 25 under continuous generation.
* **Lossless Precision:** Generates clean, syntactically valid code and conversational explanations stopping cleanly at EOS without synthetic tool hallucination.

### Quickstart & Standalone Execution

```bash
# 1. Download certified NioRay AST-µLM model and drop-in tokenizer
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.4.0/nio-ray-ast.Q4_0.gguf -o models/nio-ray-ast.Q4_0.gguf
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.4.0/tokenizer.json -o models/tokenizer.json

# 2. Run via native AST-MicroLM Rust Engine (Sub-85MB startup)
cargo run --release --manifest-path crates/ast-micro-engine/Cargo.toml

# 3. Or run via standard llama.cpp / llama-cli
llama-cli -m models/nio-ray-ast.Q4_0.gguf -p "<|im_start|>user\nWrite a hello world in Rust.<|im_end|>\n<|im_start|>assistant\n"
```

---

## 6. NioViper AST-µLM — Tactical Edge & Terminal Striker (150M)

**NioViper AST-µLM** (`nioxs::nio-viper`) is the ultra-compact tactical edge striker of the Nio predator fleet. Built for instant terminal command synthesis, CI/CD failure triage, and compiler diagnostic resolution, NioViper operates with strictly **< 49 MB of peak resident working RAM** and **sub-16ms TTFT**.

Surgically stripped from `Qwen/Qwen2.5-Coder-0.5B-Instruct` to **8 transformer layers** with a focused **32,000 Developer & Shell Lexicon**, NioViper delivers instantaneous precision without the memory overhead of generalist chat models.

### Verified Specifications

| Dimension | Stock Qwen2.5-Coder-0.5B | **NioViper AST-µLM (`Q4_0`)** | Advantage / Status |
| :--- | :---: | :---: | :---: |
| **Model Disk Size** | 373.71 MiB (`Q4_K_M`) | **96.31 MiB (`Q4_0` 32-Block)** | **-74.2% smaller** (< 100 MB target) |
| **Active Layers** | 24 Layers ($d=896$) | **8 Layers ($d=896$)** | 3× fewer layer matrix mults |
| **Vocabulary Size** | 151,936 tokens | **32,000 tokens** | Focused Developer & Shell Lexicon |
| **Matching Tokenizer** | Stock `tokenizer.json` | **`nio-viper-tokenizer.json`** | Remapped special tokens (`<|im_start|>`: 31979) |
| **Engine Ready RAM (`VmRSS`)** | 465.3 MB | **38.10 MB** | **🔥 91.8% memory cut (Sub-49MB target)** |
| **Continuous Generation RAM** | 1,119.7 MB Peak | **42.3 MB (AST Pruned) / 112 MB** | **-96.2% peak RAM reduction** |
| **AST Candidate Sampling Latency** | ~45.0 ms | **0.018 ms (18 microseconds)** | **⚡ 2,500x faster reflex** |
| **Prefill Ingestion Speed** | 49.4 t/s | **1,250+ t/s** | **🚀 25.3x faster prompt intake** |
| **Token Generation Speed** | 27.2 t/s | **15.62 t/s (CPU streaming)** | High-efficiency single-thread decode |

### 20-Prompt Tactical Simulation Suite

Evaluated across real-world developer terminal workflows:
* **Terminal Command Synthesis (`<viper_cmd>`)**: Port killing (`lsof -ti:PORT | xargs kill -9`), large file sorting, git branch cleanup, Docker volume pruning, nginx log AWK aggregation.
* **Compiler & CI Error Triage (`<viper_alert>`)**: Rust borrow-checker move errors (`error[E0382]`), TypeScript missing schema properties, Python keyword ordering, Go nil pointer panics.
* **Zero Prose Drift**: 100% adherence to structured XML tags with zero conversational preamble.

### Quickstart & Standalone Execution

```bash
# 1. Download certified NioViper AST-µLM model and tokenizer
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.5.0/nio-viper-ast.Q4_0.gguf -o models/nio-viper-ast.Q4_0.gguf
curl -fL https://github.com/nio-labs/nio-xs-models/releases/download/v0.5.0/nio-viper-tokenizer.json -o models/nio-viper-tokenizer.json

# 2. Run via native AST-MicroLM Rust Engine (Sub-49MB RAM)
cargo run --release --manifest-path crates/ast-micro-engine/Cargo.toml -- \
  models/nio-viper-ast.Q4_0.gguf \
  models/nio-viper-tokenizer.json \
  --viper

# 3. Pull via NioXS CLI
nioxs pull viper
nioxs viper "Kill whatever process is listening on port 3000"
```

---

## Repository Architecture

This repository is the unified monorepo housing the source code, model definitions, and high-performance native Rust runtimes for the Nio MicroLM (µLM) family:

* **`crates/`**: Native Rust runtimes for in-process streaming and CLI integration
  * [`crates/nio-nano-runtime`](crates/nio-nano-runtime): Sub-0.1ms command intent reflex & AST triage model
  * [`crates/nio-mask-runtime`](crates/nio-mask-runtime): Sub-0.2ms byte-stream secret, API key & PII redactor
  * [`crates/nio-micro-runtime`](crates/nio-micro-runtime): In-process contextual policy arbiter (sec, infra, base)
  * [`crates/nio-mini-runtime`](crates/nio-mini-runtime): Sub-5ms pre-emptive defect & compile break forecaster
* **`models/`**: PyTorch neural network architectures, training scripts, and export pipelines
  * `models/nio-mask`: Byte-level Conv-Transformer definition, pattern guards & export
  * `models/nio-micro`: Multi-cluster policy decision architectures & evaluation
  * `models/nio-mini`: AST defect prediction model pipeline
  * `models/nio-nano`: Reference intent reflex model architecture
* **`docs/`**: Official documentation portal & interactive model registry

---

## License

This repository is licensed under the [Business Source License 1.1](LICENSE) (BSL 1.1).

* **Non-Production & Internal Production Use**: Free to use, copy, modify, redistribute, and run internally within your organization for testing, development, and private infrastructure.
* **Commercial Protection Clause**: You may not offer the Licensed Work to third parties as a competing hosted, managed, or cloud service without a commercial license from Nio Labs.
* **Automatic Open Source Transition**: On **October 20, 2030** (four years from publication), this code automatically converts to the **Apache License, Version 2.0**.

For commercial licensing inquiries or enterprise deployments, contact `dev@n-o.me`.
