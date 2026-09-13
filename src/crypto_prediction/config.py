"""
Central configuration for Crypto Prediction core.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure dirs exist
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, MODELS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@dataclass
class DataConfig:
    """Data fetching & preprocessing config"""
    default_symbol: str = "BTC-USD"
    supported_symbols: List[str] = field(default_factory=lambda: [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD", "DOT-USD", "MATIC-USD"
    ])
    interval: str = "1d"  # 1m, 5m, 15m, 1h, 1d
    period: str = "2y"    # 1mo, 6mo, 1y, 2y, 5y, max
    test_size: float = 0.2
    val_size: float = 0.1
    sequence_length: int = 60  # for LSTM
    prediction_horizon: int = 7  # days to predict

@dataclass
class FeatureConfig:
    """Feature engineering config"""
    use_technical_indicators: bool = True
    use_price_features: bool = True
    use_volume_features: bool = True
    use_lag_features: bool = True
    lag_periods: List[int] = field(default_factory=lambda: [1, 3, 7, 14])
    sma_windows: List[int] = field(default_factory=lambda: [7, 14, 30, 50])
    ema_windows: List[int] = field(default_factory=lambda: [12, 26, 50])
    rsi_window: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_window: int = 20
    bb_std: float = 2.0
    atr_window: int = 14

@dataclass
class ModelConfig:
    """Model hyperparameters"""
    # LSTM
    lstm_hidden_size: int = 128
    lstm_num_layers: int = 2
    lstm_dropout: float = 0.2
    lstm_learning_rate: float = 0.001
    lstm_epochs: int = 100
    lstm_batch_size: int = 32
    lstm_patience: int = 10

    # XGBoost
    xgb_n_estimators: int = 500
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.05
    xgb_subsample: float = 0.8
    xgb_colsample_bytree: float = 0.8

    # ARIMA
    arima_order: tuple = (5, 1, 0)

    # Ensemble
    ensemble_weights: dict = field(default_factory=lambda: {
        "lstm": 0.5,
        "xgboost": 0.3,
        "arima": 0.2
    })

@dataclass
class TrainingConfig:
    """Training pipeline config"""
    random_state: int = 42
    n_splits: int = 5  # for time series CV
    save_models: bool = True
    experiment_name: str = "crypto_pred_v1"

@dataclass
class APIConfig:
    """API config"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    project_root: Path = PROJECT_ROOT

# Singleton
_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
