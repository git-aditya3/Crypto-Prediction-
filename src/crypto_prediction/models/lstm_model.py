"""
LSTM model using PyTorch for crypto price prediction
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

class LSTMNetwork(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, dropout: float = 0.2, output_size: int = 1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.dropout = nn.Dropout(dropout)
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        # x: (batch, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))  # out: (batch, seq_len, hidden)
        out = out[:, -1, :]  # last time step
        out = self.dropout(out)
        out = self.fc_layers(out)
        return out.squeeze()

class LSTMModel(BaseModel):
    def __init__(self, input_size: int, hidden_size: int = None, num_layers: int = None, dropout: float = None, 
                 learning_rate: float = None, device: str = None):
        super().__init__(name="lstm")
        self.input_size = input_size
        self.hidden_size = hidden_size or config.model.lstm_hidden_size
        self.num_layers = num_layers or config.model.lstm_num_layers
        self.dropout = dropout or config.model.lstm_dropout
        self.lr = learning_rate or config.model.lstm_learning_rate
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.network = LSTMNetwork(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=self.lr)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=5, factor=0.5)
        
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

        logger.info(f"Training LSTM on {self.device} | input_size={self.input_size} hidden={self.hidden_size} | epochs={epochs}")

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

                if verbose and (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} | train_loss={train_loss:.6f} val_loss={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.6f}")

                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
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
                'dropout': self.dropout
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, path)
        logger.info(f"Saved LSTM torch model to {path}")

    @classmethod
    def load_torch(cls, path: str, device: str = None):
        checkpoint = torch.load(path, map_location=device or "cpu")
        cfg = checkpoint['config']
        model = cls(
            input_size=cfg['input_size'],
            hidden_size=cfg['hidden_size'],
            num_layers=cfg['num_layers'],
            dropout=cfg['dropout'],
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded LSTM torch model from {path}")
        return model

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7, preprocessor=None) -> np.ndarray:
        """
        last_sequence: (seq_len, n_features) scaled
        Autoregressively predict future scaled targets, then inverse if preprocessor provided externally
        Returns scaled predictions
        """
        self.network.eval()
        seq = last_sequence.copy()  # (seq_len, n_features)
        preds_scaled = []

        with torch.no_grad():
            for _ in range(steps):
                X_input = torch.FloatTensor(seq).unsqueeze(0).to(self.device)  # (1, seq_len, features)
                pred = self.network(X_input).cpu().numpy()  # scalar scaled target
                preds_scaled.append(pred)

                # For autoregressive, we need to create next feature vector.
                # Simplification: repeat last feature vector but replace? 
                # Better: shift sequence and append last features (approx)
                # Since we don't have true future features, we use last feature row as proxy
                # In production, you'd re-engineer features iteratively
                next_row = seq[-1].copy()
                # We don't know exact mapping, so keep as is - model will still trend
                seq = np.vstack([seq[1:], next_row.reshape(1, -1)])

        return np.array(preds_scaled).ravel()
