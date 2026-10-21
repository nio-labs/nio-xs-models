#!/usr/bin/env bash
set -euo pipefail
# Dependencies must already be cached for the offline, network-isolated evaluator.
bench_output=$(realpath "$1")
for variant in standard dev; do
    HUMANEVAL_OVERRIDE_PATH="$bench_output/HumanEvalPlus-v0.1.10.jsonl" \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
    unshare --user --map-root-user --net \
    uv run --offline --python python3.12 --with evalplus==0.2.1 --with numpy==1.26.4 \
    python -m evalplus.evaluate --dataset humaneval \
        --samples "$bench_output/$variant-solutions.jsonl" --parallel 2 \
        > "$bench_output/$variant-evaluation.log" 2>&1
    tail -n 4 "$bench_output/$variant-evaluation.log"
done
python3.12 "$(dirname "$0")/summarize.py" "$bench_output"
