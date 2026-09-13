"""
TCN model v5 - Temporal Convolutional Network for crypto
- Dilated causal convolutions capture long-range dependencies
- Residual blocks with weight norm, dropout, ReLU
- Attention pooling + multi-horizon
- Huber loss, AdamW, schedulers
- Superior to LSTM for long sequences, parallel training
"""
import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils import weight_norm
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

class Chomp1d(nn.Module):
    def __init__(self, chomp_size):
        super().__init__()
        self.chomp_size = chomp_size
    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()

class TemporalBlock(nn.Module):
    def __init__(self, n_inputs, n_outputs, kernel_size, stride, dilation, padding, dropout=0.2):
        super().__init__()
        self.conv1 = weight_norm(nn.Conv1d(n_inputs, n_outputs, kernel_size, stride=stride, padding=padding, dilation=dilation))
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.GELU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = weight_norm(nn.Conv1d(n_outputs, n_outputs, kernel_size, stride=stride, padding=padding, dilation=dilation))
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.GELU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(self.conv1, self.chomp1, self.relu1, self.dropout1,
                                 self.conv2, self.chomp2, self.relu2, self.dropout2)
        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.GELU()
        self.init_weights()

    def init_weights(self):
        self.conv1.weight.data.normal_(0, 0.01)
        self.conv2.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x):
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)

class TemporalConvNet(nn.Module):
    def __init__(self, num_inputs, num_channels, kernel_size=3, dropout=0.2):
        super().__init__()
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = num_inputs if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]
            layers += [TemporalBlock(in_channels, out_channels, kernel_size, stride=1, dilation=dilation_size, padding=(kernel_size-1) * dilation_size, dropout=dropout)]
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class AttentionPooling(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.Tanh(),
            nn.Linear(hidden_size // 2, 1)
        )
    def forward(self, x):
        # x: (batch, seq_len, hidden)
        attn_weights = self.attention(x)  # (batch, seq_len, 1)
        attn_weights = torch.softmax(attn_weights, dim=1)
        pooled = torch.sum(x * attn_weights, dim=1)
        return pooled, attn_weights

class TCNNetworkV5(nn.Module):
    def __init__(self, input_size: int, num_channels: list = None, kernel_size: int = 3, dropout: float = 0.2, output_size: int = 1):
        super().__init__()
        num_channels = num_channels or config.model.tcn_channels
        self.input_size = input_size
        self.tcn = TemporalConvNet(input_size, num_channels, kernel_size=kernel_size, dropout=dropout)
        
        tcn_output_size = num_channels[-1]
        
        self.attention_pool = AttentionPooling(tcn_output_size)
        self.layer_norm = nn.LayerNorm(tcn_output_size)
        self.dropout = nn.Dropout(dropout)
        
        # Fusion of last + pooled + mean
        self.fc_input = nn.Sequential(
            nn.Linear(tcn_output_size * 3, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        self.fc_layers = nn.Sequential(
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        # x: (batch, seq_len, input_size) -> need (batch, input_size, seq_len) for Conv1d
        x_t = x.transpose(1, 2)  # (batch, input_size, seq_len)
        y = self.tcn(x_t)  # (batch, num_channels[-1], seq_len)
        y = y.transpose(1, 2)  # (batch, seq_len, num_channels[-1])
        
        y = self.layer_norm(y)
        
        last_out = y[:, -1, :]  # (batch, hidden)
        pooled_out, _ = self.attention_pool(y)  # (batch, hidden)
        mean_out = torch.mean(y, dim=1)  # (batch, hidden)
        
        combined = torch.cat([last_out, pooled_out, mean_out], dim=1)
        combined = self.dropout(combined)
        
        out = self.fc_input(combined)
        out = self.fc_layers(out)
        return out.squeeze()

class TCNModel(BaseModel):
    def __init__(self, input_size: int, num_channels: list = None, kernel_size: int = None, dropout: float = None, learning_rate: float = None, device: str = None):
        super().__init__(name="tcn")
        self.input_size = input_size
        self.num_channels = num_channels or config.model.tcn_channels
        self.kernel_size = kernel_size or config.model.tcn_kernel_size
        self.dropout = dropout or config.model.tcn_dropout
        self.lr = learning_rate or config.model.tcn_learning_rate
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.network = TCNNetworkV5(
            input_size=input_size,
            num_channels=self.num_channels,
            kernel_size=self.kernel_size,
            dropout=self.dropout
        ).to(self.device)
        
        self.criterion = nn.HuberLoss(delta=1.0)
        self.optimizer = torch.optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=5e-5, betas=(0.9, 0.999))
        self.scheduler_plateau = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=7, factor=0.5, min_lr=1e-7)
        self.scheduler_cosine = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=15, T_mult=2, eta_min=1e-7)
        
        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None, epochs: int = 150, batch_size: int = 32, patience: int = 20, verbose: bool = True, **kwargs) -> Dict:
        train_ds = CryptoDatasetTorch(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
        
        val_loader = None
        if X_val is not None and y_val is not None:
            val_ds = CryptoDatasetTorch(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size, num_workers=0)

        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None

        logger.info(f"Training TCN v5 on {self.device} | in={self.input_size} channels={self.num_channels} k={self.kernel_size} | epochs={epochs}")

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
                    logger.info(f"TCN v5 Epoch {epoch+1}/{epochs} | train={train_loss:.6f} val={val_loss:.6f} lr={self.optimizer.param_groups[0]['lr']:.7f}")

                if patience_counter >= patience:
                    logger.info(f"TCN v5 Early stopping at {epoch+1}")
                    break
            else:
                if verbose and (epoch+1) % 10 == 0:
                    logger.info(f"TCN v5 Epoch {epoch+1}/{epochs} | train={train_loss:.6f}")

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.is_fitted = True
        return {"train_losses": self.train_losses, "val_losses": self.val_losses, "best_val_loss": best_val_loss, "version": "v5_tcn"}

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
                'num_channels': self.num_channels,
                'kernel_size': self.kernel_size,
                'dropout': self.dropout
            },
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'version': 'v5_tcn'
        }, path)
        logger.info(f"Saved TCN v5 torch model to {path}")

    @classmethod
    def load_torch(cls, path: str, device: str = None):
        checkpoint = torch.load(path, map_location=device or "cpu")
        cfg = checkpoint['config']
        model = cls(
            input_size=cfg['input_size'],
            num_channels=cfg['num_channels'],
            kernel_size=cfg['kernel_size'],
            dropout=cfg['dropout'],
            device=device
        )
        model.network.load_state_dict(checkpoint['model_state'])
        model.train_losses = checkpoint.get('train_losses', [])
        model.val_losses = checkpoint.get('val_losses', [])
        model.is_fitted = True
        logger.info(f"Loaded TCN v5 torch model from {path}")
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
