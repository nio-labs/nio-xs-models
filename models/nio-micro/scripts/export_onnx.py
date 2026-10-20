"""
NioMicro ONNX Exporter & Benchmark
Exports a versioned candidate checkpoint and benchmarks ONNX Runtime inference.
"""

import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
import onnx
import onnxruntime as ort

try:
    from .artifacts import load_model, sha256
except ImportError:
    from artifacts import load_model, sha256

def export_and_benchmark(models_dir):
    ckpt_path = models_dir / "nio_micro.pt"
    onnx_path = models_dir / "nio_micro.onnx"
    
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Missing {ckpt_path}. Run train.py first!")

    model, checkpoint = load_model(ckpt_path)
    if sha256(models_dir / "tokenizer.json") != checkpoint["tokenizer_sha256"]:
        raise ValueError("Tokenizer does not match the trained checkpoint")
    model.eval()

    # Create dummy inputs
    dummy_input_ids = torch.randint(0, 8000, (2, 64), dtype=torch.long)
    dummy_mask = torch.ones((2, 64), dtype=torch.long)
    batch_dim = torch.export.Dim("batch_size", min=1)
    sequence_dim = torch.export.Dim("sequence_length", min=1, max=256)

    print(f"Exporting NioMicro to ONNX: {onnx_path}...")
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

    # Verify model
    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    file_size_mb = onnx_path.stat().st_size / (1024 * 1024)
    print(f"ONNX model verified successfully! File size: {file_size_mb:.2f} MB")

    # Benchmark ONNX Runtime
    print("\n--- Benchmarking ONNX Runtime (CPU) ---")
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.intra_op_num_threads = 4
    
    session = ort.InferenceSession(str(onnx_path), session_options, providers=["CPUExecutionProvider"])

    parity = []
    for batch, length in ((1, 1), (1, 16), (2, 64), (2, 128), (1, 256)):
        ids = torch.randint(1, model.config["vocab_size"], (batch, length))
        if length > 4:
            ids[:, -4:] = 0
        mask = ids.ne(0).long()
        with torch.no_grad():
            expected = model(ids, mask)
        actual = session.run(None, {"input_ids": ids.numpy(), "attention_mask": mask.numpy()})
        for reference, output in zip(expected, actual):
            np.testing.assert_allclose(reference.numpy(), output, rtol=1e-4, atol=1e-5)
        parity.append({"batch_size": batch, "sequence_length": length})
    print("PyTorch/ONNX parity passed at sequence lengths 1, 16, 64, 128, 256")
    
    # Warmup
    input_feed = {
        "input_ids": np.random.randint(0, 8000, size=(1, 64), dtype=np.int64),
        "attention_mask": np.ones((1, 64), dtype=np.int64),
    }
    for _ in range(20):
        _ = session.run(None, input_feed)

    # Benchmark loop
    runs = 200
    start = time.perf_counter()
    for _ in range(runs):
        _ = session.run(None, input_feed)
    duration = time.perf_counter() - start
    
    avg_latency_ms = (duration / runs) * 1000
    throughput = runs / duration
    
    print(f"Runs: {runs}")
    print(f"Average Latency: {avg_latency_ms:.2f} ms")
    print(f"Throughput: {throughput:.1f} inferences/sec")
    print("Benchmark complete!")
    report = {"trainable_parameters": model.count_parameters(), "onnx_bytes": onnx_path.stat().st_size,
              "parity_cases": parity, "warm_runs": runs, "average_latency_ms": avg_latency_ms,
              "batch_size": 1, "sequence_length": 64, "cpu_threads": 4,
              "excludes": ["tokenization", "session_startup"]}
    (models_dir / "export_report.json").write_text(json.dumps(report, indent=2) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent / "models/5m-context")
    export_and_benchmark(parser.parse_args().models_dir)
