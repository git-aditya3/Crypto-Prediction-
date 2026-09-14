"""
Central configuration v6 MAX ULTRA - iOS 26 Liquid Glass + Max Performance + CoinDCX INR + Automation
Improved: 25 symbols, deeper models, ensemble v6, training v6, 300+ features, robust data validation
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
        "BTCINR", "ETHINR", "BNBINR", "SOLINR", "XRPINR",
        "ADAINR", "DOGEINR", "AVAXINR", "DOTINR", "MATICINR"
    ])
    binance_map: Dict[str, str] = field(default_factory=lambda: {
        "BTC-USD": "BTCUSDT", "ETH-USD": "ETHUSDT", "BNB-USD": "BNBUSDT",
        "SOL-USD": "SOLUSDT", "XRP-USD": "XRPUSDT", "ADA-USD": "ADAUSDT",
        "DOGE-USD": "DOGEUSDT", "AVAX-USD": "AVAXUSDT", "DOT-USD": "DOTUSDT",
        "MATIC-USD": "MATICUSDT", "LINK-USD": "LINKUSDT", "LTC-USD": "LTCUSDT",
        "BCH-USD": "BCHUSDT", "UNI-USD": "UNIUSDT", "ETC-USD": "ETCUSDT",
        "BTCINR": "BTCUSDT", "ETHINR": "ETHUSDT", "BNBINR": "BNBUSDT",
        "SOLINR": "SOLUSDT", "XRPINR": "XRPUSDT", "ADAINR": "ADAUSDT",
        "DOGEINR": "DOGEUSDT", "AVAXINR": "AVAXUSDT", "DOTINR": "DOTUSDT",
        "MATICINR": "MATICUSDT",
    })
    coindcx_map: Dict[str, str] = field(default_factory=lambda: {
        "BTC-USD": "BTCINR", "ETH-USD": "ETHINR", "BNB-USD": "BNBINR",
        "SOL-USD": "SOLINR", "XRP-USD": "XRPINR", "ADA-USD": "ADAINR",
        "DOGE-USD": "DOGEINR", "AVAX-USD": "AVAXINR", "DOT-USD": "DOTINR",
        "MATIC-USD": "MATICINR", "LINK-USD": "LINKINR", "LTC-USD": "LTCINR",
        "BTCINR": "BTCINR", "ETHINR": "ETHINR", "BNBINR": "BNBINR",
        "SOLINR": "SOLINR", "XRPINR": "XRPINR", "ADAINR": "ADAINR",
    })
    interval: str = "1d"
    period: str = "2y"
    test_size: float = 0.12
    val_size: float = 0.13
    sequence_length: int = 60
    prediction_horizon: int = 7
    cache_ttl_hours: int = 12  # v6: reduced to 12h for fresher data
    use_coindcx_primary_for_inr: bool = True
    max_price_jump_pct: float = 50.0  # v6: detect anomaly >50% daily jump
    validation_strict: bool = True
    use_multi_source_merge: bool = True  # v6: merge binance+yfinance+coingecko

@dataclass
class FeatureConfig:
    use_technical_indicators: bool = True
    use_price_features: bool = True
    use_volume_features: bool = True
    use_lag_features: bool = True
    # Sentiment enrichment is OFF by default so that data + prediction work
    # out of the box with no API keys / no news network access. Enable via
    # CRYPTOPRED_USE_SENTIMENT=1 (optionally with news/Reddit keys in .env).
    use_sentiment: bool = field(default_factory=lambda: os.getenv("CRYPTOPRED_USE_SENTIMENT", "0") == "1")
    use_advanced_indicators: bool = True
    use_volatility_features: bool = True
    use_market_regime: bool = True
    use_order_flow: bool = True  # v6 new
    use_liquidity_features: bool = True  # v6 new
    use_microstructure: bool = True  # v6 new
    lag_periods: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 7, 10, 14, 21, 30, 60])
    sma_windows: List[int] = field(default_factory=lambda: [5, 7, 10, 14, 20, 30, 50, 100, 200])
    ema_windows: List[int] = field(default_factory=lambda: [9, 12, 21, 26, 50, 100, 200])
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
    # v6 new
    use_kalman_filter: bool = True
    use_fourier_features: bool = True
    use_orderbook_features: bool = True
    use_kelly_features: bool = True
    use_hurst: bool = True
    use_supertrend: bool = True
    use_donchian: bool = True
    use_aroon: bool = True
    target_feature_count: int = 300  # v6 goal

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
    cache_hours: int = 1  # v6: fresher sentiment
    expanded_lexicon: bool = True  # v6

@dataclass
class RealtimeConfig:
    enabled: bool = True
    exchange: str = "binance"
    ws_url: str = "wss://stream.binance.com:9443/ws"
    rest_url: str = "https://api.binance.com"
    coindcx_rest_url: str = "https://api.coindcx.com"
    buffer_size: int = 2000  # v6 increased
    reconnect_interval: int = 3  # v6 faster reconnect
    use_coindcx_for_inr: bool = True
    max_reconnect_attempts: int = 10
    backoff_jitter: bool = True

@dataclass
class ModelConfig:
    # LSTM v6 - Deeper + More attention + Residual + Better regularization + MC Dropout
    lstm_hidden_size: int = 384
    lstm_num_layers: int = 4
    lstm_dropout: float = 0.20
    lstm_learning_rate: float = 0.00025
    lstm_epochs: int = 250
    lstm_batch_size: int = 32
    lstm_patience: int = 25
    lstm_bidirectional: bool = True
    lstm_use_attention: bool = True
    lstm_weight_decay: float = 3e-5
    lstm_use_residual: bool = True
    lstm_attention_heads: int = 8
    lstm_use_layer_norm: bool = True
    lstm_use_mc_dropout: bool = True  # v6 new for uncertainty
    lstm_mc_samples: int = 20

    # Transformer v6 - Larger + More robust + Learnable PE + Pre-LN + Uncertainty
    transformer_d_model: int = 384
    transformer_nhead: int = 8
    transformer_num_layers: int = 6
    transformer_dim_feedforward: int = 768
    transformer_dropout: float = 0.12
    transformer_learning_rate: float = 0.00018
    transformer_epochs: int = 220
    transformer_batch_size: int = 32
    transformer_patience: int = 25
    transformer_use_learnable_pe: bool = True
    transformer_use_attention_pooling: bool = True
    transformer_use_pre_ln: bool = True
    transformer_use_mc_dropout: bool = True

    # XGBoost v6 - Heavily tuned + GPU + SHAP + Early stopping
    xgb_n_estimators: int = 2000
    xgb_max_depth: int = 12
    xgb_learning_rate: float = 0.015
    xgb_subsample: float = 0.85
    xgb_colsample_bytree: float = 0.70
    xgb_reg_alpha: float = 0.03
    xgb_reg_lambda: float = 2.0
    xgb_min_child_weight: int = 1
    xgb_gamma: float = 0.03
    xgb_use_gpu: bool = False
    xgb_early_stopping_rounds: int = 80
    xgb_use_shap: bool = True

    # GRU v6 - Improved
    gru_hidden_size: int = 320
    gru_num_layers: int = 4
    gru_dropout: float = 0.20
    gru_learning_rate: float = 0.0003
    gru_epochs: int = 180
    gru_batch_size: int = 32
    gru_patience: int = 25
    gru_bidirectional: bool = True

    # TCN v6 - Deeper temporal convolutions
    tcn_channels: List[int] = field(default_factory=lambda: [64, 128, 256, 256])
    tcn_kernel_size: int = 3
    tcn_dropout: float = 0.15
    tcn_learning_rate: float = 0.00025
    tcn_epochs: int = 150
    tcn_batch_size: int = 32
    tcn_patience: int = 25
    tcn_use_attention: bool = True
    tcn_use_residual: bool = True

    # ARIMA v6 - Auto order + SARIMAX + Exogenous
    arima_order: tuple = (5, 1, 3)
    arima_seasonal_order: tuple = (2, 1, 2, 7)
    arima_use_auto: bool = True
    arima_use_exog: bool = True  # v6: use sentiment/vol as exog

    # Ensemble v6 - Advanced weighting + stacking + calibration + TCN + Bayesian
    ensemble_weights: dict = field(default_factory=lambda: {
        "lstm": 0.22,
        "transformer": 0.26,
        "xgboost": 0.18,
        "gru": 0.10,
        "tcn": 0.16,
        "arima": 0.08
    })
    ensemble_use_stacking: bool = True
    ensemble_use_dynamic_weights: bool = True
    ensemble_use_sharpe_weighting: bool = True
    ensemble_use_bayesian: bool = True  # v6 new
    ensemble_meta_learner: str = "ridge"  # ridge, lgbm, xgboost, elastic
    ensemble_calibrate_confidence: bool = True
    ensemble_version: str = "v6_ultra"
    ensemble_use_uncertainty: bool = True
    ensemble_confidence_threshold: float = 0.68
    ensemble_use_dir_accuracy: bool = True

@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_free_rate: float = 0.02
    use_coindcx_fees: bool = True
    use_trailing_stop: bool = True  # v6
    use_kelly_sizing: bool = True  # v6

@dataclass
class TrainingConfig:
    random_state: int = 42
    n_splits: int = 5
    save_models: bool = True
    experiment_name: str = "crypto_pred_v6_ultra"
    use_robust_scaler: bool = True
    use_log_returns_target: bool = False
    use_feature_selection: bool = True
    feature_selection_k: int = 120  # v6 increased from 100
    feature_selection_method: str = "hybrid"  # mi, xgb, rf, hybrid, shap
    use_kalman_smoothing: bool = True
    auto_retrain_on_drift: bool = True
    drift_threshold: float = 0.12  # v6 more sensitive
    version: str = "v6"
    use_mixed_precision: bool = True  # v6
    gradient_accumulation_steps: int = 1
    use_early_stopping: bool = True
    early_stopping_min_delta: float = 1e-6

@dataclass
class AutomationConfig:
    # Background auto-retraining loop. OFF by default (the bundled models are
    # enough for out-of-the-box prediction). Enable with CRYPTOPRED_AUTOMATION=1
    # or at runtime via POST /training/start.
    enabled: bool = field(default_factory=lambda: os.getenv("CRYPTOPRED_AUTOMATION", "0") == "1")
    retrain_interval_hours: int = 6  # v6: more frequent 6h vs 8h
    check_interval_minutes: int = 20  # v6: faster checks
    accuracy_threshold: float = 10.0  # v6: stricter 10% vs 12%
    auto_rollback_on_degradation: bool = True
    max_models_per_symbol: int = 8  # v6 increased
    use_model_registry: bool = True
    auto_strategy_selection: bool = True
    auto_risk_adjustment: bool = True
    market_regime_detection: bool = True
    use_ks_drift_detection: bool = True  # v6 new

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_min: int = 120
    use_caching: bool = True
    cache_ttl: int = 20  # v6 reduced for fresher
    enable_metrics: bool = True
    enable_security_headers: bool = True

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
    version: str = "v6_ultra_ios26_liquid_glass"

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def validate_config() -> bool:
    """v6: validate config consistency"""
    cfg = get_config()
    total_w = sum(cfg.model.ensemble_weights.values())
    assert abs(total_w - 1.0) < 0.01, f"Ensemble weights must sum to 1.0, got {total_w}"
    assert cfg.data.test_size + cfg.data.val_size < 0.5, "Test+val too large"
    assert cfg.model.lstm_hidden_size % cfg.model.lstm_attention_heads == 0, "LSTM hidden must be divisible by heads"
    assert cfg.model.transformer_d_model % cfg.model.transformer_nhead == 0, "Transformer d_model must be divisible by nhead"
    return True
