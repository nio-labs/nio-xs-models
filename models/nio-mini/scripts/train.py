"""
NioMini (~8.5M) Training & ONNX Export Pipeline
Can run locally or via: colab exec -f scripts/train.py
"""

import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from model import NioMiniDefectForecaster, NioMiniConfig

class SyntheticDiffDataset(Dataset):
    def __init__(self, num_samples=25000, seq_len=128):
        self.num_samples = num_samples
        self.seq_len = seq_len
        self.tokens = torch.randint(0, 8192, (num_samples, seq_len))
        self.ast_feats = torch.randn(num_samples, seq_len, 32)
        self.categories = torch.randint(0, 5, (num_samples,))
        self.will_break = (self.categories > 0).float().unsqueeze(1)
        self.risk_scores = torch.where(
            self.categories == 0,
            torch.rand(num_samples) * 0.15,
            0.6 + torch.rand(num_samples) * 0.4
        ).unsqueeze(1)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        return {
            "input_ids": self.tokens[idx],
            "ast_features": self.ast_feats[idx],
            "will_break": self.will_break[idx],
            "category": self.categories[idx],
            "risk_score": self.risk_scores[idx],
        }

def train_and_export(epochs=2, batch_size=64, lr=3e-4, onnx_out="/content/nio-mini.onnx"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[NioMini] Training on device: {device}")

    config = NioMiniConfig()
    model = NioMiniDefectForecaster(config).to(device)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[NioMini] Total trainable parameters: {params:,} (~{params/1e6:.2f}M)")

    train_ds = SyntheticDiffDataset(num_samples=5000)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    criterion_bce = nn.BCELoss()
    criterion_ce = nn.CrossEntropyLoss()
    criterion_mse = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            ast_features = batch["ast_features"].to(device)
            will_break = batch["will_break"].to(device)
            category = batch["category"].to(device)
            risk_score = batch["risk_score"].to(device)

            optimizer.zero_grad()
            pred_break, pred_cat, pred_risk = model(input_ids, ast_features)
            loss = (
                criterion_bce(pred_break, will_break) * 1.0 +
                criterion_ce(pred_cat, category) * 1.5 +
                criterion_mse(pred_risk, risk_score) * 1.0
            )
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            if (step + 1) % 25 == 0 or (step + 1) == len(train_loader):
                print(f"  [Epoch {epoch+1}/{epochs}] Step [{step+1}/{len(train_loader)}] Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(train_loader)
        print(f"[NioMini] Epoch [{epoch+1}/{epochs}] Completed - Avg Loss: {avg_loss:.4f}")

    # Export to ONNX
    print(f"[NioMini] Exporting model to ONNX: {onnx_out}")
    model.eval().to("cpu")
    dummy_input_ids = torch.randint(0, 8192, (1, 128))
    dummy_ast = torch.randn(1, 128, 32)

    os.makedirs(os.path.dirname(onnx_out) or ".", exist_ok=True)
    torch.onnx.export(
        model,
        (dummy_input_ids, dummy_ast),
        onnx_out,
        input_names=["input_ids", "ast_features"],
        output_names=["will_break", "defect_category", "risk_score"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "seq_len"},
            "ast_features": {0: "batch_size", 1: "seq_len"},
        },
        opset_version=17,
    )
    import onnx
    m = onnx.load(onnx_out, load_external_data=True)
    onnx.save(m, onnx_out, save_as_external_data=False)
    data_file = f"{onnx_out}.data"
    if os.path.exists(data_file):
        os.remove(data_file)

    size_mb = os.path.getsize(onnx_out) / (1024 * 1024)
    print(f"[NioMini] Export complete: {onnx_out} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--onnx-out", type=str, default="/content/nio-mini.onnx")
    args, _ = parser.parse_known_args()

    train_and_export(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        onnx_out=args.onnx_out
    )
