# Nio Models — Official ONNX Model Registry

This repository serves as the official distribution hub for compiled, production-ready neural models (**Nio Models**) used across the **Nio** and **NioXS** edge ecosystem.

Training datasets, raw curriculums, and internal training pipelines remain 100% private. Only compiled mathematical model binaries (`.onnx`) and domain tokenizers are distributed here as public release assets.

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
  Footprint:   7B to 400B+ parameters                Compact edge parameter budgets (e.g. 3.5M)
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
   Every parameter in a MicroLM must earn its place. Models are engineered to exact, bounded capacities (e.g. `NioMicro` has exactly 3,500,000 parameters) to guarantee low latency and predictable resident memory.

---

## 1. NioMicro — Decision Model (3.5M)

**NioMicro** (`nioxs::nio-micro`) is the flagship decision engine in the Nio Models registry. It serves as an autonomous, deterministic gatekeeper for pull requests, code reviews, and safety policy gating.

### Specifications
* **Architecture:** 4-Layer Bidirectional Transformer Encoder
* **Parameters:** **3,500,000 (Exact 3.5M)**
* **Inference Latency:** **< 5ms** on standard CPU (zero GPU needed)
* **Memory Footprint:** ~35 MB resident in RAM
* **Multi-Task Heads:**
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
# Download latest production ONNX binary from GitHub Releases
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
