"""
Unit tests for NioMask architecture and dataset generator.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import torch
import pytest
from model import NioMaskConfig, NioMaskModel, VOCAB_SIZE, NUM_CLASSES
from dataset_generator import generate_sample, text_to_bytes


def test_model_parameter_count():
    config = NioMaskConfig()
    model = NioMaskModel(config)
    param_count = sum(p.numel() for p in model.parameters())
    # Verify EXACTLY 1,100,000 parameters
    assert param_count == 1_100_000, f"Expected exactly 1,100,000 parameters, got: {param_count}"


def test_model_forward_shapes():
    config = NioMaskConfig()
    model = NioMaskModel(config)
    batch_size = 4
    seq_len = 64
    input_ids = torch.randint(0, 256, (batch_size, seq_len), dtype=torch.long)
    attention_mask = torch.ones((batch_size, seq_len), dtype=torch.float32)

    token_logits, risk_score = model(input_ids, attention_mask)

    assert token_logits.shape == (batch_size, seq_len, NUM_CLASSES)
    assert risk_score.shape == (batch_size, 1)
    assert (risk_score >= 0.0).all() and (risk_score <= 1.0).all()


def test_dataset_generator():
    sample = generate_sample("secret")
    assert "text" in sample
    assert "input_ids" in sample
    assert "labels" in sample
    assert "risk_score" in sample
    assert len(sample["input_ids"]) == len(sample["labels"])
    assert sample["risk_score"] == 1.0
    # Must contain at least one secret token
    assert any(label in (1, 2) for label in sample["labels"])


def test_benign_hash_sample():
    sample = generate_sample("benign_hash")
    assert sample["risk_score"] < 0.2
    assert any(label in (5, 6) for label in sample["labels"])
