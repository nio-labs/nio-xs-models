# NioCuda v0.5.2 — Tactical Swarm Conductor (AST-µLM)

`NioCuda` is the official tactical swarm conductor and air-traffic controller for NioXS. It plans and synchronizes multi-stage execution pipelines across the predator fleet:
- **`nio-nano`** (AST navigation & symbol triage)
- **`nio-ray`** (Keystroke code generation & inline completion)
- **`nio-mini`** (Defect auditing & AST linting)
- **`nio-viper`** (Terminal verification & bash execution)
- **`nio-micro`** (Policy verdict & diff approval)
- **`nio-manta`** (Companion architectural dialogue)

---

## Technical Specifications

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | Qwen2.5-Coder-0.5B-Instruct sliced to 16 Transformer Layers |
| **Active Parameters** | ~374.73 Million |
| **Hidden Dimension ($d$)** | 896 ($896 / 32 = 28$ blocks, 100% 32-byte SIMD clean block alignment) |
| **Quantization Format** | GGUF `Q4_0` (`nio-cuda-ast.Q4_0.gguf`) |
| **Engine Footprint** | Initial RSS: ~3.8 MB \| Engine Ready: ~110.5 MB \| Working RAM: ~85.7 MB |
| **Load Latency** | **35.62 ms** on standard CPU |
| **Target Runtime** | In-process native Rust Candle runtime (`crates/nio-cuda-runtime`) |

---

## Output Protocols

### 1. Sequential Coordination Plan (`<cuda_plan>`)
```xml
<cuda_plan task="Upgrade password hashing from bcrypt to Argon2id" goal="Deterministic zero-defect completion">
  <stage id="1" model="nio-nano" action="symbol_triage" path="crates/auth/src/hash.rs" goal="Index AST symbols" />
  <stage id="2" model="nio-ray" action="keystroke_code" file="crates/auth/src/hash.rs" task="Upgrade hashing" />
  <stage id="3" model="nio-mini" action="defect_audit" file="crates/auth/src/hash.rs" target="AST syntax" />
  <stage id="4" model="nio-viper" action="terminal_verify" cmd="cargo test -p auth" />
  <stage id="5" model="nio-micro" action="policy_verdict" scope="Diff approval" />
</cuda_plan>
```

### 2. Dependency Graph (`<cuda_dag>`)
```xml
<cuda_dag id="task-auth-0" task="Upgrade hashing">
  <node id="triage" model="nio-nano" action="symbol_triage" path="crates/auth/src/hash.rs" />
  <node id="codegen" model="nio-ray" depends_on="triage" file="crates/auth/src/hash.rs" task="Upgrade hashing" />
  <node id="audit" model="nio-mini" depends_on="codegen" file="crates/auth/src/hash.rs" />
  <node id="verify" model="nio-viper" depends_on="audit" cmd="cargo test -p auth" />
  <node id="verdict" model="nio-micro" depends_on="verify" policy="security_audit_pass" />
</cuda_dag>
```

---

## Release Assets & Cryptographic Checksums

| File | Size | Format | SHA-256 Checksum |
| :--- | :---: | :---: | :--- |
| **`nio-cuda-ast.Q4_0.gguf`** | **271.76 MiB** (284,962,368 bytes) | GGUF (`Q4_0`) | `09566c2f463dfae5475b2747c4338cf3a9b887f8382a21052766d1f97803c58c` |
| **`nio-cuda-tokenizer.json`** | **10.89 MiB** (11,422,170 bytes) | JSON (BPE) | `3fb3240da20c0754d6aa77f959f9f7d4cbdff79cb07f50121898036c54d40454` |

---

## Quickstart

```bash
cargo run --release -p nio-cuda-runtime -- \
  --model models/nio-cuda/nio-cuda-ast.Q4_0.gguf \
  --tokenizer models/nio-cuda/nio-cuda-tokenizer.json \
  --prompt "Upgrade password hashing from bcrypt to Argon2id in authentication service"
```
