"""Train a separate exact-5M contextual candidate and calibrate on its own split."""

import argparse
import json
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tokenizers import Tokenizer

try:
    from .artifacts import sha256, load_model
    from .context_policy import LABELS, POLICY_VERSION, CONTEXT_MODEL_CONFIG
except ImportError:
    from artifacts import sha256, load_model
    from context_policy import LABELS, POLICY_VERSION, CONTEXT_MODEL_CONFIG


class ContextDataset(Dataset):
    def __init__(self, path, tokenizer):
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
    return dict(input_ids=ids, attention_mask=ids.ne(0).long(),
                decision=torch.tensor([row["decision"] for _, row in samples]),
                sentiment=torch.tensor([row["sentiment"] for _, row in samples]),
                score=torch.tensor([float("nan") if row["score"] is None else row["score"]
                                    for _, row in samples]))


def masked_losses(outputs, batch, class_weights=None):
    decision, sentiment, score = outputs
    decision_loss = nn.functional.cross_entropy(decision, batch["decision"], weight=class_weights)
    sentiment_mask = batch["sentiment"] != -100
    sentiment_loss = (nn.functional.cross_entropy(sentiment[sentiment_mask], batch["sentiment"][sentiment_mask])
                      if sentiment_mask.any() else sentiment.sum() * 0)
    score_mask = torch.isfinite(batch["score"])
    score_loss = (nn.functional.mse_loss(score[score_mask], batch["score"][score_mask])
                  if score_mask.any() else score.sum() * 0)
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
    return dict(examples=len(labels), accuracy=(predictions == labels).float().mean().item(),
                macro_f1=sum(f1) / 3, confusion_matrix=confusion.tolist(),
                false_approvals=((predictions == 1) & (labels != 1)).sum().item(),
                unsafe_approvals=((predictions == 1) & (labels == 0)).sum().item(),
                false_rejections=((predictions == 0) & (labels == 1)).sum().item(),
                review_rate=(predictions == 2).float().mean().item(),
                automatic_decision_rate=(predictions != 2).float().mean().item())


def gate(probabilities, approval_threshold, confidence_threshold):
    confidence, predictions = probabilities.max(-1)
    predictions = predictions.clone()
    uncertain = confidence < confidence_threshold
    uncertain |= (predictions == 1) & (probabilities[:, 1] < approval_threshold)
    predictions[uncertain] = 2
    return predictions


def fit_calibration(logits, labels, minimum_approvals=20):
    # Fit using calibration data only, never validation or test labels.
    temperatures = torch.logspace(-0.3, 1.0, 80)
    losses = [nn.functional.cross_entropy(logits / t, labels).item() for t in temperatures]
    temperature = temperatures[int(np.argmin(losses))].item()
    probabilities = (logits / temperature).softmax(-1)
    threshold = 1.000001  # No automatic approvals if calibration provides no supported cutoff.
    for candidate in sorted(set([0.8] + probabilities[:, 1].tolist())):
        if candidate < 0.8:
            continue
        approved = (probabilities.argmax(-1) == 1) & (probabilities[:, 1] >= candidate)
        if approved.sum() >= minimum_approvals and (labels[approved] == 1).all():
            threshold = candidate
            break
    routed = gate(probabilities, threshold, 0.8)
    return dict(temperature=temperature, approval_threshold=threshold, confidence_threshold=0.8,
                calibration_examples=len(labels), minimum_supported_approvals=minimum_approvals,
                nll_before=nn.functional.cross_entropy(logits, labels).item(),
                nll_after=min(losses), routed_metrics=metrics(labels, routed),
                note="A fitted temperature and zero calibration errors do not guarantee calibrated probabilities or safe decisions on new data.")


def audit(datasets):
    names = list(datasets)
    for name in names:
        rows = datasets[name].rows
        if len({r["text"] for r in rows}) != len(rows):
            raise ValueError(f"Duplicate texts in {name}")
        if {r["decision"] for r in rows} != {0, 1, 2}:
            raise ValueError(f"Missing decision class in {name}")
        for right in names[names.index(name) + 1:]:
            for field in ("text", "scenario_group"):
                if {r[field] for r in rows} & {r[field] for r in datasets[right].rows}:
                    raise ValueError(f"Cross-split {field} overlap: {name}/{right}")


