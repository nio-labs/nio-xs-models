# MicroLM (µLM) Core Production Suite v0.1.0

Official **v0.1.0** release of the unified Micro Learning Model (µLM) production family and Localhost MCP Server.

```bash
# Instant One-Liner Installer
curl -fsSL https://nio-labs.github.io/nio-xs-models/install.sh | bash
```

---

### 🏛️ The Production MicroLM Fleet (Zero `Nio` Prefix)

1. **Viper (100M Tactical Terminal & DevOps Striker)**:
   - **100,000,000 parameter** locked pure-Rust AST-MicroLM tactical terminal striker and DevOps reflex engine.
   - Industry-leading **27.14 MB peak resident RAM (`VmHWM`)** on Linux via default `nio-viper-runtime` (11.70 MB init).
   - **Sub-20µs Tactical AST Candidate Reflex** sampling (< 25MB envelope).
   - 61.69 MB quantized `Q4_0` GGUF with dedicated 17,451 ByteLevel BPE vocabulary (`viper.Q4_0.gguf`).
   - Integrated Swiss Gear 2.0 with Destructive Safety Clutch, spider search hygiene, and dynamic slot grounding.
   - Full PowerShell object pipeline and POSIX multi-pipe chaining support.

2. **Nano (~0.5M Intent & Directive Router)**:
   - In-process Rust feature engine operating in **< 0.1ms (sub-100 microseconds)**.
   - Intercepts zero-token directives (`--bash`, `--tools`, `--code`) and performs instant intent routing.

3. **Micro (5.0M Contextual Policy Arbiter)**:
   - 4-layer bidirectional Transformer operating in **< 5ms** as an autonomous policy gate.
   - Partitioned into independent 5M clusters (`sec`, `infra`, `base`) approving/rejecting terminal mutations with continuous risk calibrations.

4. **Mask (1.1M Real-Time Stream Redactor)**:
   - 2-layer Byte-Level Convolutional Transformer operating in **< 0.2ms (sub-200 microseconds)**.
   - Real-time secret, API key, and sensitive PII redactor embedded directly in terminal streams and MCP gateways (99.95% accuracy, zero false positives on commit SHAs).

5. **Mini (7.1M Pre-Emptive Defect Forecaster)**:
   - Bidirectional AST encoder operating in **< 5ms**.
   - Pre-emptive code radar predicting build breaks, lifetime violations, and regressions before test suites execute.

---

### 📦 Certified Clean Release Artifacts & Checksums

| Asset | Role | Size | SHA-256 Checksum |
|---|---|:---:|---|
| **`viper.Q4_0.gguf`** | Viper (100M) Flagship Reflex | 61.69 MB | `58633aa691b80840dc85586cf2cb8616deff480c64ddf406bf848db749ecc3d4` |
| **`viper-tokenizer.json`** | Viper (100M) Tokenizer | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` |
| **`nano.json`** | Nano (~0.5M) Intent Matrix | 46.8 KB | `9b03e97096d232b76a4de3143b9ef0c76b6e9b64d241a289e99fe1e4977fe125` |
| **`mask.onnx`** | Mask (1.1M) Stream Redactor | 4.43 MB | `a52fdcbc7c749b2d8b41b0c38f8f0cde1eafd7fef0b8ef1688ac80b6ae79b7ad` |
| **`mini.onnx`** | Mini (7.1M) Defect Forecaster | 27.14 MB | `dd6516d85748aa64a1f1f7500ed07949813c2e35ede6e096a89e5fb57fa8e731` |
| **`micro_base.onnx`** | Micro (5.0M) Base Cluster | 13.82 MB | `4b19ceaf36d0e545c64542fc4988e18a2b1f586f7485dd6d70c3001c374ebcdb` |
| **`micro_infra.onnx`** | Micro (5.0M) Infra Cluster | 19.66 MB | `9e4b541a150d0c3674d537cbc0300c3a3d84a89d72a84a4b0fad64817f6eb294` |
| **`micro_sec.onnx`** | Micro (5.0M) Security Cluster | 19.66 MB | `c86d350d7fea0dc90e0eda046d14e324534cbea8e1e6c7ba9e0276496d15426b` |

---

### 🌐 Localhost MCP Server & Token Savings
- **Empirical Token Conservation**: **99.62%** verified across all 5 models.
- **Dual Transport**: Supports standard I/O (`nioxs-mcp --stdio`) and HTTP/SSE (`nioxs-mcp --port 8080`).
- **Zero-Config Agent Setup**: Native drop-in integration with OpenCode, Claude Code, Cursor, Windsurf, and Zed.
