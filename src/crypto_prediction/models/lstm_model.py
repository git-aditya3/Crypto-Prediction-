"""
LSTM model v3 Improved Accuracy
- Bidirectional LSTM
- Attention mechanism
- LayerNorm, Residual, Deeper network
- Huber loss, AdamW, Cosine scheduler
"""
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional, Dict
import os
from pathlib import Path

from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CryptoDatasetTorch(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class AttentionLayer(nn.Module):
    """Self-attention over LSTM outputs"""
    def __init__(self, hidden_size):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, batch_first=True)
        self.norm = nn.LayerNorm(hidden_size)
        
    def forward(self, lstm_out):
        # lstm_out: (batch, seq_len, hidden)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        # Residual + Norm
        out = self.norm(lstm_out + attn_out)
        return out

class LSTMNetworkV3(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 256, num_layers: int = 3, 
                 dropout: float = 0.3, output_size: int = 1, bidirectional: bool = True,
                 use_attention: bool = True):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.use_attention = use_attention
        
        lstm_hidden = hidden_size
        # Bidirectional doubles hidden
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=lstm_hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        lstm_output_size = hidden_size * 2 if bidirectional else hidden_size
        
        self.attention = AttentionLayer(lstm_output_size) if use_attention else None
        
        self.layer_norm1 = nn.LayerNorm(lstm_output_size)
        self.dropout = nn.Dropout(dropout)
        
        # Deeper FC with residual
        self.fc_layers = nn.Sequential(
            nn.Linear(lstm_output_size, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )
        
        # Residual projection if needed
        self.residual_proj = nn.Linear(lstm_output_size, 32) if lstm_output_size != 32 else None

    def forward(self, x):
        # x: (batch, seq_len, input_size)
        batch_size = x.size(0)
        num_directions = 2 if self.bidirectional else 1
        
        h0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        
        lstm_out, _ = self.lstm(x, (h0, c0))  # (batch, seq_len, hidden*dir)
        
        if self.use_attention and self.attention is not None:
            lstm_out = self.attention(lstm_out)
        
        lstm_out = self.layer_norm1(lstm_out)
        
        # Use last time step + attention pooling for better representation
        last_out = lstm_out[:, -1, :]  # (batch, hidden)
        
        # Also compute mean pooling as additional signal
        mean_out = torch.mean(lstm_out, dim=1)  # (batch, hidden)
        
        # Combine last + mean
        combined = (last_out + mean_out) / 2
        
        combined = self.dropout(combined)
        out = self.fc_layers(combined)
        return out.squeeze()

class LSTMModel(BaseModel):
    def __init__(self, input_size: int, hidden_size: int = None, num_layers: int = None, dropout: float = None, 
                 learning_rate: float = None, device: str = None, bidirectional: bool = None, use_attention: bool = None):
        super().__init__(name="lstm")
        self.input_size = input_size
        self.hidden_size = hidden_size or config.model.lstm_hidden_size
        self.num_layers = num_layers or config.model.lstm_num_layers
        self.dropout = dropout or config.model.lstm_dropout
        self.lr = learning_rate or config.model.lstm_learning_rate
        self.bidirectional = bidirectional if bidirectional is not None else config.model.lstm_bidirectional
        self.use_attention = use_attention if use_attention is not None else config.model.lstm_use_attention
        self.weight_decay = config.model.lstm_weight_decay
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.network = LSTMNetworkV3(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            bidirectional=self.bidirectional,
            use_attention=self.use_attention
        ).to(self.device)
        
        # Huber loss for robustness to outliers (better for crypto)
        self.criterion = nn.HuberLoss(delta=1.0)
        # AdamW with weight decay for better generalization
        self.optimizer = torch.optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        # Cosine annealing + ReduceLROnPlateau combo
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=5, factor=0.5, min_lr=1e-6)
        self.cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=10, T_mult=2)
        
        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None,
            epochs: int = None, batch_size: int = None, patience: int = None, verbose: bool = True, **kwargs) -> Dict:
        
        epochs = epochs or config.model.lstm_epochs
        batch_size = batch_size or config.model.lstm_batch_size
        patience = patience or config.model.lstm_patience

        train_ds = CryptoDatasetTorch(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

        val_loader = None
        if X_val is not None and y_val is not None:
            val_ds = CryptoDatasetTorch(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size)

        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None

        logger.info(f"Training LSTM v3 on {self.device} | input={self.input_size} hidden={self.hidden_size} layers={self.num_layers} bidir={self.bidirectional} attn={self.use_attention} | epochs={epochs}")

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
                self.scheduler.step(val_loss)
                # self.cosine_scheduler.step()

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in self.network.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1

                if verbose and (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} | train_loss={train_loss:.6f} val_loss={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.6f}")

                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1} | best_val={best_val_loss:.6f}")
                    break
            else:
                if verbose and (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} | train_loss={train_loss:.6f}")

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.is_fitted = True
        return {"train_losses": self.train_losses, "val_losses": self.val_losses, "best_val_loss": best_val_loss}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            logger.warning("LSTM model not fitted, but predicting anyway")
        self.network.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            preds = self.network(X_tensor)
            return preds.cpu().numpy()

    def save_torch(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self.network.state_dict(),
            'config': {
                'input_size': self.input_size,
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers,
                'dropout': self.dropout,
                'bidirectional': self.bidirectional,
                'use_attention': self.use_attention
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, path)
        logger.info(f"Saved LSTM v3 torch model to {path}")

    @classmethod
    def load_torch(cls, path: str, device: str = None):
        checkpoint = torch.load(path, map_location=device or "cpu")
        cfg = checkpoint['config']
        model = cls(
            input_size=cfg['input_size'],
            hidden_size=cfg['hidden_size'],
            num_layers=cfg['num_layers'],
            dropout=cfg['dropout'],
            bidirectional=cfg.get('bidirectional', True),
            use_attention=cfg.get('use_attention', True),
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded LSTM v3 torch model from {path}")
        return model

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7, preprocessor=None) -> np.ndarray:
        self.network.eval()
        seq = last_sequence.copy()
        preds_scaled = []

        with torch.no_grad():
            for _ in range(steps):
                X_input = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
                pred = self.network(X_input).cpu().numpy()
                preds_scaled.append(pred)
                next_row = seq[-1].copy()
                seq = np.vstack([seq[1:], next_row.reshape(1, -1)])

        return np.array(preds_scaled).ravel()

# Keep old name for backward compat
LSTMNetwork = LSTMNetworkV3
