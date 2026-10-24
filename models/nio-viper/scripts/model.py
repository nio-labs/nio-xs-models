"""Viper 2.0 (100M) — Tactical Terminal & DevOps Reflex Engine.

Architecture Invariant:
Total Parameter Budget == EXACTLY 100,000,000 parameters.
- Layers (L): 14
- Hidden Dimension (d): 800 (SIMD 32-byte block clean: 800 / 32 = 25)
- Attention: Grouped-Query Attention (GQA 10/2, dk = 80)
- MLP: SwiGLU with d_ff = 1,920 (2.4x d)
- Vocabulary Size: 17,451 ByteLevel BPE tokens
- Weight Tying: lm_head.weight == embed_tokens.weight
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class Viper2Config:
    vocab_size: int = 17451
    hidden_size: int = 800
    intermediate_size: int = 1920
    num_hidden_layers: int = 14
    num_attention_heads: int = 10
    num_key_value_heads: int = 2
    max_position_embeddings: int = 512
    rms_norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    tie_word_embeddings: bool = True
    exact_parameter_target: int = 100_000_000

    @property
    def head_dim(self) -> int:
        return self.hidden_size // self.num_attention_heads


class ViperRMSNorm(nn.Module):
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_dtype = x.dtype
        x = x.to(torch.float32)
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return (self.weight * x).to(input_dtype)


class ViperRotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_position_embeddings: int = 512, base: float = 10000.0):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        inv_freq = 1.0 / (self.base ** (torch.arange(0, self.dim, 2).float() / self.dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        t = torch.arange(seq_len, device=x.device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    # q, k shape: [batch, heads, seq_len, head_dim]
    cos = cos.unsqueeze(0).unsqueeze(1) # [1, 1, seq_len, head_dim]
    sin = sin.unsqueeze(0).unsqueeze(1)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class ViperAttention(nn.Module):
    def __init__(self, config: Viper2Config):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = config.head_dim
        self.num_key_value_heads = config.num_key_value_heads
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads

        # Projections without bias for minimal overhead & exact budget
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)

    def forward(
        self,
        hidden_states: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch_size, seq_len, _ = hidden_states.shape

        q = self.q_proj(hidden_states).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(batch_size, seq_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(batch_size, seq_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)

        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # Expand KV heads for GQA
        if self.num_key_value_groups > 1:
            k = k.repeat_interleave(self.num_key_value_groups, dim=1)
            v = v.repeat_interleave(self.num_key_value_groups, dim=1)

        # Scaled dot-product attention
        attn_output = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attention_mask, is_causal=(attention_mask is None and seq_len > 1)
        )

        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.hidden_size)
        return self.o_proj(attn_output)


class ViperMLP(nn.Module):
    def __init__(self, config: Viper2Config):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SwiGLU activation
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class ViperDecoderLayer(nn.Module):
    def __init__(self, config: Viper2Config):
        super().__init__()
        self.input_layernorm = ViperRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.self_attn = ViperAttention(config)
        self.post_attention_layernorm = ViperRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.mlp = ViperMLP(config)

    def forward(
        self,
        hidden_states: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.self_attn(hidden_states, cos, sin, attention_mask)
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        return hidden_states


class Viper2ForCausalLM(nn.Module):
    def __init__(self, config: Viper2Config):
        super().__init__()
        self.config = config

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = nn.ModuleList([ViperDecoderLayer(config) for _ in range(config.num_hidden_layers)])
        self.norm = ViperRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.rotary_emb = ViperRotaryEmbedding(config.head_dim, max_position_embeddings=config.max_position_embeddings)

        # Output projection head (tied with embeddings)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        if config.tie_word_embeddings:
            self.lm_head.weight = self.embed_tokens.weight

        # Parameter invariant verification
        self.verify_parameter_invariant()

    def verify_parameter_invariant(self):
        total_params = sum(p.numel() for p in self.parameters())
        expected = self.config.exact_parameter_target
        if total_params != expected:
            raise AssertionError(
                f"Viper 2.0 Parameter Invariant Failed! Expected {expected:,} parameters, got {total_params:,}"
            )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        batch_size, seq_len = input_ids.shape
        hidden_states = self.embed_tokens(input_ids)

        cos, sin = self.rotary_emb(hidden_states, seq_len)

        for layer in self.layers:
            hidden_states = layer(hidden_states, cos, sin, attention_mask)

        hidden_states = self.norm(hidden_states)
        logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            # Shift tokens for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(shift_logits.view(-1, self.config.vocab_size), shift_labels.view(-1))

        return logits, loss


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


if __name__ == "__main__":
    cfg = Viper2Config()
    model = Viper2ForCausalLM(cfg)
    total = count_parameters(model)
    print(f"✅ Viper 2.0 Model Successfully Initialized!")
    print(f"📊 Total Parameters: {total:,}")
    assert total == 100_000_000
