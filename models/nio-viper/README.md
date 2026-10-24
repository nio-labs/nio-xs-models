# 🐍 NioViper (Exact 100M) — Tactical Terminal & DevOps Reflex Engine

**NioViper** is an edge-native tactical reflex engine engineered from scratch with an **exact 100,000,000 locked parameter budget**. It translates natural language developer intent into production POSIX bash and Windows PowerShell reflexes with **sub-105MB resident RAM** and **35ms – 50ms warm inference** on ordinary CPUs.

---

## 🏛️ Architectural Specifications

| Specification | Value | Mathematical Detail |
|---|:---:|---|
| **Exact Parameter Budget** | **`100,000,000`** | Enforced by PyTorch invariant assertion |
| **Transformer Layers ($L$)** | **14** | Uniform RMSNorm + Attention + SwiGLU |
| **Hidden Dimension ($d$)** | **800** | SIMD 32-byte block clean ($800 / 32 = 25$) |
| **Intermediate Dimension ($d_{ff}$)** | **1,920** | SwiGLU feedforward ($2.4 \times d$) |
| **Attention Configuration** | **GQA 10/2** | 10 Query heads ($d_k = 80$), 2 Key/Value heads |
| **Vocabulary Size ($V$)** | **17,451** | ByteLevel BPE covering shell syntax & cmdlets |
| **Weight Tying** | **Yes** | `lm_head.weight == embed_tokens.weight` |
| **Quantized Format** | **`Q4_0` GGUF** | **~56.8 MB** single-file binary |
| **Peak RAM Envelope** | **< 105 MB** | Linux `VmHWM` / macOS / Windows edge ceiling |
| **Warm CPU Reflex** | **35ms – 50ms** | Commodity x86_64 / ARM64 without GPU |

---

## 🚀 Capabilities (100M Architecture)

1. **Multi-Stage Command Pipelines**: Fluent multi-utility chaining (`find ... | xargs grep ... | awk ... | sort -nr`).
2. **Modern DevOps Ecosystem**: Rich subcommand fluency across `kubectl`, `docker compose`, `terraform`, `gh`, `aws`, and `systemctl`.
3. **Idiomatic Windows PowerShell**: Deep object pipeline expressions (`Get-Process | Where-Object WorkingSet64 -gt 100MB | Select-Object Name`).
4. **Swiss Gear 2.0**: Deterministic slot grounding anchors quoted literals and ports; active Destructive Safety Clutch prompts before hazardous mutations.

---

## 🧪 Verification & Testing

Verify the exact 100M parameter count and forward pass:

```bash
uv run --with torch --with pytest pytest tests/test_model.py -v
```

---

## 🏋️ Training Pipeline

Train locally or inside a compute instance via CLI:
```bash
# 1. Generate 250k synthetic curriculum
python scripts/dataset_generator.py --samples 250000 --out data/curriculum.jsonl

# 2. Train dedicated BPE tokenizer (17,451 vocab)
python scripts/tokenizer_train.py --corpus data/curriculum.jsonl --out nio-viper-tokenizer.json

# 3. Train NioViper across 3 epochs
python scripts/train.py --curriculum data/curriculum.jsonl --tokenizer nio-viper-tokenizer.json --epochs 3

# 4. Export quantized GGUF
python scripts/export_gguf.py --weights checkpoints/best.pt --tokenizer nio-viper-tokenizer.json --out nio-viper.Q4_0.gguf
```

---

## 📄 License

This model architecture and training pipeline are licensed under the [Business Source License 1.1](../../LICENSE) (BSL 1.1) converting to Apache 2.0 on October 20, 2030.
