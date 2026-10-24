"""
ONNX Export and Latency Benchmarking for NioMask (~1.0M Secret & PII Redactor)
Exports PyTorch weights to production ONNX and benchmarks inference latency.
"""

import os
import json
import time
import hashlib
import argparse
import numpy as np
import torch
import onnx
import onnxruntime as ort
from rich.console import Console

from model import NioMaskConfig, NioMaskModel, VOCAB_SIZE, NUM_CLASSES, LABEL_NAMES

console = Console()


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def export_onnx():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="models/nio_mask_checkpoint.pt")
    parser.add_argument("--output-onnx", type=str, default="models/nio_mask.onnx")
    parser.add_argument("--benchmark-runs", type=int, default=500)
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        raise FileNotFoundError(f"Checkpoint not found at: {args.checkpoint}")

    console.print(f"[bold cyan]Exporting NioMask to ONNX[/bold cyan] from {args.checkpoint}")

    # Load checkpoint
    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    config = NioMaskConfig(**ckpt["config"])
    model = NioMaskModel(config)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    # Dummy inputs for tracing
    batch_size = 1
    seq_len = 128
    dummy_input_ids = torch.randint(0, 256, (batch_size, seq_len), dtype=torch.long)
    dummy_attention_mask = torch.ones((batch_size, seq_len), dtype=torch.float32)

    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "seq_len"},
        "attention_mask": {0: "batch_size", 1: "seq_len"},
        "token_logits": {0: "batch_size", 1: "seq_len"},
        "risk_score": {0: "batch_size"},
    }

    # Export
    torch.onnx.export(
        model,
        (dummy_input_ids, dummy_attention_mask),
        args.output_onnx,
        input_names=["input_ids", "attention_mask"],
        output_names=["token_logits", "risk_score"],
        dynamic_axes=dynamic_axes,
        opset_version=17,
        do_constant_folding=True,
    )

    # Validate and consolidate to single self-contained binary
    onnx_model = onnx.load(args.output_onnx, load_external_data=True)
    onnx.save(onnx_model, args.output_onnx, save_as_external_data=False)
    data_file = f"{args.output_onnx}.data"
    if os.path.exists(data_file):
        os.remove(data_file)

    onnx_model = onnx.load(args.output_onnx)
    onnx.checker.check_model(onnx_model)
    file_size_mb = os.path.getsize(args.output_onnx) / (1024 * 1024)
    sha256_hash = compute_sha256(args.output_onnx)

    console.print(f"[bold green]ONNX export verified successfully![/bold green]")
    console.print(f"File: [yellow]{args.output_onnx}[/yellow] ({file_size_mb:.2f} MB)")
    console.print(f"SHA-256: [cyan]{sha256_hash}[/cyan]")

    # Run Benchmark with ONNX Runtime
    console.print(f"\n[bold cyan]Benchmarking ONNX Runtime Inference on CPU...[/bold cyan]")
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 1
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(args.output_onnx, sess_options, providers=["CPUExecutionProvider"])

    # Warmup
    ort_inputs = {
        "input_ids": dummy_input_ids.numpy(),
        "attention_mask": dummy_attention_mask.numpy(),
    }
    for _ in range(50):
        session.run(None, ort_inputs)

    # Benchmark loop
    latencies = []
    for _ in range(args.benchmark_runs):
        t0 = time.perf_counter()
        session.run(None, ort_inputs)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    avg_latency = np.mean(latencies)

    console.print(f"Benchmark Results ({args.benchmark_runs} runs on batch=1, seq_len={seq_len}):")
    console.print(f"  • Avg Latency: [bold green]{avg_latency:.3f} ms ({avg_latency*1000:.1f} µs)[/bold green]")
    console.print(f"  • p50: [green]{p50:.3f} ms[/green]")
    console.print(f"  • p95: [yellow]{p95:.3f} ms[/yellow]")
    console.print(f"  • p99: [yellow]{p99:.3f} ms[/yellow]")

    # Write metadata.json
    metadata = {
        "model_name": "nio-mask",
        "version": "0.1.0",
        "architecture": "2-Layer Byte-Level Conv-Transformer & Entropy Stream Scanner",
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "file_size_mb": round(file_size_mb, 2),
        "sha256": sha256_hash,
        "input_schema": {
            "input_ids": "int64[batch_size, seq_len]",
            "attention_mask": "float32[batch_size, seq_len]"
        },
        "output_schema": {
            "token_logits": "float32[batch_size, seq_len, 7]",
            "risk_score": "float32[batch_size, 1]"
        },
        "labels": LABEL_NAMES,
        "benchmark": {
            "seq_len": seq_len,
            "avg_ms": round(float(avg_latency), 4),
            "p50_ms": round(float(p50), 4),
            "p95_ms": round(float(p95), 4),
            "p99_ms": round(float(p99), 4),
        },
        "training_metrics": ckpt.get("metrics", {})
    }

    meta_path = os.path.join(os.path.dirname(args.output_onnx), "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    console.print(f"Saved metadata: [cyan]{meta_path}[/cyan]")


if __name__ == "__main__":
    export_onnx()
