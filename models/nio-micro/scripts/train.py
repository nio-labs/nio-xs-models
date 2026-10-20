"""
NioMicro Training Loop
Trains the contextual candidate by default; --binary-baseline retains the earlier trainer.
"""

import argparse
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Any

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tokenizers import Tokenizer

try:
    from .model import NioMicro
    from .artifacts import sha256
except ImportError:
    from model import NioMicro
    from artifacts import sha256

class NioDataset(Dataset):
    def __init__(self, data_file: Path, tokenizer: Tokenizer, max_len: int = 256):
        self.rows = []
        self.input_ids = []
        self.attention_masks = []
        self.decisions = []
        self.sentiments = []
        self.scores = []
        
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    self.rows.append(item)
                    encoded = tokenizer.encode(item["text"])
                    if len(encoded.ids) > max_len:
                        raise ValueError(f"Input exceeds {max_len} tokens in {data_file}")
                    ids = encoded.ids[:max_len]
                    mask = [1] * len(ids)
                    if len(ids) < max_len:
                        pad = max_len - len(ids)
                        ids = ids + [0] * pad
                        mask = mask + [0] * pad
                    self.input_ids.append(ids)
                    self.attention_masks.append(mask)
                    self.decisions.append(item["decision"])
                    self.sentiments.append(item["sentiment"])
                    self.scores.append(item["score"])

        self.input_ids = torch.tensor(self.input_ids, dtype=torch.long)
        self.attention_masks = torch.tensor(self.attention_masks, dtype=torch.long)
        self.decisions = torch.tensor(self.decisions, dtype=torch.long)
        self.sentiments = torch.tensor(self.sentiments, dtype=torch.long)
        self.scores = torch.tensor(self.scores, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.decisions)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return {
            "input_ids": self.input_ids[idx],
            "attention_mask": self.attention_masks[idx],
            "decision": self.decisions[idx],
            "sentiment": self.sentiments[idx],
            "score": self.scores[idx],
        }

def audit_splits(datasets):
    names = list(datasets)
    for name, dataset in datasets.items():
        if not len(dataset):
            raise ValueError(f"Empty dataset: {name}")
        texts = [r["text"] for r in dataset.rows]
        if len(texts) != len(set(texts)):
            raise ValueError(f"Duplicate text in {name}")
        for row in dataset.rows:
            if not row.get("scenario_group"):
                raise ValueError("Missing scenario_group; run prepare_upgrade_data.py")
            if row["decision"] not in (0, 1) or row["sentiment"] not in (0, 1):
                raise ValueError("Invalid binary label")
            if not 0 <= row["score"] <= 1:
                raise ValueError("Invalid score")
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            for field in ("text", "scenario_group"):
                if {r[field] for r in datasets[left].rows} & {r[field] for r in datasets[right].rows}:
                    raise ValueError(f"Cross-split {field} overlap: {left}, {right}")


def trim_batch(batch, device):
    length = int(batch["attention_mask"].sum(1).max())
    return (batch["input_ids"][:, :length].to(device),
            batch["attention_mask"][:, :length].to(device))


