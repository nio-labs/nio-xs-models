# AST runtime 20-prompt session — Intel Core i7-8650U

2026-10-21. The tested runtime uses a 4,096-token RoPE window, releases unused embedded GGUF tokenizer metadata, and trims the heap after initialization and each layer. Native CPU release build, four Rayon threads, Linux/WSL2. Each model loaded once in its own process and handled 20 independent tasks. KV caches reset between tasks; the engine, tokenizer, mmap, RoPE tensors, mask cache and candidate pool were retained. Greedy candidate selection used the same pools as the CLI AST modes, with natural EOS/EOT and up to 32 new tokens per task. No generated command was executed.

| Model | Initial RSS | Session peak VmHWM | Final RSS | Nonempty outputs | Generated tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| NioRay | 46.46 MiB | 76.16 MiB | 57.93 MiB | 20/20 | 613 |
| NioViper | 17.39 MiB | 44.98 MiB | 28.11 MiB | 9/20 | 198 |

These are i7-8650U measurements, not Intel Core Ultra 5 results. Earlier Core Ultra speedup ratios are not established by this experiment. One session per model is a descriptive observation, not a repeatability or tail-latency study.

Peak means the Linux process high-water resident set. Per-task HWM is cumulative, not the peak isolated to that task. MiB is 2^20 bytes; this excludes the system file cache. Short input prompts and a 32-token generation cap do not establish long-context or unlimited-generation RAM limits. Independent tasks do not represent a growing 20-turn chat history.

Natural EOS makes the Viper workload sparse: nonempty outputs are recorded separately. Output nonemptiness is not correctness or tag adherence. The fixed CLI candidate pools are not a Tree-sitter syntax evaluation. Growth in end-of-task RSS is not sufficient to diagnose or rule out a memory leak.

| Model | Input-token range | Median prefill | Aggregate decode | EOS stops | Length stops |
| --- | ---: | ---: | ---: | ---: | ---: |
| NioRay | 22–45 | 2678.1 ms | 1.84 tok/s | 1 | 19 |
| NioViper | 17–29 | 846.8 ms | 5.62 tok/s | 15 | 5 |

Decode aggregates timed forward/selection decisions after the first token, including EOS decisions. Prefill excludes model loading and token selection and is not TTFT. No matched stock-Qwen baseline or quality score is part of this run.

Reproduce using the [session benchmark instructions](../../benchmark/ast-session/README.md). [Metadata and hashes](metadata.json), [summary](summary.json), [NioRay raw records](ray-results.ndjson), [Viper raw records](viper-results.ndjson). The metadata identifies the exact runtime source hashes because the engine changes were uncommitted during this run.

The [earlier 32,768-context configuration](context-32768/REPORT.md) is retained separately, including the measured source snapshots. Its numbers are not pooled with this updated configuration. Exact measured runtime sources are retained under `source/`; metadata records source hashes and whether the working tree still matched at publication.

## Per-task memory

| Task | NioRay RSS | NioRay session peak | Viper RSS | Viper session peak |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 51.90 MiB | 74.77 MiB | 23.98 MiB | 37.05 MiB |
| 2 | 52.05 MiB | 74.77 MiB | 24.41 MiB | 41.82 MiB |
| 3 | 52.48 MiB | 74.77 MiB | 24.69 MiB | 42.01 MiB |
| 4 | 53.05 MiB | 74.77 MiB | 24.96 MiB | 42.01 MiB |
| 5 | 53.66 MiB | 74.77 MiB | 25.09 MiB | 42.01 MiB |
| 6 | 53.77 MiB | 74.77 MiB | 25.03 MiB | 42.01 MiB |
| 7 | 54.42 MiB | 74.77 MiB | 25.39 MiB | 42.18 MiB |
| 8 | 55.07 MiB | 74.77 MiB | 25.42 MiB | 42.18 MiB |
| 9 | 54.84 MiB | 74.77 MiB | 25.42 MiB | 42.18 MiB |
| 10 | 55.26 MiB | 74.77 MiB | 25.61 MiB | 42.50 MiB |
| 11 | 55.29 MiB | 74.77 MiB | 25.94 MiB | 42.50 MiB |
| 12 | 55.86 MiB | 74.77 MiB | 26.03 MiB | 42.55 MiB |
| 13 | 56.09 MiB | 74.77 MiB | 26.09 MiB | 42.56 MiB |
| 14 | 56.51 MiB | 74.77 MiB | 26.54 MiB | 42.56 MiB |
| 15 | 56.70 MiB | 74.77 MiB | 26.61 MiB | 43.23 MiB |
| 16 | 56.77 MiB | 74.77 MiB | 26.81 MiB | 43.48 MiB |
| 17 | 57.36 MiB | 74.99 MiB | 27.19 MiB | 43.73 MiB |
| 18 | 57.52 MiB | 74.99 MiB | 27.66 MiB | 44.14 MiB |
| 19 | 57.96 MiB | 76.16 MiB | 27.68 MiB | 44.37 MiB |
| 20 | 57.93 MiB | 76.16 MiB | 28.11 MiB | 44.98 MiB |

## Earlier configuration comparison

The earlier and current sessions used the same prompts, candidate pools and 32-token cap; all generated token ID sequences matched. The configurations differ in RoPE context allocation, tokenizer-metadata retention, and heap trimming. This is a comparison of these two measured configurations, not an unchanged-context algorithm-only comparison.

| Model | Earlier session peak (32,768-token allocation) | Current session peak (4,096-token window + metadata release/trim) | Reduction |
| --- | ---: | ---: | ---: |
| NioRay | 118.07 MiB | 76.16 MiB | 35.5% |
| NioViper | 65.73 MiB | 44.98 MiB | 31.6% |
