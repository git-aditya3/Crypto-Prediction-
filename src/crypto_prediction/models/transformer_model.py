"""
Transformer model v4 Max Performance - TFT-inspired + Deeper + Pre-LN
- 320 d_model, 8 heads, 6 layers
- Learnable PE + Fourier features
- Attention pooling + mean + last fusion
- Pre-LN, GELU, deeper decoder with residual
- Huber loss, AdamW, Cosine + Plateau
"""
import math
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Dict

from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class PositionalEncodingV4(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.15, learnable: bool = True):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.learnable = learnable
        
        if learnable:
            self.pe = nn.Parameter(torch.zeros(1, max_len, d_model))
            nn.init.trunc_normal_(self.pe, std=0.02)
            # Also learnable scaling
            self.alpha = nn.Parameter(torch.ones(1))
        else:
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            pe = pe.unsqueeze(0)
            self.register_buffer('pe', pe)
            self.alpha = 1.0

    def forward(self, x):
        if self.learnable:
            x = x + self.alpha * self.pe[:, :x.size(1), :]
        else:
            x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class AttentionPoolingV4(nn.Module):
    def __init__(self, d_model):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.LayerNorm(d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, 1)
        )
        self.norm = nn.LayerNorm(d_model)
    
    def forward(self, x):
        attn_weights = self.attention(x)
        attn_weights = torch.softmax(attn_weights, dim=1)
        pooled = torch.sum(x * attn_weights, dim=1)
        pooled = self.norm(pooled)
        return pooled, attn_weights

