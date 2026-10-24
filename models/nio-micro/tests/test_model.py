import unittest
import sys
from pathlib import Path

micro_dir = str(Path(__file__).resolve().parents[1])
if micro_dir not in sys.path:
    sys.path.insert(0, micro_dir)

import torch

from scripts.model import NioMicro


class NioMicroTests(unittest.TestCase):
    def test_exact_parameter_count_and_training(self):
        model = NioMicro(dropout=0.0)
        self.assertEqual(model.count_parameters(), 5_000_000)
        self.assertEqual(
            sum(p.numel() for p in model.parameters() if p.requires_grad),
            5_000_000,
        )

        input_ids = torch.tensor([[1, 2, 3, 0], [1, 4, 0, 0]])
        decision, sentiment, score = model(input_ids, input_ids.ne(0))
        self.assertEqual(decision.shape, (2, 2))
        self.assertEqual(sentiment.shape, (2, 2))
        self.assertEqual(score.shape, (2,))
        loss = (
            torch.nn.functional.cross_entropy(decision, torch.tensor([0, 1]))
            + torch.nn.functional.cross_entropy(sentiment, torch.tensor([1, 0]))
            + torch.nn.functional.mse_loss(score, torch.tensor([0.2, 0.8]))
        )
        loss.backward()
        for name, parameter in model.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
            self.assertTrue(torch.isfinite(parameter.grad).all(), name)
            self.assertGreater(parameter.grad.abs().sum().item(), 0, name)


if __name__ == "__main__":
    unittest.main()
