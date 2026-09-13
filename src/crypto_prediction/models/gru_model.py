"""
GRU model v4 Max Performance - Fast + Accurate for crypto
- Bidirectional GRU 3 layers 256 hidden
- Attention pooling + residual
- Huber loss, AdamW, schedulers
"""
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Dict
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
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

class AttentionPooling(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.Tanh(),
            nn.Linear(hidden_size // 2, 1)
        )
    def forward(self, x):
        attn_weights = self.attention(x)
        attn_weights = torch.softmax(attn_weights, dim=1)
        pooled = torch.sum(x * attn_weights, dim=1)
        return pooled, attn_weights

class ResidualBlock(nn.Module):
    def __init__(self, hidden_size, dropout=0.25):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size)
        self.ln1 = nn.LayerNorm(hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
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

class GRUNetworkV4(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 256, num_layers: int = 3, 
                 dropout: float = 0.25, output_size: int = 1, bidirectional: bool = True):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        gru_output_size = hidden_size * 2 if bidirectional else hidden_size
        
        self.attention_pool = AttentionPooling(gru_output_size)
        self.layer_norm = nn.LayerNorm(gru_output_size)
        self.dropout = nn.Dropout(dropout)
        
        self.fc_input = nn.Sequential(
            nn.Linear(gru_output_size * 2, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        self.res_blocks = nn.Sequential(
            ResidualBlock(256, dropout=dropout),
            ResidualBlock(256, dropout=dropout)
        )
        
        self.fc_layers = nn.Sequential(
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.GELU(),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        batch_size = x.size(0)
        num_directions = 2 if self.bidirectional else 1
        h0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size, device=x.device)
        
        gru_out, _ = self.gru(x, h0)
        gru_out = self.layer_norm(gru_out)
        
        last_out = gru_out[:, -1, :]
        pooled_out, _ = self.attention_pool(gru_out)
        
        combined = torch.cat([last_out, pooled_out], dim=1)
        combined = self.dropout(combined)
        
        out = self.fc_input(combined)
        out = self.res_blocks(out)
        out = self.fc_layers(out)
        return out.squeeze()

class GRUModel(BaseModel):
    def __init__(self, input_size: int, hidden_size: int = None, num_layers: int = None, 
                 dropout: float = None, learning_rate: float = None, device: str = None,
                 bidirectional: bool = None):
        super().__init__(name="gru")
        self.input_size = input_size
        self.hidden_size = hidden_size or config.model.gru_hidden_size
        self.num_layers = num_layers or config.model.gru_num_layers
        self.dropout = dropout or config.model.gru_dropout
        self.lr = learning_rate or config.model.gru_learning_rate
        self.bidirectional = bidirectional if bidirectional is not None else config.model.gru_bidirectional
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.network = GRUNetworkV4(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            bidirectional=self.bidirectional
        ).to(self.device)
        
        self.criterion = nn.HuberLoss(delta=1.0)
        self.optimizer = torch.optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=5e-5)
        self.scheduler_plateau = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=7, factor=0.5, min_lr=1e-7)
        self.scheduler_cosine = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=15, T_mult=2, eta_min=1e-7)
        
        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None,
            epochs: int = None, batch_size: int = 32, patience: int = 20, verbose: bool = True, **kwargs) -> Dict:
        
        epochs = epochs or config.model.gru_epochs
        train_ds = CryptoDatasetTorch(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
        
        val_loader = None
        if X_val is not None and y_val is not None:
            val_ds = CryptoDatasetTorch(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size, num_workers=0)

        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None

        logger.info(f"Training GRU v4 MAX on {self.device} | in={self.input_size} h={self.hidden_size} L={self.num_layers} bidir={self.bidirectional} | epochs={epochs}")

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
                    logger.info(f"GRU v4 Epoch {epoch+1}/{epochs} | train={train_loss:.6f} val={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.7f}")

                if patience_counter >= patience:
                    logger.info(f"GRU v4 Early stopping at {epoch+1}")
                    break
            else:
                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"GRU v4 Epoch {epoch+1}/{epochs} | train={train_loss:.6f}")

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
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self.network.state_dict(),
            'config': {
                'input_size': self.input_size,
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers,
                'dropout': self.dropout,
                'bidirectional': self.bidirectional
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'version': 'v4_max'
        }, path)
        logger.info(f"Saved GRU v4 MAX torch model to {path}")

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
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded GRU v4 MAX torch model from {path}")
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

GRUNetworkV3 = GRUNetworkV4
GRUNetwork = GRUNetworkV4
