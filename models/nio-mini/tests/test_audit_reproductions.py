"""
Regression and audit reproduction tests for NioMini.
Covers:
  - Clean function generalization (e.g. pub fn add ...)
  - Dynamic batching on exported ONNX
  - Late defect preservation without silent truncation
  - Disjoint train/validation model inputs (0 leaks)
"""

import sys
import random
import hashlib
from pathlib import Path
import numpy as np
import pytest
import torch
import onnxruntime as ort

scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from mini_infer import NioMiniPredictor
from mini_dataset_generator import generate_dataset, text_to_token_ids, extract_ast_features

MODEL_PATH = str(Path(__file__).resolve().parents[1] / "nio-mini.onnx")


def test_real_onnx_preserves_clean_add_verdict():
    verdict = NioMiniPredictor(MODEL_PATH).predict("pub fn add(a: i32, b: i32) -> i32 { a + b }")
    assert verdict["model_backend"] == "onnx"
    assert not verdict["will_break"], f"Expected clean verdict, got: {verdict}"
    assert verdict["category"] == "CLEAN"


def test_dynamic_batch_two():
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    sess = ort.InferenceSession(MODEL_PATH, sess_options=options, providers=["CPUExecutionProvider"])
    out = sess.run(
        None,
        {
            "input_ids": np.ones((2, 128), dtype=np.int64),
            "ast_features": np.zeros((2, 128, 32), dtype=np.float32),
        },
    )
    assert [a.shape for a in out] == [(2, 1), (2, 5), (2, 1)]


def test_late_defect_must_not_be_silently_lost():
    prefix = "// " + ("x" * 256) + "\n"
    clean = prefix + "fn main() { let x: u32 = 1; }"
    broken = prefix + 'fn main() { let x: u32 = "text"; }'
    assert not (
        np.array_equal(text_to_token_ids(clean), text_to_token_ids(broken))
        and np.array_equal(extract_ast_features(clean), extract_ast_features(broken))
    ), "Clean and broken program produce identical model inputs"


def test_training_validation_model_inputs_are_disjoint():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    dataset = generate_dataset(10000)
    order = torch.randperm(len(dataset)).tolist()

    def signature(item):
        return hashlib.sha256(item["input_ids"].tobytes() + item["ast_features"].tobytes()).digest()

    train = {signature(dataset[i]) for i in order[:9000]}
    val = {signature(dataset[i]) for i in order[9000:]}
    assert train.isdisjoint(val), f"{len(train & val)} distinct model inputs overlap"
