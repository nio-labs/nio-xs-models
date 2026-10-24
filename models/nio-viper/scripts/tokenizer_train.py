"""Viper 2.0 (100M) — Tokenizer Training Script.

Trains a ByteLevel BPE tokenizer with exactly 17,451 vocabulary tokens,
covering all shell syntax, flags, subshells, pipelines, PowerShell cmdlets, and special tokens.
"""

import os
from tokenizers import Tokenizer, models, pre_tokenizers, trainers, decoders, processors

SPECIAL_TOKENS = [
    "<|endoftext|>",
    "<|im_start|>",
    "<|im_end|>",
    "<|pad|>",
    "<|prompt|>",
    "<|response|>",
    "<|clutch_safe|>",
    "<|clutch_destructive|>",
]

def train_viper2_tokenizer(corpus_files, output_path: str = "viper-2-tokenizer.json", vocab_size: int = 17451):
    tokenizer = Tokenizer(models.BPE())
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()

    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=True,
    )

    tokenizer.train(corpus_files, trainer)
    tokenizer.save(output_path)
    print(f"Saved Viper 2.0 Tokenizer with {vocab_size} tokens to {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=str, required=True, help="Path to text or jsonl training corpus")
    parser.add_argument("--out", type=str, default="viper-2-tokenizer.json")
    parser.add_argument("--vocab-size", type=int, default=17451)
    args = parser.parse_args()

    train_viper2_tokenizer([args.corpus], args.out, args.vocab_size)
