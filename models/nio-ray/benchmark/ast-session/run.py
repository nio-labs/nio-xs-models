"""Run 20 tasks per model using the actual AST runtime crates."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for model in ('ray', 'viper'):
        parser.add_argument(f'--{model}-model', type=Path, required=True)
        parser.add_argument(f'--{model}-tokenizer', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--max-new-tokens', type=int, default=32)
    parser.add_argument('--binary', type=Path, default=ROOT / 'target/release/nio-ast-session-benchmark')
    args = parser.parse_args()
    if args.threads < 1 or args.max_new_tokens < 1:
        parser.error('threads and max-new-tokens must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    sources = ['crates/nio-ray-runtime/src/lib.rs', 'crates/nio-ray-runtime/src/main.rs',
               'crates/nio-viper-runtime/src/lib.rs', 'crates/nio-viper-runtime/src/main.rs']
    metadata = dict(platform=platform.platform(),
        cpu=subprocess.check_output(['lscpu'], text=True), threads=args.threads,
        max_new_tokens=args.max_new_tokens, binary_sha256=digest(args.binary),
        source_sha256={p: digest(ROOT / p) for p in sources},
        benchmark_source_sha256=digest(HERE / 'src/main.rs'),
        protocol='One process/model, 20 independent tasks, KV reset, CLI AST pools, natural EOS, cumulative VmHWM.',
        models=[])
    for model in ('viper', 'ray'):
        path = getattr(args, f'{model}_model').resolve()
        tok = getattr(args, f'{model}_tokenizer').resolve()
        metadata['models'].append(dict(name=model, model_sha256=digest(path),
            model_bytes=path.stat().st_size, tokenizer_sha256=digest(tok),
            prompts_sha256=digest(HERE / f'{model}-prompts.json')))
    (args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    for model in ('viper', 'ray'):
        cmd = [str(args.binary.resolve()), str(getattr(args, f'{model}_model').resolve()),
               str(getattr(args, f'{model}_tokenizer').resolve()), model,
               str(HERE / f'{model}-prompts.json'), str(args.max_new_tokens)]
        with (args.output / f'{model}-results.ndjson').open('w') as dest, \
             (args.output / f'{model}-stderr.txt').open('w') as err:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=err, text=True,
                env=dict(os.environ, RAYON_NUM_THREADS=str(args.threads), TOKENIZERS_PARALLELISM='false'))
            for line in process.stdout:
                row = json.loads(line)
                dest.write(line)
                dest.flush()
                if row['type'] == 'prompt':
                    print(f"{model} {row['id']}/20: {row['generated_tokens']} tokens; "
                          f"session peak {row['process_hwm_mib']:.2f} MiB", flush=True)
            if process.wait() != 0:
                raise SystemExit(f'{model} failed; inspect {model}-stderr.txt')


if __name__ == '__main__':
    main()
