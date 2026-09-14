# ₿ Crypto Prediction

**End-to-end cryptocurrency forecasting platform — pretrained ML ensemble, web dashboard, REST API, backtesting.**

One `pip install` + one command and everything runs: pretrained models ship in
`models/`, the data layer falls back gracefully (live APIs → local cache →
labelled synthetic series), and the web dashboard is prebuilt. No training
step, no API keys, no extra commands.

> ⚠️ **Disclaimer:** This is a research/education platform. Forecasts are
> statistical estimates, not financial advice. Crypto markets are extremely
> volatile — never trade real money on the basis of model output alone.

---

## 🚀 Quick start (Windows git bash / macOS / Linux)

```bash
git clone https://github.com/git-aditya3/Crypto-Prediction-
cd Crypto-Prediction-

./install.sh          # creates .venv and installs all dependencies
./start.sh            # starts the web app + API on http://localhost:8000
```

Open **http://localhost:8000** — the React dashboard with live charts,
forecasts, signals, backtests. (Windows without git bash: use `install.bat`
and `start.bat` in cmd/PowerShell.)

Everything is verified with the self-diagnostic:

```bash
python run.py check          # or: python run.py check --offline
```

### One-command CLI (same for all of these)

```bash
python run.py                          # serve web app + API (default)
python run.py predict                  # predict BTC-USD, next 7 days
python run.py predict --symbol ETH-USD --steps 14
python run.py train --symbol BTC-USD   # retrain on fresh live data
python run.py backtest --symbol BTC-USD --strategy ensemble
python run.py dashboard                # Streamlit dashboard on :8501
python run.py check --offline          # self-diagnostic (no network)
python run.py install                  # (re)install dependencies
```

If you `pip install -e .` (or `pip install .`), the same commands are
available as `crypto-prediction`, `crypto-predict`, `crypto-train`,
`crypto-backtest`, `crypto-check`.

---

## 📦 What works out of the box

| Feature | Status |
|---|---|
| Price data (BTC/ETH/XRP/ADA/BNB/SOL/… + INR pairs) | ✅ Binance → Yahoo → CoinGecko → CoinDCX → local cache → labelled synthetic fallback. Works fully offline. |
| ML price prediction | ✅ **Pretrained models bundled** for `BTC-USD`, `XRP-USD`, `ADA-USD`, `BNB-USD` (LSTM + Transformer + XGBoost + ARIMA, weighted ensemble). Any other symbol: one `train` command. |
| Web dashboard (React) | ✅ Prebuilt in `frontend/dist`, served by the API — no node/npm needed. |
| REST API + docs | ✅ FastAPI on `:8000`, Swagger at `/docs`. |
| Backtesting | ✅ MA / RSI / ensemble / prediction strategies. |
| Realtime feed | ✅ Binance WebSocket (browser-side) + REST fallback. |
| Sentiment (news/Reddit/FinBERT) | ⚙️ Optional — off by default, no keys needed to run the rest. |
| Trading / brokers / autotrading | ⚙️ Optional — endpoints included, disabled by default, paper-first. |

---

## 🧠 Models

Bundled pretrained models (`models/*_v6.*`):

* **LSTM** — 2× bidirectional layers (96 hidden), attention pooling, Huber loss
* **Transformer** — 2 layers, d_model 96, learnable positional encoding, attention pooling
* **XGBoost** — 400 trees, early stopping
* **ARIMA** — auto order selection (SARIMAX, weekly seasonality)
* **Ensemble** — inverse-MAPE weighted (weights come from each symbol's
  training report, recomputed automatically at prediction time)

They were trained on 2–3 years of daily data (real cached data where
available; clearly-labelled realistic synthetic data otherwise) with the same
300-feature pipeline (50+ technical indicators, volatility, regime,
microstructure features; 60-day input windows; next-day close target).

**Retrain on live data** (recommended after a few weeks, or any time):

```bash
python run.py train --symbol BTC-USD          # full-size models, ~30-60 min on CPU
python run.py train --symbol ETH-USD --epochs 100
```

Retraining overwrites the bundled artifacts for that symbol.

*Honest expectations:* the bundled baselines are for demo/production plumbing,
not a trading edge. Daily close MAPE on recent data typically lands in the
10–25% range; directional accuracy hovers near coin-flip, which is normal for
daily horizons. Judge any model (including yours) on walk-forward backtests.

---

## 🌐 API

Base URL `http://localhost:8000` (same-origin `/api/...` also works — the
server strips the prefix). Interactive docs: **/docs**.