def train(args):
    data_dir = args.data_dir
    models_dir = args.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")
    
    # Load tokenizer
    tokenizer_path = models_dir / "tokenizer.json"
    if not tokenizer_path.exists():
        raise FileNotFoundError(f"Missing {tokenizer_path}. Run train_tokenizer.py first!")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    
    # Datasets and Loaders
    datasets = {name: NioDataset(data_dir / f"{name}.jsonl", tokenizer)
                for name in ("train", "val", "test")}
    audit_splits(datasets)
    train_dataset, val_dataset = datasets["train"], datasets["val"]
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False)
    
    # Model
    model = NioMicro().to(device)
    if model.count_parameters() != 5_000_000:
        raise ValueError("Expected exactly 5,000,000 trainable parameters")
    if tokenizer.get_vocab_size() > 8000 or tokenizer.token_to_id("[PAD]") != 0:
        raise ValueError("Tokenizer is incompatible with the model")
    print(f"Loaded NioMicro: {model.count_parameters():,} trainable parameters.")
    print(f"Split sizes: { {name: len(ds) for name, ds in datasets.items()} }", flush=True)
    metadata = {
        "schema_version": 1, "model_config": model.config,
        "trainable_parameters": model.count_parameters(), "seed": args.seed,
        "tokenizer_sha256": sha256(tokenizer_path),
        "dataset_sha256": {name: sha256(data_dir / f"{name}.jsonl") for name in datasets},
        "decision_labels": ["reject", "approve"], "sentiment_labels": ["negative", "positive"],
        "max_input_length": 256, "confidence_calibrated": False,
        "training": {"epochs": args.epochs, "batch_size": args.batch_size, "learning_rate": 6e-4},
    }
    history = []
    
    # Objectives
    ce_loss = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    epochs = args.epochs
    best_val_loss = float("inf")
    
    print("\n--- Starting Training ---")
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_examples = 0
        
        for step, batch in enumerate(train_loader, start=1):
            input_ids, attention_mask = trim_batch(batch, device)
            dec_target = batch["decision"].to(device)
            sent_target = batch["sentiment"].to(device)
            score_target = batch["score"].to(device)
            
            optimizer.zero_grad()
            dec_logits, sent_logits, score_pred = model(input_ids, attention_mask)
            
            l_dec = ce_loss(dec_logits, dec_target)
            l_sent = ce_loss(sent_logits, sent_target)
            l_score = mse_loss(score_pred, score_target)
            
            total_loss = l_dec + l_sent + (2.0 * l_score)
            if not torch.isfinite(total_loss):
                raise ValueError("Non-finite training loss")
            total_loss.backward()
            
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += total_loss.item() * len(input_ids)
            train_examples += len(input_ids)

            if step % 10 == 0 or step == len(train_loader):
                print(
                    f"Epoch [{epoch}/{epochs}] | Batch [{step}/{len(train_loader)}] "
                    f"| Train Loss: {train_loss / train_examples:.4f}",
                    flush=True,
                )
            
        scheduler.step()
        train_loss /= train_examples
        
        # Validation
        model.eval()
        val_loss = 0.0
        dec_correct = 0
        total_eval = 0
        score_diff = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids, attention_mask = trim_batch(batch, device)
                dec_target = batch["decision"].to(device)
                sent_target = batch["sentiment"].to(device)
                score_target = batch["score"].to(device)
                
                dec_logits, sent_logits, score_pred = model(input_ids, attention_mask)
                
                l_dec = ce_loss(dec_logits, dec_target)
                l_sent = ce_loss(sent_logits, sent_target)
                l_score = mse_loss(score_pred, score_target)
                total_loss = l_dec + l_sent + (2.0 * l_score)
                val_loss += total_loss.item() * len(input_ids)
                
                preds = dec_logits.argmax(dim=-1)
                dec_correct += (preds == dec_target).sum().item()
                score_diff += torch.abs(score_pred - score_target).sum().item()
                total_eval += dec_target.size(0)
                
        val_loss /= total_eval
        dec_acc = (dec_correct / total_eval) * 100.0
        mae_score = score_diff / total_eval
        history.append({"epoch": epoch, "train_loss": train_loss, "validation_loss": val_loss,
                        "validation_decision_accuracy": dec_acc / 100, "validation_score_mae": mae_score})
        
        print(f"Epoch [{epoch}/{epochs}] | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Decision Acc: {dec_acc:.2f}% | Score MAE: {mae_score:.3f}", flush=True)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            ckpt_path = models_dir / "nio_micro.pt"
            torch.save({**metadata, "epoch": epoch, "model_state_dict": model.state_dict()}, ckpt_path)
            (models_dir / "metadata.json").write_text(json.dumps({**metadata, "epoch": epoch}, indent=2) + "\n")
            print(f"  -> Saved new best checkpoint to {ckpt_path}", flush=True)

    checkpoint = torch.load(models_dir / "nio_micro.pt", map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    confusion = torch.zeros((2, 2), dtype=torch.long)
    score_error = 0.0
    with torch.no_grad():
        for batch in DataLoader(datasets["test"], batch_size=128):
            input_ids, attention_mask = trim_batch(batch, device)
            decision, _, score = model(input_ids, attention_mask)
            pairs = batch["decision"] * 2 + decision.argmax(-1).cpu()
            confusion += torch.bincount(pairs, minlength=4).reshape(2, 2)
            score_error += (score.cpu() - batch["score"]).abs().sum().item()
    count = len(datasets["test"])
    test = {"examples": count, "decision_accuracy": confusion.diag().sum().item() / count,
            "confusion_matrix": confusion.tolist(), "false_approvals": confusion[0, 1].item(),
            "false_rejections": confusion[1, 0].item(), "score_mae": score_error / count}
    elapsed = time.time() - start_time
    report = {**metadata, "best_epoch": checkpoint["epoch"], "history": history,
              "test": test, "elapsed_seconds": elapsed,
              "limitations": "Small synthetic developer dataset; sentiment is coupled to decision; confidence is not calibrated."}
    (models_dir / "training_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Held-out test: {json.dumps(test)}", flush=True)
    print(f"\nTraining completed in {elapsed:.1f}s!", flush=True)

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary-baseline", action="store_true", help="Train the earlier binary comparison model")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    profile = "5m" if args.binary_baseline else "5m-context"
    args.data_dir = args.data_dir or base / "data" / profile
    args.models_dir = args.models_dir or base / "models" / profile
    args.epochs = args.epochs if args.epochs is not None else (3 if args.binary_baseline else 12)
    args.seed = args.seed if args.seed is not None else (42 if args.binary_baseline else 73)
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    if args.binary_baseline:
        train(args)
    else:
        try:
            from .train_contextual import train as train_contextual
        except ImportError:
            from train_contextual import train as train_contextual
        train_contextual(args)
