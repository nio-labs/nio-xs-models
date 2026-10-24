"""
Cluster Data Synthesizer for NioMicro.
Generates isolated, held-out action family dataset splits for any cluster.
Guarantees 0% cross-split leakage and full combinatorial coverage.
"""

import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import random

try:
    from .cluster_definitions import CLUSTER_ACTIONS
    from .context_policy import format_input, policy_label, POLICY_VERSION
except ImportError:
    from cluster_definitions import CLUSTER_ACTIONS
    from context_policy import format_input, policy_label, POLICY_VERSION

TONES = [
    ("", -100),
    ("Please handle this carefully. Thank you!", 1),
    ("Do it now, idiot. Your work is garbage.", 0),
]


def generate_cluster_dataset(cluster: str, output_dir: Path, seed: int = 73) -> dict:
    if cluster not in CLUSTER_ACTIONS:
        raise ValueError(f"Unknown cluster '{cluster}'. Available: {list(CLUSTER_ACTIONS.keys())}")

    actions_dict = CLUSTER_ACTIONS[cluster]
    rng = random.Random(seed)
    splits = {name: [] for name in ("train", "val", "calibration", "test")}
    manifests = {}

    for kind, actions in actions_dict.items():
        actions = sorted(actions)
        rng.shuffle(actions)
        # Partitions: 7 train, 2 val, 1 calibration, 2 test
        partitions = dict(
            train=actions[:7],
            val=actions[7:9],
            calibration=actions[9:10],
            test=actions[10:],
        )
        for split, families in partitions.items():
            for family, *variants in families:
                manifests[family] = split
                for action, environment, authorization, target, (feedback, sentiment) in itertools.product(
                    variants,
                    ("sandbox", "staging", "production", "unknown"),
                    ("granted", "denied", "unknown"),
                    ("known", "unknown"),
                    TONES,
                ):
                    context = dict(
                        domain=cluster,
                        environment=environment,
                        authorization=authorization,
                        target=target,
                    )
                    decision = policy_label(kind, environment, authorization, target)
                    text = format_input(action, context, feedback)
                    splits[split].append(
                        dict(
                            text=text,
                            action=action,
                            context=context,
                            feedback=feedback,
                            decision=decision,
                            sentiment=sentiment,
                            score=None if decision == 2 else float(decision),
                            scenario_group=family,
                            annotation_kind=kind,
                            cluster=cluster,
                            label_source="synthetic_policy_rule",
                            policy_version=POLICY_VERSION,
                        )
                    )

    output_dir.mkdir(parents=True, exist_ok=True)
    report = dict(
        seed=seed,
        cluster=cluster,
        policy_version=POLICY_VERSION,
        label_source="Auditable synthetic rules with zero cross-split leakage",
        split_unit="Complete action family, including all contextual and tone variants",
        action_family_split=manifests,
        splits={},
    )

    texts, groups = {}, {}
    for name, rows in splits.items():
        rng.shuffle(rows)
        texts[name] = {r["text"] for r in rows}
        groups[name] = {r["scenario_group"] for r in rows}
        if len(texts[name]) != len(rows):
            raise ValueError(f"Duplicate text in {name} for cluster {cluster}")
        path = output_dir / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        report["splits"][name] = dict(
            rows=len(rows),
            groups=len(groups[name]),
            decisions=dict(Counter(r["decision"] for r in rows)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    for left, right in itertools.combinations(splits, 2):
        if texts[left] & texts[right] or groups[left] & groups[right]:
            raise ValueError(f"Cross-split overlap: {left}/{right} in cluster {cluster}")

    report["cross_split_text_overlap"] = 0
    report["cross_split_family_overlap"] = 0
    (output_dir / "split_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster", type=str, required=True, choices=list(CLUSTER_ACTIONS.keys()))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=73)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out = args.output_dir or (root / "data" / args.cluster)
    rep = generate_cluster_dataset(args.cluster, out, seed=args.seed)
    print(json.dumps(rep, indent=2))
