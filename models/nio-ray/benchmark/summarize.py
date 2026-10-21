"""Summarize recorded timings and EvalPlus verdicts without rerunning inference."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import statistics


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(directory):
    summary = {'qwen_published_reference': {
        'model': 'Qwen2.5-Coder-0.5B-Instruct', 'humaneval_pass1': 0.616,
        'humaneval_plus_pass1': 0.573,
        'source': 'https://arxiv.org/html/2409.12186v2#S7.T16',
        'locally_executed': False, 'latency_speedup_comparison': 'not available: no matched local baseline',
    }, 'variants': {}}
    csv_rows = []
    for variant in ('standard', 'dev'):
        records = [json.loads(line) for line in (directory / f'{variant}.ndjson').read_text().splitlines()]
        load = records[0]
        quality = [json.loads(line) for line in (directory / f'{variant}-quality.ndjson').read_text().splitlines()]
        assert len(quality) == len({row['task_id'] for row in quality}) == 164
        scores = json.loads((directory / f'{variant}-solutions_eval_results.json').read_text())['eval']
        assert set(scores) == {row['task_id'] for row in quality}
        passed = sum(scores[row['task_id']][0]['base_status'] == 'pass' for row in quality)
        plus_passed = sum(scores[row['task_id']][0]['base_status'] == scores[row['task_id']][0]['plus_status'] == 'pass' for row in quality)
        for row in quality:
            result = scores[row['task_id']][0]
            response = row['response']
            csv_rows.append({'variant':variant, 'task_id':row['task_id'],
                             'prompt_tokens':response.get('tokens_evaluated'),
                             'generated_tokens':response.get('tokens_predicted'),
                             'stop_type':response.get('stop_type'), 'wall_seconds':row['wall_seconds'],
                             'base_status':result['base_status'], 'plus_status':result['plus_status']})
        perf = {}
        for length in (32, 128, 512):
            trials = [row for row in records if row.get('task_id', '').startswith(f'perf/{length}/')]
            assert len(trials) == 5
            perf[str(length)] = {'repetitions': 5, 'output_tokens': 64,
                'ttft_median_ms': statistics.median(row['ttft_ms'] for row in trials),
                'ttft_min_ms': min(row['ttft_ms'] for row in trials),
                'ttft_max_ms': max(row['ttft_ms'] for row in trials),
                'ttft_p95_ms': percentile([row['ttft_ms'] for row in trials], .95),
                'prefill_median_tokens_per_second': statistics.median(length / (row['prefill_ms']/1000) for row in trials),
                'decode_median_tokens_per_second': statistics.median(row['decode_tokens_per_second'] for row in trials)}
        summary['variants'][variant] = {
            'tasks':164, 'humaneval_passed':passed, 'humaneval_pass1':passed/164,
            'humaneval_plus_passed':plus_passed, 'humaneval_plus_pass1':plus_passed/164,
            'stop_reasons':dict(Counter(row['response'].get('stop_type', 'unknown') for row in quality)),
            'generated_tokens_total':sum(row['response']['tokens_predicted'] for row in quality),
            'load_ms':load['load_ms'], 'load_rss_mib':load['memory']['rss_kib']/1024,
            'peak_rss_mib':max(row['memory']['peak_rss_kib'] for row in records)/1024,
            'perf':perf,
            'quality_total_seconds':sum(row['wall_seconds'] for row in quality),
            'quality_backend':'llama.cpp b11778 CPU; separate from Candle performance',
        }
    metadata = json.loads((directory / 'run-metadata.json').read_text())
    summary['run'] = {key: metadata[key] for key in ['started_utc', 'threads', 'dataset_sha256', 'runtime', 'build']}
    summary['quality_run'] = json.loads((directory / 'quality-metadata.json').read_text())
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    with (directory / 'per-task.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    summarize(parser.parse_args().directory)
