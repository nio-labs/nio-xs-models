"""Build an external tokenizer that exactly matches a NioRay GGUF vocabulary.

Uses the Standard tokenizer's BPE configuration and checks every retained token
and merge against the exported GGUF. No model weights are changed.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct


def read_gguf(path):
    with Path(path).open('rb') as stream:
        def number(fmt):
            return struct.unpack('<' + fmt, stream.read(struct.calcsize('<' + fmt)))[0]

        def string():
            return stream.read(number('Q')).decode('utf-8')

        def value(kind):
            if kind == 8:
                return string()
            if kind == 9:
                subtype, count = number('I'), number('Q')
                return [value(subtype) for _ in range(count)]
            return number({0: 'B', 1: 'b', 2: 'H', 3: 'h', 4: 'I', 5: 'i',
                           6: 'f', 7: '?', 10: 'Q', 11: 'q', 12: 'd'}[kind])

        if stream.read(4) != b'GGUF' or number('I') not in (2, 3):
            raise ValueError('Expected GGUF v2 or v3')
        tensor_count, metadata_count = number('Q'), number('Q')
        metadata = {}
        for _ in range(metadata_count):
            key = string()
            metadata[key] = value(number('I'))
        parameters = 0
        for _ in range(tensor_count):
            string()
            parameters += math.prod(number('Q') for _ in range(number('I')))
            number('I')
            number('Q')
    return metadata, parameters


def validate_tokenizer(tokenizer, metadata):
    tokens = metadata['tokenizer.ggml.tokens']
    vocab = dict(tokenizer['model']['vocab'])
    for token in tokenizer.get('added_tokens', []):
        if token['content'] in vocab and vocab[token['content']] != token['id']:
            raise ValueError('Conflicting added token ID')
        vocab[token['content']] = token['id']
    for token, token_id in vocab.items():
        if token_id >= len(tokens) or token_id < 0 or tokens[token_id] != token:
            raise ValueError(f'Tokenizer mismatch: {token!r} at ID {token_id}')
    # Standard GGUF pads its vocabulary to 151936 with unused entries.
    for token_id, token in enumerate(tokens):
        if not token.startswith('[PAD') and vocab.get(token) != token_id:
            raise ValueError(f'Missing model token: {token!r} at ID {token_id}')
    merges = [' '.join(m) if isinstance(m, list) else m for m in tokenizer['model']['merges']]
    if merges != metadata['tokenizer.ggml.merges']:
        raise ValueError('BPE merges do not match the GGUF')


def build_tokenizer(source, metadata):
    result = copy.deepcopy(source)
    tokens = metadata['tokenizer.ggml.tokens']
    ids = {token: i for i, token in enumerate(tokens)}
    original_vocab = source['model']['vocab']
    result['model']['vocab'] = {token: ids[token] for token in original_vocab if token in ids}
    result['added_tokens'] = [dict(token, id=ids[token['content']])
                              for token in source['added_tokens'] if token['content'] in ids]
    retained = result['model']['vocab']
    result['model']['merges'] = []
    for merge in source['model']['merges']:
        parts = merge if isinstance(merge, list) else merge.split(' ')
        if len(parts) == 2 and all(part in retained for part in parts) and ''.join(parts) in retained:
            result['model']['merges'].append(merge)
    validate_tokenizer(result, metadata)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--source-tokenizer', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    metadata, parameters = read_gguf(args.model)
    tokenizer = build_tokenizer(json.loads(args.source_tokenizer.read_text()), metadata)
    args.output.write_text(json.dumps(tokenizer, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'parameters': parameters, 'vocabulary': len(metadata['tokenizer.ggml.tokens']),
                      'tokenizer': str(args.output), 'bytes': args.output.stat().st_size,
                      'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
