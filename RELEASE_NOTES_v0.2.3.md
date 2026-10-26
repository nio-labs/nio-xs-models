# Release Notes: v0.2.3 — Viper (100M) Multi-Dialect Neural Reflex & 61.69MB Q4_0 GGUF

Official **v0.2.3** release distributing the retrained **Viper (100M)** tactical reflex engine (`viper.Q4_0.gguf`), dedicated trimmed developer vocabulary tokenizer (`viper-tokenizer.json`), and native multi-shell runtime.

---

### 🐍 1. Viper (100M) — Pure-Rust Multi-Shell Neural Dialect Reflex Engine

Viper achieves full zero-shot cross-platform terminal precision across POSIX, Windows, and modern shells:

- **Architecture Invariant**: Exactly **100,000,000 parameters** ($L=14$ layers, $d=800$, SwiGLU $d_{ff}=1,920$, GQA 10/2, tied embeddings).
- **Dedicated 17,451 Lexicon**: Pruned and trimmed developer-only Byte-Level BPE vocabulary (`viper-tokenizer.json`, **3.17 MB**), discarding extraneous multilingual tokens.
- **Physical Footprint**: Quantized **`Q4_0` GGUF** takes exactly **61.69 MB** on disk.
- **Peak RAM Envelope**: Resident peak memory under active query decoding stays strictly within **36 – 41 MB** (`VmHWM`), beating the < 50MB ceiling with margin to spare.
- **Multi-Dialect Prompt Conditioning**:
  - `[bash]`: POSIX pipelines, `lsof`, `fuser`, `xargs`, `systemd`, `awk`, `find`, `git`, `docker`, `kubectl`, `terraform`.
  - `[powershell]`: Native Windows object pipelines (`Get-Process`, `Stop-Process`, `Get-Service`, `Where-Object`, `Select-Object`, `Get-NetTCPConnection`).
  - `[fish]`: Fish subshells `(...)`, native command substitution, pattern searching.
  - `[zsh]`: Zsh glob qualifiers `**/*(...)`, recursive pattern matching.
- **Spider Search Hygiene**: Automatic noise filtering that appends clean build exclusions (`--exclude-dir={target,.git,node_modules,dist,.venv}`) to `grep` and path pruning to `find` / `Get-ChildItem`.
- **Destructive Clutch Guard**: Structured `<viper_alert level='warn'>` interception for high-impact filesystem operations (`rm -rf`, disk formatting, service kills).

---

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | SHA-256 Checksum | Target Hardware Peak RAM |
|---|---|:---:|:---:|---|:---:|
| `viper.Q4_0.gguf` | Viper (100M, Multi-Dialect Tactical Terminal Reflex) | GGUF Q4_0 | 61.69 MB | `45d9796b27728544af66c11d294b07e5a0fb241a310b3a93f54e26fb1ff1766e` | **40.32 MB** (< 50 MB) |
| `viper-tokenizer.json` | Viper Dedicated Developer Tokenizer (17,451 Vocab) | JSON | 3.17 MB | `a136e7acd3d47fe1a2572bf0fe7af79528e4492bf15f1ecea24e2216cf78c690` | N/A |

---

### 🔬 20-Scenario Real-World Benchmark Verification (Intel Core Ultra 5 135H)

| # | Benchmark Scenario | Shell Dialect | Hardware Latency | Peak Resident RAM | Generated Output Verdict | Status |
|---|---|:---:|:---:|:---:|---|:---:|
| 1 | Port 3000 Kill | bash | 3,608 ms | 40.0 MB | `lsof -ti:3000 \| xargs kill -9` | **PASS** |
| 2 | Directory Deep Tree | bash | 3,230 ms | 40.2 MB | `tree -h` | **PASS** |
| 3 | Heavy Log Search | bash | 4,197 ms | 40.6 MB | `find /var/log -type f -not -path...` | **PASS** |
| 4 | Git Soft Rollback | bash | 3,882 ms | 40.5 MB | `git reset --soft HEAD~1` | **PASS** |
| 5 | Docker Engine Prune | bash | 3,778 ms | 40.4 MB | `docker container prune -f && docker volume prune -f` | **PASS** |
| 6 | RAM Hog Triage | bash | 4,213 ms | 40.7 MB | `ps aux --sort=-%mem \| awk '$6 > 1048576'` | **PASS** |
| 7 | PowerShell Top 5 | powershell | 3,658 ms | 40.2 MB | `Get-Process \| Sort-Object WorkingSet64 -Descending \| Select-Object -First 5` | **PASS** |
| 8 | PowerShell Services | powershell | 3,641 ms | 40.2 MB | `Get-Service \| Where-Object Status -eq Running` | **PASS** |
| 9 | Fish Port Kill | fish | 3,734 ms | 40.3 MB | `kill -9 (lsof -t -i:4000)` | **PASS** |
| 10 | Fish File Finder | fish | 4,249 ms | 40.3 MB | `find . -type f -not -path '*...'` | **PASS** |
| 11 | Zsh Secret Search | zsh | 4,849 ms | 40.6 MB | `grep -rIn "DATABASE_URL" **/*` | **PASS** |
| 12 | K8s Rollout Restart | bash | 4,279 ms | 40.1 MB | `kubectl rollout restart deployment/...` | **PASS** |
| 13 | Terraform Drift Plan | bash | 4,466 ms | 40.3 MB | `terraform plan -detailed-exitcode` | **PASS** |
| 14 | Docker Compose JQ | bash | 6,538 ms | 40.2 MB | `docker compose config --format json \| jq...` | **PASS** |
| 15 | Spider Hygiene Search | bash | 8,902 ms | 40.2 MB | `grep -rIn "API_KEY" . --exclude-dir=...` | **PASS** |
| 16 | Recent Temp Files | bash | 6,645 ms | 40.4 MB | `find . -type f -not -path '*...'` | **PASS** |
| 17 | Destructive Log Wipe | bash | 7,670 ms | 40.1 MB | `rm -rf /var/log/nginx/*.log` | **PASS** |
| 18 | Socket Port 8080 | bash | 10,134 ms | 40.3 MB | `ss -tlpn \| grep ':8080'` | **PASS** |
| 19 | Git Worktree Spawn | bash | 10,600 ms | 40.6 MB | `git worktree add ../hotfix-auth hotfix-auth` | **PASS** |
| 20 | Disk Volume Health | bash | 5,576 ms | 40.2 MB | `df -h` | **PASS** |

---

### ⚡ Installation & Verification

Run Viper directly via `nioxs` or `nio-viper-runtime`:

```bash
# Direct terminal execution with dialect conditioning
nio-viper-runtime -p "Kill whatever process is listening on port 3000" --shell bash

# PowerShell object pipeline
nio-viper-runtime -p "get top 5 processes by memory" --shell powershell

# Fish subshell syntax
nio-viper-runtime -p "kill whatever process is holding port 4000" --shell fish
```
