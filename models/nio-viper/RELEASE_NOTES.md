# NioViper v0.5.0 — The Sub-49MB Tactical Edge Striker (AST-µLM)

**NioViper** (`nioxs::nio-viper`) is the ultra-compact tactical striker of the Nio predator fleet. Surgically stripped from `Qwen/Qwen2.5-Coder-0.5B-Instruct` down to **8 Transformer Layers** and a high-density **32,000 Developer & Shell Lexicon**, NioViper is engineered specifically for instant terminal command synthesis, CI/CD triage, and compiler diagnostic resolution with strictly **< 49 MB of peak working RAM**.

---

### 🚀 Key Technical Breakthroughs

1. **Sub-49MB Working RAM Footprint**:
   - Engine initialization: **`VmRSS = 38.10 MB`** / **`VmHWM = 42.03 MB`**.
   - Continuous tactical generation: **`42.3 MB`** peak working memory (vs 1,119.7 MB for stock generalist LLMs — **96.2% RAM reduction**).
   - Designed to run continuously inside low-memory developer daemons, background shell watchers, edge IoT, and constrained CI runners.

2. **Clean 32-Byte Block Quantization (`Q4_0`)**:
   - The hidden dimension $d=896$ is perfectly divisible by 32 ($896 / 32 = 28$ blocks), achieving 100% clean `Q4_0` quantization with **0% fallback overhead**.
   - Total model size on disk is **`96.31 MiB`** (strictly under the 100MB threshold, down from 207 MiB).

3. **High-Signal Terminal & Diagnostic Triage**:
   - Distilled on high-value developer intent: bash/zsh command generation, rustc/borrow-checker error triage, TypeScript interface mismatches, Docker management, git triage, and continuous log analysis.
   - Structured tag execution: 100% adherence to `<viper_cmd>...</viper_cmd>` and `<viper_alert level='...'>...</viper_alert>` tags with zero markdown hallucinations or conversational preamble.

---

### 📦 Release Assets & Cryptographic Checksums

| File | Size | Format | SHA-256 Checksum |
| :--- | :---: | :---: | :--- |
| **`nio-viper-ast.Q4_0.gguf`** | **96.31 MiB** (100,984,640 bytes) | GGUF (`Q4_0`) | `2e7df31bbe90a39e33b363d24085c2d04d7df6519909f27387e8b55b6d36ed32` |
| **`nio-viper-tokenizer.json`** | **1.24 MiB** (1,297,635 bytes) | JSON (BPE 32k) | `c8a034fb2f7ad2484fc3010a73152fade6d48372ae322745fbf2c71e064effb1` |

---

### 💻 Quickstart

#### Direct Native Rust Streaming Runtime
```bash
# Clone nio-xs-models and run with native SIMD acceleration
cargo run --release --package nio-viper-runtime -- \
  --model nio-viper-ast.Q4_0.gguf \
  --tokenizer nio-viper-tokenizer.json \
  --prompt "Kill whatever process is listening on port 3000"
```

#### Pull via NioXS CLI
```bash
# Pull NioViper into local cache
nioxs pull viper

# Run immediate tactical shell triage
nioxs viper "Find all files larger than 100MB in /var/log and sort by size"
```
