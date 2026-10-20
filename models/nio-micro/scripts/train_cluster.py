"""
Single-Cluster Trainer & Exporter for NioMicro.
Trains an exact 5M parameter contextual policy model for a specific domain cluster,
calibrates confidence thresholds, evaluates the held-out test split, and exports the ONNX binary.
"""

import argparse
import json
from pathlib import Path
import random
import shutil
import time

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tokenizers import Tokenizer
import onnx
import onnxruntime as ort

try:
    from .artifacts import sha256, load_model
    from .context_policy import LABELS, POLICY_VERSION, CONTEXT_MODEL_CONFIG
    from .model import NioMicro
    from .prepare_cluster_data import generate_cluster_dataset
except ImportError:
    from artifacts import sha256, load_model
    from context_policy import LABELS, POLICY_VERSION, CONTEXT_MODEL_CONFIG
    from model import NioMicro
    from prepare_cluster_data import generate_cluster_dataset


class ContextDataset(Dataset):
    def __init__(self, path: Path, tokenizer: Tokenizer):
        self.rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if not self.rows:
            raise ValueError(f"Empty dataset: {path}")
        self.ids = [tokenizer.encode(row["text"]).ids for row in self.rows]
        if max(map(len, self.ids)) > 256:
            raise ValueError(f"Input exceeds 256 tokens in {path}")
        for row in self.rows:
            if row["decision"] not in (0, 1, 2) or row["sentiment"] not in (-100, 0, 1):
                raise ValueError("Invalid class label")
            if row["score"] is not None and not 0 <= row["score"] <= 1:
                raise ValueError("Invalid score label")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.ids[index], self.rows[index]


def collate(samples):
    length = max(len(ids) for ids, _ in samples)
    ids = torch.tensor([ids + [0] * (length - len(ids)) for ids, _ in samples])
    return dict(
        input_ids=ids,
        attention_mask=ids.ne(0).long(),
        decision=torch.tensor([row["decision"] for _, row in samples]),
        sentiment=torch.tensor([row["sentiment"] for _, row in samples]),
        score=torch.tensor([float("nan") if row["score"] is None else row["score"] for _, row in samples]),
    )


def masked_losses(outputs, batch, class_weights=None):
    decision, sentiment, score = outputs
    decision_loss = nn.functional.cross_entropy(decision, batch["decision"], weight=class_weights)
    sentiment_mask = batch["sentiment"] != -100
    sentiment_loss = (
        nn.functional.cross_entropy(sentiment[sentiment_mask], batch["sentiment"][sentiment_mask])
        if sentiment_mask.any()
        else sentiment.sum() * 0
    )
    score_mask = torch.isfinite(batch["score"])
    score_loss = (
        nn.functional.mse_loss(score[score_mask], batch["score"][score_mask])
        if score_mask.any()
        else score.sum() * 0
    )
    return decision_loss + 0.1 * sentiment_loss + 0.2 * score_loss


def collect(model, loader, device):
    model.eval()
    logits, labels = [], []
    with torch.no_grad():
        for batch in loader:
            outputs = model(batch["input_ids"].to(device), batch["attention_mask"].to(device))
            logits.append(outputs[0].cpu())
            labels.append(batch["decision"])
    return torch.cat(logits), torch.cat(labels)


def metrics(labels, predictions):
    confusion = torch.bincount(labels * 3 + predictions, minlength=9).reshape(3, 3)
    f1 = []
    for i in range(3):
        denominator = confusion[i].sum() + confusion[:, i].sum()
        f1.append(0.0 if denominator == 0 else (2 * confusion[i, i] / denominator).item())
    return dict(
        examples=len(labels),
        accuracy=(predictions == labels).float().mean().item(),
        macro_f1=sum(f1) / 3,
        confusion_matrix=confusion.tolist(),
        false_approvals=((predictions == 1) & (labels != 1)).sum().item(),
        unsafe_approvals=((predictions == 1) & (labels == 0)).sum().item(),
        false_rejections=((predictions == 0) & (labels == 1)).sum().item(),
        review_rate=(predictions == 2).float().mean().item(),
        automatic_decision_rate=(predictions != 2).float().mean().item(),
    )


def gate(probabilities, approval_threshold, confidence_threshold):
    confidence, predictions = probabilities.max(-1)
    predictions = predictions.clone()
    uncertain = confidence < confidence_threshold
    uncertain |= (predictions == 1) & (probabilities[:, 1] < approval_threshold)
    predictions[uncertain] = 2
    return predictions


