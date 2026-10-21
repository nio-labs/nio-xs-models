# AST runtime 20-task memory benchmark

This driver links the actual `nio-ray-runtime::AstMicroEngine` and `nio-viper-runtime` crates. It uses the CLI AST candidate pools: NioRay's fixed Rust example pool and Viper's `tactical_candidates`. It does not use the separate `nio-ideas` decoder or standard Candle `ModelWeights` inference.

Each model gets one fresh process, loads its engine/tokenizer once, and handles 20 independent tasks. KV caches reset between tasks; the engine, memory map, RoPE tensors, mask cache, and candidate pool remain allocated. Generation uses greedy candidate selection, natural EOS/EOT stopping, and at most 32 new tokens per task. Tasks that stop immediately are recorded as zero tokens. Generated commands are never executed.

The prompt files contain the first 20 NioRay tasks and all 20 Viper tasks from `nio-ideas` commit `a6b5343`. They are short developer/terminal requests, not 20 turns of growing chat history. Exact input token lengths and generated counts are recorded per task.

`process_hwm_mib` is Linux VmHWM for the process lifetime: it is the session peak so far, not a separate per-task peak. `rss_after_prompt_mib` is the current resident set. MiB means 2^20 bytes. Process RSS excludes the system file cache. This short session does not establish a universal RAM bound or prove absence of memory leaks.

From the repository root:

```bash
RUSTFLAGS='-C target-cpu=native' cargo build --release \
  --manifest-path models/nio-ray/benchmark/ast-session/Cargo.toml \
  --target-dir target
python3 models/nio-ray/benchmark/ast-session/run.py \
  --ray-model /path/to/nio-ray-ast.Q4_0.gguf \
  --ray-tokenizer /path/to/tokenizer.json \
  --viper-model /path/to/nio-viper-ast.Q4_0.gguf \
  --viper-tokenizer /path/to/nio-viper-tokenizer.json \
  --output /tmp/nio-ast-session --threads 4 --max-new-tokens 32
python3 models/nio-ray/benchmark/ast-session/summarize.py /tmp/nio-ast-session
```

Use the same protocol on the Intel Core Ultra 5 to compare hosts. Rebuild with `target-cpu=native` on each host. Record the CPU/OS, thread count, binary and source hashes, and asset hashes. No matched stock-Qwen baseline or generated-code quality score is part of this benchmark.

The current runtime caps context precomputation at 4,096 tokens. The load record includes the actual precomputed context length; this setting affects RAM independently of the short test prompt lengths. Results for earlier context configurations must be kept separate.