```
GET  /health                  liveness + component status
GET  /info                    API description (JSON)
GET  /predict?symbol=BTC-USD  next-day prediction per model + ensemble
GET  /forecast?symbol=BTC-USD&steps=7   multi-day forecast + confidence bands
GET  /signal?symbol=BTC-USD   trading signal (BUY/SELL/...) + SL/TP
GET  /history?symbol=BTC-USD  OHLCV history (+RSI, sentiment if enabled)
GET  /market/tickers          24h tickers (Binance, cached 10s)
GET  /market/klines           Binance klines
GET  /backtest (POST)         run a backtest {symbol, strategy, initial_capital}
GET  /backtest/compare        compare strategies
GET  /sentiment?symbol=BTC-USD&days=14      (optional feature)
GET  /sentiment/analyze?text=...
GET  /realtime/price?symbol=BTC-USD
GET  /models                  bundled model artifacts + versions
GET  /symbols                 supported symbols
GET  /metrics                 API + component metrics
... 70+ endpoints incl. portfolio, strategies, alerts, scanner, journal
```

The web dashboard and every endpoint run on the bundled models immediately.

---

## 🏗️ Architecture

```
Crypto-Prediction-/
├── run.py                     # single entry point (serve/predict/train/check/...)
├── install.sh / start.sh      # one-shot install & start (git bash)
├── install.bat / start.bat    # same for Windows cmd
├── requirements.txt           # core deps (only install step needed)
├── requirements-optional.txt  # sentiment extras (praw/transformers)
├── requirements-dev.txt       # test suite deps (pytest + TestClient)
├── models/                    # PRETRAINED model artifacts (bundled)
├── data/raw/                  # local OHLCV cache (auto-populated)
├── src/crypto_prediction/
│   ├── config.py              # central config (env-overridable)
│   ├── data/                  # fetcher (multi-source + offline fallback),
│   │                          # synthetic generator, preprocessor, realtime WS
│   ├── features/technical.py  # 300+ indicator features
│   ├── features/sentiment.py  # optional: lexicon/FinBERT + news/Reddit
│   ├── models/                # LSTM, Transformer, GRU, TCN, XGBoost, ARIMA,
│   │                          # ensemble (all with save/load)
│   ├── training/trainer.py    # full training pipeline + model registry
│   ├── prediction/predictor.py# loads bundled artifacts, forecasts, signals
│   ├── backtesting/           # engine + strategies + metrics
│   ├── evaluation/            # MAPE/RMSE/R²/dir-accuracy/Sharpe reports
│   ├── trading/ portfolio/ strategies/ brokers/ autotrading/   # optional
│   ├── alerts/ scanner/ analytics/ journal/ crash_detector/    # optional
│   └── cli.py                 # run.py backend (all subcommands)
├── api/main.py                # FastAPI app (REST + serves the React build)
├── app/streamlit_app.py       # Streamlit dashboard (alternative UI)
├── frontend/                  # React + Vite + Tailwind (dist/ prebuilt)
├── scripts/                   # pretrain.py (bundled models), train, predict, backtest
└── tests/                     # unit tests
```

**Data layer:** `Binance REST → Yahoo (yfinance) → CoinGecko → CoinDCX (INR) →
stale local cache → deterministic synthetic series`. Fresh data is cached in
`data/raw/` (TTL 12h) so repeated calls are instant and offline-friendly.
The synthetic fallback is always labelled and never written to cache, so the
first live fetch always wins.

---

## ⚙️ Optional features

**Sentiment** (news + Reddit + FinBERT) — off by default:

```bash
pip install -r requirements-optional.txt
echo "CRYPTOPRED_USE_SENTIMENT=1" >> .env        # + API keys in .env (see .env.example)
python run.py train --symbol BTC-USD             # retrains with sentiment features
```

**Trading / autotrading** — endpoints exist under `/brokers`, `/autotrade`,
`/portfolio`, `/strategies`. Config in `data/autotrading_config.json` is
disabled by default; enable paper mode first, and only ever use keys with
trading permissions (no withdrawals).

**Docker:**

```bash
docker build -t crypto-prediction .
docker run -p 8000:8000 -p 8501:8501 crypto-prediction
```

---

## 🔧 Development

```bash
pip install -e .[dev]                    # + test deps (or: pip install -r requirements-dev.txt)
python -m pytest tests -q                # full suite (~1 min): models, data, API, out-of-box
make test                                # same thing
cd frontend && npm install && npm run build   # rebuild the web dashboard (needs node)
```

The test suite (`tests/`) covers the core acceptance criteria: bundled model
artifacts exist for all four symbols, predictions work with zero training
steps, the data layer never hard-fails offline, and the API routes browser
deep links to the SPA while serving JSON to API clients.

Configuration lives in `src/crypto_prediction/config.py` (env-overridable via
`.env` — every key is optional, see `.env.example`). The project version is
defined once in `src/crypto_prediction/__init__.py` (the API and package
metadata read it from there).
