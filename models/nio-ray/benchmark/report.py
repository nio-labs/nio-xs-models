"""Render a readable comparison from summary.json; never changes raw results."""
from pathlib import Path
import ast
import hashlib
import json
import sys


def main(directory):
    summary=json.loads((directory/'summary.json').read_text())
    variants=summary['variants']
    lines=['# NioRay v0.4.0 benchmark — 2026-10-21', '',
           'NioRay was run locally. Qwen2.5-Coder-0.5B-Instruct was not run; its scores below are the authors’ published reference results.', '',
           '## Code correctness', '',
           'All 164 HumanEval+ v0.1.10 tasks, one greedy completion per task, 2048-token output cap, Qwen’s published ChatML prompt and stop strings, no retries or repairs. Quality inference used official llama.cpp b11778 on CPU for both NioRay variants. EvalPlus 0.2.1 scored both base and expanded tests.', '',
           '| Model | HumanEval pass@1 | HumanEval+ pass@1 | Evidence |',
           '| --- | ---: | ---: | --- |',
           '| Qwen2.5-Coder-0.5B-Instruct | 61.6% | 57.3% | Published, not rerun |']
    for name in ['standard','dev']:
        row=variants[name]
        lines.append(f"| NioRay {name.title()} Q4_K_M | {100*row['humaneval_pass1']:.2f}% ({row['humaneval_passed']}/164) | {100*row['humaneval_plus_pass1']:.2f}% ({row['humaneval_plus_passed']}/164) | Measured locally |")
    lines+=['', 'Reference: [Qwen2.5-Coder technical report, Table 16](https://arxiv.org/html/2409.12186v2#S7.T16). The published Qwen setup differs in precision/backend and may differ in evaluator version. These are reference score comparisons, not a controlled local Qwen-versus-NioRay experiment. Public-benchmark training contamination has not been audited.', '',
            '## Native Candle CPU performance', '',
            'Intel Core Ultra 5 135H under WSL2, 18 logical CPUs exposed, 6 Rayon threads, Candle 0.8.4, release build with native CPU targeting. Batch size 1, one warmup, five trials per input length, 64 generated tokens per trial. Each trial resets the KV cache. EOS stopping is disabled for these fixed-length synthetic trials.', '',
            '| Input tokens | Standard TTFT median [min–max] | Dev TTFT median [min–max] | Standard decode tok/s | Dev decode tok/s |',
            '| ---: | ---: | ---: | ---: | ---: |']
    for length in ['32','128','512']:
        a,b=variants['standard']['perf'][length],variants['dev']['perf'][length]
        lines.append(f"| {length} | {a['ttft_median_ms']:.1f} [{a['ttft_min_ms']:.1f}–{a['ttft_max_ms']:.1f}] ms | {b['ttft_median_ms']:.1f} [{b['ttft_min_ms']:.1f}–{b['ttft_max_ms']:.1f}] ms | {a['decode_median_tokens_per_second']:.2f} | {b['decode_median_tokens_per_second']:.2f} |")
    lines+=['', '| Variant | New-process load time | RSS after loading | Peak RSS across native trials |', '| --- | ---: | ---: | ---: |']
    for name in ['standard','dev']:
        row=variants[name]
        lines.append(f"| {name.title()} | {row['load_ms']:.1f} ms | {row['load_rss_mib']:.1f} MiB | {row['peak_rss_mib']:.1f} MiB |")
    lines+=['', 'TTFT includes tokenization, input tensor creation, prefill, and first-token selection, excluding model loading. For synthetic trials, the shared source text is tokenized before truncation to the requested model input length. Decode throughput measures 63 forward/sampling steps after the first generated token. Memory includes the whole process, including dequantized tensors and KV cache. OS page caches were not cleared. Five-trial p95 is retained in summary.json as a descriptive statistic; laptop host load, scheduling, thermals, and power state were not controlled.', '',
            'These direct Candle harness measurements are separate from the llama.cpp quality experiment. They do not measure full CLI/IDE latency and do not support a speedup claim against Qwen, since no matched local Qwen speed baseline was run.', '',
            '## Completion diagnostics', '', '| Variant | Stop reasons | Syntactically valid Python solutions |', '| --- | --- | ---: |']
    for name in ['standard','dev']:
        valid=0
        for line in (directory/f'{name}-solutions.jsonl').read_text().splitlines():
            try:ast.parse(json.loads(line)['solution']);valid+=1
            except SyntaxError:pass
        lines.append(f"| {name.title()} | {json.dumps(variants[name]['stop_reasons'],sort_keys=True)} | {valid}/164 |")
    tokenization=json.loads((directory/'tokenization.json').read_text())
    lines+=['', '## Tokenization overhead', '',
            f"Across the same 164 formatted prompts, Standard used {tokenization['standard_tokens_total']:,} input tokens and Dev used {tokenization['dev_tokens_total']:,}: **{100*(tokenization['aggregate_token_ratio']-1):.2f}% more tokens** for Dev. This measures this benchmark’s prompts, not general developer workloads. See [tokenization records](tokenization.json)."]
    lines+=['', '## Reproduction and evidence', '',
            '- [Harness protocol and commands](../../benchmark/README.md)',
            '- [Machine, dataset, and model fingerprints](run-metadata.json)',
            '- [Quality backend and decoding settings](quality-metadata.json)',
            '- [Machine-readable summary](summary.json)',
            '- [Per-task scores](per-task.csv)',
            '- Raw native records: [Standard](standard.ndjson), [Dev](dev.ndjson).',
            '- Raw quality responses: [Standard](standard-quality.ndjson), [Dev](dev-quality.ndjson).',
            '- Full EvalPlus verdicts: [Standard](standard-solutions_eval_results.json), [Dev](dev-solutions_eval_results.json).',
            '', 'Existing released model weights were used unchanged. This report records a measurement, not a new performance guarantee.', '']
    (directory/'REPORT.md').write_text('\n'.join(lines))
    assets=[]
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix not in ['.log'] and path.name != 'artifact-hashes.json':
            assets.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (directory/'artifact-hashes.json').write_text(json.dumps(assets,indent=2)+'\n')
    print(directory/'REPORT.md')


if __name__=='__main__':main(Path(sys.argv[1]))
