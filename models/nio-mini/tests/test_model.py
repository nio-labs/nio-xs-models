"""
Unit tests for NioMini architecture and inference.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import torch
from model import NioMiniConfig, NioMiniDefectForecaster, NUM_CLASSES, VOCAB_SIZE


def test_model_parameter_count():
    config = NioMiniConfig()
    model = NioMiniDefectForecaster(config)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Verify EXACTLY 7,100,000 parameters
    assert param_count == 7_100_000, f"Expected exactly 7,100,000 parameters, got: {param_count}"


def test_model_forward_shapes():
    config = NioMiniConfig()
    model = NioMiniDefectForecaster(config)
    batch_size = 4
    seq_len = 64
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len), dtype=torch.long)
    ast_features = torch.randn(batch_size, seq_len, config.ast_feature_dim, dtype=torch.float32)

    will_break, category_logits, risk_score = model(input_ids, ast_features)

    assert will_break.shape == (batch_size, 1)
    assert category_logits.shape == (batch_size, NUM_CLASSES)
    assert risk_score.shape == (batch_size, 1)
    assert (will_break >= 0.0).all() and (will_break <= 1.0).all()
    assert (risk_score >= 0.0).all() and (risk_score <= 1.0).all()
