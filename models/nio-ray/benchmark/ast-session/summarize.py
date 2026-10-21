"""Summarize a completed AST session directory without rerunning inference."""
import argparse
import json
import statistics
from pathlib import Path


def summarize(folder):
    result = {}
    for model in ('ray', 'viper'):
        rows = [json.loads(line) for line in (folder / f'{model}-results.ndjson').read_text().splitlines()]
        load, end = rows[0], rows[-1]
        tasks = [row for row in rows if row['type'] == 'prompt']
        if load['type'] != 'load' or end['type'] != 'end' or len(tasks) != 20:
            raise ValueError(f'{model}: incomplete 20-task session')
        if [row['id'] for row in tasks] != list(range(1, 21)):
            raise ValueError(f'{model}: unexpected task IDs')
        if any(row['generated_tokens'] != len(row['generated_ids']) for row in tasks):
            raise ValueError(f'{model}: inconsistent token counts')
        steps = sum(row['decode_steps'] for row in tasks)
        milliseconds = sum(row['decode_ms'] for row in tasks)
        result[model] = {
            'initial_rss_mib': load['rss_mib'],
            'peak_rss_mib': end['peak_rss_mib'],
            'final_rss_mib': end['rss_mib'],
            'precomputed_context_tokens': load.get('precomputed_context_tokens'),
            'prompt_tokens_min': min(row['prompt_tokens'] for row in tasks),
            'prompt_tokens_max': max(row['prompt_tokens'] for row in tasks),
            'generated_tokens': sum(row['generated_tokens'] for row in tasks),
            'nonempty_outputs': sum(row['generated_tokens'] > 0 for row in tasks),
            'empty_outputs': sum(row['generated_tokens'] == 0 for row in tasks),
            'median_prefill_ms': statistics.median(row['prefill_ms'] for row in tasks),
            'aggregate_decode_tps': 1000 * steps / milliseconds if steps else None,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.session), indent=2))


if __name__ == '__main__':
    main()
