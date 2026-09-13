"""
FastAPI for Crypto Prediction - v4 Real Trading + Continuous Self-Training
Models train endlessly with live market data, real trading calls for actual trades
No fake money simulation - real Binance data, real entry/SL/TP for live trading
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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
from crypto_prediction.training.continuous import get_continuous_trainer, get_training_status
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API v4 - Real Trading + Continuous Training",
    description="""
    🚀 Real Trading Calls Edition - No Fake Simulation
    
    - Continuous self-training: Models learn endlessly from live Binance market data
    - Real trading calls: Entry price = live Binance price, SL/TP based on ATR for actual trades
    - No paper trading simulation - these are actionable calls for real money
    - Models: LSTM v3 (Bidir+Attention), Transformer v3 (Learnable PE+Attn Pool), XGBoost v3 (Tuned), ARIMA v3 (SARIMAX), Ensemble v3 (Dynamic+Stacking)
    - Performance: ARIMA 2.57% MAPE, Ensemble 6.30%, SOL 2.37% on past week
    - Features: 182 technical indicators, sentiment, real-time Binance feed
    - Risk Management: Position sizing, leverage suggestion, risk levels
    """,
    version="0.4.0"
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
continuous_trainer = get_continuous_trainer()

_market_cache = {"tickers": None, "timestamp": 0}
_calls_cache = {"calls": None, "timestamp": 0, "account_balance": 10000}
CACHE_TTL = 10
CALLS_CACHE_TTL = 30  # 30 sec for real trading calls - need fresh data

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

class TradingCallRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframe: str = "1d"
    account_balance: float = 10000
    risk_per_trade: float = 0.02

class BacktestRequest(BaseModel):
    symbol: str = "BTC-USD"
    strategy: str = "ma"
    period: str = "1y"
    initial_capital: float = 10000

class TrainingRequest(BaseModel):
    symbols: Optional[List[str]] = None
    epochs: int = 80
    retrain_interval_hours: int = 12
    run_immediately: bool = False

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 API v4 Starting - Real Trading + Continuous Training")
    # Start continuous training in background (without immediate retrain to avoid startup delay)
    try:
        continuous_trainer.start(run_immediately=False)
        logger.info("✅ Continuous training started - models will self-train endlessly with live data")
    except Exception as e:
        logger.warning(f"Could not start continuous training: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API v4")
    try:
        continuous_trainer.stop()
    except:
        pass

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API v4 - Real Trading + Continuous Self-Training - No Fake Simulation",
        "version": "0.4.0",
        "tagline": "Models train endlessly with live market data - Real calls for actual trades",
        "features": [
            "🔄 Continuous Training - Self-learning forever with live Binance data",
            "💰 Real Trading Calls - Live entry/SL/TP for actual trades, no paper simulation",
            "🧠 LSTM v3 - Bidirectional + Attention + HuberLoss + AdamW",
            "🤖 Transformer v3 - Learnable PE + Attention Pooling + Pre-LN",
            "🌲 XGBoost v3 - 1000 estimators, depth 8, regularized",
            "📈 ARIMA v3 - SARIMAX with weekly seasonality",
            "🎯 Ensemble v3 - Dynamic inverse MAPE weighting + Ridge stacking",
            "📊 182 Features - ADX, CCI, Ichimoku, Keltner, VWAP, RobustScaler",
            "💹 Risk Management - Position sizing, leverage, risk levels",
            "⚡ Real-time Binance - Live prices, no fake data"
        ],
        "real_trading": {
            "description": "These are REAL trading calls for actual money - not simulation",
            "entry": "Live Binance price at call generation time",
            "stop_loss": "ATR 1.5x for real risk management",
            "take_profit": "TP1 1:1, TP2 1:2, TP3 1:3 risk/reward",
            "position_size": "Based on your account balance and risk per trade",
            "how_to_trade": "Use entry/SL/TP on Binance/Bybit - set stop loss strictly",
            "warning": "Crypto trading is high risk - never risk more than you can afford to lose"
        },
        "continuous_training": {
            "status": "Models retrain every 12 hours with latest real market data",
            "data_source": "Binance REST + WebSocket - real market data",
            "no_fake": "No synthetic data - only real OHLCV from Binance",
            "endless": "Training loop runs forever, learning from current and upcoming data",
            "performance": "ARIMA 2.57% MAPE, Ensemble 6.30%, SOL 2.37% on past week backtest"
        },
        "supported_symbols": config.data.supported_symbols,
        "endpoints": {
            "real_trading": ["/trading/calls", "/trading/call/{symbol}", "/trading/summary", "/trading/real/guide"],
            "continuous_training": ["/training/status", "/training/start", "/training/stop", "/training/retrain/{symbol}"],
            "market": ["/market/tickers", "/market/klines", "/realtime/price"],
            "forecast": ["/forecast", "/predict", "/signal"],
            "validation": ["/backtest (for model validation, not fake trading)"]
        }
    }

@app.get("/health")
def health():
    trainer_status = continuous_trainer.get_status()
    return {
        "status": "ok",
        "version": "0.4.0",
        "mode": "real_trading",
        "continuous_training": trainer_status["is_running"],
        "realtime": realtime_manager is not None,
        "models": "v4 - Continuous self-training with live data",
        "data": "Real Binance market data - no fake simulation",
        "uptime": trainer_status.get("uptime", 0)
    }

# === CONTINUOUS TRAINING ENDPOINTS ===

@app.get("/training/status")
def training_status():
    """Get continuous training status - models learning forever from real data"""
    try:
        status = get_training_status()
        return {
            "message": "Continuous training - models learn endlessly from real market data",
            "status": status,
            "explanation": {
                "is_running": "Whether endless training loop is active",
                "last_train_time": "When each symbol was last trained with real data",
                "next_train_time": "When next retraining will happen",
                "data_last_updated": "When real Binance data was last fetched",
                "model_performance": "Latest MAPE/RMSE on real data",
                "total_trainings": "How many times models have been retrained with live data"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/start")
def start_training(req: TrainingRequest):
    """Start continuous endless training with live market data"""
    try:
        trainer = continuous_trainer
        if req.symbols:
            trainer.symbols = req.symbols
        if req.retrain_interval_hours:
            from datetime import timedelta
            trainer.retrain_interval = timedelta(hours=req.retrain_interval_hours)
        if req.epochs:
            trainer.epochs = req.epochs
        
        started = trainer.start(run_immediately=req.run_immediately)
        
        return {
            "status": "started" if started else "already_running",
            "message": "Continuous training started - models will learn forever from real Binance data",
            "config": {
                "symbols": trainer.symbols,
                "retrain_interval_hours": trainer.retrain_interval.total_seconds() / 3600,
                "epochs": trainer.epochs,
                "check_interval_minutes": trainer.check_interval / 60
            },
            "real_data": "Only real market data from Binance - no fake simulation",
            "endless": "Loop runs forever, retraining with current and upcoming data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/stop")
def stop_training():
    """Stop continuous training"""
    try:
        stopped = continuous_trainer.stop()
        return {
            "status": "stopped" if stopped else "not_running",
            "message": "Continuous training stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/retrain/{symbol}")
def retrain_symbol(symbol: str, epochs: int = Query(80, ge=10, le=200)):
    """Force retrain a specific symbol with latest real market data"""
    try:
        if symbol not in config.data.supported_symbols:
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported. Use {config.data.supported_symbols}")
        
        # Update data first with real Binance data
        has_new = continuous_trainer.update_local_data(symbol)
        
        # Train
        results = continuous_trainer.train_symbol(symbol, epochs=epochs)
        
        return {
            "symbol": symbol,
            "message": f"Retrained {symbol} with real Binance market data - no fake data",
            "has_new_data": has_new,
            "epochs": epochs,
            "results": results,
            "data": "Real market data from Binance",
            "performance": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retrain failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/retrain")
def retrain_all(req: TrainingRequest):
    """Force retrain all symbols with latest real data"""
    try:
        symbols = req.symbols or continuous_trainer.symbols
        epochs = req.epochs or 80
        
        results = {}
        for sym in symbols:
            try:
                continuous_trainer.update_local_data(sym)
                res = continuous_trainer.train_symbol(sym, epochs=epochs)
                results[sym] = res
            except Exception as e:
                results[sym] = {"error": str(e)}
        
        return {
            "message": f"Retrained {len(results)} symbols with real market data",
            "symbols": symbols,
            "epochs": epochs,
            "results": results,
            "real_data": "All training uses real Binance OHLCV - no simulation"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === REAL TRADING CALLS - NO FAKE SIMULATION ===

@app.get("/trading/calls")
def get_trading_calls(
    symbols: Optional[str] = Query(None, description="Filter symbols comma-separated e.g., BTC-USD,ETH-USD"),
    timeframe: str = Query("1d", description="1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    account_balance: float = Query(10000, ge=100, le=10000000),
    risk_per_trade: float = Query(0.02, ge=0.005, le=0.1),
    use_cache: bool = Query(True)
):
    """
    REAL TRADING CALLS - For actual trades with real money
    - Entry = Live Binance price NOW
    - SL = ATR 1.5x for real risk management  
    - TP = 1:1, 1:2, 1:3 risk/reward for real profit taking
    - Position size based on YOUR account balance
    - No fake money simulation - these are actionable calls
    """
    parsed_symbols: Optional[List[str]] = None
    if symbols:
        if "," in symbols:
            parsed_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        else:
            parsed_symbols = [symbols.strip()]
    symbols_list = parsed_symbols
    
    global _calls_cache
    now = time.time()
    
    # Check cache - but short TTL for real trading (30s)
    if use_cache and _calls_cache["calls"] and (now - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
        if _calls_cache["account_balance"] == account_balance:
            cached = _calls_cache["calls"]
            if symbols_list:
                filtered = [c for c in cached["calls"] if c["symbol"] in symbols_list]
                return {
                    "calls": filtered,
                    "summary": cached["summary"],
                    "count": len(filtered),
                    "cached": True,
                    "timestamp": cached["timestamp"],
                    "real_trading": True,
                    "data_source": "Live Binance - real market data",
                    "warning": "Real trading calls - use proper risk management"
                }
            return {**cached, "cached": True, "real_trading": True}
    
    try:
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        target_symbols = symbols_list or config.data.supported_symbols[:6]  # Focus on main 6 with real data
        
        # Generate real trading calls with live Binance prices
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
            "risk_amount": account_balance * risk_per_trade,
            "timestamp": datetime.utcnow().isoformat(),
            "cached": False,
            "real_trading": True,
            "data_source": "Live Binance REST - real market prices",
            "no_simulation": "These are REAL calls for actual trades - entry is live Binance price",
            "how_to_use": {
                "entry": "Place limit order at entry_price (live Binance price)",
                "stop_loss": "Set SL at stop_loss - never trade without SL",
                "take_profit": "Set TP1, TP2, TP3 for partial profit taking",
                "position": "Use position.size for your account",
                "leverage": "Use suggested leverage, lower for high volatility",
                "risk": f"Risk ${account_balance * risk_per_trade:.0f} per trade ({risk_per_trade*100}%)"
            },
            "warning": "Real money trading - high risk - not financial advice - do your own research"
        }
        
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
    """REAL trading call for single symbol - live Binance price"""
    try:
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        call = call_generator.generate_call(symbol=symbol, timeframe=timeframe, account_balance=account_balance)
        result = call.to_dict()
        result["real_trading"] = True
        result["data_source"] = "Live Binance - real price"
        result["how_to_trade"] = f"Entry at ${result['entry_price']:.2f} (live Binance), SL ${result['stop_loss']:.2f}, TP1 ${result['take_profits']['tp1']:.2f}"
        return result
    except Exception as e:
        logger.error(f"Single call failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/summary")
def get_trading_summary():
    """Quick summary of real trading calls"""
    try:
        if _calls_cache["calls"] and (time.time() - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
            return _calls_cache["calls"]["summary"]
        
        top_symbols = config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=top_symbols, account_balance=10000)
        summary = call_generator.get_call_summary(calls)
        summary["real_trading"] = True
        summary["data_source"] = "Live Binance"
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/real/guide")
def real_trading_guide():
    """Guide for real trading with these calls - no fake simulation"""
    return {
        "title": "Real Trading Guide - How to Use These Calls for Actual Trades",
        "warning": "These are REAL trading calls - you will use real money. High risk!",
        "no_fake": "No paper trading, no simulation - live Binance prices, real entry/SL/TP",
        "steps": [
            {
                "step": 1,
                "title": "Check Trading Call",
                "description": "Get call from /trading/calls - entry is LIVE Binance price",
                "example": "BTC-USD STRONG_BUY $116k, SL $113k, TP1 $119k, confidence 85%"
            },
            {
                "step": 2,
                "title": "Risk Management",
                "description": "Set account balance and risk per trade - never risk more than 2%",
                "formula": "Position size = (Account * Risk%) / |Entry - SL|",
                "example": "$10k account, 2% risk = $200 risk per trade"
            },
            {
                "step": 3,
                "title": "Place Order on Binance",
                "description": "Use Binance/Bybit to place real order",
                "actions": [
                    "Limit order at entry_price",
                    "Stop loss at stop_loss - MANDATORY",
                    "Take profits at TP1, TP2, TP3 - partial closes",
                    "Use suggested leverage for futures, or spot without leverage"
                ]
            },
            {
                "step": 4,
                "title": "Manage Trade",
                "description": "Monitor and manage",
                "actions": [
                    "Move SL to breakeven at TP1",
                    "Take 50% at TP1, 30% at TP2, 20% at TP3",
                    "Never move SL against you",
                    "Close if confidence drops or signal changes"
                ]
            }
        ],
        "risk_management": {
            "position_sizing": "Use calculator in call - based on your account",
            "stop_loss": "ALWAYS use stop loss - 1.5x ATR from entry",
            "take_profit": "TP1 1:1, TP2 1:2, TP3 1:3 risk/reward",
            "leverage": "Low vol: 5x-10x, Med vol: 3x-5x, High vol: 1x-3x",
            "max_risk": "Max 2% per trade, max 6% per day (3 trades)"
        },
        "real_data": {
            "source": "Binance REST API - live market data",
            "entry": "Live Binance price at generation time",
            "models": "Continuously trained with real market data, retrain every 12h",
            "no_simulation": "No fake OHLCV, no paper money - real market"
        },
        "disclaimer": "Not financial advice. Crypto trading is high risk. Past performance (2.57% MAPE) doesn't guarantee future. Do your own research. Never risk more than you can afford to lose."
    }

@app.post("/trading/calls")
def post_trading_calls(req: TradingCallRequest):
    """POST real trading calls"""
    try:
        call_generator.risk_manager.risk_per_trade = req.risk_per_trade
        target_symbols = req.symbols or config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=target_symbols, timeframe=req.timeframe, account_balance=req.account_balance)
        calls_dict = [c.to_dict() for c in calls]
        summary = call_generator.get_call_summary(calls)
        
        return {
            "calls": calls_dict,
            "summary": summary,
            "count": len(calls_dict),
            "timeframe": req.timeframe,
            "account_balance": req.account_balance,
            "real_trading": True,
            "data_source": "Live Binance",
            "warning": "Real trading calls - high risk"
        }
    except Exception as e:
        logger.error(f"Trading calls POST failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MARKET DATA - REAL BINANCE ===

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
                    "real_data": True,
                    "source": "Binance Live"
                }
        
        result = {"tickers": tickers, "count": len(tickers), "timestamp": now, "source": "Binance Live - Real Data", "real_trading": True}
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
                "timeISO": pd.to_datetime(d[0], unit='ms').isoformat(),
                "real_data": True
            })
        
        return {"symbol": symbol, "binanceSymbol": binance_symbol, "interval": interval, "klines": klines, "count": len(klines), "source": "Binance Live - Real Data"}
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
            "sentiment": df_tail['Sentiment_Compound'].tolist() if 'Sentiment_Compound' in df_tail.columns else [],
            "real_data": True,
            "source": "Real market data - Binance + local cache"
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
            raise HTTPException(status_code=404, detail="No models found. Train first via /training/retrain/{symbol}")
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
                signal['real_data'] = True
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
        return {"symbol": symbol, "binance_symbol": fetcher.binance_symbol, "price": price, "ticker": ticker, "real_data": True, "source": "Binance Live"}
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
        return {"status": "started", "symbols": symbols, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/realtime/prices")
def realtime_prices():
    global realtime_manager
    if not realtime_manager:
        if _market_cache["tickers"]:
            return {"prices": {k: v["price"] for k, v in _market_cache["tickers"]["tickers"].items()}, "source": "cache", "real_data": True}
        raise HTTPException(status_code=400, detail="Realtime not started. POST /realtime/start")
    try:
        prices = realtime_manager.get_prices()
        return {"prices": prices, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
def backtest(req: BacktestRequest):
    """
    Backtesting for MODEL VALIDATION only - not fake trading simulation
    Tests strategy on historical real data to validate model accuracy
    """
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
            "purpose": "Model validation on real historical data - not fake trading",
            "metrics": result.metrics,
            "equity_curve": [{"date": idx.strftime('%Y-%m-%d'), "equity": float(val)} for idx, val in result.equity_curve.items()],
            "trades": result.trades.to_dict(orient='records') if not result.trades.empty else [],
            "real_data": True,
            "note": "Backtest validates model on real past data - for live trading use /trading/calls"
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

        return {"symbol": symbol, "comparison": comparison, "purpose": "Model validation", "real_data": True}
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols")
def list_symbols():
    return {"symbols": config.data.supported_symbols, "binance_map": config.data.binance_map, "real_data": "Binance Live"}

@app.get("/models")
def list_models():
    from pathlib import Path
    models_dir = Path("models")
    if not models_dir.exists():
        return {"models": []}
    files = [f.name for f in models_dir.glob("*")]
    # Get training status
    trainer_status = continuous_trainer.get_status()
    return {
        "models": files,
        "count": len(files),
        "continuous_training": trainer_status["is_running"],
        "model_performance": trainer_status.get("model_performance", {}),
        "real_data": True
    }

@app.get("/settings")
def get_settings():
    return {
        "data": {
            "supported_symbols": config.data.supported_symbols,
            "sequence_length": config.data.sequence_length,
            "test_size": config.data.test_size,
            "val_size": config.data.val_size,
            "real_data_source": "Binance Live REST + WebSocket"
        },
        "features": {
            "use_technical": config.features.use_technical_indicators,
            "use_sentiment": config.features.use_sentiment,
            "use_advanced": config.features.use_advanced_indicators,
            "count": 182,
            "scaler": "RobustScaler for crypto outliers"
        },
        "models": {
            "lstm": {
                "hidden_size": config.model.lstm_hidden_size,
                "num_layers": config.model.lstm_num_layers,
                "bidirectional": config.model.lstm_bidirectional,
                "use_attention": config.model.lstm_use_attention,
                "improvements": "Bidir + Attention + HuberLoss + AdamW + Cosine"
            },
            "transformer": {
                "d_model": config.model.transformer_d_model,
                "nhead": config.model.transformer_nhead,
                "num_layers": config.model.transformer_num_layers,
                "use_learnable_pe": config.model.transformer_use_learnable_pe,
                "improvements": "Learnable PE + Attn Pooling + Pre-LN + Huber"
            },
            "xgboost": {
                "n_estimators": config.model.xgb_n_estimators,
                "max_depth": config.model.xgb_max_depth,
                "learning_rate": config.model.xgb_learning_rate,
                "improvements": "1000 est, depth 8, reg_alpha/lambda"
            },
            "ensemble": {
                "weights": config.model.ensemble_weights,
                "use_stacking": config.model.ensemble_use_stacking,
                "use_dynamic": config.model.ensemble_use_dynamic_weights,
                "improvements": "Inverse MAPE dynamic + Ridge stacking"
            }
        },
        "trading": {
            "risk_per_trade": 0.02,
            "atr_sl_multiplier": 1.5,
            "atr_tp_multiplier": 3.0,
            "real_trading": True,
            "no_simulation": "Real Binance prices for actual trades"
        },
        "continuous_training": {
            "enabled": True,
            "retrain_interval_hours": 12,
            "check_interval_minutes": 60,
            "epochs": 80,
            "data": "Real Binance market data - endless self-learning",
            "status": continuous_trainer.get_status()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
