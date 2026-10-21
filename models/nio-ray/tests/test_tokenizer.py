"""Run with: python3.12 -m unittest discover -s models/nio-ray/tests"""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_tokenizer import build_tokenizer, validate_tokenizer


class TokenizerCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            'model': {'vocab': {'a': 0, 'b': 1, 'ab': 2, 'unused': 3},
                      'merges': [['a', 'b']]},
            'added_tokens': [{'content': '<|im_end|>', 'id': 4, 'special': True}],
            'normalizer': {'type': 'NFC'},
        }
        self.metadata = {'tokenizer.ggml.tokens': ['a', 'b', 'ab', '<|im_end|>'],
                         'tokenizer.ggml.merges': ['a b']}

    def test_remaps_special_tokens_and_preserves_source(self):
        before = copy.deepcopy(self.source)
        result = build_tokenizer(self.source, self.metadata)
        self.assertEqual(result['added_tokens'][0]['id'], 3)
        self.assertNotIn('unused', result['model']['vocab'])
        self.assertEqual(result['normalizer'], self.source['normalizer'])
        self.assertEqual(self.source, before)

    def test_rejects_standard_tokenizer_for_dev(self):
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            validate_tokenizer(self.source, self.metadata)

    def test_rejects_different_merge_order(self):
        self.metadata['tokenizer.ggml.merges'] = []
        with self.assertRaisesRegex(ValueError, 'merges'):
            build_tokenizer(self.source, self.metadata)

    def test_rejects_missing_model_token(self):
        self.metadata['tokenizer.ggml.tokens'].append('missing')
        with self.assertRaisesRegex(ValueError, 'Missing model token'):
            build_tokenizer(self.source, self.metadata)


if __name__ == '__main__':
    unittest.main()
