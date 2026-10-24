"""Load versioned checkpoints without assuming the current default architecture."""

import hashlib
from pathlib import Path
import torch

try:
    from .model import NioMicro
except ImportError:
    from model import NioMicro


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_model(path):
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if "model_config" not in checkpoint:
        raise ValueError("Legacy state dictionary: use the original 3.5M architecture. "
                         "The 5M exporter requires a versioned checkpoint from train.py.")
    model = NioMicro(**checkpoint["model_config"])
    model.load_state_dict(checkpoint["model_state_dict"])
    if model.count_parameters() != checkpoint["trainable_parameters"]:
        raise ValueError("Checkpoint parameter count does not match its metadata")
    return model, checkpoint
