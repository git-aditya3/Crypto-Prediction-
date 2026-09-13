"""
Transformer model for crypto prediction - TFT-inspired
Uses multi-head self-attention over time series sequences
"""
import math
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Dict, Optional

from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class CryptoDatasetTorch(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

class TransformerNetwork(nn.Module):
    def __init__(self, input_size: int, d_model: int = 128, nhead: int = 4, num_layers: int = 2,
                 dim_feedforward: int = 256, dropout: float = 0.1, output_size: int = 1):
        super().__init__()
        self.d_model = d_model
        self.input_projection = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.decoder = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        # x: (batch, seq_len, input_size)
        x = self.input_projection(x)  # (batch, seq_len, d_model)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)  # (batch, seq_len, d_model)
        x = x[:, -1, :]  # last token
        x = self.decoder(x)
        return x.squeeze()

class TransformerModel(BaseModel):
    def __init__(self, input_size: int, d_model: int = None, nhead: int = None, num_layers: int = None,
                 dim_feedforward: int = None, dropout: float = None, learning_rate: float = None, device: str = None):
        super().__init__(name="transformer")
        self.input_size = input_size
        self.d_model = d_model or config.model.transformer_d_model
        self.nhead = nhead or config.model.transformer_nhead
        self.num_layers = num_layers or config.model.transformer_num_layers
        self.dim_feedforward = dim_feedforward or config.model.transformer_dim_feedforward
        self.dropout = dropout or config.model.transformer_dropout
        self.lr = learning_rate or config.model.transformer_learning_rate
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.network = TransformerNetwork(
            input_size=input_size,
            d_model=self.d_model,
            nhead=self.nhead,
            num_layers=self.num_layers,
            dim_feedforward=self.dim_feedforward,
            dropout=self.dropout
        ).to(self.device)

        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=self.lr, weight_decay=1e-5)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=5, factor=0.5)

        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None,
            epochs: int = None, batch_size: int = None, patience: int = None, verbose: bool = True, **kwargs) -> Dict:

        epochs = epochs or config.model.transformer_epochs
        batch_size = batch_size or config.model.transformer_batch_size
        patience = patience or config.model.transformer_patience

        train_ds = CryptoDatasetTorch(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

        val_loader = None
        if X_val is not None and y_val is not None:
            val_ds = CryptoDatasetTorch(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size)

        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None

        logger.info(f"Training Transformer on {self.device} | d_model={self.d_model} nhead={self.nhead} layers={self.num_layers} | epochs={epochs}")

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

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = self.network.state_dict().copy()
                    patience_counter = 0
                else:
                    patience_counter += 1

                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} | train={train_loss:.6f} val={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.6f}")

                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
            else:
                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} | train={train_loss:.6f}")

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.is_fitted = True
        return {"train_losses": self.train_losses, "val_losses": self.val_losses, "best_val_loss": best_val_loss}

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
                'dropout': self.dropout
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, path)
        logger.info(f"Saved Transformer torch model to {path}")

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
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded Transformer torch model from {path}")
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
        """Extract attention weights for interpretability - simplified"""
        # For true TFT, you'd need to expose attention layers
        # Here we return dummy for API compatibility
        return None
