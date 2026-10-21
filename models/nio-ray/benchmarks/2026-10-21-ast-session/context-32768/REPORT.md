# AST runtime 20-prompt session — Intel Core i7-8650U

2026-10-21. Native CPU release build, four Rayon threads, Linux/WSL2. Each model loaded once in its own process and handled 20 independent tasks. KV caches reset between tasks; the engine, tokenizer, mmap, RoPE tensors, mask cache and candidate pool were retained. Greedy candidate selection used the same pools as the CLI AST modes, with natural EOS/EOT and up to 32 new tokens per task. No generated command was executed.

| Model | Initial RSS | Session peak VmHWM | Final RSS | Nonempty outputs | Generated tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| NioRay | 84.60 MiB | 118.07 MiB | 99.65 MiB | 20/20 | 613 |
| NioViper | 38.18 MiB | 65.73 MiB | 48.85 MiB | 9/20 | 198 |

These are i7-8650U measurements, not Intel Core Ultra 5 results. Earlier Core Ultra speedup ratios are not established by this experiment. One session per model is a descriptive observation, not a repeatability or tail-latency study.

Peak means the Linux process high-water resident set. Per-task HWM is cumulative, not the peak isolated to that task. MiB is 2^20 bytes; this excludes the system file cache. Short input prompts and a 32-token generation cap do not establish long-context or unlimited-generation RAM limits. Independent tasks do not represent a growing 20-turn chat history.

Natural EOS makes the Viper workload sparse: nonempty outputs are recorded separately. Output nonemptiness is not correctness or tag adherence. The fixed CLI candidate pools are not a Tree-sitter syntax evaluation. Growth in end-of-task RSS is not sufficient to diagnose or rule out a memory leak.

| Model | Input-token range | Median prefill | Aggregate decode | EOS stops | Length stops |
| --- | ---: | ---: | ---: | ---: | ---: |
| NioRay | 22–45 | 2443.4 ms | 2.71 tok/s | 1 | 19 |
| NioViper | 17–29 | 730.7 ms | 6.41 tok/s | 15 | 5 |

Decode aggregates timed forward/selection decisions after the first token, including EOS decisions. Prefill excludes model loading and token selection and is not TTFT. No matched stock-Qwen baseline or quality score is part of this run.

Reproduce using the [session benchmark instructions](../../../benchmark/ast-session/README.md). [Metadata and hashes](metadata.json), [summary](summary.json), [NioRay raw records](ray-results.ndjson), [Viper raw records](viper-results.ndjson). The metadata identifies the exact runtime source hashes because the engine changes were uncommitted during this run.

## Per-task memory

| Task | NioRay RSS | NioRay session peak | Viper RSS | Viper session peak |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 85.57 MiB | 104.29 MiB | 44.70 MiB | 57.45 MiB |
| 2 | 87.70 MiB | 105.59 MiB | 45.16 MiB | 62.33 MiB |
| 3 | 90.00 MiB | 107.75 MiB | 45.37 MiB | 62.33 MiB |
| 4 | 90.51 MiB | 107.85 MiB | 45.65 MiB | 62.33 MiB |
| 5 | 92.96 MiB | 110.77 MiB | 45.82 MiB | 62.33 MiB |
| 6 | 95.01 MiB | 111.81 MiB | 45.77 MiB | 62.33 MiB |
| 7 | 95.67 MiB | 113.62 MiB | 46.11 MiB | 62.47 MiB |
| 8 | 96.27 MiB | 115.81 MiB | 46.12 MiB | 62.47 MiB |
| 9 | 95.91 MiB | 115.81 MiB | 46.13 MiB | 62.47 MiB |
| 10 | 98.12 MiB | 115.81 MiB | 46.35 MiB | 62.70 MiB |
| 11 | 97.77 MiB | 116.27 MiB | 46.68 MiB | 62.70 MiB |
| 12 | 98.28 MiB | 116.27 MiB | 46.84 MiB | 63.00 MiB |
| 13 | 98.37 MiB | 116.27 MiB | 46.89 MiB | 63.11 MiB |
| 14 | 98.54 MiB | 116.27 MiB | 47.29 MiB | 63.11 MiB |
| 15 | 98.77 MiB | 116.27 MiB | 47.36 MiB | 63.69 MiB |
| 16 | 98.81 MiB | 116.27 MiB | 47.57 MiB | 64.12 MiB |
| 17 | 99.25 MiB | 116.94 MiB | 48.00 MiB | 64.41 MiB |
| 18 | 99.24 MiB | 116.94 MiB | 48.42 MiB | 64.52 MiB |
| 19 | 99.66 MiB | 118.07 MiB | 48.46 MiB | 64.82 MiB |
| 20 | 99.65 MiB | 118.07 MiB | 48.85 MiB | 65.73 MiB |
