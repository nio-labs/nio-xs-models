"""
Training Pipeline for NioMask (~1.0M Secret & PII Redactor)
Multi-task loss: Token-level BIO Classification + Stream-level Continuous Risk Score.
"""

import os
import json
import time
import argparse
from typing import List, Dict, Any

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from rich.console import Console
from rich.table import Table

from model import NioMaskConfig, NioMaskModel, PAD_ID, NUM_CLASSES, LABEL_NAMES

console = Console()


class MaskDataset(Dataset):
    def __init__(self, jsonl_path: str, max_seq_len: int = 256):
        self.samples = []
        self.max_seq_len = max_seq_len
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.samples[idx]
        input_ids = item["input_ids"][: self.max_seq_len]
        labels = item["labels"][: self.max_seq_len]
        risk_score = float(item["risk_score"])
        return {
            "input_ids": input_ids,
            "labels": labels,
            "risk_score": risk_score,
        }


def collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    batch_size = len(batch)
    max_len = max(len(x["input_ids"]) for x in batch)

    padded_ids = torch.full((batch_size, max_len), PAD_ID, dtype=torch.long)
    padded_labels = torch.full((batch_size, max_len), -100, dtype=torch.long)  # -100 ignored by CE
    attention_mask = torch.zeros((batch_size, max_len), dtype=torch.float32)
    risk_scores = torch.zeros((batch_size, 1), dtype=torch.float32)

    for i, item in enumerate(batch):
        seq_len = len(item["input_ids"])
        padded_ids[i, :seq_len] = torch.tensor(item["input_ids"], dtype=torch.long)
        padded_labels[i, :seq_len] = torch.tensor(item["labels"], dtype=torch.long)
        attention_mask[i, :seq_len] = 1.0
        risk_scores[i, 0] = item["risk_score"]

    return {
        "input_ids": padded_ids,
        "attention_mask": attention_mask,
        "labels": padded_labels,
        "risk_score": risk_scores,
    }


def evaluate(model: nn.Module, val_loader: DataLoader, criterion_ce: nn.Module, criterion_mse: nn.Module, device: torch.device):
    model.eval()
    total_token_loss = 0.0
    total_risk_loss = 0.0
    correct_tokens = 0
    total_tokens = 0

    secret_tp, secret_fp, secret_fn = 0, 0, 0
    pii_tp, pii_fp, pii_fn = 0, 0, 0

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            targets_risk = batch["risk_score"].to(device)

            token_logits, pred_risk = model(input_ids, attention_mask)

            loss_token = criterion_ce(token_logits.view(-1, NUM_CLASSES), labels.view(-1))
            loss_risk = criterion_mse(pred_risk, targets_risk)

            total_token_loss += loss_token.item()
            total_risk_loss += loss_risk.item()

            preds = torch.argmax(token_logits, dim=-1)
            valid_mask = labels != -100

            correct_tokens += ((preds == labels) & valid_mask).sum().item()
            total_tokens += valid_mask.sum().item()

            # Compute precision / recall for secret tokens (labels 1, 2)
            is_secret_true = (labels == 1) | (labels == 2)
            is_secret_pred = (preds == 1) | (preds == 2)
            secret_tp += ((is_secret_pred & is_secret_true) & valid_mask).sum().item()
            secret_fp += ((is_secret_pred & ~is_secret_true) & valid_mask).sum().item()
            secret_fn += ((~is_secret_pred & is_secret_true) & valid_mask).sum().item()

            # Compute precision / recall for PII tokens (labels 3, 4)
            is_pii_true = (labels == 3) | (labels == 4)
            is_pii_pred = (preds == 3) | (preds == 4)
            pii_tp += ((is_pii_pred & is_pii_true) & valid_mask).sum().item()
            pii_fp += ((is_pii_pred & ~is_pii_true) & valid_mask).sum().item()
            pii_fn += ((~is_pii_pred & is_pii_true) & valid_mask).sum().item()

    num_batches = len(val_loader)
    token_acc = correct_tokens / max(1, total_tokens)
    
    secret_prec = secret_tp / max(1, secret_tp + secret_fp)
    secret_rec = secret_tp / max(1, secret_tp + secret_fn)
    secret_f1 = (2 * secret_prec * secret_rec) / max(1e-9, secret_prec + secret_rec)

    pii_prec = pii_tp / max(1, pii_tp + pii_fp)
    pii_rec = pii_tp / max(1, pii_tp + pii_fn)
    pii_f1 = (2 * pii_prec * pii_rec) / max(1e-9, pii_prec + pii_rec)

    return {
        "val_loss": (total_token_loss + 0.5 * total_risk_loss) / num_batches,
        "token_acc": token_acc,
        "secret_f1": secret_f1,
        "secret_rec": secret_rec,
        "pii_f1": pii_f1,
        "pii_rec": pii_rec,
    }


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--output-dir", type=str, default="models", help="Model output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    console.print(f"[bold cyan]NioMask Training Pipeline[/bold cyan] on device: [bold yellow]{device}[/bold yellow]")

    # Datasets
    train_dataset = MaskDataset(os.path.join(args.data_dir, "train.jsonl"))
    val_dataset = MaskDataset(os.path.join(args.data_dir, "val.jsonl"))

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    # Model
    config = NioMaskConfig()
    model = NioMaskModel(config).to(device)

    # Class weights for CrossEntropy: upweight secrets and PII
    class_weights = torch.tensor([1.0, 5.0, 4.0, 4.0, 3.0, 2.0, 2.0], device=device)
    criterion_ce = nn.CrossEntropyLoss(weight=class_weights, ignore_index=-100)
    criterion_mse = nn.MSELoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_f1 = 0.0
    checkpoint_path = os.path.join(args.output_dir, "nio_mask_checkpoint.pt")

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        start_time = time.time()

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            targets_risk = batch["risk_score"].to(device)

            optimizer.zero_grad()
            token_logits, pred_risk = model(input_ids, attention_mask)

            loss_token = criterion_ce(token_logits.view(-1, NUM_CLASSES), labels.view(-1))
            loss_risk = criterion_mse(pred_risk, targets_risk)
            loss = loss_token + 0.5 * loss_risk

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()

        scheduler.step()
        elapsed = time.time() - start_time
        metrics = evaluate(model, val_loader, criterion_ce, criterion_mse, device)

        console.print(
            f"Epoch {epoch:02d}/{args.epochs:02d} | "
            f"Train Loss: {total_loss / len(train_loader):.4f} | "
            f"Val Loss: {metrics['val_loss']:.4f} | "
            f"Acc: {metrics['token_acc']*100:.2f}% | "
            f"Secret F1: [bold green]{metrics['secret_f1']*100:.2f}%[/bold green] (Recall: {metrics['secret_rec']*100:.2f}%) | "
            f"PII F1: {metrics['pii_f1']*100:.2f}% | "
            f"Time: {elapsed:.1f}s"
        )

        if metrics["secret_f1"] > best_f1:
            best_f1 = metrics["secret_f1"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "config": config.__dict__,
                "metrics": metrics,
            }, checkpoint_path)

    console.print(f"[bold green]Training complete![/bold green] Best Secret F1: [bold yellow]{best_f1*100:.2f}%[/bold yellow]")
    console.print(f"Checkpoint saved to: {checkpoint_path}")


if __name__ == "__main__":
    train()
