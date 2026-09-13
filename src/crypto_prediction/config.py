"""
Central configuration v4 - Max Performance + CoinDCX INR + Automation
Improved: more symbols, better model hyperparams, ensemble v4, training v4
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

for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, MODELS_DIR, LOGS_DIR, FRONTEND_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@dataclass
class DataConfig:
    default_symbol: str = "BTC-USD"
    supported_symbols: List[str] = field(default_factory=lambda: [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD", "DOT-USD", "MATIC-USD",
        "LINK-USD", "LTC-USD", "BCH-USD", "UNI-USD", "ETC-USD",
        "BTCINR", "ETHINR", "BNBINR", "SOLINR", "XRPINR"
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
        "MATIC-USD": "MATICUSDT",
        "LINK-USD": "LINKUSDT",
        "LTC-USD": "LTCUSDT",
        "BCH-USD": "BCHUSDT",
        "UNI-USD": "UNIUSDT",
        "ETC-USD": "ETCUSDT",
        "BTCINR": "BTCUSDT",
        "ETHINR": "ETHUSDT",
        "BNBINR": "BNBUSDT",
        "SOLINR": "SOLUSDT",
        "XRPINR": "XRPUSDT",
    })
    coindcx_map: Dict[str, str] = field(default_factory=lambda: {
        "BTC-USD": "BTCINR",
        "ETH-USD": "ETHINR",
        "BNB-USD": "BNBINR",
        "SOL-USD": "SOLINR",
        "XRP-USD": "XRPINR",
        "ADA-USD": "ADAINR",
        "DOGE-USD": "DOGEINR",
        "AVAX-USD": "AVAXINR",
        "DOT-USD": "DOTINR",
        "MATIC-USD": "MATICINR",
        "BTCINR": "BTCINR",
        "ETHINR": "ETHINR",
    })
    interval: str = "1d"
    period: str = "2y"
    test_size: float = 0.12
    val_size: float = 0.13
    sequence_length: int = 60
    prediction_horizon: int = 7
    cache_ttl_hours: int = 24
    use_coindcx_primary_for_inr: bool = True

@dataclass
class FeatureConfig:
    use_technical_indicators: bool = True
    use_price_features: bool = True
    use_volume_features: bool = True
    use_lag_features: bool = True
    use_sentiment: bool = True
    use_advanced_indicators: bool = True
    use_volatility_features: bool = True
    use_market_regime: bool = True
    lag_periods: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 7, 10, 14, 21, 30])
    sma_windows: List[int] = field(default_factory=lambda: [5, 7, 10, 14, 20, 30, 50, 100, 200])
    ema_windows: List[int] = field(default_factory=lambda: [9, 12, 21, 26, 50, 100])
    rsi_window: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_window: int = 20
    bb_std: float = 2.0
    atr_window: int = 14
    adx_window: int = 14
    cci_window: int = 20
    williams_window: int = 14
    mfi_window: int = 14
    # New v4
    use_kalman_filter: bool = True
    use_fourier_features: bool = True
    use_orderbook_features: bool = False

@dataclass
class SentimentConfig:
    enabled: bool = True
    sources: List[str] = field(default_factory=lambda: ["news", "reddit", "twitter", "fear_greed"])
    cryptopanic_key: str = field(default_factory=lambda: os.getenv("CRYPTOPANIC_API_KEY", ""))
    newsapi_key: str = field(default_factory=lambda: os.getenv("NEWSAPI_KEY", ""))
    reddit_client_id: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", ""))
    reddit_secret: str = field(default_factory=lambda: os.getenv("REDDIT_SECRET", ""))
    twitter_bearer: str = field(default_factory=lambda: os.getenv("TWITTER_BEARER_TOKEN", ""))
    use_vader: bool = True
    use_finbert: bool = False
    aggregation: str = "mean"
    cache_hours: int = 2

@dataclass
class RealtimeConfig:
    enabled: bool = True
    exchange: str = "binance"
    ws_url: str = "wss://stream.binance.com:9443/ws"
    rest_url: str = "https://api.binance.com"
    coindcx_rest_url: str = "https://api.coindcx.com"
    buffer_size: int = 1000
    reconnect_interval: int = 5
    use_coindcx_for_inr: bool = True

@dataclass
class ModelConfig:
    # LSTM v4 - Deeper + More attention + Residual + Better regularization
    lstm_hidden_size: int = 320
    lstm_num_layers: int = 4
    lstm_dropout: float = 0.25
    lstm_learning_rate: float = 0.0003
    lstm_epochs: int = 200
    lstm_batch_size: int = 32
    lstm_patience: int = 20
    lstm_bidirectional: bool = True
    lstm_use_attention: bool = True
    lstm_weight_decay: float = 5e-5
    lstm_use_residual: bool = True
    lstm_attention_heads: int = 8
    lstm_use_layer_norm: bool = True

    # Transformer v4 - Larger + More robust
    transformer_d_model: int = 320
    transformer_nhead: int = 8
    transformer_num_layers: int = 6
    transformer_dim_feedforward: int = 640
    transformer_dropout: float = 0.15
    transformer_learning_rate: float = 0.0002
    transformer_epochs: int = 180
    transformer_batch_size: int = 32
    transformer_patience: int = 20
    transformer_use_learnable_pe: bool = True
    transformer_use_attention_pooling: bool = True
    transformer_use_pre_ln: bool = True

    # XGBoost v4 - Heavily tuned
    xgb_n_estimators: int = 1500
    xgb_max_depth: int = 10
    xgb_learning_rate: float = 0.02
    xgb_subsample: float = 0.85
    xgb_colsample_bytree: float = 0.75
    xgb_reg_alpha: float = 0.05
    xgb_reg_lambda: float = 1.5
    xgb_min_child_weight: int = 1
    xgb_gamma: float = 0.05
    xgb_use_gpu: bool = False

    # GRU v4 - New model
    gru_hidden_size: int = 256
    gru_num_layers: int = 3
    gru_dropout: float = 0.25
    gru_learning_rate: float = 0.0004
    gru_epochs: int = 150
    gru_bidirectional: bool = True

    # TCN v5 - Temporal Convolutional Network for temporal patterns
    tcn_channels: List[int] = field(default_factory=lambda: [64, 128, 256])
    tcn_kernel_size: int = 3
    tcn_dropout: float = 0.2
    tcn_learning_rate: float = 0.0003
    tcn_epochs: int = 120
    tcn_batch_size: int = 32
    tcn_patience: int = 20

    # ARIMA v4 - Auto order + SARIMAX
    arima_order: tuple = (5, 1, 3)
    arima_seasonal_order: tuple = (2, 1, 2, 7)
    arima_use_auto: bool = True

    # Ensemble v5 - Advanced weighting + stacking + calibration + TCN
    ensemble_weights: dict = field(default_factory=lambda: {
        "lstm": 0.24,
        "transformer": 0.28,
        "xgboost": 0.18,
        "gru": 0.10,
        "tcn": 0.12,
        "arima": 0.08
    })
    ensemble_use_stacking: bool = True
    ensemble_use_dynamic_weights: bool = True
    ensemble_use_sharpe_weighting: bool = True
    ensemble_meta_learner: str = "ridge"  # ridge, lgbm, xgboost
    ensemble_calibrate_confidence: bool = True
    ensemble_version: str = "v5_max_perf"
    ensemble_use_uncertainty: bool = True
    ensemble_confidence_threshold: float = 0.65

@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_free_rate: float = 0.02
    use_coindcx_fees: bool = True  # 0.2% maker/taker

@dataclass
class TrainingConfig:
    random_state: int = 42
    n_splits: int = 5
    save_models: bool = True
    experiment_name: str = "crypto_pred_v4_max_perf"
    use_robust_scaler: bool = True
    use_log_returns_target: bool = False
    use_feature_selection: bool = True
    feature_selection_k: int = 100
    use_kalman_smoothing: bool = True
    auto_retrain_on_drift: bool = True
    drift_threshold: float = 0.15
    version: str = "v4"

@dataclass
class AutomationConfig:
    enabled: bool = False
    retrain_interval_hours: int = 8
    check_interval_minutes: int = 30
    accuracy_threshold: float = 12.0
    auto_rollback_on_degradation: bool = True
    max_models_per_symbol: int = 5
    use_model_registry: bool = True
    auto_strategy_selection: bool = True
    auto_risk_adjustment: bool = True
    market_regime_detection: bool = True

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_min: int = 120
    use_caching: bool = True
    cache_ttl: int = 30

@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    realtime: RealtimeConfig = field(default_factory=RealtimeConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    api: APIConfig = field(default_factory=APIConfig)
    project_root: Path = PROJECT_ROOT
    version: str = "v5_max_perf_coindcx_tcn"

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