def train(args):
    try:
        from .model import NioMicro
    except ImportError:
        from model import NioMicro
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer_path = args.models_dir / "tokenizer.json"
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    if tokenizer.token_to_id("[PAD]") != 0 or tokenizer.get_vocab_size() > 8000:
        raise ValueError("Incompatible tokenizer")
    datasets = {name: ContextDataset(args.data_dir / f"{name}.jsonl", tokenizer)
                for name in ("train", "val", "calibration", "test")}
    audit(datasets)
    loaders = {name: DataLoader(ds, batch_size=args.batch_size, shuffle=name == "train", collate_fn=collate)
               for name, ds in datasets.items()}
    model = NioMicro(**CONTEXT_MODEL_CONFIG).to(device)
    if model.count_parameters() != 5_000_000:
        raise ValueError("Expected exactly 5,000,000 parameters")
    counts = torch.bincount(torch.tensor([r["decision"] for r in datasets["train"].rows]), minlength=3)
    weights = (counts.sum() / (3 * counts.float())).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    metadata = dict(schema_version=2, model_config=model.config, trainable_parameters=model.count_parameters(),
                    policy_version=POLICY_VERSION, input_contract="developer_action_context_v1",
                    decision_labels=LABELS, sentiment_labels=["negative", "positive"],
                    max_input_length=256, tokenizer_sha256=sha256(tokenizer_path), seed=args.seed,
                    dataset_sha256={name: sha256(args.data_dir / f"{name}.jsonl") for name in datasets},
                    training=dict(epochs=args.epochs, batch_size=args.batch_size, learning_rate=3e-4),
                    limitations="Synthetic fixed-policy examples, not externally reviewed. No evidence of arbitrary-policy or cross-domain competence.")
    start = time.monotonic()
    history, best_f1, stale = [], -1, 0
    print(f"Exact parameters: {model.count_parameters():,}; device: {device}; splits: { {n: len(d) for n,d in datasets.items()} }", flush=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum = 0.0
        for step, batch in enumerate(loaders["train"], 1):
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss = masked_losses(model(batch["input_ids"], batch["attention_mask"]), batch, weights)
            if not torch.isfinite(loss):
                raise ValueError("Non-finite loss")
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            loss_sum += loss.item() * len(batch["decision"])
            if step % 20 == 0 or step == len(loaders["train"]):
                print(f"Epoch {epoch}/{args.epochs}, batch {step}/{len(loaders['train'])}, loss {loss.item():.4f}", flush=True)
        scheduler.step()
        logits, labels = collect(model, loaders["val"], device)
        validation = metrics(labels, logits.argmax(-1))
        history.append(dict(epoch=epoch, train_loss=loss_sum / len(datasets["train"]), validation=validation))
        print(f"Validation: {json.dumps(validation)}", flush=True)
        if validation["macro_f1"] > best_f1 + 1e-5:
            best_f1, stale = validation["macro_f1"], 0
            torch.save({**metadata, "epoch": epoch, "model_state_dict": model.state_dict()}, args.models_dir / "nio_micro.pt")
        else:
            stale += 1
            if stale >= 3:
                print("Early stopping after three epochs without validation macro-F1 improvement", flush=True)
                break
    model, checkpoint = load_model(args.models_dir / "nio_micro.pt")
    model.to(device)
    calibration_logits, calibration_labels = collect(model, loaders["calibration"], device)
    calibration = fit_calibration(calibration_logits, calibration_labels)
    metadata.update(epoch=checkpoint["epoch"], calibration=calibration, confidence_calibration_fitted=True)
    # Thresholds and temperature are frozen before the single final test evaluation.
    logits, labels = collect(model, loaders["test"], device)
    probabilities = (logits / calibration["temperature"]).softmax(-1)
    routed = gate(probabilities, calibration["approval_threshold"], calibration["confidence_threshold"])
    report = dict(metadata=metadata, history=history, raw_test=metrics(labels, logits.argmax(-1)),
                  routed_test=metrics(labels, routed), elapsed_seconds=time.monotonic() - start)
    (args.models_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (args.models_dir / "training_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Final raw test: {json.dumps(report['raw_test'])}", flush=True)
    print(f"Final routed test: {json.dumps(report['routed_test'])}", flush=True)
    print(f"Elapsed: {report['elapsed_seconds']:.1f}s", flush=True)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=root / "data/5m-context")
    parser.add_argument("--models-dir", type=Path, default=root / "models/5m-context")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=73)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    train(args)
