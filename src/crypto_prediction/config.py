"""
Central configuration for Crypto Prediction core - Extended v2
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Ensure dirs exist
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, MODELS_DIR, LOGS_DIR, FRONTEND_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@dataclass
class DataConfig:
    default_symbol: str = "BTC-USD"
    supported_symbols: List[str] = field(default_factory=lambda: [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD", "DOT-USD", "MATIC-USD"
    ])
    binance_map: Dict[str, str] = field(default_factory=lambda: {
        "BTC-USD": "BTCUSDT",
        "ETH-USD": "ETHUSDT",
        "BNB-USD": "BNBUSDT",
        "SOL-USD": "SOLUSDT",
        "XRP-USD": "XRPUSDT",
        "ADA-USD": "ADAUSDT",
        "DOGE-USD": "DOGEUSDT",
        "AVAX-USD": "AVAXUSDT",
        "DOT-USD": "DOTUSDT",
        "MATIC-USD": "MATICUSDT"
    })
    interval: str = "1d"
    period: str = "2y"
    test_size: float = 0.2
    val_size: float = 0.1
    sequence_length: int = 60
    prediction_horizon: int = 7

@dataclass
class FeatureConfig:
    use_technical_indicators: bool = True
    use_price_features: bool = True
    use_volume_features: bool = True
    use_lag_features: bool = True
    use_sentiment: bool = True
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
class SentimentConfig:
    enabled: bool = True
    sources: List[str] = field(default_factory=lambda: ["news", "reddit", "twitter"])
    # API keys from env
    cryptopanic_key: str = field(default_factory=lambda: os.getenv("CRYPTOPANIC_API_KEY", ""))
    newsapi_key: str = field(default_factory=lambda: os.getenv("NEWSAPI_KEY", ""))
    reddit_client_id: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", ""))
    reddit_secret: str = field(default_factory=lambda: os.getenv("REDDIT_SECRET", ""))
    twitter_bearer: str = field(default_factory=lambda: os.getenv("TWITTER_BEARER_TOKEN", ""))
    # Fallback lexicon weights
    use_vader: bool = True
    use_finbert: bool = False  # requires transformers torch
    aggregation: str = "mean"  # mean, weighted
    cache_hours: int = 4

@dataclass
class RealtimeConfig:
    enabled: bool = True
    exchange: str = "binance"
    ws_url: str = "wss://stream.binance.com:9443/ws"
    rest_url: str = "https://api.binance.com"
    buffer_size: int = 1000
    reconnect_interval: int = 5

@dataclass
class ModelConfig:
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

    # Transformer (TFT-inspired)
    transformer_d_model: int = 128
    transformer_nhead: int = 4
    transformer_num_layers: int = 2
    transformer_dim_feedforward: int = 256
    transformer_dropout: float = 0.1
    transformer_learning_rate: float = 0.0005
    transformer_epochs: int = 80
    transformer_batch_size: int = 32
    transformer_patience: int = 12

    # Ensemble
    ensemble_weights: dict = field(default_factory=lambda: {
        "lstm": 0.35,
        "transformer": 0.35,
        "xgboost": 0.2,
        "arima": 0.1
    })

@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005
    risk_free_rate: float = 0.02

@dataclass
class TrainingConfig:
    random_state: int = 42
    n_splits: int = 5
    save_models: bool = True
    experiment_name: str = "crypto_pred_v2"

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    realtime: RealtimeConfig = field(default_factory=RealtimeConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    project_root: Path = PROJECT_ROOT

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
