"""
Tests for NioMini dataset generator, inference engine, and end-to-end pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import numpy as np
from mini_dataset_generator import generate_dataset, text_to_token_ids, extract_ast_features, LABELS, MAX_SEQ_LEN
from mini_infer import NioMiniPredictor


def test_dataset_generator():
    samples = generate_dataset(num_samples=25)
    assert len(samples) == 25
    for s in samples:
        assert "text" in s
        assert "input_ids" in s
        assert "ast_features" in s
        assert "category" in s
        assert "will_break" in s
        assert "risk_score" in s
        assert s["category"] in range(5)
        assert s["input_ids"].shape == (MAX_SEQ_LEN,)
        assert s["ast_features"].shape == (MAX_SEQ_LEN, 32)
        if s["category"] == 0:
            assert s["will_break"] == 0.0
            assert s["risk_score"] < 0.20
        else:
            assert s["will_break"] == 1.0
            assert s["risk_score"] > 0.60


def test_infer_fallback():
    predictor = NioMiniPredictor("nonexistent_model.onnx")

    # Clean code
    clean_sample = "pub fn add(a: i32, b: i32) -> i32 { a + b }"
    res_clean = predictor.predict(clean_sample)
    assert res_clean["will_break"] is False
    assert res_clean["category"] == "CLEAN"

    # Syntax error (unbalanced brace)
    broken_syntax = "pub fn foo() { let x = 1;"
    res_syntax = predictor.predict(broken_syntax)
    assert res_syntax["will_break"] is True
    assert res_syntax["category"] == "SYNTAX_ERROR"