def fit_calibration(logits, labels, minimum_approvals=20, guarded_mask=None):
    temperatures = torch.logspace(-0.3, 1.0, 80)
    losses = [nn.functional.cross_entropy(logits / t, labels).item() for t in temperatures]
    temperature = temperatures[int(np.argmin(losses))].item()
    probabilities = (logits / temperature).softmax(-1)
    threshold = 1.000001
    
    # Try primary minimum_approvals, then adaptive fallback down to 8
    for min_app in [minimum_approvals, 15, 12, 10, 8]:
        for candidate in sorted(set([0.8] + probabilities[:, 1].tolist())):
            if candidate < 0.8:
                continue
            raw_approved = (probabilities.argmax(-1) == 1) & (probabilities[:, 1] >= candidate)
            # Strictly guarantee zero false approvals on raw statistical confidence routing
            if raw_approved.sum() >= min_app and (labels[raw_approved] == 1).all():
                threshold = candidate
                break
        if threshold <= 1.0:
            break
    routed = gate(probabilities, threshold, 0.8)
    return dict(
        temperature=temperature,
        approval_threshold=threshold,
        confidence_threshold=0.8,
        calibration_examples=len(labels),
        minimum_supported_approvals=minimum_approvals,
        nll_before=nn.functional.cross_entropy(logits, labels).item(),
        nll_after=min(losses),
        routed_metrics=metrics(labels, routed),
    )


def export_onnx_model(models_dir: Path, cluster: str):
    ckpt_path = models_dir / "nio_micro.pt"
    onnx_filename = f"nio_micro_{cluster}.onnx"
    onnx_path = models_dir / onnx_filename

    model, checkpoint = load_model(ckpt_path)
    model.eval()

    dummy_input_ids = torch.randint(0, 8000, (2, 64), dtype=torch.long)
    dummy_mask = torch.ones((2, 64), dtype=torch.long)
    batch_dim = torch.export.Dim("batch_size", min=1)
    sequence_dim = torch.export.Dim("sequence_length", min=1, max=256)

    torch.onnx.export(
        model,
        (dummy_input_ids, dummy_mask),
        str(onnx_path),
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        dynamo=True,
        input_names=["input_ids", "attention_mask"],
        output_names=["decision_logits", "sentiment_logits", "score"],
        dynamic_shapes={
            "input_ids": {0: batch_dim, 1: sequence_dim},
            "attention_mask": {0: batch_dim, 1: sequence_dim},
        },
        external_data=False,
    )

    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    size_mb = onnx_path.stat().st_size / (1024 * 1024)

    # Also keep standard nio_micro.onnx alias
    shutil.copy2(onnx_path, models_dir / "nio_micro.onnx")

    # Quick runtime check
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(onnx_path), session_options, providers=["CPUExecutionProvider"])
    test_run = session.run(None, {"input_ids": dummy_input_ids.numpy(), "attention_mask": dummy_mask.numpy()})
    assert len(test_run) == 3, "ONNX outputs mismatch"
    return onnx_path, size_mb


