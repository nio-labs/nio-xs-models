# NioViper v0.1.0 — The Tactical Edge Reflex Engine (50M)

The official **v0.1.0 General Availability (GA)** release of **NioViper**, the 50-million parameter tactical edge reflex engine engineered from scratch for high-velocity developer terminals, DevOps surgery, and autonomous CLI operations.

---

### 🚀 Highlights & Capabilities

- **Exact 50,000,000 Parameter Architecture**: 10 Transformer layers ($d=640$, $d_{ff}=1600$), Grouped-Query Attention (10 query heads, 2 KV heads), SwiGLU activation, RMSNorm, and tied embeddings.
- **Dedicated 14,744 Vocabulary Tokenizer**: Custom ByteLevel BPE tokenizer covering high-frequency POSIX, Windows PowerShell, Git, Docker, and terminal commands with zero vocab bloat.
- **Sub-55MB Resident RAM Hard Cap**: Measured at **51.8 MB average / 53.1 MB absolute peak RAM** (`VmHWM` via Linux Kernel) — runs in-process on minimal laptops, containers, and edge servers.
- **26.9 MB Quantized Artifact**: Compact Q4_0 GGUF binary ready for instant cold start (< 1.5s) and 15–35ms warm reflex latency on CPU.
- **Swiss Gear Hybrid Engine**:
  - **Deterministic Slot Grounding**: Automatic extraction and parameter alignment for quoted literals (`'TODO'`) and dynamic port numbers (`4000`).
  - **Spider Search Hygiene**: Automatic binary suppression (`-rIn`), path anchoring (`.`), and directory exclusion (`--exclude-dir={target,.git,node_modules}`).
  - **Destructive Safety Clutch**: Real-time interactive protection against dangerous operations (`rm -rf`, `kill -9`, `git reset --hard`, `Stop-Process`).
  - **Isolated Python Sandbox**: Dedicated plugin environment (`~/.nioxs/plugins/venv`) managed via `nioxs viper plugin install/list`.

---

### 📦 Artifacts & Integrity Checksums

| Asset | Size | SHA-256 Checksum |
|---|:---:|---|
| **`nio-viper.Q4_0.gguf`** | 26.91 MB (28,214,368 bytes) | `acaa8a21c8d37d12398a2e7ac67ad367d2e3786b261ce95195e6e0cc08363e9c` |
| **`nio-viper-tokenizer.json`** | 923 KB (945,102 bytes) | `25e0b493570d3f1cd338033a685f69eb3fefd4f307424bca5709fa8bb1994806` |

---

### 💻 Quickstart

```bash
# Pull and verify NioViper weights
nioxs pull viper

# Natural language shell reflex
nioxs viper "list folder pls"

# Execute natively with Destructive Safety Clutch
nioxs viper -x "spider search .rs files for 'fn main'"
```
