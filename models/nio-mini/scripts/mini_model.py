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


class DynamicMultiheadAttention(nn.Module):
    """
    Explicit multi-head attention supporting genuinely dynamic sequence lengths
    without baking static sequence dimensions into ONNX Reshape ops.
    """
    def __init__(self, d_model: int = 256, num_heads: int = 8):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        self.in_proj = nn.Linear(d_model, 3 * d_model)
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, L, _ = x.shape
        qkv = self.in_proj(x)
        qkv = qkv.view(B, L, 3, self.num_heads, self.head_dim)
        q = qkv[:, :, 0].permute(0, 2, 1, 3)  # (B, num_heads, L, head_dim)
        k = qkv[:, :, 1].permute(0, 2, 1, 3)
        v = qkv[:, :, 2].permute(0, 2, 1, 3)

        scale = 1.0 / math.sqrt(self.head_dim)
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * scale
        attn_weights = F.softmax(attn_scores, dim=-1)
        context = torch.matmul(attn_weights, v)  # (B, num_heads, L, head_dim)
        context = context.permute(0, 2, 1, 3).reshape(B, L, self.d_model)
        return self.out_proj(context)


class DynamicTransformerBlock(nn.Module):
    """
    Transformer encoder block with norm-first residual architecture.
    Matches PyTorch TransformerEncoderLayer parameter count exactly.
    """
    def __init__(self, d_model: int = 256, num_heads: int = 8, d_ff: int = 1024, dropout: float = 0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = DynamicMultiheadAttention(d_model, num_heads)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x


class NioMiniDefectForecaster(nn.Module):
    """
    NioMini: Exactly 7,100,000 Parameter AST Diff & Defect Forecasting Transformer.
    Fully supports dynamic batch sizes and dynamic sequence lengths in ONNX.
    """
    def __init__(self, config: NioMiniConfig = None):
        super().__init__()
        if config is None:
            config = NioMiniConfig()
        self.config = config

        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        self.ast_feature_proj = nn.Linear(config.ast_feature_dim, config.d_model)

        self.layers = nn.ModuleList([
            DynamicTransformerBlock(
                d_model=config.d_model,
                num_heads=config.num_heads,
                d_ff=config.d_ff,
                dropout=config.dropout,
            )
            for _ in range(config.num_layers)
        ])
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
        pos_idx = torch.arange(L, device=input_ids.device).unsqueeze(0).expand(B, L)
        x = self.token_embedding(input_ids) + self.pos_embedding(pos_idx)
        if ast_features is not None:
            x = x + self.ast_feature_proj(ast_features)

        for layer in self.layers:
            x = layer(x)

        pooled = self.norm(x[:, 0, :])  # [CLS] representation

        will_break = self.break_head(pooled)
        category_logits = self.category_head(pooled)
        risk_score = self.risk_head(pooled)

        return will_break, category_logits, risk_score
