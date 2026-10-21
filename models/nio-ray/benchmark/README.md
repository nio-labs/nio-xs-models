# NioRay benchmark harness

This benchmark runs only the two released NioRay v0.4.0 Q4_K_M artifacts. Qwen2.5-Coder-0.5B-Instruct scores are taken from the authors' [technical report, Table 16](https://arxiv.org/html/2409.12186v2#S7.T16): 61.6% HumanEval and 57.3% HumanEval+. Qwen is not loaded or executed locally. These are published reference scores, not a matched local speed baseline.

## Protocol

- Quality: all 164 HumanEval+ v0.1.10 tasks from the pinned Qwen evaluation repository, one greedy sample per task, at most 2048 new tokens, batch size 1. Quality inference uses official llama.cpp b11778, CPU only, 6 threads, 4096-token context, prompt cache disabled, repeat penalty 1. Both the original base inputs and expanded inputs are scored with EvalPlus 0.2.1.
- Prompts and stop strings follow Qwen's published `qwencoder-eval/instruct/eval_plus/model.py` ChatML evaluation template, including the assistant's Python fence prefix. Generated text is used as the complete solution, with tabs replaced by four spaces, without retries, repair, or task-specific prompt changes. Tool execution is disabled.
- Performance: CPU Candle 0.8.4 in release mode, native CPU compiler target, 6 Rayon threads. One 32-token/16-output-token warmup, then five trials each at 32, 128, and 512 input tokens with exactly 64 output tokens. EOS stopping is disabled for these synthetic workloads only. Each prompt starts at KV-cache position zero.
- Native Candle performance and llama.cpp quality are separate experiments; do not present them as a single production-stack result. For synthetic workloads the shared source text is tokenized before truncation to the requested model input length; that tokenization cost is included in TTFT. TTFT includes input tokenization, input tensor creation, prefill, and greedy selection of the first token. Model loading is excluded and measured separately. Decode throughput counts forward/sampling steps after the first token, including a final EOS decision when applicable. Synthetic measurements use 63 decode steps for 64 output tokens. JSON serialization and final text detokenization are excluded; stop-string detokenization is included where applicable.
- Memory is Linux process RSS and high-water RSS, including weights, dequantized tensors, tokenizer, and KV cache. New processes load each variant; OS file caches are not cleared. These are direct Candle harness timings, not full CLI/IDE timings.
- Five-trial p95 is a descriptive interpolated percentile, not a stable tail-latency estimate. WSL2 laptop results depend on host scheduling, power, and thermal state.

The source of each dataset/prompt and exact model hashes are recorded in `run-metadata.json`; `quality-metadata.json` identifies the separate quality backend and binary hash. Public-benchmark training contamination has not been audited. Published Qwen results may differ in model precision, inference backend, evaluation version, and environment; score differences alone do not isolate the effect of fine-tuning or pruning.

## Reproduce

```bash
RUSTFLAGS='-C target-cpu=native' cargo +stable build --release --manifest-path models/nio-ray/benchmark/Cargo.toml
python3.12 models/nio-ray/benchmark/run.py --models /path/to/verified/assets --output /tmp/nioray-run --threads 6 --suite performance
python3.12 models/nio-ray/benchmark/quality.py --models /path/to/verified/assets --output /tmp/nioray-run --threads 6 --server /path/to/llama-b11778/llama-server

# Run after inference to avoid CPU contention with timed measurements.
# Network namespace isolates generated solutions from the network on Linux.
HUMANEVAL_OVERRIDE_PATH=/tmp/nioray-run/HumanEvalPlus-v0.1.10.jsonl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
unshare --user --map-root-user --net \
uv run --offline --python python3.12 --with evalplus==0.2.1 --with numpy==1.26.4 \
python -m evalplus.evaluate --dataset humaneval --samples /tmp/nioray-run/standard-solutions.jsonl --parallel 2

# Repeat the evaluation command with dev-solutions.jsonl.
python3.12 models/nio-ray/benchmark/summarize.py /tmp/nioray-run
uv run --with tokenizers==0.21.4 python models/nio-ray/benchmark/tokenization.py --models /path/to/verified/assets --output /tmp/nioray-run
python3.12 models/nio-ray/benchmark/report.py /tmp/nioray-run
# evaluate.sh runs both evaluation commands and the summary in sequence.
```

Install the pinned evaluation dependencies once before using the offline command. The evaluator uses EvalPlus's temporary directories, process timeouts, and reliability guard. Keep execution confined to a disposable benchmark environment. No reference-model inference is part of this workflow.
