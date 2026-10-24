"""
NioMicro Model Definition (PyTorch)
Compact 4-Layer Bidirectional Transformer Encoder with Multi-Task Heads
"""

import math
import torch
import torch.nn as nn
from typing import Tuple, Optional

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is [batch, seq_len, d_model]
        return x + self.pe[:, :x.size(1), :]

class NioMicro(nn.Module):
    def __init__(
        self,
        vocab_size: int = 8000,
        d_model: int = 224,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 1304,
        dropout: float = 0.1,
        max_seq_len: int = 256,
        score_hidden_dim: int = 238,
        num_decision_classes: int = 2,
        score_output_bias: bool = False,
    ):
        super().__init__()
        self.config = dict(
            vocab_size=vocab_size, d_model=d_model, nhead=nhead,
            num_layers=num_layers, dim_feedforward=dim_feedforward,
            dropout=dropout, max_seq_len=max_seq_len,
            score_hidden_dim=score_hidden_dim,
            num_decision_classes=num_decision_classes,
            score_output_bias=score_output_bias,
        )
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len)
        self.dropout = nn.Dropout(dropout)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )
        self.encoder = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=num_layers,
            enable_nested_tensor=False
        )
        self.norm = nn.LayerNorm(d_model)

        # Multi-task heads
        self.decision_head = nn.Linear(d_model, num_decision_classes)
        self.sentiment_head = nn.Linear(d_model, 2)
        # With the default encoder, this head gives exactly 5,000,000
        # trainable parameters. Every parameter participates in inference.
        self.score_head = nn.Sequential(
            nn.Linear(d_model, score_hidden_dim),
            nn.GELU(),
            nn.Linear(score_hidden_dim, 1, bias=score_output_bias),
            nn.Sigmoid()
        )

    def forward(
        self, 
        input_ids: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # input_ids: [batch, seq_len]
        batch_size, seq_len = input_ids.shape
        
        if attention_mask is not None:
            # PyTorch TransformerEncoder takes src_key_padding_mask where True means masked (ignore)
            # attention_mask is 1 for valid tokens, 0 for padding
            src_key_padding_mask = (attention_mask == 0)
        else:
            src_key_padding_mask = None

        x = self.embedding(input_ids) * math.sqrt(self.d_model)
        x = self.pos_encoder(x)
        x = self.dropout(x)

        hidden_states = self.encoder(x, src_key_padding_mask=src_key_padding_mask)
        hidden_states = self.norm(hidden_states)

        # Use [CLS] representation (index 0) for sequence classification
        cls_repr = hidden_states[:, 0, :]

        decision_logits = self.decision_head(cls_repr)
        sentiment_logits = self.sentiment_head(cls_repr)      # [batch, 2]
        score = self.score_head(cls_repr).squeeze(-1)         # [batch]

        return decision_logits, sentiment_logits, score

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

if __name__ == "__main__":
    model = NioMicro()
    params = model.count_parameters()
    print(f"NioMicro Total Trainable Parameters: {params:,} (~{params * 2 / (1024*1024):.2f} MiB in FP16)")
    dummy_input = torch.randint(0, 8000, (2, 64))
    dec, sent, scr = model(dummy_input)
    print("Decision shape:", dec.shape)
    print("Sentiment shape:", sent.shape)
    print("Score shape:", scr.shape)
