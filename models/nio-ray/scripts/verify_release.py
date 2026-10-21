"""Verify downloaded NioRay release assets and tokenizer compatibility.

Usage: uv run --with tokenizers python models/nio-ray/scripts/verify_release.py ARTIFACT_DIR
"""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_tokenizer import read_gguf, validate_tokenizer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts', type=Path)
    args = parser.parse_args()
    from tokenizers import Tokenizer
    manifest = json.loads((Path(__file__).resolve().parents[1] / 'release-manifest.json').read_text())
    for asset in manifest['assets']:
        path = args.artifacts / asset['name']
        assert path.stat().st_size == asset['size_bytes'], f'Wrong size: {path}'
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == asset['sha256'], f'Wrong hash: {path}'
        if asset['name'].endswith('.gguf'):
            metadata, parameters = read_gguf(path)
            assert parameters == asset['parameters']
            assert len(metadata['tokenizer.ggml.tokens']) == asset['vocabulary_size']
            tokenizer_path = args.artifacts / asset['external_tokenizer']
            validate_tokenizer(json.loads(tokenizer_path.read_text()), metadata)
            tokenizer = Tokenizer.from_file(str(tokenizer_path))
            assert tokenizer.token_to_id('<|im_end|>') == metadata['tokenizer.ggml.eos_token_id']
            for text in [
                '<|im_start|>user\nWrite a Rust function.<|im_end|>\n<|im_start|>assistant\n',
                'const π = "你好 สวัสดี 🚀";',
                'fn main() { println!("hello"); }',
            ]:
                ids = tokenizer.encode(text).ids
                assert all(0 <= token_id < asset['vocabulary_size'] for token_id in ids)
                assert tokenizer.decode(ids, skip_special_tokens=False) == text
        print(f"PASS {asset['name']}")
    dev = read_gguf(args.artifacts / 'nio-ray-dev.Q4_K_M.gguf')[0]
    standard = json.loads((args.artifacts / 'tokenizer.json').read_text())
    try:
        validate_tokenizer(standard, dev)
    except ValueError:
        print('PASS Standard tokenizer rejected for Dev')
    else:
        raise AssertionError('Standard tokenizer incorrectly accepted for Dev')


if __name__ == '__main__':
    main()
