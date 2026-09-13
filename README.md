# ₿ Crypto Prediction v2

**End-to-end cryptocurrency forecasting platform — now with Transformer, Sentiment, Realtime Binance, Backtesting, and React Frontend**

> Production-ready core: data ingestion, 50+ technical indicators, sentiment (News/Reddit/Twitter), LSTM + Transformer (TFT) + XGBoost + ARIMA ensemble, training pipeline, FastAPI service, Streamlit dashboard, and React frontend with TradingView lightweight-charts.

---

## 🏗️ Architecture v2

```
Crypto-Prediction-/
├── src/crypto_prediction/
│   ├── config.py              # Centralized config v2
│   ├── data/
│   │   ├── fetcher.py         # yfinance + CoinGecko fallback
│   │   ├── preprocessor.py    # Scaling, splitting, sequences
│   │   ├── dataset.py         # Full pipeline
│   │   └── realtime.py        # NEW: Binance WS + REST live feed
│   ├── features/
│   │   ├── technical.py       # 50+ indicators
│   │   └── sentiment.py       # NEW: VADER-like + FinBERT, News, Reddit
│   ├── models/
│   │   ├── base.py
│   │   ├── lstm_model.py
│   │   ├── transformer_model.py # NEW: TFT-inspired Transformer
│   │   ├── xgboost_model.py
│   │   ├── arima_model.py
│   │   └── ensemble.py        # Updated weights: LSTM 35% + Transformer 35%
│   ├── training/trainer.py    # v2 with sentiment & transformer
│   ├── prediction/predictor.py# v2
│   ├── backtesting/           # NEW
│   │   ├── engine.py          # Portfolio simulation
│   │   ├── strategies.py      # MA, RSI, Prediction, Ensemble
│   │   └── metrics.py         # Sharpe, DD, win rate, profit factor
│   ├── evaluation/metrics.py
│   └── utils/
├── api/main.py                # v2: /sentiment, /realtime, /backtest
├── app/streamlit_app.py       # v2: 6 tabs including sentiment, realtime, backtest
├── frontend/                  # NEW: React + Vite + Tailwind + lightweight-charts
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/Navbar, PriceChart
│   │   └── pages/Dashboard, Forecast, Sentiment, Realtime, Backtest, Models
│   └── package.json
├── scripts/
│   ├── train.py               # v2 with --use-sentiment
│   ├── predict.py
│   └── backtest.py            # NEW
└── tests/
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
# frontend
cd frontend && npm install && npm run dev
```

### 2. Train Models v2
```bash
python scripts/train.py --symbol BTC-USD --period 2y --models all --use-sentiment

# Only transformer
python scripts/train.py --symbol ETH-USD --period 1y --models transformer --epochs 50
```

### 3. Predict
```bash
python scripts/predict.py --symbol BTC-USD --steps 7
```

### 4. Backtest
```bash
python scripts/backtest.py --symbol BTC-USD --strategy ensemble
python scripts/backtest.py --symbol BTC-USD --strategy all
```

### 5. API v2
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# New endpoints:
# GET /sentiment?symbol=BTC-USD&days=14
# GET /sentiment/analyze?text=Bitcoin is bullish!
# GET /realtime/price?symbol=BTC-USD
# POST /realtime/start?symbols=BTC-USD&symbols=ETH-USD
# GET /realtime/prices
# POST /backtest {symbol, strategy, initial_capital}
# GET /backtest/compare?symbol=BTC-USD
```

### 6. Dashboards
```bash
# Streamlit v2
streamlit run app/streamlit_app.py --server.port 8501

