"""
NioMask Model Architecture (~1.0M Parameters)
Real-time Byte-Level Conv-Transformer & Entropy Stream Scanner for Secret & PII Redaction.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

# Vocabulary: 0=PAD, 1=UNK, 2=BOS, 3=EOS, 4..259 = byte values 0..255
VOCAB_SIZE = 260
PAD_ID = 0
UNK_ID = 1
BOS_ID = 2
EOS_ID = 3

# BIO Classification labels:
# 0: O (Clean text)
# 1: B-SECRET (API keys, Tokens, Private Keys)
# 2: I-SECRET
# 3: B-PII (Emails, IPs, Phone, Passwords)
# 4: I-PII
# 5: B-HASH (Benign high-entropy like git commit SHA, UUID, base64 assets)
# 6: I-HASH
NUM_CLASSES = 7

LABEL_NAMES = [
    "O",
    "B-SECRET",
    "I-SECRET",
    "B-PII",
    "I-PII",
    "B-HASH",
    "I-HASH"
]


class NioMaskConfig:
    def __init__(
        self,
        vocab_size: int = VOCAB_SIZE,
        d_model: int = 128,
        num_layers: int = 2,
        num_heads: int = 4,
        d_ff: int = 1500,
        conv_kernel_size: int = 5,
        max_seq_len: int = 256,
        d_classifier_mid: int = 118,
        d_risk_mid: int = 120,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.1,
    ):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.d_ff = d_ff
        self.conv_kernel_size = conv_kernel_size
        self.max_seq_len = max_seq_len
        self.d_classifier_mid = d_classifier_mid
        self.d_risk_mid = d_risk_mid
        self.num_classes = num_classes
        self.dropout = dropout


class NioMaskModel(nn.Module):
    """
    NioMask: ~1.0M Parameter Byte-Level Stream Redactor.
    Combines 1D convolution for local byte patterns with a 2-layer transformer encoder
    and dual heads (Token Classification + Stream Risk Score).
    """

    def __init__(self, config: NioMaskConfig = None):
        super().__init__()
        if config is None:
            config = NioMaskConfig()
        self.config = config

        # Byte Embedding
        self.token_embedding = nn.Embedding(
            config.vocab_size, config.d_model, padding_idx=PAD_ID
        )
        self.pos_embedding = nn.Embedding(config.max_seq_len, config.d_model)

        # 1D Convolution for sub-byte pattern extraction (capturing prefixes like ghp_, AKIA, etc.)
        self.conv1 = nn.Conv1d(
            in_channels=config.d_model,
            out_channels=config.d_model,
            kernel_size=config.conv_kernel_size,
            padding=config.conv_kernel_size // 2,
        )
        self.conv_norm = nn.LayerNorm(config.d_model)

        # Transformer Encoder Layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.num_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=config.num_layers
        )
        self.final_norm = nn.LayerNorm(config.d_model)

        # Head 1: Token Classification (Token-level BIO tag prediction)
        self.token_classifier = nn.Sequential(
            nn.Linear(config.d_model, config.d_classifier_mid),
            nn.GELU(),
            nn.Linear(config.d_classifier_mid, config.num_classes),
        )

        # Head 2: Stream-level Risk Score (0.0 to 1.0 continuous risk score)
        self.risk_head = nn.Sequential(
            nn.Linear(config.d_model * 2, config.d_risk_mid),
            nn.GELU(),
            nn.Linear(config.d_risk_mid, 1),
            nn.Sigmoid(),
        )

        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None):
        """
        Args:
            input_ids: [batch_size, seq_len] int64 tensor
            attention_mask: [batch_size, seq_len] bool or float tensor (1 for valid, 0 for pad)
        Returns:
            token_logits: [batch_size, seq_len, num_classes]
            risk_score: [batch_size, 1]
        """
        B, L = input_ids.shape

        # Positional indices
        positions = torch.arange(0, L, device=input_ids.device).unsqueeze(0).expand(B, L)

        # Embeddings
        x = self.token_embedding(input_ids) + self.pos_embedding(positions)

        # 1D Convolution along sequence dimension: Conv1d expects [B, Channels, SeqLen]
        conv_out = self.conv1(x.transpose(1, 2)).transpose(1, 2)
        x = self.conv_norm(x + F.gelu(conv_out))

        # Transformer Encoder
        src_key_padding_mask = None
        if attention_mask is not None:
            # nn.Transformer expects True for padded positions
            if attention_mask.dtype == torch.bool:
                src_key_padding_mask = ~attention_mask
            else:
                src_key_padding_mask = attention_mask == 0

        features = self.transformer(x, src_key_padding_mask=src_key_padding_mask)
        features = self.final_norm(features)

        # Token-level classification logits
        token_logits = self.token_classifier(features)

        # Stream-level risk score: combine mean-pooling and max-pooling
        if attention_mask is not None:
            mask_expanded = attention_mask.unsqueeze(-1).float()
            sum_features = (features * mask_expanded).sum(dim=1)
            mean_features = sum_features / mask_expanded.sum(dim=1).clamp(min=1e-9)
            # For max pooling, mask out pad tokens with -1e9
            features_masked = features.masked_fill(~attention_mask.unsqueeze(-1).bool(), -1e9)
            max_features = features_masked.max(dim=1).values
        else:
            mean_features = features.mean(dim=1)
            max_features = features.max(dim=1).values

        pooled = torch.cat([mean_features, max_features], dim=-1)
        risk_score = self.risk_head(pooled)

        return token_logits, risk_score


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    cfg = NioMaskConfig()
    model = NioMaskModel(cfg)
    total_params = count_parameters(model)
    print(f"NioMask Parameter Count: {total_params:,} parameters")

    # Quick test forward pass
    dummy_input = torch.randint(0, 256, (2, 128), dtype=torch.long)
    dummy_mask = torch.ones((2, 128), dtype=torch.long)
    logits, risk = model(dummy_input, dummy_mask)
    print(f"Logits shape: {logits.shape} (expected [2, 128, 7])")
    print(f"Risk shape: {risk.shape} (expected [2, 1])")
