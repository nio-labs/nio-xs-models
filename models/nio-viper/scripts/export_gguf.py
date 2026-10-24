"""Viper (100M) — GGUF Export & Q4_0 Quantization Pipeline.

Converts PyTorch checkpoint (`.pt`) to standard GGUF format with Q4_0 quantization for weights
and F32 for layer norms. Compatible with AstMicroEngine / llama.cpp / Candle.
"""

import os
import argparse
import numpy as np
import torch
from tokenizers import Tokenizer
import gguf

from model import Viper2Config, Viper2ForCausalLM


def export_viper_to_gguf(
    checkpoint_path: str,
    output_gguf_path: str,
    tokenizer_path: str,
    quantize: bool = True,
):
    print(f"Exporting Viper 100M checkpoint {checkpoint_path} to GGUF format at {output_gguf_path}...")
    
    config = Viper2Config()
    model = Viper2ForCausalLM(config)
    state_dict = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model verified with {total_params:,} parameters.")

    # Initialize GGUF writer with 'qwen2' architecture compatible with AstMicroEngine
    writer = gguf.GGUFWriter(output_gguf_path, "qwen2")
    
    # Architecture Metadata
    writer.add_architecture()
    writer.add_block_count(config.num_hidden_layers)
    writer.add_embedding_length(config.hidden_size)
    writer.add_feed_forward_length(config.intermediate_size)
    writer.add_head_count(config.num_attention_heads)
    writer.add_head_count_kv(config.num_key_value_heads)
    writer.add_context_length(config.max_position_embeddings)
    writer.add_layer_norm_rms_eps(config.rms_norm_eps)
    writer.add_rope_freq_base(1000000.0)

    # Tokenizer metadata
    if os.path.exists(tokenizer_path):
        tok = Tokenizer.from_file(tokenizer_path)
        vocab = tok.get_vocab()
        tokens = [b"" for _ in range(len(vocab))]
        scores = [0.0] * len(vocab)
        for token_str, idx in vocab.items():
            if idx < len(tokens):
                tokens[idx] = token_str.encode("utf-8")
        writer.add_tokenizer_model("gpt2")
        writer.add_token_list(tokens)
        writer.add_token_scores(scores)
        print(f"Added {len(tokens)} tokenizer tokens to GGUF header.")

    # Tensor mapping (supporting both direct and 'model.' prefixes)
    tensor_map = {
        "embed_tokens.weight": "token_embd.weight",
        "norm.weight": "output_norm.weight",
        "lm_head.weight": "output.weight",
    }
    for i in range(config.num_hidden_layers):
        tensor_map[f"layers.{i}.input_layernorm.weight"] = f"blk.{i}.attn_norm.weight"
        tensor_map[f"layers.{i}.self_attn.q_proj.weight"] = f"blk.{i}.attn_q.weight"
        tensor_map[f"layers.{i}.self_attn.k_proj.weight"] = f"blk.{i}.attn_k.weight"
        tensor_map[f"layers.{i}.self_attn.v_proj.weight"] = f"blk.{i}.attn_v.weight"
        tensor_map[f"layers.{i}.self_attn.o_proj.weight"] = f"blk.{i}.attn_output.weight"
        tensor_map[f"layers.{i}.post_attention_layernorm.weight"] = f"blk.{i}.ffn_norm.weight"
        tensor_map[f"layers.{i}.mlp.gate_proj.weight"] = f"blk.{i}.ffn_gate.weight"
        tensor_map[f"layers.{i}.mlp.down_proj.weight"] = f"blk.{i}.ffn_down.weight"
        tensor_map[f"layers.{i}.mlp.up_proj.weight"] = f"blk.{i}.ffn_up.weight"

    tensor_count = 0
    for pt_name, gguf_name in tensor_map.items():
        tensor = None
        if pt_name in state_dict:
            tensor = state_dict[pt_name]
        elif f"model.{pt_name}" in state_dict:
            tensor = state_dict[f"model.{pt_name}"]
        elif pt_name == "lm_head.weight" and "embed_tokens.weight" in state_dict:
            tensor = state_dict["embed_tokens.weight"]
        elif pt_name == "lm_head.weight" and "model.embed_tokens.weight" in state_dict:
            tensor = state_dict["model.embed_tokens.weight"]

        if tensor is None:
            print(f"Warning: Missing tensor {pt_name}")
            continue

        data = tensor.detach().cpu().to(torch.float32).numpy()
        
        # 1D tensors (RMSNorms) remain F32; 2D weight matrices quantize to Q4_0
        if quantize and data.ndim == 2 and data.shape[-1] % 32 == 0:
            q_data = gguf.quants.quantize(data, gguf.GGMLQuantizationType.Q4_0)
            writer.add_tensor(gguf_name, q_data, raw_dtype=gguf.GGMLQuantizationType.Q4_0)
        else:
            writer.add_tensor(gguf_name, data)
        tensor_count += 1

    print(f"Added {tensor_count} tensors to GGUF graph.")

    # Write GGUF file
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_tensors_to_file()
    writer.close()
    
    file_size_mb = os.path.getsize(output_gguf_path) / (1024 * 1024)
    print(f"Successfully generated {output_gguf_path} ({file_size_mb:.2f} MB, {tensor_count} tensors).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--tokenizer", type=str, required=True)
    parser.add_argument("--out", type=str, default="viper.Q4_0.gguf")
    parser.add_argument("--no-quant", action="store_true")
    args = parser.parse_args()

    export_viper_to_gguf(args.checkpoint, args.out, args.tokenizer, quantize=not args.no_quant)
