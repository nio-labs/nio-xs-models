"""
NioMicro Multi-Cluster Parallel Training Orchestrator.
Spawns and monitors concurrent training processes for multiple domain clusters (e.g. infra, sec, fin).
Enforces CPU thread caps (torch.set_num_threads) to prevent resource thrashing.
Exports and verifies ONNX binaries for all clusters simultaneously.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
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


def run_worker(cluster: str, root_dir: str, epochs: int, batch_size: int, threads: int, seed: int) -> Dict[str, Any]:
    root = Path(root_dir)
    data_dir = root / "data" / cluster
    models_dir = root / "models" / cluster

    # Ensure dataset is generated
    if not (data_dir / "train.jsonl").exists():
        generate_cluster_dataset(cluster, data_dir, seed=seed)

    # Train and export
    report = train_cluster(
        cluster=cluster,
        data_dir=data_dir,
        models_dir=models_dir,
        epochs=epochs,
        batch_size=batch_size,
        seed=seed,
        threads=threads,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clusters", nargs="+", default=["infra", "sec", "fin"])
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--threads-per-cluster", type=int, default=2)
    parser.add_argument("--seed", type=int, default=73)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    clusters: List[str] = args.clusters
    num_jobs = len(clusters)

    print("=" * 80)
    print(f"🚀 Launching Parallel Training for {num_jobs} Clusters: {clusters}")
    print(f"   Epochs: {args.epochs} | Batch size: {args.batch_size} | Threads per job: {args.threads_per_cluster}")
    print("=" * 80, flush=True)

    start_total = time.monotonic()

    # Pre-generate datasets cleanly before multiprocessing
    for cluster in clusters:
        data_dir = root / "data" / cluster
        if not (data_dir / "train.jsonl").exists():
            print(f"Synthesizing dataset for '{cluster}' -> {data_dir}...")
            generate_cluster_dataset(cluster, data_dir, seed=args.seed)

    # Launch parallel jobs
    results = {}
    with ProcessPoolExecutor(max_workers=num_jobs) as executor:
        futures = {
            executor.submit(
                run_worker,
                cluster,
                str(root),
                args.epochs,
                args.batch_size,
                args.threads_per_cluster,
                args.seed,
            ): cluster
            for cluster in clusters
        }

        for future in futures:
            cluster = futures[future]
            try:
                report = future.result()
                results[cluster] = report
            except Exception as e:
                print(f"❌ Error in cluster '{cluster}': {e}")
                raise e

    total_time = time.monotonic() - start_total

    print("\n" + "=" * 80)
    print(f"🎉 All {num_jobs} Clusters Completed in {total_time:.1f}s!")
    print("=" * 80)
    header = f"{'Cluster':<12} | {'Test Acc':<9} | {'False App':<10} | {'False Rej':<10} | {'Review %':<9} | {'ONNX Size':<10} | {'Elapsed':<8}"
    print(header)
    print("-" * len(header))

    summary = {}
    for cluster, rep in results.items():
        rt = rep["routed_test"]
        onnx_sz = rep["onnx_export"]["size_mb"]
        elapsed = rep["elapsed_seconds"]
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
            "onnx_path": rep["onnx_export"]["path"],
            "elapsed_seconds": elapsed,
        }

    # Write parallel summary report
    summary_path = root / "models" / "parallel_clusters_summary.json"
    summary_path.write_text(json.dumps(dict(total_time_seconds=total_time, clusters=summary), indent=2) + "\n")
    print("-" * len(header))
    print(f"Detailed summary saved to {summary_path}\n")


if __name__ == "__main__":
    main()