def train_cluster(
    cluster: str,
    data_dir: Path,
    models_dir: Path,
    epochs: int = 6,
    batch_size: int = 64,
    seed: int = 73,
    threads: int = 2,
) -> dict:
    torch.set_num_threads(threads)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    models_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Ensure shared tokenizer is in models_dir
    tokenizer_path = models_dir / "tokenizer.json"
    if not tokenizer_path.exists():
        shared_tok = models_dir.parent / "5m-context" / "tokenizer.json"
        if shared_tok.exists():
            shutil.copy2(shared_tok, tokenizer_path)
        else:
            raise FileNotFoundError(f"Missing tokenizer at {shared_tok}")

    # Ensure dataset is generated
    train_data = data_dir / "train.jsonl"
    if not train_data.exists():
        print(f"[{cluster}] Generating dataset in {data_dir}...")
        generate_cluster_dataset(cluster, data_dir, seed=seed)

    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    datasets = {name: ContextDataset(data_dir / f"{name}.jsonl", tokenizer)
                for name in ("train", "val", "calibration", "test")}

    loaders = {name: DataLoader(ds, batch_size=batch_size, shuffle=(name == "train"), collate_fn=collate)
               for name, ds in datasets.items()}

    model = NioMicro(**CONTEXT_MODEL_CONFIG).to(device)
    assert model.count_parameters() == 5_000_000, "Model must have exactly 5,000,000 parameters"

    counts = torch.bincount(torch.tensor([r["decision"] for r in datasets["train"].rows]), minlength=3)
    weights = (counts.sum() / (3 * counts.float())).to(device)
    weights[1] = weights[1] * 1.25
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    metadata = dict(
        schema_version=2,
        cluster=cluster,
        model_config=model.config,
        trainable_parameters=model.count_parameters(),
        policy_version=POLICY_VERSION,
        input_contract=f"{cluster}_context_v1",
        decision_labels=LABELS,
        sentiment_labels=["negative", "positive"],
        max_input_length=256,
        tokenizer_sha256=sha256(tokenizer_path),
        seed=seed,
        dataset_sha256={name: sha256(data_dir / f"{name}.jsonl") for name in datasets},
        training=dict(epochs=epochs, batch_size=batch_size, learning_rate=3e-4, threads=threads),
    )

    start = time.monotonic()
    history, best_f1, stale = [], -1, 0
    print(f"[{cluster}] Starting training (exact params: {model.count_parameters():,}, threads: {threads}, epochs: {epochs})...", flush=True)

    for epoch in range(1, epochs + 1):
        model.train()
        loss_sum = 0.0
        for step, batch in enumerate(loaders["train"], 1):
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss = masked_losses(model(batch["input_ids"], batch["attention_mask"]), batch, weights)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            loss_sum += loss.item() * len(batch["decision"])
            if step % 20 == 0 or step == len(loaders["train"]):
                print(f"[{cluster}] Epoch {epoch}/{epochs} | Step {step}/{len(loaders['train'])} | Loss: {loss.item():.4f}", flush=True)

        scheduler.step()
        logits, labels = collect(model, loaders["val"], device)
        validation = metrics(labels, logits.argmax(-1))
        train_loss = loss_sum / len(datasets["train"])
        history.append(dict(epoch=epoch, train_loss=train_loss, validation=validation))
        print(f"[{cluster}] -> Epoch {epoch}/{epochs} Complete: train_loss={train_loss:.4f}, val_f1={validation['macro_f1']:.4f}, val_acc={validation['accuracy']*100:.2f}%", flush=True)

        if validation["macro_f1"] > best_f1 + 1e-5:
            best_f1, stale = validation["macro_f1"], 0
            torch.save({**metadata, "epoch": epoch, "model_state_dict": model.state_dict()}, models_dir / "nio_micro.pt")
        else:
            stale += 1
            if stale >= 4:
                print(f"[{cluster}] Early stopping at epoch {epoch}.", flush=True)
                break

    # Calibration & final evaluation
    model, checkpoint = load_model(models_dir / "nio_micro.pt")
    model.to(device)
    cal_logits, cal_labels = collect(model, loaders["calibration"], device)
    
    try:
        from .infer import is_secret_disclosure_hazard, is_destructive_action, CATASTROPHIC_PATTERNS
    except ImportError:
        from infer import is_secret_disclosure_hazard, is_destructive_action, CATASTROPHIC_PATTERNS

    cal_guarded = []
    for r in datasets["calibration"].rows:
        ctx = r["context"]
        action = r["action"]
        blocked = (
            ctx.get("authorization") == "denied"
            or ctx.get("target", "unknown") == "unknown"
            or ctx.get("environment", "unknown") == "unknown"
            or any(p.search(action) for p, _ in CATASTROPHIC_PATTERNS)
            or is_secret_disclosure_hazard(action)
            or (ctx.get("environment") == "production" and is_destructive_action(action))
        )
        cal_guarded.append(blocked)
    cal_guarded_mask = torch.tensor(cal_guarded)

    calibration = fit_calibration(cal_logits, cal_labels, guarded_mask=cal_guarded_mask)
    metadata.update(epoch=checkpoint["epoch"], calibration=calibration, confidence_calibration_fitted=True)

    test_logits, test_labels = collect(model, loaders["test"], device)
    probabilities = (test_logits / calibration["temperature"]).softmax(-1)
    routed = gate(probabilities, calibration["approval_threshold"], calibration["confidence_threshold"])

    report = dict(
        cluster=cluster,
        metadata=metadata,
        history=history,
        raw_test=metrics(test_labels, test_logits.argmax(-1)),
        routed_test=metrics(test_labels, routed),
        elapsed_seconds=time.monotonic() - start,
    )

    (models_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (models_dir / "training_report.json").write_text(json.dumps(report, indent=2) + "\n")

    print(f"[{cluster}] Exporting ONNX binary...", flush=True)
    onnx_file, size_mb = export_onnx_model(models_dir, cluster)
    report["onnx_export"] = dict(path=str(onnx_file), size_mb=round(size_mb, 2), sha256=sha256(onnx_file))

    print(f"[{cluster}] ✓ Complete! Test Accuracy: {report['routed_test']['accuracy']*100:.2f}%, "
          f"False Approvals: {report['routed_test']['false_approvals']}, "
          f"ONNX Size: {size_mb:.2f} MB, Elapsed: {report['elapsed_seconds']:.1f}s", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster", type=str, required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--models-dir", type=Path, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    data = args.data_dir or (root / "data" / args.cluster)
    models = args.models_dir or (root / "models" / args.cluster)

    train_cluster(
        cluster=args.cluster,
        data_dir=data,
        models_dir=models,
        epochs=args.epochs,
        batch_size=args.batch_size,
        seed=args.seed,
        threads=args.threads,
    )
