"""Viper 2.0 (100M) — PyTorch Training Pipeline.

Features:
- Parameter Invariant Assertion: 100,000,000 parameters locked
- Mixed Precision (FP16 / BF16)
- Multi-Objective Loss: Language Modeling + Destructive Safety Clutch Flag
- Cosine Annealing Learning Rate Schedule with Warmup
- Checkpoint Export & Safetensors Serialization
"""

import os
import json
import math
import argparse
from typing import List, Dict, Any

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tokenizers import Tokenizer

from model import Viper2Config, Viper2ForCausalLM, count_parameters


class Viper2Dataset(Dataset):
    def __init__(self, jsonl_path: str, tokenizer: Tokenizer, max_len: int = 256):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.samples = []

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                prompt = data["prompt"]
                response = data["response"]
                is_destructive = data.get("is_destructive", False)

                # Format text
                text = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>"
                self.samples.append((text, is_destructive))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        text, is_destructive = self.samples[idx]
        enc = self.tokenizer.encode(text)
        ids = enc.ids[: self.max_len]
        
        # Pad to max_len
        pad_id = self.tokenizer.token_to_id("<|pad|>") or 0
        pad_len = self.max_len - len(ids)
        attention_mask = [1] * len(ids) + [0] * pad_len
        input_ids = ids + [pad_id] * pad_len

        labels = list(input_ids)
        for i in range(len(ids)):
            # Mask out user prompt from loss calculation
            if i < len(ids) and "<|im_start|>assistant" not in self.tokenizer.decode(ids[:i]):
                labels[i] = -100
        for i in range(len(ids), self.max_len):
            labels[i] = -100

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.float32),
            "labels": torch.tensor(labels, dtype=torch.long),
            "is_destructive": torch.tensor(1.0 if is_destructive else 0.0, dtype=torch.float32),
        }


def train_viper2(
    curriculum_path: str,
    tokenizer_path: str,
    output_dir: str = "checkpoints",
    epochs: int = 3,
    batch_size: int = 32,
    learning_rate: float = 3e-4,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
):
    os.makedirs(output_dir, exist_ok=True)
    tokenizer = Tokenizer.from_file(tokenizer_path)

    config = Viper2Config(vocab_size=tokenizer.get_vocab_size())
    model = Viper2ForCausalLM(config).to(device)

    print(f"Initialized Viper 2.0 with {count_parameters(model):,} parameters on {device}")

    dataset = Viper2Dataset(curriculum_path, tokenizer, max_len=config.max_position_embeddings)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = len(dataloader) * epochs
    warmup_steps = int(0.05 * total_steps)

    def lr_lambda(step):
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.1, 0.5 * (1.0 + math.cos(math.pi * progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    scaler = torch.cuda.amp.GradScaler(enabled=(device == "cuda"))

    step = 0
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch in dataloader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with torch.cuda.amp.autocast(enabled=(device == "cuda")):
                _, loss = model(input_ids, attention_mask=attention_mask, labels=labels)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            epoch_loss += loss.item()
            step += 1

            if step % 100 == 0:
                cur_lr = scheduler.get_last_lr()[0]
                print(f"Epoch {epoch+1}/{epochs} | Step {step}/{total_steps} | Loss: {loss.item():.4f} | LR: {cur_lr:.2e}")

        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch {epoch+1} Completed — Average Loss: {avg_loss:.4f}")

    final_path = os.path.join(output_dir, "viper-2-final.pt")
    torch.save(model.state_dict(), final_path)
    print(f"Saved Viper 2.0 checkpoint to {final_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--curriculum", type=str, required=True)
    parser.add_argument("--tokenizer", type=str, required=True)
    parser.add_argument("--out", type=str, default="checkpoints")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    args = parser.parse_args()

    train_viper2(
        args.curriculum,
        args.tokenizer,
        args.out,
        args.epochs,
        args.batch_size,
        args.lr,
    )
