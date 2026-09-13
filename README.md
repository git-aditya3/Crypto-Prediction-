# ₿ Crypto Prediction Core

**End-to-end cryptocurrency price forecasting platform with ML/DL ensemble**

> Production-ready core built from scratch: data ingestion, technical indicators, feature engineering, LSTM + XGBoost + ARIMA ensemble, training pipeline, FastAPI service, and Streamlit dashboard.

---

## 🏗️ Architecture

```
Crypto-Prediction-/
├── src/crypto_prediction/
│   ├── config.py              # Centralized configuration
│   ├── data/
│   │   ├── fetcher.py         # yfinance + CoinGecko fallback
│   │   ├── preprocessor.py    # Scaling, splitting, sequences
│   │   └── dataset.py         # Full pipeline orchestrator
│   ├── features/
│   │   └── technical.py       # 50+ indicators: SMA, EMA, RSI, MACD, BB, ATR, Stoch, OBV, lags, time
│   ├── models/
│   │   ├── base.py            # Abstract interface
│   │   ├── lstm_model.py      # PyTorch LSTM with attention-like FC
│   │   ├── xgboost_model.py   # Gradient boosting
│   │   ├── arima_model.py     # Statistical baseline
│   │   └── ensemble.py        # Weighted ensemble
│   ├── training/
│   │   └── trainer.py         # Orchestrates full training
│   ├── prediction/
│   │   └── predictor.py       # Inference + trading signals
│   ├── evaluation/
│   │   └── metrics.py         # RMSE, MAE, MAPE, R2, directional accuracy
│   └── utils/
│       ├── logger.py
│       └── viz.py             # Plotly visualizations
├── api/
│   └── main.py                # FastAPI service
├── app/
│   └── streamlit_app.py       # Interactive dashboard
├── scripts/
│   ├── train.py
│   └── predict.py
├── data/                      # cached raw/processed
├── models/                    # saved artifacts
└── tests/
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
# or
pip install -e .
```

### 2. Train Models
```bash
# Train all models for BTC
python scripts/train.py --symbol BTC-USD --period 2y --models all

# Train only LSTM with custom epochs
python scripts/train.py --symbol ETH-USD --period 1y --models lstm --epochs 50

# Train multiple symbols
for sym in BTC-USD ETH-USD SOL-USD; do python scripts/train.py --symbol $sym --period 2y; done
```

### 3. Predict
```bash
python scripts/predict.py --symbol BTC-USD --steps 7

# JSON output
python scripts/predict.py --symbol BTC-USD --steps 14 --json
```

### 4. Run API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Endpoints:
# GET /              - info
# GET /history?symbol=BTC-USD
# GET /predict?symbol=BTC-USD
# GET /forecast?symbol=BTC-USD&steps=7
# GET /signal?symbol=BTC-USD
```

### 5. Run Dashboard
```bash
streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🧠 Models

### LSTM (Deep Learning)
- Input: 60-day sequences, 50+ engineered features
- Architecture: 2-layer LSTM (128 hidden) + Dropout + FC(64,32)
- Training: Adam, ReduceLROnPlateau, early stopping, grad clipping
- Purpose: Captures long-term temporal dependencies

### XGBoost (Gradient Boosting)
- Input: Flat feature vector
- Hyperparams: 500 trees, max_depth=6, lr=0.05
- Purpose: Non-linear feature interactions, feature importance

### ARIMA (Statistical)
- Input: Raw close price series
- Order: (5,1,0) auto-fallback to (1,1,0)
- Purpose: Baseline, trend/seasonality

### Ensemble
- Weighted average: LSTM 50%, XGB 30%, ARIMA 20%
- Configurable via `config.py`
- Future forecast uses autoregressive approximation for each model

---

## 📊 Features (50+)

- **Price**: Returns, Log Returns, Range, Volatility, Cumulative
- **Trend**: SMA(7,14,30,50), EMA(12,26,50), MACD, Bollinger Bands, ATR
- **Momentum**: RSI, Stochastic %K/%D, ROC, Momentum
- **Volume**: Volume SMA, Ratio, OBV, Change
- **Lags**: Close/Returns/Volume/RSI lags 1,3,7,14
- **Time**: DayOfWeek, Month, Quarter + sin/cos cyclical encoding
- **Targets**: Next close, next returns, direction, 3d/7d ahead

---

## 🔮 Prediction Flow

1. **Fetch**: yfinance (OHLCV) → fallback CoinGecko
2. **Engineer**: 50+ indicators
3. **Preprocess**: Clean NaNs, time-series split (70/10/20), StandardScaler, sequence creation
4. **Train**: LSTM (seq), XGB (flat), ARIMA (price)
5. **Evaluate**: RMSE, MAE, MAPE, R2, Directional Accuracy
6. **Forecast**: 1 to 30 days ahead, ensemble weighted
7. **Signal**: STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL based on predicted % change

---

## 📈 Example Output

```
=== BTC-USD Prediction ===
Current Price: $67,234.12

Next Price Predictions:
  lstm      : $68,102.45
  xgboost   : $67,890.11
  arima     : $67,543.20
  ensemble  : $67,956.33

7-Day Forecast (Ensemble):
  2025-09-14: $67,956.33
  2025-09-15: $68,234.10
  ...

Trading Signal: BUY (42.5% confidence)
  Predicted +1.07% change
```

---

## 🛠️ Configuration

Edit `src/crypto_prediction/config.py`:

```python
DataConfig: period=2y, interval=1d, seq_length=60
FeatureConfig: sma_windows, rsi_window, lag_periods
ModelConfig: lstm_hidden_size=128, xgb_n_estimators=500, ensemble_weights
```

---

## 🧪 Tests

```bash
python tests/test_fetcher.py
python tests/test_features.py
python tests/test_models.py
```

---

## 🗺️ Roadmap

- [x] Core data + features + models
- [x] Training pipeline + evaluation
- [x] FastAPI + Streamlit
- [ ] Sentiment from Twitter/Reddit (VADER, FinBERT)
- [ ] Real-time WebSocket ingestion (Binance)
- [ ] Transformer model (Temporal Fusion Transformer)
- [ ] Backtesting engine with portfolio simulation
- [ ] Docker + CI/CD
- [ ] Frontend React with TradingView charts

---

## 📜 License

MIT © 2026 Aditya

---

## 🤝 Contributing

PRs welcome! This is the **core** – keep modules decoupled, add tests, and follow the existing `BaseModel` interface for new models.
