"""
FastAPI for Crypto Prediction - v3 with Trading Calls, Improved Accuracy, Polished UI
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path
import pandas as pd
import requests
import time
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.config import get_config
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.features.sentiment import SentimentFeatureEngineer, SentimentAnalyzer
from crypto_prediction.data.realtime import BinanceRealtimeFetcher, RealtimeManager
from crypto_prediction.backtesting.engine import BacktestEngine
from crypto_prediction.backtesting.strategies import MovingAverageStrategy, RSIStrategy, PredictionStrategy, EnsembleSignalStrategy
from crypto_prediction.trading.calls import TradingCallGenerator
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API v3 - Trading Calls Edition",
    description="End-to-end crypto forecasting with trading calls: LSTM v3, Transformer v3, XGBoost v3, ARIMA v3, Ensemble v3, Sentiment, Realtime Binance, Backtesting, Trading Calls with SL/TP",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

realtime_manager: Optional[RealtimeManager] = None
call_generator = TradingCallGenerator(risk_per_trade=0.02)

_market_cache = {"tickers": None, "timestamp": 0}
_calls_cache = {"calls": None, "timestamp": 0, "account_balance": 10000}
CACHE_TTL = 10
CALLS_CACHE_TTL = 60  # 1 minute for trading calls

class ForecastResponse(BaseModel):
    symbol: str
    current_price: Optional[float]
    dates: List[str]
    lstm: Optional[List[float]] = None
    transformer: Optional[List[float]] = None
    xgboost: Optional[List[float]] = None
    arima: Optional[List[float]] = None
    ensemble: Optional[List[float]] = None

class PredictResponse(BaseModel):
    symbol: str
    predictions: Dict[str, float]

class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    current_price: float
    predicted_price: float
    change_pct: float
    reason: str
    sentiment: Optional[float] = 0

class SentimentResponse(BaseModel):
    symbol: str
    daily: List[Dict]
    average_compound: float

class BacktestRequest(BaseModel):
    symbol: str = "BTC-USD"
    strategy: str = "ma"
    period: str = "1y"
    initial_capital: float = 10000

class TradingCallRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframe: str = "1d"
    account_balance: float = 10000
    risk_per_trade: float = 0.02

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API v3 - Trading Calls Edition",
        "version": "0.3.0",
        "features": ["LSTM v3", "Transformer v3", "XGBoost v3", "ARIMA v3", "Ensemble v3 (Dynamic+Stacking)", "Trading Calls with SL/TP", "Sentiment", "Realtime Binance", "Backtesting", "Polished UI v3"],
        "supported_symbols": config.data.supported_symbols,
        "binance_map": config.data.binance_map,
        "data_status": {
            "historical": "987 rows each (BTC, ETH, SOL, BNB, XRP, ADA) 2023-2025",
            "realtime": "Binance WebSocket + REST live feed",
            "features": "182 features v3 (RobustScaler)",
            "accuracy": "BTC ARIMA 2.57% MAPE, Ensemble 6.30%, SOL 2.37%, ADA 3.16% on past week"
        },
        "endpoints": ["/predict", "/forecast", "/signal", "/trading/calls", "/trading/call/{symbol}", "/trading/summary", "/history", "/sentiment", "/market/tickers", "/backtest", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0", "realtime": realtime_manager is not None, "models": "v3 improved"}

# === TRADING CALLS - NEW ===

@app.get("/trading/calls")
def get_trading_calls(
    symbols: Optional[str] = Query(None, description="Filter symbols comma-separated e.g., BTC-USD,ETH-USD"),
    timeframe: str = Query("1d", description="1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    account_balance: float = Query(10000, ge=100, le=10000000),
    risk_per_trade: float = Query(0.02, ge=0.005, le=0.1),
    use_cache: bool = Query(True)
):
    """Get trading calls for all or selected symbols with entry, SL, TP, risk management"""
    # Parse symbols: support comma-separated
    parsed_symbols: Optional[List[str]] = None
    if symbols:
        if "," in symbols:
            parsed_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        else:
            parsed_symbols = [symbols.strip()]
    symbols_list = parsed_symbols
    global _calls_cache
    now = time.time()
    
    # Check cache
    if use_cache and _calls_cache["calls"] and (now - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
        if _calls_cache["account_balance"] == account_balance:
            cached = _calls_cache["calls"]
            # Filter if needed
            if symbols_list:
                filtered = [c for c in cached["calls"] if c["symbol"] in symbols_list]
                return {"calls": filtered, "summary": cached["summary"], "count": len(filtered), "cached": True, "timestamp": cached["timestamp"]}
            return {**cached, "cached": True}
    
    try:
        # Update risk manager
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        
        # Generate calls
        target_symbols = symbols_list or config.data.supported_symbols
        calls = call_generator.generate_all_calls(symbols=target_symbols, timeframe=timeframe, account_balance=account_balance)
        
        calls_dict = [c.to_dict() for c in calls]
        summary = call_generator.get_call_summary(calls)
        
        result = {
            "calls": calls_dict,
            "summary": summary,
            "count": len(calls_dict),
            "timeframe": timeframe,
            "account_balance": account_balance,
            "risk_per_trade": risk_per_trade,
            "timestamp": datetime.utcnow().isoformat(),
            "cached": False
        }
        
        # Cache
        _calls_cache["calls"] = result
        _calls_cache["timestamp"] = now
        _calls_cache["account_balance"] = account_balance
        
        return result
        
    except Exception as e:
        logger.error(f"Trading calls failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/call/{symbol}")
def get_single_call(
    symbol: str,
    timeframe: str = Query("1d"),
    account_balance: float = Query(10000, ge=100),
    risk_per_trade: float = Query(0.02, ge=0.005, le=0.1)
):
    """Get trading call for single symbol"""
    try:
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        call = call_generator.generate_call(symbol=symbol, timeframe=timeframe, account_balance=account_balance)
        return call.to_dict()
    except Exception as e:
        logger.error(f"Single call failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/summary")
def get_trading_summary():
    """Get quick summary of market calls"""
    try:
        # Use cached if available
        if _calls_cache["calls"] and (time.time() - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
            return _calls_cache["calls"]["summary"]
        
        # Generate quick summary with top 6 symbols for speed
        top_symbols = config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=top_symbols, account_balance=10000)
        summary = call_generator.get_call_summary(calls)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trading/calls")
def post_trading_calls(req: TradingCallRequest):
    """POST version for trading calls with body"""
    try:
        call_generator.risk_manager.risk_per_trade = req.risk_per_trade
        target_symbols = req.symbols or config.data.supported_symbols
        calls = call_generator.generate_all_calls(symbols=target_symbols, timeframe=req.timeframe, account_balance=req.account_balance)
        calls_dict = [c.to_dict() for c in calls]
        summary = call_generator.get_call_summary(calls)
        
        return {
            "calls": calls_dict,
            "summary": summary,
            "count": len(calls_dict),
            "timeframe": req.timeframe,
            "account_balance": req.account_balance
        }
    except Exception as e:
        logger.error(f"Trading calls POST failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MARKET DATA ===

@app.get("/market/tickers")
def market_tickers():
    global _market_cache
    now = time.time()
    
    if _market_cache["tickers"] and (now - _market_cache["timestamp"]) < CACHE_TTL:
        return _market_cache["tickers"]
    
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        resp.raise_for_status()
        all_tickers = resp.json()
        
        wanted = set(config.data.binance_map.values())
        filtered = [t for t in all_tickers if t["symbol"] in wanted]
        
        reverse_map = {v: k for k, v in config.data.binance_map.items()}
        tickers = {}
        for t in filtered:
            our_sym = reverse_map.get(t["symbol"])
            if our_sym:
                tickers[our_sym] = {
                    "symbol": our_sym,
                    "binanceSymbol": t["symbol"],
                    "price": float(t["lastPrice"]),
                    "lastPrice": float(t["lastPrice"]),
                    "priceChange": float(t["priceChange"]),
                    "priceChangePercent": float(t["priceChangePercent"]),
                    "high": float(t["highPrice"]),
                    "low": float(t["lowPrice"]),
                    "volume": float(t["volume"]),
                    "quoteVolume": float(t["quoteVolume"]),
                    "open": float(t["openPrice"]),
                    "trades": t["count"],
                    "raw": t
                }
        
        result = {"tickers": tickers, "count": len(tickers), "timestamp": now, "source": "binance"}
        _market_cache["tickers"] = result
        _market_cache["timestamp"] = now
        return result
        
    except Exception as e:
        logger.warning(f"Binance ticker fetch failed: {e}")
        try:
            if realtime_manager:
                prices = realtime_manager.get_prices()
                tickers = {}
                for sym, price in prices.items():
                    if price:
                        tickers[sym] = {
                            "symbol": sym,
                            "price": price,
                            "lastPrice": price,
                            "priceChangePercent": 0,
                            "source": "realtime_manager"
                        }
                return {"tickers": tickers, "count": len(tickers), "source": "fallback"}
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Market data fetch failed: {e}")

@app.get("/market/klines")
def market_klines(
    symbol: str = Query("BTC-USD"),
    interval: str = Query("1d"),
    limit: int = Query(200, ge=1, le=1000)
):
    try:
        binance_symbol = config.data.binance_map.get(symbol, symbol.replace("-", ""))
        resp = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": binance_symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        klines = []
        for d in data:
            klines.append({
                "openTime": d[0],
                "open": float(d[1]),
                "high": float(d[2]),
                "low": float(d[3]),
                "close": float(d[4]),
                "volume": float(d[5]),
                "closeTime": d[6],
                "time": pd.to_datetime(d[0], unit='ms').strftime('%Y-%m-%d'),
                "timeISO": pd.to_datetime(d[0], unit='ms').isoformat()
            })
        
        return {"symbol": symbol, "binanceSymbol": binance_symbol, "interval": interval, "klines": klines, "count": len(klines)}
    except Exception as e:
        logger.error(f"Klines fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/orderbook")
def market_orderbook(symbol: str = Query("BTC-USD"), limit: int = Query(20, ge=5, le=100)):
    try:
        binance_symbol = config.data.binance_map.get(symbol, symbol.replace("-", ""))
        resp = requests.get(
            "https://api.binance.com/api/v3/depth",
            params={"symbol": binance_symbol, "limit": limit},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history(symbol: str = Query("BTC-USD"), period: str = Query("1y"), interval: str = Query("1d")):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        df_tail = df.tail(300)
        try:
            eng = SentimentFeatureEngineer()
            df_tail = eng.enrich_price_df(df_tail, symbol=symbol)
        except:
            pass

        data = {
            "symbol": symbol,
            "dates": df_tail.index.strftime('%Y-%m-%d').tolist(),
            "open": df_tail['Open'].tolist(),
            "high": df_tail['High'].tolist(),
            "low": df_tail['Low'].tolist(),
            "close": df_tail['Close'].tolist(),
            "volume": df_tail['Volume'].tolist(),
            "rsi": df_tail['RSI'].tolist() if 'RSI' in df_tail.columns else [],
            "sentiment": df_tail['Sentiment_Compound'].tolist() if 'Sentiment_Compound' in df_tail.columns else []
        }
        return data
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict", response_model=PredictResponse)
def predict_next(symbol: str = Query("BTC-USD"), period: str = Query("1y")):
    try:
        predictor = CryptoPredictor(symbol=symbol)
        preds = predictor.predict_next(period=period)
        if not preds:
            raise HTTPException(status_code=404, detail="No models found. Train first.")
        return {"symbol": symbol, "predictions": preds}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predict failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast")
def forecast(symbol: str = Query("BTC-USD"), steps: int = Query(7, ge=1, le=30), period: str = Query("1y")):
    try:
        predictor = CryptoPredictor(symbol=symbol)
        fc = predictor.forecast(steps=steps, period=period)
        if not fc or len(fc) <= 2:
            raise HTTPException(status_code=404, detail="No models found. Train first.")
        return fc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signal", response_model=SignalResponse)
def trading_signal(symbol: str = Query("BTC-USD"), steps: int = Query(7)):
    try:
        predictor = CryptoPredictor(symbol=symbol)
        fc = predictor.forecast(steps=steps)
        signal = predictor.get_trading_signal(fc)
        signal['symbol'] = symbol
        
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            live_price = fetcher.get_current_price()
            if live_price:
                signal['live_price'] = live_price
                pred = signal['predicted_price']
                signal['live_change_pct'] = (pred - live_price) / live_price * 100 if live_price else 0
        except:
            pass
            
        return signal
    except Exception as e:
        logger.error(f"Signal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment")
def sentiment(symbol: str = Query("BTC-USD"), days: int = Query(14, ge=1, le=90)):
    try:
        eng = SentimentFeatureEngineer()
        df = eng.get_daily_sentiment(symbol=symbol, days=days)
        if df.empty:
            return {"symbol": symbol, "daily": [], "average_compound": 0.0}
        daily = [{"date": idx.strftime('%Y-%m-%d'), "compound": row['sentiment_compound'], "pos": row['sentiment_pos'], "neg": row['sentiment_neg'], "count": int(row['sentiment_count'])} for idx, row in df.iterrows()]
        avg = float(df['sentiment_compound'].mean())
        return {"symbol": symbol, "daily": daily, "average_compound": avg}
    except Exception as e:
        logger.error(f"Sentiment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment/analyze")
def analyze_text(text: str = Query(..., description="Text to analyze")):
    try:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(text)
        return {"text": text, "sentiment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/realtime/price")
def realtime_price(symbol: str = Query("BTC-USD")):
    try:
        fetcher = BinanceRealtimeFetcher(symbol=symbol)
        price = fetcher.get_current_price()
        ticker = fetcher.fetch_ticker_rest()
        return {"symbol": symbol, "binance_symbol": fetcher.binance_symbol, "price": price, "ticker": ticker}
    except Exception as e:
        logger.error(f"Realtime price failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/realtime/start")
def realtime_start(symbols: List[str] = Query(["BTC-USD"])):
    global realtime_manager
    try:
        if realtime_manager:
            realtime_manager.stop_all()
        realtime_manager = RealtimeManager(symbols=symbols)
        realtime_manager.start_all()
        return {"status": "started", "symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/realtime/prices")
def realtime_prices():
    global realtime_manager
    if not realtime_manager:
        if _market_cache["tickers"]:
            return {"prices": {k: v["price"] for k, v in _market_cache["tickers"]["tickers"].items()}, "source": "cache"}
        raise HTTPException(status_code=400, detail="Realtime not started. POST /realtime/start")
    try:
        prices = realtime_manager.get_prices()
        return {"prices": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
def backtest(req: BacktestRequest):
    try:
        fetcher = CryptoDataFetcher(symbol=req.symbol)
        df = fetcher.load_or_fetch(symbol=req.symbol)
        from crypto_prediction.features.technical import FeatureEngineer
        eng = FeatureEngineer()
        df = eng.engineer(df)

        if req.strategy == "ma":
            strat = MovingAverageStrategy(short_window=20, long_window=50)
        elif req.strategy == "rsi":
            strat = RSIStrategy(rsi_low=30, rsi_high=70)
        elif req.strategy == "prediction":
            try:
                predictor = CryptoPredictor(symbol=req.symbol)
                fc = predictor.forecast(steps=len(df), period=req.period)
                if 'ensemble' in fc:
                    pred_series = pd.Series(fc['ensemble'], index=pd.to_datetime(fc['dates']))
                    df = df.copy()
                    df['Predicted'] = pred_series.reindex(df.index, method='ffill').fillna(method='bfill')
                    strat = PredictionStrategy(prediction_col="Predicted", threshold=0.01)
                else:
                    strat = MovingAverageStrategy()
            except:
                strat = MovingAverageStrategy()
        elif req.strategy == "ensemble":
            strat = EnsembleSignalStrategy()
        else:
            strat = MovingAverageStrategy()

        engine = BacktestEngine(initial_capital=req.initial_capital)
        result = engine.run(df, strat)

        return {
            "symbol": req.symbol,
            "strategy": strat.name,
            "metrics": result.metrics,
            "equity_curve": [{"date": idx.strftime('%Y-%m-%d'), "equity": float(val)} for idx, val in result.equity_curve.items()],
            "trades": result.trades.to_dict(orient='records') if not result.trades.empty else [],
            "signals": result.signals[result.signals != 0].to_dict()
        }
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest/compare")
def backtest_compare(symbol: str = Query("BTC-USD"), period: str = Query("1y"), initial_capital: float = Query(10000)):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        from crypto_prediction.features.technical import FeatureEngineer
        eng = FeatureEngineer()
        df = eng.engineer(df)

        strategies = [
            MovingAverageStrategy(20, 50),
            MovingAverageStrategy(10, 30),
            RSIStrategy(30, 70),
            EnsembleSignalStrategy()
        ]

        engine = BacktestEngine(initial_capital=initial_capital)
        results = engine.compare_strategies(df, strategies)

        comparison = {}
        for name, res in results.items():
            comparison[name] = res.metrics

        return {"symbol": symbol, "comparison": comparison}
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols")
def list_symbols():
    return {"symbols": config.data.supported_symbols, "binance_map": config.data.binance_map}

@app.get("/models")
def list_models():
    from pathlib import Path
    models_dir = Path("models")
    if not models_dir.exists():
        return {"models": []}
    files = [f.name for f in models_dir.glob("*")]
    return {"models": files}

@app.get("/settings")
def get_settings():
    """Get current settings and config"""
    return {
        "data": {
            "supported_symbols": config.data.supported_symbols,
            "sequence_length": config.data.sequence_length,
            "test_size": config.data.test_size,
            "val_size": config.data.val_size
        },
        "features": {
            "use_technical": config.features.use_technical_indicators,
            "use_sentiment": config.features.use_sentiment,
            "use_advanced": config.features.use_advanced_indicators,
            "sma_windows": config.features.sma_windows,
            "rsi_window": config.features.rsi_window
        },
        "models": {
            "lstm": {
                "hidden_size": config.model.lstm_hidden_size,
                "num_layers": config.model.lstm_num_layers,
                "bidirectional": config.model.lstm_bidirectional,
                "use_attention": config.model.lstm_use_attention
            },
            "transformer": {
                "d_model": config.model.transformer_d_model,
                "nhead": config.model.transformer_nhead,
                "num_layers": config.model.transformer_num_layers,
                "use_learnable_pe": config.model.transformer_use_learnable_pe
            },
            "xgboost": {
                "n_estimators": config.model.xgb_n_estimators,
                "max_depth": config.model.xgb_max_depth,
                "learning_rate": config.model.xgb_learning_rate
            },
            "ensemble": {
                "weights": config.model.ensemble_weights,
                "use_stacking": config.model.ensemble_use_stacking,
                "use_dynamic": config.model.ensemble_use_dynamic_weights
            }
        },
        "trading": {
            "risk_per_trade": 0.02,
            "atr_sl_multiplier": 1.5,
            "atr_tp_multiplier": 3.0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
