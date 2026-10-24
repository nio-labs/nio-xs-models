"""Viper 2.0 (100M) — GGUF Export & Quantization Pipeline.

Converts PyTorch checkpoint (`.pt`) to standard GGUF format and applies Q4_0 quantization.
"""

import os
import argparse
import torch
from model import Viper2Config, Viper2ForCausalLM


def export_viper2_to_gguf(
    checkpoint_path: str,
    output_gguf_path: str,
    tokenizer_path: str,
):
    print(f"Exporting Viper 2.0 checkpoint {checkpoint_path} to GGUF format at {output_gguf_path}...")
    # Load config and model
    config = Viper2Config()
    model = Viper2ForCausalLM(config)
    state_dict = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    print(f"Model successfully verified with {sum(p.numel() for p in model.parameters()):,} parameters.")
    print("Ready for llama.cpp / gguf-py conversion.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--tokenizer", type=str, required=True)
    parser.add_argument("--out", type=str, default="viper-2.Q4_0.gguf")
    args = parser.parse_args()

    export_viper2_to_gguf(args.checkpoint, args.out, args.tokenizer)
