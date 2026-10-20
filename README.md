# Nio Models — Official ONNX Model Registry

This repository serves as the official distribution hub for compiled, production-ready neural models (**Nio Models**) used across the **Nio** and **NioXS** edge ecosystem.

Training datasets, raw curriculums, and internal training pipelines remain 100% private. Only compiled mathematical model binaries (`.onnx`) and domain tokenizers are distributed here as compiled release assets.

---

## What is a MicroLM? (Micro Learning Model)

> [!NOTE]  
> **MicroLM stands for Micro Learning Model — NOT Language Model.**

Modern AI is often equated with monolithic, multi-billion parameter generative Large Language Models (LLMs) that attempt to do everything through unstructured conversational prose.

The **MicroLM methodology** represents a fundamental departure: instead of relying on slow, resource-heavy, and hallucination-prone generative models, Nio develops **compact, task-dedicated Micro Learning Models** engineered for specific operational disciplines.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM) PARADIGM                     │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Generative Chatbot LLM ]                  [ Nio MicroLM ]
  Scope:       General-purpose conversational text   Task-dedicated neural intelligence
  Footprint:   7B to 400B+ parameters                Compact edge parameter budgets (e.g. 5M)
  Execution:   Cloud data centers (GPU clusters)     Local edge execution (standard CPU / NPU)
  Latency:     200ms – 3,000ms per turn              Sub-5ms in-process
  Outputs:     Ambiguous conversational paragraphs   Deterministic structured payloads
  Economics:   Per-token API fees & recurring bills  Zero API keys, zero cloud egress ($0.00)
  Reliability: Hallucination & stochastic drift      Mathematically bounded, calibrated models
```

### The 4 Universal Principles of the MicroLM Methodology

1. **Task-Dedicated Neural Intelligence:**  
   Rather than asking a general chatbot to guess answers through prompting, a Micro Learning Model is trained with targeted domain loss functions (e.g. multi-task cross-entropy and regression loss) to produce exact, calibrated outputs without conversational fluff.

2. **Purpose-Engineered Artifacts:**  
   MicroLMs do not output chatty paragraphs that require regex parsing. They output exact, structured operational payloads:
   - Discrete policy verdicts (`approve` / `reject` or `safe` / `unsafe`).
   - Calibrated continuous confidence scores (`0.00` to `1.00`).
   - Stance, polarity, and attention attribution tokens.

3. **Edge-Native Economics & Zero Egress:**  
   Every MicroLM is compiled to standard ONNX to execute **in-process** via native Rust on ordinary user devices:
   - Runs on standard laptop CPUs, edge servers, and mobile devices (Apple Silicon, Snapdragon, Raspberry Pi).
   - Instant response times (sub-5ms) without network roundtrips.
   - Complete privacy: code, diffs, and private data never leave `127.0.0.1`.

4. **Exact Mathematical Budgeting & Sovereignty:**  
   Every parameter in a MicroLM must earn its place. Models are engineered to exact, bounded capacities (e.g. `NioMicro` has exactly 5,000,000 parameters per cluster) to guarantee low latency and predictable resident memory.

---

## Available Production Models

| Model | Role | Parameters | Specialization & Output Artifact | Status | Official Release |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **`NioNano`** | Assist Layer | ~0.5M | Lexical AST triage, command shortcuts & heuristic intent routing | Active | In Nio core |
| **`NioMicro`**| Decision Engine | **5.0M / Cluster** | Domain-clustered policy gate (`sec`, `infra`, `base`, `fin`) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases) |
| **`NioMask`** | Security & Privacy | **1.1M** | Real-time byte-stream secret, API key & PII stream scrubber (< 0.2ms) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.3.0) |
| **`NioMini`** | Predictive Engine | **7.1M** | Pre-emptive defect forecaster, build break & regression prediction (< 5ms) | **Released** | [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases) |

---

## 1. NioNano — Command Triage & Intent Reflex (~0.5M)

**NioNano** is the embedded, sub-0.1ms assist layer in the MicroLM family. It acts as the very first line of defense inside developer terminals, IDE extensions, and CLI processes.

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

### Using with NioXS & Nio CLI

Place the downloaded cluster engines into your local NioXS model cache:
```bash
mkdir -p ~/.nioxs/models
mv nio_micro_sec.onnx ~/.nioxs/models/
mv nio_micro_infra.onnx ~/.nioxs/models/
mv nio_micro_base.onnx ~/.nioxs/models/
mv tokenizer.json ~/.nioxs/models/
```

Or pull directly via the Nio CLI:
```bash
nioxs pull nio-micro --cluster sec
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

```bash
# Pull NioMask via Nio CLI
nioxs pull nio-mask --version v0.1.0
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
* **Sha256:** `3bfb25d31d45ec1bfa61c697e25af944989655c01762bf9d7075c1fef942ef14`
* **Official Release Asset:** [`v0.3.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.3.0)
* **Training Pipeline:** Trainable via Google Colab T4 GPU: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nio-labs/nio-xs-models/blob/main/models/nio-mini/colab/NioMini_Training.ipynb) (see [`models/nio-mini/colab`](models/nio-mini/colab/README.md))

```bash
# Pull NioMini via Nio CLI
nioxs pull nio-mini --version v0.1.0
```

---

## Repository Architecture

This repository is the unified monorepo housing the source code, model definitions, and high-performance native Rust runtimes for the Nio MicroLM family:

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
