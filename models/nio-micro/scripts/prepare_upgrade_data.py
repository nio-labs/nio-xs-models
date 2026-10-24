"""Deduplicate developer examples and keep wrapped copies in the same split."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random

try:
    from .dataset_generator import CONTEXT_WRAPPERS
except ImportError:
    from dataset_generator import CONTEXT_WRAPPERS


def scenario_key(text):
    for wrapper in CONTEXT_WRAPPERS:
        prefix, suffix = wrapper.split("{}")
        if text.startswith(prefix) and (not suffix or text.endswith(suffix)):
            text = text[len(prefix):len(text) - len(suffix) if suffix else None]
            break
    return " ".join(text.split())


def prepare(source_paths, output_dir, seed=42):
    examples = defaultdict(list)
    for path in source_paths:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                examples[row["text"]].append(row)

    groups = defaultdict(list)
    for text, copies in sorted(examples.items()):
        labels = {(r["decision"], r["sentiment"]) for r in copies}
        if len(labels) != 1:
            raise ValueError(f"Conflicting labels for {text!r}")
        row = dict(copies[0])
        if row["decision"] not in (0, 1) or row["sentiment"] not in (0, 1):
            raise ValueError("The first 5M upgrade requires binary labels")
        if any(not 0 <= r["score"] <= 1 for r in copies):
            raise ValueError("Scores must be between zero and one")
        row["score"] = round(sum(r["score"] for r in copies) / len(copies), 6)
        row["scenario_group"] = scenario_key(text)
        groups[row["scenario_group"]].append(row)

    by_label = defaultdict(list)
    for key, rows in groups.items():
        decisions = {r["decision"] for r in rows}
        if len(decisions) != 1:
            raise ValueError(f"Conflicting decisions in scenario {key!r}")
        by_label[next(iter(decisions))].append(key)

    rng = random.Random(seed)
    splits = {name: [] for name in ("train", "val", "test")}
    for keys in by_label.values():
        keys.sort()
        rng.shuffle(keys)
        held_out = max(1, round(len(keys) * 0.15))
        if len(keys) <= 2 * held_out:
            raise ValueError("Insufficient scenario groups for three splits")
        for name, selected in (
            ("val", keys[:held_out]),
            ("test", keys[held_out:2 * held_out]),
            ("train", keys[2 * held_out:]),
        ):
            splits[name].extend(row for key in selected for row in groups[key])

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"seed": seed, "source_rows": sum(map(len, examples.values())),
              "unique_texts": len(examples), "scenario_groups": len(groups),
              "grouping": "Base snippet with known contextual wrappers removed",
              "limitations": "Small synthetic developer dataset; semantic similarity beyond wrappers is not audited. Sentiment remains coupled to decision in the source labels."}
    for name, rows in splits.items():
        rng.shuffle(rows)
        with (output_dir / f"{name}.jsonl").open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        report[name] = {"rows": len(rows),
                        "scenario_groups": len({r["scenario_group"] for r in rows}),
                        "decisions": dict(Counter(r["decision"] for r in rows))}
    report["cross_split_text_overlap"] = 0
    report["cross_split_scenario_overlap"] = 0
    (output_dir / "split_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=base / "data")
    parser.add_argument("--output-dir", type=Path, default=base / "data/5m")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(prepare([args.source_dir / "train.jsonl", args.source_dir / "val.jsonl"],
                             args.output_dir, args.seed), indent=2))
