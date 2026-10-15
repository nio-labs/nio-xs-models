# Nio Models — Official ONNX Model Registry

This repository serves as the official distribution hub for compiled, production-ready neural models (**Nio Models**) used across the **Nio** and **NioXS** edge ecosystem.

Training datasets, raw curriculums, and internal training pipelines remain 100% private. Only compiled mathematical model binaries (`.onnx`) and domain tokenizers are distributed here as public release assets.

---

## What is a MicroLM? (Micro Learning Model)

> [!NOTE]  
> **MicroLM stands for Micro Learning Model — NOT Language Model.**

Modern AI is often equated with monolithic, 70B+ parameter generative Large Language Models (LLMs) that attempt to do everything through unstructured conversational prose. 

The **MicroLM methodology** represents a fundamental departure: instead of one bloated, slow, and hallucination-prone model, the Nio ecosystem uses a coordinated suite of **compact, task-dedicated Micro Learning Models** engineered for specific operational disciplines.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE MICRO LEARNING MODEL (MicroLM) PARADIGM                     │
└────────────────────────────────────────────────────────────────────────────────────────┘

        [ Monolithic Generative LLM ]               [ Nio MicroLM Suite ]
  Scope:       Jack-of-all-trades chatbot        Task-dedicated neural specialists
  Footprint:   7B to 400B+ parameters            0.5M to 250M parameter budgets
  Execution:   Cloud data centers (GPU clusters) Local edge execution (CPU / NPU)
  Latency:     200ms – 3,000ms per turn          0.5ms – 80ms in-process
  Outputs:     Ambiguous conversational text     Purpose-built artifacts (verdicts, vectors, code, DAGs)
  Economics:   Per-token API fees & recurring $   Zero API keys, zero cloud egress ($0.00)
  Reliability: Hallucination & stochastic drift  Mathematically bounded, calibrated models
```

### The 4 Universal Principles of the MicroLM Methodology

1. **Task-Dedicated Neural Intelligence:**  
   Rather than asking a general chatbot to guess answers through prompting, each MicroLM is built with a specialized architecture and trained against targeted domain loss functions:
   - **Analytical & Decision Heads:** Multi-head transformer encoders trained on cross-entropy and mean-squared error for policy verdicts and risk scoring (`NioMicro`).
   - **Predictive Forecasters:** Temporal and graph-loss networks trained to anticipate build failures and regression hazards before execution (`NioMini`).
   - **Coordinate & Geometric Decoders:** Continuous numerical decoders trained on SVG bezier curves, path geometry, and icon primitives (`NioMice`).
   - **Syntax-Constrained Generators:** Tree-aware decoders trained on abstract syntax trees (ASTs) and execution DAGs for clean code synthesis (`NioMega`, `NioMax`).
   - **Dense Retrieval Navigators:** Vector-indexed associative networks for fast knowledge mapping and web search synthesis (`NioMaze`).

2. **Purpose-Engineered Artifacts (Not Conversational Fluff):**  
   MicroLMs do not output chatty paragraphs that require regex parsing. They output exact, structured operational payloads:
   - Discrete verdicts (`approve` / `reject`) and continuous calibrated floats (`0.00` to `1.00`).
   - Clean, scalable SVG XML strings ready to render in browsers in < 100ms.
   - Deterministic refactoring diffs and dependency execution graphs.

3. **Edge-Native Economics & Zero Egress:**  
   Every MicroLM is compiled to standard ONNX or Candle tensors to execute **in-process** via native Rust on ordinary user devices:
   - Runs on standard laptop CPUs, edge servers, and mobile devices (Apple Silicon, Snapdragon, Raspberry Pi).
   - Instant response times (0.5ms to 80ms) without network roundtrips.
   - Complete privacy: code, diffs, and private data never leave `127.0.0.1`.

4. **Exact Mathematical Budgeting & Sovereignty:**  
   Every parameter in a MicroLM must earn its place. Models are engineered to exact, bounded capacities (e.g. `NioMicro` has exactly 3,500,000 parameters) to guarantee sub-millisecond latency and predictable resident memory.

---

## The Three Pillars of the MicroLM Galaxy (The 7 Titans)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 7 TITANS OF NIO                                    │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [ 1. COMPUTING & SYSTEMS ]      [ 2. VISUAL & CREATIVE ]       [ 3. WORLD & HUMANITIES ]
  • NioNano  — Command Triage     • NioMice — Scalable SVG,      • NioMaze — World History,
  • NioMicro — Decision Model                Avatars, Logos,                 Geography, Science,
  • NioMini  — Defect Forecaster             Badges & Icons                  Math, PM & Search
  • NioMega  — Code & Planning               (In < 100ms)                    Navigator
  • NioMax   — Swarm Architect
```

### Complete Model Family Matrix

| Titan | Role | Parameters | Specialization & Output Artifact | Status | Release Tag |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`NioNano`** | Assist Layer | ~0.5M | Lexical AST triage, command shortcuts & heuristic intent routing | Active | In Nio core |
| **`NioMicro`**| Decision Model | **3.5M (Exact)** | Multi-head policy gate: verdicts (`approve`/`reject`), sentiment & continuous risk score (`0.0`–`1.0`) | **Released** | [`v0.1.0`](https://github.com/nio-labs/nio-xs-models/releases/tag/v0.1.0) |
| **`NioMini`** | Predictive Model | ~8.5M | Pre-emptive defect forecaster, build-break & runtime regression predictor | Roadmap | Coming next |
| **`NioMice`** | Vector & Visual | ~55M | Instant scalable SVG generator: avatars, logos, icons & badges in < 100ms | Roadmap | In design |
| **`NioMega`** | Code & Planning | ~50M | High-precision code synthesis, AST refactoring patches & execution DAGs | Roadmap | In design |
| **`NioMaze`** | World Knowledge | ~150M | Knowledge retrieval, history, science, geography, math & live search navigator | Roadmap | Planned |
| **`NioMax`**  | Flagship Conductor| ~250M | Swarm conductor, repo-wide multi-file refactoring leader & macro architect | Roadmap | Planned |

---

## 1. NioMicro — Decision Model (3.5M)

**NioMicro** is the first published model in the Nio Models registry. It serves as the deterministic gatekeeper and decision arbiter for pull requests, security audits, and agent tool execution.

### Specifications
* **Architecture:** 4-Layer Bidirectional Transformer Encoder
* **Parameters:** **3,500,000 (Exact 3.5M)**
* **Inference Latency:** **< 5ms** on standard CPU (zero GPU needed)
* **Memory Footprint:** ~35 MB resident in RAM
* **Model Heads:**
  1. **Decision Head:** Binary verdict (`approve` / `reject`).
  2. **Sentiment Head:** Polarity detection (`positive` / `negative`).
  3. **Score Head:** Continuous calibrated score (`0.00` to `1.00`).

### Checksum Verification

```text
File:   nio_micro.onnx
Size:   14,588,852 bytes (~13.91 MiB)
SHA256: 4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb
```

### Direct Download

```bash
# Download latest production ONNX binary
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/download/v0.1.0/nio_micro.onnx"

# Verify integrity
sha256sum nio_micro.onnx
# 4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb  nio_micro.onnx
```

### Using with NioXS & Nio CLI

Place the downloaded model into the local NioXS model directory:
```bash
mkdir -p ~/.nioxs/models
mv nio_micro.onnx ~/.nioxs/models/
```

Or pull directly via the Nio CLI:
```bash
nioxs pull nio-micro
```

---

## License

The compiled model weights are distributed under the [MIT License](LICENSE).  
Internal training datasets, synthetic curriculums, and data generators are private and proprietary to Nio Labs.