class ResidualBlockV4(nn.Module):
    def __init__(self, dim, dropout=0.15):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.ln1 = nn.LayerNorm(dim)
        self.fc2 = nn.Linear(dim, dim)
        self.ln2 = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()
        
    def forward(self, x):
        residual = x
        out = self.fc1(x)
        out = self.ln1(out)
        out = self.activation(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.ln2(out)
        out = self.dropout(out)
        out = out + residual
        out = self.activation(out)
        return out

class CryptoDatasetTorch(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

class TransformerNetworkV4(nn.Module):
    def __init__(self, input_size: int, d_model: int = 320, nhead: int = 8, num_layers: int = 6,
                 dim_feedforward: int = 640, dropout: float = 0.15, output_size: int = 1,
                 use_learnable_pe: bool = True, use_attention_pooling: bool = True, use_pre_ln: bool = True):
        super().__init__()
        self.d_model = d_model
        self.use_attention_pooling = use_attention_pooling
        
        self.input_projection = nn.Sequential(
            nn.Linear(input_size, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        self.pos_encoder = PositionalEncodingV4(d_model, dropout=dropout, learnable=use_learnable_pe)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=use_pre_ln
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.layer_norm = nn.LayerNorm(d_model)
        
        if use_attention_pooling:
            self.pooling = AttentionPoolingV4(d_model)
        else:
            self.pooling = None
        
        # Fusion of last + mean + pooled
        self.fusion = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        self.decoder_blocks = nn.Sequential(
            ResidualBlockV4(d_model, dropout=dropout),
            ResidualBlockV4(d_model, dropout=dropout)
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        x_proj = self.input_projection(x)
        x_pe = self.pos_encoder(x_proj)
        x_enc = self.transformer_encoder(x_pe)
        x_norm = self.layer_norm(x_enc)
        
        last_token = x_norm[:, -1, :]
        mean_token = torch.mean(x_norm, dim=1)
        
        if self.pooling is not None:
            pooled_token, _ = self.pooling(x_norm)
            fused = torch.cat([last_token, mean_token, pooled_token], dim=1)
        else:
            # If no pooling, duplicate mean for fusion
            fused = torch.cat([last_token, mean_token, mean_token], dim=1)
        
        fused = self.fusion(fused)
        fused = self.decoder_blocks(fused)
        out = self.decoder(fused)
        return out.squeeze()

class TransformerModel(BaseModel):
    def __init__(self, input_size: int, d_model: int = None, nhead: int = None, num_layers: int = None,
                 dim_feedforward: int = None, dropout: float = None, learning_rate: float = None, 
                 device: str = None, use_learnable_pe: bool = None, use_attention_pooling: bool = None, use_pre_ln: bool = None):
        super().__init__(name="transformer")
        self.input_size = input_size
        self.d_model = d_model or config.model.transformer_d_model
        self.nhead = nhead or config.model.transformer_nhead
        self.num_layers = num_layers or config.model.transformer_num_layers
        self.dim_feedforward = dim_feedforward or config.model.transformer_dim_feedforward
        self.dropout = dropout or config.model.transformer_dropout
        self.lr = learning_rate or config.model.transformer_learning_rate
        self.use_learnable_pe = use_learnable_pe if use_learnable_pe is not None else config.model.transformer_use_learnable_pe
        self.use_attention_pooling = use_attention_pooling if use_attention_pooling is not None else config.model.transformer_use_attention_pooling
        self.use_pre_ln = use_pre_ln if use_pre_ln is not None else config.model.transformer_use_pre_ln
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.network = TransformerNetworkV4(
            input_size=input_size,
            d_model=self.d_model,
            nhead=self.nhead,
            num_layers=self.num_layers,
            dim_feedforward=self.dim_feedforward,
            dropout=self.dropout,
            use_learnable_pe=self.use_learnable_pe,
            use_attention_pooling=self.use_attention_pooling,
            use_pre_ln=self.use_pre_ln
        ).to(self.device)

        self.criterion = nn.HuberLoss(delta=1.0)
        self.optimizer = torch.optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=1e-4, betas=(0.9, 0.999))
        self.scheduler_plateau = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=7, factor=0.5, min_lr=1e-7)
        self.scheduler_cosine = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=20, T_mult=2, eta_min=1e-7)

        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None,
            epochs: int = None, batch_size: int = None, patience: int = None, verbose: bool = True, **kwargs) -> Dict:

        epochs = epochs or config.model.transformer_epochs
        batch_size = batch_size or config.model.transformer_batch_size
        patience = patience or config.model.transformer_patience

        train_ds = CryptoDatasetTorch(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)

        val_loader = None
        if X_val is not None and y_val is not None:
            val_ds = CryptoDatasetTorch(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size, num_workers=0)

        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None

        logger.info(f"Training Transformer v4 MAX on {self.device} | d_model={self.d_model} nhead={self.nhead} L={self.num_layers} ff={self.dim_feedforward} learnable_pe={self.use_learnable_pe} pool={self.use_attention_pooling} pre_ln={self.use_pre_ln} | epochs={epochs}")

        for epoch in range(epochs):
            self.network.train()
            train_loss = 0.0
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                self.optimizer.zero_grad()
                outputs = self.network(X_batch)
                loss = self.criterion(outputs, y_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.network.parameters(), 1.0)
                self.optimizer.step()
                train_loss += loss.item()

            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)
            self.scheduler_cosine.step()

            val_loss = None
            if val_loader:
                self.network.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for X_batch, y_batch in val_loader:
                        X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                        outputs = self.network(X_batch)
                        loss = self.criterion(outputs, y_batch)
                        val_loss += loss.item()
                val_loss /= len(val_loader)
                self.val_losses.append(val_loss)
                self.scheduler_plateau.step(val_loss)

                if val_loss < best_val_loss - 1e-6:
                    best_val_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in self.network.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1

                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"Transformer v4 Epoch {epoch+1}/{epochs} | train={train_loss:.6f} val={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.7f} best={best_val_loss:.6f}")

                if patience_counter >= patience:
                    logger.info(f"Transformer v4 Early stopping at epoch {epoch+1} | best_val={best_val_loss:.6f}")
                    break
            else:
                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"Transformer v4 Epoch {epoch+1}/{epochs} | train={train_loss:.6f}")

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.is_fitted = True
        return {"train_losses": self.train_losses, "val_losses": self.val_losses, "best_val_loss": best_val_loss, "version": "v4_max"}

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.network.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            preds = self.network(X_tensor)
            return preds.cpu().numpy()

    def save_torch(self, path: str):
        from pathlib import Path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self.network.state_dict(),
            'config': {
                'input_size': self.input_size,
                'd_model': self.d_model,
                'nhead': self.nhead,
                'num_layers': self.num_layers,
                'dim_feedforward': self.dim_feedforward,
                'dropout': self.dropout,
                'use_learnable_pe': self.use_learnable_pe,
                'use_attention_pooling': self.use_attention_pooling,
                'use_pre_ln': self.use_pre_ln
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'version': 'v4_max'
        }, path)
        logger.info(f"Saved Transformer v4 MAX torch model to {path}")

    @classmethod
    def load_torch(cls, path: str, device: str = None):
        checkpoint = torch.load(path, map_location=device or "cpu")
        cfg = checkpoint['config']
        model = cls(
            input_size=cfg['input_size'],
            d_model=cfg['d_model'],
            nhead=cfg['nhead'],
            num_layers=cfg['num_layers'],
            dim_feedforward=cfg['dim_feedforward'],
            dropout=cfg['dropout'],
            use_learnable_pe=cfg.get('use_learnable_pe', True),
            use_attention_pooling=cfg.get('use_attention_pooling', True),
            use_pre_ln=cfg.get('use_pre_ln', True),
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded Transformer v4 MAX torch model from {path}")
        return model

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7) -> np.ndarray:
        self.network.eval()
        seq = last_sequence.copy()
        preds = []
        with torch.no_grad():
            for _ in range(steps):
                X_input = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
                pred = self.network(X_input).cpu().numpy()
                preds.append(pred)
                next_row = seq[-1].copy()
                seq = np.vstack([seq[1:], next_row.reshape(1, -1)])
        return np.array(preds).ravel()

    def get_attention_weights(self, X: np.ndarray):
        return None

TransformerNetworkV3 = TransformerNetworkV4
TransformerNetwork = TransformerNetworkV4
PositionalEncoding = PositionalEncodingV4
