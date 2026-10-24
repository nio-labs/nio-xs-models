import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import torch
from model import Viper2Config, Viper2ForCausalLM, count_parameters


def test_viper2_exact_parameter_budget():
    config = Viper2Config()
    model = Viper2ForCausalLM(config)
    total_params = count_parameters(model)
    assert total_params == 100_000_000, f"Expected exactly 100,000,000 parameters, got {total_params}"


def test_viper2_forward_pass():
    config = Viper2Config()
    model = Viper2ForCausalLM(config)
    model.eval()

    batch_size = 2
    seq_len = 16
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))

    with torch.no_grad():
        logits, loss = model(input_ids)

    assert logits.shape == (batch_size, seq_len, config.vocab_size)
    assert loss is None


def test_viper2_loss_computation():
    config = Viper2Config()
    model = Viper2ForCausalLM(config)

    batch_size = 2
    seq_len = 16
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))
    labels = input_ids.clone()

    logits, loss = model(input_ids, labels=labels)
    assert loss is not None
    assert loss.item() > 0.0
    assert torch.isfinite(loss)
