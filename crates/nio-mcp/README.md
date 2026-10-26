# Nio Localhost Model Context Protocol (MCP) Server (`nioxs-mcp`)

The **Nio Localhost MCP Server** (`nioxs-mcp`) is a single-binary, sub-1MB Model Context Protocol server that bridges edge MicroLMs (µLMs) directly into modern AI developer tools (Claude Desktop, Cursor, Windsurf, Antigravity, and Zed).

Instead of routing every trivial terminal command, secret sanitization check, safety gate, or documentation scraping request to multi-billion parameter cloud LLMs, `nioxs-mcp` handles them locally on CPU in sub-millisecond to sub-40ms times with **zero token cost**.

---

## ⚡ The Token-Cutting Architecture: 99.62% Workload Conservation

Using `nioxs-mcp` as a local client-side proxy achieves **99.62% direct token conservation** across developer tool workloads (reducing 58,450 cloud prompt tokens to 225 tokens across the suite), delivering an overall **70% to 85% net reduction** in daily frontier model API token billing.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      NIO MCP LOCALHOST TOKEN-CUTTING ARCHITECTURE                      │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [ Developer / IDE ] ──► [ Nio Localhost MCP Server ]
                               │
                               ├──► Nano (0.5M)    ──► 100% token cut on directives (--bash, --tools)
                               ├──► Mask (1.1M)    ──► Zero prompt secret leaks & 0 retry penalties
                               ├──► Micro (5.0M)   ──► Eliminates 1,500-3,000 CoT safety gate tokens
                               ├──► Mini (7.1M)    ──► Eliminates 10k-30k tokens per broken build retry
                               ├──► Viper (100M)   ──► Replaces 500+ token bash explanations with 38ms reflex
                               └──► Mako (150M)    ──► 85%-95% reduction on raw HTML via Wire DSL
```

### Detailed Token Reduction Breakdown

| MCP Tool | MicroLM Engine | Local Latency | Cloud Equivalent Cost | Token Savings Per Call |
| :--- | :--- | :---: | :--- | :---: |
| **`nano_route`** | **Nano (~0.5M)** | **45 µs** | Upstream prompt triage | **5,000 – 12,000 tokens** |
| **`mask_sanitize`** | **Mask (1.1M)** | **140 µs** | Cloud guardrail re-prompts | **2,000 – 5,000 tokens** |
| **`micro_audit`** | **Micro (5.0M)** | **3.8 ms** | Deliberation CoT reasoning | **1,500 – 3,000 tokens** |
| **`mini_predict_defect`** | **Mini (7.1M)** | **4.2 ms** | Multi-turn build failure loops | **10,000 – 30,000 tokens** |
| **`viper_synthesize`** | **Viper (100M)** | **38.2 ms** | Verbose LLM bash prose | **300 – 800 tokens** |
| **`mako_web_scout`** | **Mako (150M)** | **8 – 15 ms** | 100KB–300KB raw HTML bloat | **20,000 – 60,000 tokens (85–95%)** |

---

## 🛠️ Exposed MCP Tools

1. **`nano_route(text)`**: Sub-0.1ms command intent triage and zero-token directive router (`--bash`, `--tools`, `--code`, AST symbol lookups).
2. **`mask_sanitize(content)`**: Sub-0.2ms zero-cloud secret and PII redactor. Redacts API tokens, private keys, and sensitive credentials with 0 false positives on git hashes.
3. **`micro_audit(action, cluster)`**: Sub-4ms contextual policy gate. Returns deterministic `APPROVE` or `REJECT` verdicts with continuous risk scoring.
4. **`mini_predict_defect(diff)`**: Sub-5ms pre-emptive code diff and AST analyzer. Forecasts compiler errors, borrow check fails, and regressions before running build suites.
5. **`viper_synthesize(intent, shell, simulate_clutch)`**: Tactical reflex command synthesis from developer intent with active Destructive Safety Clutch.
6. **`mako_web_scout(query, force_refresh)`**: Zero-API key live web scraper, RFC/CVE/sysctl navigator, and HTML pre-scrubber outputting LLM-Native Wire DSL with HTTP 304 ETag caching.

---

## 🚀 Installation & Quick Start

### Option 1: Download Standalone Binary (Recommended)
Download the standalone executable (~994 KB) from the latest GitHub Release:
```bash
# Linux (x86_64)
curl -fsSL -o /usr/local/bin/nioxs-mcp https://github.com/nio-labs/nio-xs-models/releases/download/v0.2.5/nioxs-mcp
chmod +x /usr/local/bin/nioxs-mcp
```

### Option 2: Install via Cargo
```bash
cargo install --git https://github.com/nio-labs/nio-xs-models nio-mcp
```

### Option 3: Run Diagnostic Self-Test
Verify all 6 MicroLM engines locally in one shot:
```bash
nioxs-mcp --test
```

---

## ⚙️ IDE & Client Configuration

### 1. Claude Desktop
Add to `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nio": {
      "command": "nioxs-mcp",
      "args": ["--stdio"]
    }
  }
}
```

### 2. Cursor / Antigravity / Windsurf
Add to your project's `.cursor/mcp.json` or global settings:
```json
{
  "mcpServers": {
    "nio": {
      "command": "nioxs-mcp",
      "args": ["--stdio"]
    }
  }
}
```

### 3. Zed Editor
Add to `~/.config/zed/settings.json`:
```json
{
  "experimental": {
    "model_context_protocol": {
      "servers": {
        "nio": {
          "command": "nioxs-mcp",
          "args": ["--stdio"]
        }
      }
    }
  }
}
```

### 4. HTTP / SSE Daemon Mode
Run as a background HTTP daemon:
```bash
nioxs-mcp --port 8080
```
Health check endpoint: `http://localhost:8080/health`
