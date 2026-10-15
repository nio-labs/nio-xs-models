# Nio Models — Official ONNX Model Registry

This repository serves as the official distribution hub for compiled, production-ready neural models (**Nio Models**) used across the **Nio** and **NioXS** edge ecosystem.

Training datasets, raw curriculums, and internal training pipelines remain 100% private. Only compiled mathematical model binaries (`.onnx`) and domain tokenizers are distributed here as public release assets.

---

## What is a MicroLM? (Micro Learning Model)

> [!NOTE]  
> **MicroLM stands for Micro Learning Model — NOT Language Model.**

While modern AI is dominated by generative Large Language Models (LLMs) that output conversational paragraphs token-by-token, the **MicroLM methodology** represents a fundamental paradigm shift for autonomous edge systems, CI/CD quality gates, and developer tooling:

```
┌────────────────────────────────────────────────────────────────────────┐
│                     THE MICRO LEARNING MODEL PARADIGM                  │
└────────────────────────────────────────────────────────────────────────┘

        [ Traditional Generative LLM ]          [ Nio MicroLM ]
  Task:        Text generation (prose)        Analytical verdict & decision
  Footprint:   7B – 70B+ parameters           0.5M – 50M parameters
  Latency:     200ms – 2,000ms (Cloud)        1ms – 5ms (Local Edge CPU)
  Reliability: Hallucination risks            Deterministic calibrated math
  Output:      Paragraphs of text             Structured tensors & JSON
  Egress:      Sends code to cloud            100% Localhost / Air-gapped
```

### The 4 Pillars of MicroLM Methodology

1. **Deterministic Verification vs. Generative Hallucination:**  
   Rather than asking a chatbot *"Is this code safe?"* and parsing ambiguous text replies, a Micro Learning Model is an analytical neural encoder trained to output mathematical certainty:
   - **Binary Verdicts:** Instant `approve` / `reject` or `safe` / `unsafe`.
   - **Calibrated Risk Scores:** Continuous floats (`0.00` to `1.00`) representing verifiable quality and risk indices.
   - **Polarity & Stance:** Clean sentiment analysis without conversational noise.

2. **Multi-Head Neural Architecture:**  
   Instead of using separate models for decisions, scoring, and sentiment, a MicroLM uses a shared, ultra-compact transformer backbone paired with dedicated prediction heads. In `NioMicro`, a single inference pass simultaneously computes decisions, sentiment, and confidence scores.

3. **Sub-Millisecond Edge Economics:**  
   MicroLMs execute **in-process** via native Rust (`ort` ONNX Runtime) in **1ms to 5ms** on commodity laptop CPUs. They consume less than 35 MB of RAM, require zero GPUs, and incur zero per-token API costs.

4. **The Micro Philosophy:**  
   "Micro" defines the entire engineering discipline:
   - **Exact Parameter Budgets:** Engineered down to exact bounds (e.g. `NioMicro` has exactly 3,500,000 parameters).
   - **Zero Network Dependency:** Runs offline on `127.0.0.1` with complete data privacy.
   - **Cross-Platform Portability:** Compiles to standard ONNX running on Linux, macOS, Windows, Android, and iOS.

---

## Available Models

| Model | Target System | Parameters | Architecture | Task | Latest Release Asset |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`NioMicro`** | `nioxs::nio-micro` | **3,500,000 (Exact 3.5M)** | 4-Layer Bidirectional Transformer Encoder | Multi-head decision, sentiment & risk scoring | [`nio_micro.onnx`](https://github.com/nio-labs/nio-xs-models/releases/latest) |

---

## 1. NioMicro — Decision Model (3.5M)

**NioMicro** is the flagship decision engine of the MicroLM family. It acts as an autonomous policy gate for code reviews, pull requests, and safety evaluation.

### Model Heads
1. **Decision Head:** Binary verdict (`approve` / `reject`).
2. **Sentiment Head:** Polarity detection (`positive` / `negative`).
3. **Score Head:** Continuous calibrated score (`0.00` to `1.00`).

### Checksum Verification

```text
File:   nio_micro.onnx
Size:   14,588,852 bytes (~14 MB)
SHA256: 4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb
```

### Direct Download via CLI / Curl

```bash
# Direct download from GitHub Releases
curl -LO "https://github.com/nio-labs/nio-xs-models/releases/latest/download/nio_micro.onnx"

# Verify integrity
sha256sum nio_micro.onnx
```

### Using with NioXS

Place the downloaded model into the local NioXS cache:
```bash
mkdir -p ~/.nioxs/models
mv nio_micro.onnx ~/.nioxs/models/
```

Or pull directly via Nio CLI:
```bash
nioxs pull nio-micro
```

---

## License

The compiled model weights are distributed under the [MIT License](LICENSE).  
Internal training datasets, synthetic curriculums, and data generators are private and proprietary to Nio Labs.
