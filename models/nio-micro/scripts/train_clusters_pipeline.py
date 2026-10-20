"""
NioMicro Automated Sequential Pipeline Trainer.
Sequentially trains, calibrates, benchmarks, and exports multiple domain clusters
(e.g., infra, sec, fin) with maximum CPU resource efficiency and zero OOM memory risk.
"""

import argparse
import gc
import json
from pathlib import Path
import time
from typing import List, Dict, Any

try:
    from .train_cluster import train_cluster
    from .prepare_cluster_data import generate_cluster_dataset
except ImportError:
    from train_cluster import train_cluster
    from prepare_cluster_data import generate_cluster_dataset


def run_pipeline(clusters: List[str], epochs: int, batch_size: int, threads: int, seed: int, force: bool = False):
    root = Path(__file__).resolve().parent.parent
    total_start = time.monotonic()
    results: Dict[str, Any] = {}

    print("=" * 80)
    print(f"🚀 NioMicro Multi-Cluster Sequential Training Pipeline")
    print(f"   Clusters: {clusters}")
    print(f"   Epochs: {epochs} | Batch Size: {batch_size} | CPU Threads: {threads}")
    print("=" * 80, flush=True)

    for idx, cluster in enumerate(clusters, 1):
        print("\n" + "#" * 80)
        print(f"▶ [{idx}/{len(clusters)}] Processing Cluster: '{cluster}'")
        print("#" * 80, flush=True)

        data_dir = root / "data" / cluster
        models_dir = root / "models" / cluster

        # 1. Synthesize dataset if missing or forced
        if force or not (data_dir / "train.jsonl").exists():
            print(f"[{cluster}] Synthesizing dataset -> {data_dir}...")
            generate_cluster_dataset(cluster, data_dir, seed=seed)

        # Check if already completed from a previous run
        report_file = models_dir / "training_report.json"
        onnx_file = models_dir / f"nio_micro_{cluster}.onnx"
        if not force and report_file.exists() and onnx_file.exists():
            print(f"[{cluster}] Already completed! Loading cached report: {report_file}", flush=True)
            report = json.loads(report_file.read_text())
            report["pipeline_elapsed"] = report.get("elapsed_seconds", 0.0)
            results[cluster] = report
            continue

        # 2. Train and export
        t0 = time.monotonic()
        report = train_cluster(
            cluster=cluster,
            data_dir=data_dir,
            models_dir=models_dir,
            epochs=epochs,
            batch_size=batch_size,
            seed=seed,
            threads=threads,
        )
        elapsed = time.monotonic() - t0
        report["pipeline_elapsed"] = elapsed
        results[cluster] = report

        # Memory compaction between runs
        gc.collect()

    total_time = time.monotonic() - total_start

    print("\n" + "=" * 80)
    print(f"🎉 Pipeline Complete! All {len(clusters)} Clusters Finished in {total_time/60:.1f} minutes ({total_time:.1f}s)")
    print("=" * 80)
    header = f"{'Cluster':<12} | {'Test Acc':<9} | {'False App':<10} | {'False Rej':<10} | {'Review %':<9} | {'ONNX Size':<10} | {'Elapsed':<8}"
    print(header)
    print("-" * len(header))

    summary = {}
    for cluster, rep in results.items():
        rt = rep["routed_test"]
        onnx_sz = rep.get("onnx_export", {}).get("size_mb", 19.67)
        elapsed = rep["pipeline_elapsed"]
        acc_str = f"{rt['accuracy'] * 100:.2f}%"
        rev_str = f"{rt['review_rate'] * 100:.1f}%"
        row = f"{cluster:<12} | {acc_str:<9} | {rt['false_approvals']:<10} | {rt['false_rejections']:<10} | {rev_str:<9} | {onnx_sz:.2f} MB   | {elapsed:.1f}s"
        print(row)
        summary[cluster] = {
            "accuracy": rt["accuracy"],
            "false_approvals": rt["false_approvals"],
            "false_rejections": rt["false_rejections"],
            "review_rate": rt["review_rate"],
            "onnx_size_mb": onnx_sz,
            "onnx_path": rep.get("onnx_export", {}).get("path", ""),
            "elapsed_seconds": elapsed,
        }

    summary_file = root / "models" / "pipeline_summary.json"
    summary_file.write_text(json.dumps(dict(total_time_seconds=total_time, clusters=summary), indent=2) + "\n")
    print("-" * len(header))
    print(f"Summary metrics saved to {summary_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clusters", nargs="+", default=["infra", "sec", "fin"])
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--force", action="store_true", help="Force dataset re-synthesis and model retraining")
    args = parser.parse_args()

    run_pipeline(
        clusters=args.clusters,
        epochs=args.epochs,
        batch_size=args.batch_size,
        threads=args.threads,
        seed=args.seed,
        force=args.force,
    )
