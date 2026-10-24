"""
NioMicro BPE Tokenizer Trainer
Trains a domain-focused Byte-Pair Encoding (BPE) tokenizer for NioMicro.
Outputs an isolated tokenizer in models/5m-context by default.
"""

import argparse
import json
from pathlib import Path
from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers, processors

def train_tokenizer(data_path: Path, output_dir: Path, vocab_size: int = 8000):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize BPE model
    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    
    # Configure special tokens
    special_tokens = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=2,
        special_tokens=special_tokens,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet()
    )
    
    # Iterator over training texts
    def text_iterator():
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    yield item["text"]
                    
    print(f"Training BPE tokenizer (vocab_size={vocab_size}) on {data_path}...")
    tokenizer.train_from_iterator(text_iterator(), trainer=trainer)
    
    # Post-processor for [CLS] and [SEP]
    cls_token_id = tokenizer.token_to_id("[CLS]")
    sep_token_id = tokenizer.token_to_id("[SEP]")
    
    tokenizer.post_processor = processors.TemplateProcessing(
        single="[CLS] $A [SEP]",
        pair="[CLS] $A [SEP] $B:1 [SEP]:1",
        special_tokens=[
            ("[CLS]", cls_token_id),
            ("[SEP]", sep_token_id),
        ]
    )
    
    output_file = output_dir / "tokenizer.json"
    tokenizer.save(str(output_file))
    print(f"Tokenizer saved to {output_file}")
    
    # Validation test
    sample = "Pull Request: pub fn safe_add(a: i32, b: i32) -> i32"
    encoded = tokenizer.encode(sample)
    print(f"Test Sample: '{sample}'")
    print(f"Tokens: {encoded.tokens[:10]}...")
    print(f"IDs: {encoded.ids[:10]}...")
    print(f"Decoded: '{tokenizer.decode(encoded.ids)}'")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", type=Path, default=base / "data/5m-context/train.jsonl")
    parser.add_argument("--output-dir", type=Path, default=base / "models/5m-context")
    args = parser.parse_args()
    train_tokenizer(args.data_path, args.output_dir, vocab_size=8000)
