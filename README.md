# Nio Models — Official ONNX Model Registry

This repository serves as the official distribution hub for compiled, production-ready neural models (**Nio Models**) used across the **Nio** and **NioXS** edge ecosystem.

Training datasets, raw curriculums, and internal training pipelines remain 100% private. Only compiled mathematical model binaries (`.onnx`) and domain tokenizers are distributed here as public release assets.

---

## Available Models

| Model | Target System | Parameters | Architecture | Task | Latest Release Asset |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`NioMicro`** | `nioxs::nio-micro` | **3,500,000 (Exact 3.5M)** | 4-Layer Bidirectional Transformer Encoder | Multi-head decision, sentiment & risk scoring | [`nio_micro.onnx`](https://github.com/nio-labs/nio-xs-models/releases/latest) |

---

## 1. NioMicro — Decision Model (3.5M)

**NioMicro** is an ultra-compact, deterministic decision engine and policy gate. It runs in under **5 milliseconds** on standard CPUs with zero network egress and zero GPU requirements.

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
Internal training datasets and synthetic curriculums are private and proprietary to Nio Labs.