# React frontend
cd frontend
npm run dev  # http://localhost:5173 proxies /api to :8000
npm run build && npm run preview
```

---

## 🧠 Models v2

### LSTM
- 2-layer, 128 hidden, dropout 0.2, FC 64→32
- 60-day sequences, 60+ features

### Transformer (NEW, TFT-inspired)
- Input projection → Positional Encoding → TransformerEncoder (d_model 128, 4 heads, 2 layers, ff 256) → last token → FC
- Multi-head self-attention captures long-range dependencies, better than LSTM for 30d horizons
- Training: Adam 0.0005, ReduceLROnPlateau, early stopping patience 12
- Interpretability: attention weights placeholder for future TFT explainability

### XGBoost
- 500 trees, depth 6, feature importance

### ARIMA
- (5,1,0) baseline

### Ensemble v2
- LSTM 35% + Transformer 35% + XGB 20% + ARIMA 10%

---

## 💬 Sentiment (NEW)

**Lexicon-based VADER-like** (no external deps) + optional FinBERT:
- Positive: bullish, moon, pump, buy, surge, rally, hodl...
- Negative: bearish, crash, dump, sell, fear, panic...
- Boosters: very, extremely, absolutely

**Fetchers:**
- `NewsFetcher`: CryptoPanic API (free tier) + CoinGecko trending fallback + synthetic offline demo
- `RedditFetcher`: PRAW if keys set, else synthetic

**Aggregation:**
- Daily mean compound, pos, neg, count
- Rolling 3-day smoothing
- Merged into price DataFrame: `Sentiment_Compound`, `Sentiment_MA7`, `Sentiment_Diff`
- Trading signal boosted by sentiment: `change_pct += sentiment*0.5`

**API:**
```bash
curl /sentiment?symbol=BTC-USD&days=14
curl /sentiment/analyze?text="Bitcoin extremely bullish"
```

---

## 📡 Realtime Binance (NEW)

**BinanceRealtimeFetcher:**
- WebSocket: `wss://stream.binance.com:9443/ws/btcusdt@trade` + `@kline_1m`
- Threaded asyncio loop, deque buffer 1000, auto-reconnect 5s
- REST fallback: `/api/v3/klines`, `/api/v3/ticker/24hr`
- Callbacks for live prediction

**LivePredictor:**
- Merges live price with model forecast
- `live_change_pct` recalculated

**Manager:**
- Multi-symbol manager, start_all/stop_all

```python
from crypto_prediction.data.realtime import BinanceRealtimeFetcher
fetcher = BinanceRealtimeFetcher(symbol="BTC-USD")
fetcher.start()
print(fetcher.get_current_price())
```

---

## 📊 Backtesting Engine (NEW)

**Engine:**
- Long-only simulation, initial $10k, commission 0.1%, slippage 0.05%
- Equity curve, trades list with PnL

**Strategies:**
- `MovingAverageStrategy(20,50)`: golden/death cross
- `RSIStrategy(30,70)`: oversold/overbought
- `PredictionStrategy`: predicted return > threshold
- `EnsembleSignalStrategy`: pred*10 + sentiment*0.5 + (50-RSI)/50*0.3

**Metrics:**
- Total return, annualized, volatility, Sharpe, max DD, win rate, avg win/loss, profit factor

```python
from crypto_prediction.backtesting.engine import BacktestEngine
engine = BacktestEngine()
result = engine.run(df, strategy)
print(result.metrics)
```

---

## ⚛️ React Frontend (NEW)

**Stack:** Vite + React 18 + React Router + Tailwind + Recharts + lightweight-charts + Zustand + Axios

**Pages:**
- **Dashboard**: price, signal, sentiment, forecast, PriceChart (TradingView lightweight-charts with forecast overlay)
- **Forecast**: multi-model line chart, table
- **Sentiment**: daily trend, custom text analyzer, breakdown bar
- **Realtime**: Binance live price, ticker, history sparkline, 2s polling
- **Backtest**: run, compare, equity curve, trades
- **Models**: docs for all models

**Dev:**
```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

---

## 📈 Example Output v2

```
=== BTC-USD Prediction v2 ===
Current: $67,234.12 | Sentiment: 0.34 (bullish)

Next:
  lstm: $68,102
  transformer: $68,450  # NEW
  xgboost: $67,890
  arima: $67,543
  ensemble: $68,120

7-Day Ensemble: [...]
Signal: BUY (58% confidence) with sentiment 0.34

Backtest Ensemble:
  Total Return: 42.5% | Sharpe: 1.8 | Max DD: -12.3% | Win Rate: 58%
```

---

## 🧪 Tests v2

```bash
python tests/test_fetcher.py
python tests/test_features.py
python tests/test_models.py
python tests/test_sentiment.py
python tests/test_transformer.py
python tests/test_backtest.py
```

---

## 🔑 Env Keys (optional)

```bash
# .env
CRYPTOPANIC_API_KEY=xxx
NEWSAPI_KEY=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_SECRET=xxx
TWITTER_BEARER_TOKEN=xxx
BINANCE_API_KEY=xxx
BINANCE_SECRET=xxx
```

Without keys, system uses synthetic fallback so it works offline.

---

## 🗺️ Roadmap

- [x] Core data + features + models
- [x] FastAPI + Streamlit
- [x] Sentiment (News, Reddit, Twitter) + FinBERT option
- [x] Realtime Binance WS + REST
- [x] Transformer (TFT-inspired)
- [x] Backtesting engine
- [x] React frontend with TradingView charts
- [ ] Docker Compose (api + frontend + redis for WS)
- [ ] WebSocket push to React (live chart)
- [ ] Full TFT with variable selection & attention viz
- [ ] CI/CD + Kubernetes

---

## 📜 License

MIT © 2026 Aditya
