"""
NioMini Model Architecture (Exactly 7,100,000 Parameters)
Pre-emptive Defect Forecasting Engine.
Predicts compilation errors, broken builds, test suite failures, and regressions from AST diffs.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

VOCAB_SIZE = 8192
MAX_SEQ_LEN = 512
NUM_CLASSES = 5

LABEL_NAMES = [
    "CLEAN",
    "SYNTAX_ERROR",
    "TYPE_MISMATCH",
    "BORROW_CHECK_FAIL",
    "TEST_REGRESSION"
]


class NioMiniConfig:
    def __init__(
        self,
        vocab_size: int = VOCAB_SIZE,
        d_model: int = 256,
        num_layers: int = 6,
        num_heads: int = 8,
        d_ff: int = 1024,
        max_seq_len: int = MAX_SEQ_LEN,
        ast_feature_dim: int = 32,
        d_break_mid: int = 192,
        d_category_mid: int = 167,
        d_risk_mid: int = 120,
        num_classes: int = NUM_CLASSES,
        dropout: float = 0.1,
    ):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        self.ast_feature_dim = ast_feature_dim
        self.d_break_mid = d_break_mid
        self.d_category_mid = d_category_mid
        self.d_risk_mid = d_risk_mid
        self.num_classes = num_classes
        self.dropout = dropout


class NioMiniDefectForecaster(nn.Module):
    """
    NioMini: Exactly 7,100,000 Parameter AST Diff & Defect Forecasting Transformer.
    """
    def __init__(self, config: NioMiniConfig = None):
        super().__init__()
        if config is None:
            config = NioMiniConfig()
        self.config = config

        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        self.ast_feature_proj = nn.Linear(config.ast_feature_dim, config.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.num_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=config.num_layers)
        self.norm = nn.LayerNorm(config.d_model)

        # Multi-Head Outputs calibrated to hit exactly 7,100,000 parameters
        # 1. Binary Build Break Verdict (0.0 to 1.0)
        self.break_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_break_mid),
            nn.GELU(),
            nn.Linear(config.d_break_mid, 1, bias=False),
            nn.Sigmoid()
        )
        # 2. Defect Category Head
        self.category_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_category_mid),
            nn.GELU(),
            nn.Linear(config.d_category_mid, config.num_classes)
        )
        # 3. Continuous Calibrated Risk Head
        self.risk_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_risk_mid),
            nn.GELU(),
            nn.Linear(config.d_risk_mid, 1),
            nn.Sigmoid()
        )

    def forward(self, input_ids: torch.Tensor, ast_features: torch.Tensor = None):
        B, L = input_ids.shape
        pos_idx = torch.arange(L, device=input_ids.device).unsqueeze(0).repeat(B, 1)
        x = self.token_embedding(input_ids) + self.pos_embedding(pos_idx)
        if ast_features is not None:
            x = x + self.ast_feature_proj(ast_features)

        feat = self.transformer(x)
        pooled = self.norm(feat[:, 0, :])  # [CLS] representation

        will_break = self.break_head(pooled)
        category_logits = self.category_head(pooled)
        risk_score = self.risk_head(pooled)

        return will_break, category_logits, risk_score
