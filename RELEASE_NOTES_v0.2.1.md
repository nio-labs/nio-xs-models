# Release Notes: v0.2.1 — Mako (150M) Live Web Scout & MCP Token Scrubber (65.4MB, 99.6% Token Cut)

Official v0.2.1 release distributing the compiled **Mako (150M)** neural binary (`mako.vmicrolm-vector.gguf`), standalone tokenizer, and the first-class **MCP Web Scout** integration in `nioxs-mcp`.

---

### 🦈 1. Mako (150M) — Live Web Intelligence & Scraping Scout (`v-µLM Vector`)

- **Base Architecture**: `OuteAI/Lite-Mistral-150M-v2-Instruct` (100% full brain retained, 12 layers, $d=768$, 32K vocab, Apache 2.0).
- **Quantization Engine**: Proprietary **v-µLM Vector** (`IQ3_XXS` Vector Codebook Lattice, **65.39 MiB disk**, **~21.8 MB resident RAM**).
- **Throughput**: **207.4 – 227.6 tokens/sec** prompt ingestion; **17.7 – 30.7 tokens/sec** (11.5 – 17.5 words/sec) generation on plain single-core CPU.
- **Core Role**: Powers live web research in `nioxs-browser`, synthesizing surgical search operator queries and stripping 90%–99.6% of raw DOM noise before context injection.

---

### 🔌 2. Localhost Model Context Protocol (MCP) Web Scout Integration

Exposed directly via `nioxs mcp` over standard JSON-RPC 2.0 for **Claude Code, Cursor, OpenCode, Windsurf, and Aider**:

#### `web_fetch` (DOM Noise Scrubber & Surgical Focus Extractor)
- Intercepts raw web pages (50,000–80,000 bytes) containing ads, scripts, navbars, and cookie banners.
- Strips all HTML overhead down to clean, dense Markdown.
- Supports optional **`focus`** parameter (e.g., `focus: "RecvError"`) to surgically isolate matching structs, code blocks, or invariant explanations.
- **Measured Token Reduction**: **91.1% general reduction; 99.6% reduction with surgical focus** (76,394 bytes HTML $\rightarrow$ 308 bytes clean payload).

#### `mako_search` (Keyless Live Documentation Search)
- Formulates surgical queries with operator syntax (`site:`, exact quotes).
- Conducts keyless web search via DuckDuckGo HTML endpoints with zero API keys required.
- Emits clean, ranked documentation URLs with contextual snippets in < 1.2s.

---

### 📦 Certified Binary Assets

| Asset | Engine / Role | Format | Size | Target RAM |
|---|---|:---:|:---:|:---:|
| `mako.vmicrolm-vector.gguf` | Mako 150M (Live Web Scout & Scrubber) | GGUF IQ3_XXS Codebooks | 65.39 MB | < 22 MB |
| `mako-tokenizer.json` | Mako Tokenizer (Mistral 32K) | JSON | 1.8 MB | < 2 MB |
| `skate.vmicrolm-vector.gguf` | Skate 135M (Resident Micro-Guru) | GGUF IQ3_XXS Codebooks | 82.9 MB | ~22 MB |
| `manta.Q4_0.gguf` | Manta 494M (Full Conversational Guru) | GGUF Q4_0 | 270.9 MB | ~73 MB |
