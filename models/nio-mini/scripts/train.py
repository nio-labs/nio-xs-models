"""
NioMini (~7.1M) Defect Forecaster - Training & ONNX Export Pipeline
Supports local training or Google Colab T4/V100/A100 GPU acceleration.
"""

import os
import sys
import argparse
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split

from model import NioMiniDefectForecaster, NioMiniConfig, LABEL_NAMES
from dataset_generator import generate_dataset


class DefectDataset(Dataset):
    """
    PyTorch Dataset backed by realistic synthesized code snippets and AST features.
    """
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "ast_features": torch.tensor(item["ast_features"], dtype=torch.float32),
            "will_break": torch.tensor([item["will_break"]], dtype=torch.float32),
            "category": torch.tensor(item["category"], dtype=torch.long),
            "risk_score": torch.tensor([item["risk_score"]], dtype=torch.float32),
        }


def train_and_export(
    num_samples: int = 10000,
    epochs: int = 5,
    batch_size: int = 64,
    lr: float = 3e-4,
    onnx_out: str = "nio-mini.onnx",
    device_name: str = None,
):
    is_colab = os.path.exists("/content")
    if is_colab and onnx_out == "nio-mini.onnx":
        onnx_out = "/content/nio-mini.onnx"

    if device_name:
        device = torch.device(device_name)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"==================================================")
    print(f" NioMini Defect Forecaster Training Pipeline")
    print(f" Environment: {'Google Colab' if is_colab else 'Local / Server'}")
    print(f" Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"==================================================")

    # 1. Initialize Model
    config = NioMiniConfig()
    model = NioMiniDefectForecaster(config).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[NioMini] Total trainable parameters: {total_params:,} (Budget: 7,100,000)")
    assert total_params == 7_100_000, f"Expected 7,100,000 parameters, got {total_params}"

    # 2. Dataset Generation
    print(f"\n[1/4] Generating {num_samples:,} AST-annotated code samples...")
    t0 = time.time()
    raw_data = generate_dataset(num_samples=num_samples)
    full_ds = DefectDataset(raw_data)

    val_len = max(int(len(full_ds) * 0.1), 1)
    train_len = len(full_ds) - val_len
    train_ds, val_ds = random_split(full_ds, [train_len, val_len])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, pin_memory=(device.type == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    print(f"[NioMini] Dataset ready in {time.time() - t0:.2f}s: {train_len} train, {val_len} validation samples.")

    # 3. Optimization Setup
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion_bce = nn.BCELoss()
    criterion_ce = nn.CrossEntropyLoss()
    criterion_mse = nn.MSELoss()

    # 4. Training Loop
    print(f"\n[2/4] Starting training for {epochs} epochs (Batch Size: {batch_size})...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_steps = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device, non_blocking=True)
            ast_features = batch["ast_features"].to(device, non_blocking=True)
            will_break = batch["will_break"].to(device, non_blocking=True)
            category = batch["category"].to(device, non_blocking=True)
            risk_score = batch["risk_score"].to(device, non_blocking=True)

            optimizer.zero_grad()
            pred_break, pred_cat, pred_risk = model(input_ids, ast_features)

            loss_break = criterion_bce(pred_break, will_break)
            loss_cat = criterion_ce(pred_cat, category)
            loss_risk = criterion_mse(pred_risk, risk_score)

            total_loss = 1.0 * loss_break + 1.5 * loss_cat + 1.0 * loss_risk
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += total_loss.item()
            train_steps += 1

            if (step + 1) % 25 == 0 or (step + 1) == len(train_loader):
                print(f"  Epoch [{epoch+1}/{epochs}] Step [{step+1}/{len(train_loader)}] Loss: {total_loss.item():.4f}")

        scheduler.step()

        # Validation
        model.eval()
        val_loss = 0.0
        correct_cat = 0
        correct_break = 0
        total_val = 0

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                ast_features = batch["ast_features"].to(device)
                will_break = batch["will_break"].to(device)
                category = batch["category"].to(device)
                risk_score = batch["risk_score"].to(device)

                pred_break, pred_cat, pred_risk = model(input_ids, ast_features)
                l = (
                    criterion_bce(pred_break, will_break) * 1.0 +
                    criterion_ce(pred_cat, category) * 1.5 +
                    criterion_mse(pred_risk, risk_score) * 1.0
                )
                val_loss += l.item()

                pred_cat_class = torch.argmax(pred_cat, dim=-1)
                correct_cat += (pred_cat_class == category).sum().item()
                pred_break_bool = (pred_break >= 0.5).float()
                correct_break += (pred_break_bool == will_break).sum().item()
                total_val += category.size(0)

        val_acc_cat = (correct_cat / total_val) * 100.0 if total_val > 0 else 0.0
        val_acc_break = (correct_break / total_val) * 100.0 if total_val > 0 else 0.0
        avg_train = train_loss / max(train_steps, 1)
        avg_val = val_loss / max(len(val_loader), 1)

        print(
            f"[NioMini] Epoch [{epoch+1}/{epochs}] "
            f"Train Loss: {avg_train:.4f} | Val Loss: {avg_val:.4f} | "
            f"Cat Acc: {val_acc_cat:.1f}% | Break Acc: {val_acc_break:.1f}%"
        )

    # 5. Export to ONNX
    print(f"\n[3/4] Exporting NioMini to ONNX: {onnx_out}")
    model.eval().to("cpu")
    dummy_input_ids = torch.randint(0, config.vocab_size, (1, 128), dtype=torch.long)
    dummy_ast = torch.randn(1, 128, config.ast_feature_dim, dtype=torch.float32)

    out_dir = os.path.dirname(onnx_out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    torch.onnx.export(
        model,
        (dummy_input_ids, dummy_ast),
        onnx_out,
        input_names=["input_ids", "ast_features"],
        output_names=["will_break", "defect_category", "risk_score"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "seq_len"},
            "ast_features": {0: "batch_size", 1: "seq_len"},
            "will_break": {0: "batch_size"},
            "defect_category": {0: "batch_size"},
            "risk_score": {0: "batch_size"},
        },
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )

    # Clean external data chunks if any
    try:
        import onnx
        onnx_model = onnx.load(onnx_out, load_external_data=True)
        onnx.save(onnx_model, onnx_out, save_as_external_data=False)
        data_file = f"{onnx_out}.data"
        if os.path.exists(data_file):
            os.remove(data_file)
        onnx.checker.check_model(onnx_model)
    except Exception as e:
        print(f"[Warning] ONNX check / repack note: {e}")

    # 6. Verify with ONNX Runtime (Dynamic Batches & Dynamic Sequence Lengths)
    print(f"\n[4/4] Verifying ONNX Runtime Dynamic Batches & Sequence Lengths...")
    import onnxruntime as ort
    import numpy as np

    sess = ort.InferenceSession(onnx_out, providers=["CPUExecutionProvider"])
    
    # Test matrix of dynamic batches and dynamic sequence lengths
    for b in [1, 2, 3]:
        for seq_len in [64, 128, 256, 512]:
            test_ids = np.random.randint(0, 8192, size=(b, seq_len), dtype=np.int64)
            test_ast = np.random.randn(b, seq_len, 32).astype(np.float32)
            res = sess.run(None, {"input_ids": test_ids, "ast_features": test_ast})
            assert res[0].shape == (b, 1), f"Expected ({b}, 1), got {res[0].shape}"
            assert res[1].shape == (b, 5), f"Expected ({b}, 5), got {res[1].shape}"
            assert res[2].shape == (b, 1), f"Expected ({b}, 1), got {res[2].shape}"

    test_ids_1 = np.random.randint(0, 8192, size=(1, 128), dtype=np.int64)
    test_ast_1 = np.random.randn(1, 128, 32).astype(np.float32)
    res_1 = sess.run(None, {"input_ids": test_ids_1, "ast_features": test_ast_1})

    wb, cat, risk = res_1[0], res_1[1], res_1[2]
    cat_probs = np.exp(cat[0]) / np.sum(np.exp(cat[0]))
    pred_label = LABEL_NAMES[int(np.argmax(cat_probs))]

    print(f"  ONNX Verification Successful! Dynamic Batching Verified (Batches 1 & 2 passed).")
    print(f"  Sample Prediction: Break={wb[0,0]:.3f}, Predicted Label={pred_label}, Risk={risk[0,0]:.3f}")

    size_mb = os.path.getsize(onnx_out) / (1024 * 1024)
    print(f"\n[NioMini] Model saved successfully: {onnx_out} ({size_mb:.2f} MB)")
    return onnx_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train NioMini Defect Forecaster")
    parser.add_argument("--samples", type=int, default=10000, help="Number of synthetic/AST samples")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--onnx-out", type=str, default="nio-mini.onnx", help="Output path for ONNX file")
    parser.add_argument("--device", type=str, default=None, help="Device to use (e.g. cuda, cpu)")
    parser.add_argument("--colab", action="store_true", help="Force Colab environment mode")
    args, _ = parser.parse_known_args()

    train_and_export(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        onnx_out=args.onnx_out,
        device_name=args.device,
    )
