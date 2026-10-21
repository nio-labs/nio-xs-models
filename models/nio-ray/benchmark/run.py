"""Run both NioRay variants on fixed-length CPU workloads and all HumanEval+ tasks.

Only NioRay weights are loaded. Qwen reference scores are separately cited in
README.md. Compile the Rust driver in release mode before running this script.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import urllib.request

QWEN_COMMIT = '33bc6aabd7791ad7b32f7e92104f11f2359ba890'
DATA_URL = f'https://raw.githubusercontent.com/QwenLM/Qwen3-Coder/{QWEN_COMMIT}/qwencoder-eval/instruct/eval_plus/data/HumanEvalPlus-v0.1.10.jsonl'
STOP = ['<|endoftext|>', '<|endofmask|>', '</s>', '\nif __name__', '\ndef main(', '\nprint(', '\n#', '\n```']


def chat_prompt(prompt):
    # Qwen's published eval_plus/model.py ChatML template, including assistant prefix.
    return ('<|im_start|>system\n'
            'You are an intelligent programming assistant to produce Python algorithmic solutions<|im_end|>\n'
            '<|im_start|>user\nCan you complete the following Python function?\n```python\n'
            + prompt.strip() + '\n```\n<|im_end|>\n<|im_start|>assistant\n```python\n')


def requests(problems, suite='both'):
    synthetic = 'def example(value: int) -> int:\n    return value + 1\n' * 300
    yield {'task_id': 'warmup', 'prompt': synthetic, 'prompt_tokens': 32, 'max_tokens': 16, 'ignore_eos': True}
    for length in (32, 128, 512):
        for repeat in range(5):
            yield {'task_id': f'perf/{length}/{repeat}', 'prompt': synthetic,
                   'prompt_tokens': length, 'max_tokens': 64, 'ignore_eos': True}
    if suite == 'performance':
        return
    for problem in problems:
        yield {'task_id': problem['task_id'], 'prompt': chat_prompt(problem['prompt']),
               'max_tokens': 2048, 'stop': STOP}


def read_records(path):
    records = []
    for line in path.read_text().splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            break  # Driver may be in the middle of flushing the final line.
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--threads', type=int, default=6)
    parser.add_argument('--suite', choices=['performance', 'both'], default='both')
    parser.add_argument('--variant', choices=['standard', 'dev', 'both'], default='both')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = Path(__file__).resolve().parent / 'target/release/nioray-benchmark'
    dataset = urllib.request.urlopen(DATA_URL).read()
    problems = [json.loads(line) for line in dataset.splitlines()]
    assert len(problems) == 164 and len({p['task_id'] for p in problems}) == 164
    dataset_path = args.output / 'HumanEvalPlus-v0.1.10.jsonl'
    dataset_path.write_bytes(dataset)
    manifest = json.loads((Path(__file__).resolve().parents[1] / 'release-manifest.json').read_text())
    for asset in manifest['assets']:
        with (args.models / asset['name']).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == asset['sha256'], asset['name']
    metadata = {
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'dataset_url': DATA_URL, 'dataset_sha256': hashlib.sha256(dataset).hexdigest(),
        'dataset_tasks': 164, 'qwen_reference': 'https://arxiv.org/html/2409.12186v2#S7.T16',
        'qwen_reference_humaneval_pass1': 0.616, 'qwen_reference_humaneval_plus_pass1': 0.573,
        'qwen_prompt_source': f'https://github.com/QwenLM/Qwen3-Coder/blob/{QWEN_COMMIT}/qwencoder-eval/instruct/eval_plus/model.py',
        'sampling': 'greedy', 'samples_per_task': 1, 'max_new_tokens': 2048,
        'stop_strings': STOP, 'threads': args.threads, 'batch_size': 1,
        'platform': platform.platform(), 'python': platform.python_version(),
        'cpu': subprocess.check_output(['lscpu'], text=True),
        'rustc': subprocess.check_output(['rustc', '+stable', '--version'], text=True).strip(),
        'build': 'cargo +stable build --release; RUSTFLAGS=-C target-cpu=native',
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'cargo_lock_sha256': hashlib.sha256((binary.parents[2] / 'Cargo.lock').read_bytes()).hexdigest(),
        'runtime': 'CPU Candle 0.8.4; direct benchmark harness, not CLI end-to-end',
        'suite': args.suite,
        'load_condition': 'new process; OS page cache not cleared',
        'perf': {'prompt_tokens': [32, 128, 512], 'output_tokens': 64, 'repetitions': 5,
                 'warmup_prompt_tokens': 32, 'warmup_output_tokens': 16,
                 'stop_at_eos': False, 'prefix_cache': False},
        'models': manifest['assets'],
    }
    (args.output / ('run-metadata.json' if not (args.output / 'run-metadata.json').exists() else f'{args.variant}-metadata.json')).write_text(json.dumps(metadata, indent=2) + '\n')
    for variant in ('standard', 'dev') if args.variant == 'both' else (args.variant,):
        log_path = args.output / f'{variant}.ndjson'
        if log_path.exists():
            raise FileExistsError(f'{log_path} exists; use a new output directory to avoid overwriting results')
        name, tokenizer = ('nio-ray.Q4_K_M.gguf', 'tokenizer.json') if variant == 'standard' else ('nio-ray-dev.Q4_K_M.gguf', 'nio-ray-dev-tokenizer.json')
        with tempfile.TemporaryFile(mode='w+') as inputs, log_path.open('w') as output, (args.output / f'{variant}.stderr.log').open('w') as errors:
            for request in requests(problems, args.suite):
                inputs.write(json.dumps(request) + '\n')
            inputs.seek(0)
            process = subprocess.Popen([str(binary), str(args.models / name), str(args.models / tokenizer), str(args.threads)],
                                       stdin=inputs, stdout=output, stderr=errors)
            seen = 0
            last_notice = time.monotonic()
            while process.poll() is None:
                records = read_records(log_path)
                if len(records) > seen:
                    last = records[-1]
                    print(variant, len(records), last.get('task_id', 'loaded'),
                          f"{last.get('ttft_ms', 0):.1f}ms TTFT", flush=True)
                    seen = len(records)
                    last_notice = time.monotonic()
                elif time.monotonic() - last_notice >= 30:
                    print(variant, 'running next task;', seen, 'records complete', flush=True)
                    last_notice = time.monotonic()
                time.sleep(1)
            if process.returncode:
                raise RuntimeError(f'{variant} driver failed ({process.returncode}): {(args.output / f"{variant}.stderr.log").read_text()}')
        records = read_records(log_path)
        if args.suite == 'performance':
            print(variant, 'COMPLETE: 15 native performance trials', flush=True)
            continue
        samples = [record for record in records if record.get('task_id', '').startswith('HumanEval/')]
        assert len(samples) == 164
        with (args.output / f'{variant}-solutions.jsonl').open('w') as stream:
            for sample in samples:
                stream.write(json.dumps({'task_id': sample['task_id'], 'solution': sample['text'].replace('\t', '    ')}) + '\n')
        print(variant, 'COMPLETE: 164 HumanEval solutions', flush=True)


if __name__ == '__main__':
    main()
