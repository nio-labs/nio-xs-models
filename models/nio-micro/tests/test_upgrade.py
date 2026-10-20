import json
import sys
from pathlib import Path
import tempfile
import unittest

micro_dir = str(Path(__file__).resolve().parents[1])
if micro_dir not in sys.path:
    sys.path.insert(0, micro_dir)

import torch

from scripts.artifacts import load_model
from scripts.model import NioMicro
from scripts.prepare_upgrade_data import prepare, scenario_key
from scripts.train import audit_splits


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)


class UpgradeTests(unittest.TestCase):
    def test_groups_stay_together_and_preparation_is_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for label in (0, 1):
                for i in range(10):
                    text = f"scenario {label} number {i}"
                    for variant in (text, f"Code audit finding: {text}", text):
                        rows.append(dict(text=variant, decision=label, sentiment=label, score=float(label)))
            source = root / "source.jsonl"
            source.write_text("\n".join(json.dumps(row) for row in rows))
            report = prepare([source], root / "first")
            prepare([source], root / "second")
            self.assertEqual(report["source_rows"], 60)
            self.assertEqual(report["unique_texts"], 40)
            datasets = {}
            for name in ("train", "val", "test"):
                first = (root / "first" / f"{name}.jsonl").read_text()
                self.assertEqual(first, (root / "second" / f"{name}.jsonl").read_text())
                datasets[name] = Rows([json.loads(line) for line in first.splitlines()])
            audit_splits(datasets)
            datasets["val"].rows.append(datasets["train"].rows[0])
            with self.assertRaisesRegex(ValueError, "Cross-split"):
                audit_splits(datasets)

    def test_conflicting_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [dict(text="same", decision=label, sentiment=label, score=float(label))
                    for label in (0, 1)]
            source = root / "source.jsonl"
            source.write_text("\n".join(json.dumps(row) for row in rows))
            with self.assertRaisesRegex(ValueError, "Conflicting labels"):
                prepare([source], root / "out")

    def test_cli_wrapper_is_removed_without_removing_command_quotes(self):
        self.assertEqual(scenario_key("CLI command execution: `git status`"), "git status")
        self.assertEqual(scenario_key("git commit -m 'hello'"), "git commit -m 'hello'")

    def test_versioned_checkpoint_restores_its_own_architecture(self):
        model = NioMicro(d_model=192, dim_feedforward=844, score_hidden_dim=342).eval()
        self.assertEqual(model.count_parameters(), 3_500_000)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.pt"
            torch.save(dict(model_config=model.config, model_state_dict=model.state_dict(),
                            trainable_parameters=model.count_parameters()), path)
            loaded, _ = load_model(path)
            loaded.eval()
            self.assertEqual(loaded.count_parameters(), 3_500_000)
            ids = torch.tensor([[1, 2, 3]])
            with torch.no_grad():
                for expected, actual in zip(model(ids), loaded(ids)):
                    torch.testing.assert_close(expected, actual)
            torch.save(model.state_dict(), path)
            with self.assertRaisesRegex(ValueError, "Legacy"):
                load_model(path)


if __name__ == "__main__":
    unittest.main()
