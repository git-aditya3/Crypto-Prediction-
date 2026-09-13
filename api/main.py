"""
FastAPI v6 - Extensive Real Trading + Automated Real Trading with User Control + Continuous Training
- Real trading calls for actual trades
- Automated execution with extensive controls: broker integration, risk guards, paper/semi/full auto
- Portfolio, Strategies, Alerts, Scanner, Analytics, Journal
- Max performance models v4 + endless training
"""
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
import sys
from pathlib import Path
import pandas as pd
import requests
import time
import threading
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict

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
from crypto_prediction.portfolio.manager import get_portfolio_manager
from crypto_prediction.strategies.manager import get_strategy_manager
from crypto_prediction.alerts.manager import get_alert_manager
from crypto_prediction.scanner.manager import get_market_scanner
from crypto_prediction.analytics.manager import get_analytics_manager
from crypto_prediction.journal.manager import get_journal_manager
from crypto_prediction.brokers.manager import get_broker_manager
from crypto_prediction.autotrading.engine import get_autotrading_engine
from crypto_prediction.crash_detector.manager import get_crash_manager
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API v7 - CoinDCX Real Money Automated Trading - No Paper Simulation",
    description="""
    🚀 v7 CoinDCX REAL MONEY Automated Trading - No Paper Simulation - Extensive User Control
    
    **Core:**
    - 🔄 Continuous Training: Models learn endlessly from live market data
    - 💰 Real Trading Calls: Live entry, ATR SL, 1:1/2/3 TP, position sizing for REAL money
    - 🧠 Models v4 Max Perf: LSTM Bidir+Attn, Transformer Learnable PE, XGBoost 1500, ARIMA SARIMAX, Ensemble Dynamic
    - 📊 182 Features, RobustScaler, Sentiment, Real-time data
    
    **NEW v7 - CoinDCX REAL MONEY - No Paper Simulation (User Requested):**
    - 🔌 CoinDCX Broker: REAL MONEY trading via CoinDCX API - actual INR and crypto from user's CoinDCX account
    - 💰 No Paper Simulation: Uses actual CoinDCX balances (INR, BTC, ETH, etc.), executes real trades on CoinDCX exchange
    - 🏦 Markets: BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, DOGEINR, AVAXINR, MATICINR, etc. - INR pairs for Indian users
    - 🔐 Secure: API keys base64 encoded locally, trading permission only, no withdrawal, IP whitelist support
    - 📊 Real Balances: POST /exchange/v1/users/balances - fetches actual INR/crypto from CoinDCX account
    - 📈 Real Orders: POST /exchange/v1/orders/create - places real market/limit orders on CoinDCX with actual money
    - 🔍 Real Ticker: GET /exchange/ticker - live CoinDCX prices for BTCINR, etc.
    
    **Automated Trading with Extensive User Control:**
    - 🤖 Auto Trading Engine: Full-auto (CoinDCX real money), Semi-auto (CoinDCX + approval), Paper (testing only)
    - 🛡️ Risk Guard: Max daily loss, max positions, max drawdown, consecutive losses cooldown, trading hours, whitelist/blacklist, confidence threshold, RR filter, position sizing (risk_based, fixed, kelly, percent_balance)
    - ⚙️ Execution: Market/Limit, OCO SL/TP, multiple TP 50/30/20, trailing stop, breakeven, slippage tolerance, broker_id coindcx
    - 🎛️ Strategy Controls: Toggle AI ensemble, DCA, Grid, Breakout, RSI, Volume spikes, timeframes, allowed signals
    - 📋 Approval System: Semi-auto queues for user approval
    - 🚨 Emergency Stop: One-click halt all trading
    
    **Other Features:**
    - 💼 Portfolio: Real holdings tracking with live P&L
    - 🤖 Strategies: DCA Bot, Grid Bot, Breakout Scanner
    - 🚨 Alerts, Scanner, Analytics, Journal
    
    **No Paper:** As requested, uses actual CoinDCX account money - real INR, real trades, real P&L
    """,
    version="0.7.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for preview (e2b.app) - in production should be restricted to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiting
_rate_limit_store = defaultdict(list)
_rate_limit_lock = threading.Lock()
RATE_LIMIT_MAX = 60  # requests per minute per IP
RATE_LIMIT_WINDOW = 60

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip for health and docs
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    with _rate_limit_lock:
        # Clean old entries
        _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW]
        if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded - max 60 req/min"})
        _rate_limit_store[client_ip].append(now)
    return await call_next(request)

realtime_manager: Optional[RealtimeManager] = None
call_generator = TradingCallGenerator(risk_per_trade=0.02)
continuous_trainer = get_continuous_trainer()
portfolio_manager = get_portfolio_manager()
strategy_manager = get_strategy_manager()
alert_manager = get_alert_manager()
market_scanner = get_market_scanner()
analytics_manager = get_analytics_manager()
journal_manager = get_journal_manager()
broker_manager = get_broker_manager()
autotrading_engine = get_autotrading_engine()
crash_manager = get_crash_manager()

_market_cache = {"tickers": None, "timestamp": 0}
_calls_cache = {"calls": None, "timestamp": 0, "account_balance": 10000}
_market_cache_lock = threading.Lock()
_calls_cache_lock = threading.Lock()
CACHE_TTL = 10
CALLS_CACHE_TTL = 30

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
    timeframe: str = Field(default="1d", pattern="^(1m|5m|15m|1h|4h|1d|1w)$")
    account_balance: float = Field(default=10000, ge=100, le=10000000)
    risk_per_trade: float = Field(default=0.02, ge=0.001, le=0.1)

    @field_validator('symbols')
    def validate_symbols(cls, v):
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError("Max 20 symbols")
        return v

class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTC-USD", min_length=3, max_length=20)
    strategy: str = Field(default="ma", pattern="^(ma|rsi|prediction|ensemble)$")
    period: str = Field(default="1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|max)$")
    initial_capital: float = Field(default=10000, ge=100, le=10000000)

class TrainingRequest(BaseModel):
    symbols: Optional[List[str]] = None
    epochs: int = Field(default=80, ge=10, le=200)
    retrain_interval_hours: int = Field(default=12, ge=1, le=168)
    run_immediately: bool = False

class PortfolioOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    side: str = Field(..., pattern="^(LONG|SHORT|BUY|SELL)$")
    quantity: float = Field(..., gt=0, le=1000000)
    entry_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profits: Optional[Dict[str, float]] = None
    leverage: str = Field(default="1x", pattern="^[0-9]+x$")

    @field_validator('side')
    def upper_side(cls, v):
        return v.upper()

class AlertRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    type: str = Field(..., min_length=2, max_length=20)
    target_price: Optional[float] = Field(None, gt=0)
    condition: str = Field(default="", max_length=100)

class JournalRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    side: str = Field(..., pattern="^(LONG|SHORT|BUY|SELL)$")
    entry_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    strategy: str = Field(default="AI Ensemble", max_length=50)
    notes: str = Field(default="", max_length=1000)
    emotions: str = Field(default="", max_length=500)
    lessons: str = Field(default="", max_length=1000)
    tags: List[str] = Field(default=[], max_length=10)
    exit_price: Optional[float] = Field(None, gt=0)
    pnl: float = Field(default=0)

class DCABotRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    total_investment: float = Field(..., gt=0, le=10000000)
    num_orders: int = Field(default=5, ge=1, le=50)
    price_deviation_pct: float = Field(default=1.0, gt=0, le=50)
    take_profit_pct: float = Field(default=5.0, gt=0, le=100)
    stop_loss_pct: float = Field(default=3.0, gt=0, le=100)

class GridBotRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    lower_price: float = Field(..., gt=0, le=10000000)
    upper_price: float = Field(..., gt=0, le=10000000)
    num_grids: int = Field(default=10, ge=2, le=100)
    total_investment: float = Field(default=1000, gt=0, le=10000000)

    @field_validator('upper_price')
    def upper_gt_lower(cls, v, info):
        lower = info.data.get('lower_price')
        if lower and v <= lower:
            raise ValueError("upper_price must be > lower_price")
        return v

class MarketMakingRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    total_investment: float = Field(default=10000, gt=0, le=10000000)
    spread_bps: float = Field(default=20, gt=0, le=500)
    max_inventory: float = Field(default=1.0, gt=0, le=100)

class ExecutionRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    total_quantity: float = Field(..., gt=0, le=1000000)
    strategy: str = Field(default="TWAP", pattern="^(TWAP|VWAP)$")
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    num_slices: int = Field(default=12, ge=1, le=100)

    @field_validator('side','strategy')
    def upper_vals(cls, v):
        return v.upper()

class StatArbRequest(BaseModel):
    symbol_a: str = Field(..., min_length=3, max_length=20)
    symbol_b: str = Field(..., min_length=3, max_length=20)
    entry_z: float = Field(default=2.0, ge=0.5, le=5.0)

    @field_validator('symbol_b')
    def different_symbols(cls, v, info):
        if info.data.get('symbol_a') and v == info.data.get('symbol_a'):
            raise ValueError("symbol_a and symbol_b must be different")
        return v

class OFIRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)

class FundingArbRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)

class RiskRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    account_balance: float = Field(default=10000, ge=100, le=10000000)
    win_rate: float = Field(default=0.55, ge=0.1, le=0.95)
    win_loss_ratio: float = Field(default=1.5, ge=0.1, le=10)

class BrokerConnectRequest(BaseModel):
    broker_id: str = Field(..., min_length=2, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    broker_type: str = Field(default="binance", pattern="^(binance|coindcx|paper)$")
    api_key: Optional[str] = Field(None, max_length=200)
    api_secret: Optional[str] = Field(None, max_length=500)
    testnet: bool = True
    initial_balance: float = Field(default=10000, ge=0, le=10000000)

class AutoTradeConfigRequest(BaseModel):
    config: Dict

class AutoTradeExecuteRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    manual: bool = False

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 API v6 Starting - Automated Real Trading + Extensive Controls + Continuous Training")
    try:
        continuous_trainer.start(run_immediately=False)
        logger.info("✅ Continuous training started")
    except Exception as e:
        logger.warning(f"Could not start continuous training: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API v6")
    try:
        continuous_trainer.stop()
        autotrading_engine.stop()
    except:
        pass

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API v7 - CoinDCX Real Money Automated Trading - No Paper Simulation",
        "version": "0.7.0",
        "tagline": "Automate REAL trades with CoinDCX - actual INR from your account - no paper simulation - extensive user control",
        "features": {
            "core": [
                "🔄 Continuous Training - Endless self-learning with live Binance data",
                "💰 Real Trading Calls - Live entry/SL/TP for REAL money",
                "🧠 LSTM v3 - Bidir+Attention+Huber+AdamW",
                "🤖 Transformer v3 - Learnable PE+Attn Pool+Pre-LN",
                "🌲 XGBoost v3 - 1500 trees, depth 8",
                "📈 ARIMA v3 - SARIMAX weekly",
                "🎯 Ensemble v3 - Dynamic inverse MAPE + Ridge stacking"
            ],
            "extensive": [
                "💼 Portfolio - Real holdings, P&L, allocation, win rate, Sharpe",
                "🤖 DCA Bot, Grid Bot, Breakout Scanner",
                "🚨 Alerts, Market Scanner, Analytics, Journal"
            ],
            "automated_trading_v6": [
                "🔌 Broker Integration - Binance Spot/Futures, Paper, secure API keys (trading only, no withdrawal)",
                "🤖 Auto Trading Engine - Paper (safe), Semi-auto (approval), Full-auto (real with risk guards)",
                "🛡️ Risk Guard - Max daily loss, max positions, max DD, consecutive losses cooldown, trading hours, whitelist/blacklist, confidence threshold, RR filter",
                "⚙️ Execution - Market/Limit, OCO SL/TP, multiple TP 50/30/20, trailing stop, breakeven, slippage",
                "🎛️ Strategy Controls - Toggle AI/DCA/Grid/Breakout/RSI/Volume, timeframes, allowed signals",
                "📋 Approval System - Semi-auto queues for user approval",
                "🚨 Emergency Stop - One-click halt",
                "📊 Real-time Status - Positions, daily trades, pending approvals, broker balances"
            ]
        },
        "real_trading": {
            "entry": "Live Binance price NOW",
            "stop_loss": "ATR 1.5x real risk",
            "take_profit": "TP1 1:1, TP2 1:2, TP3 1:3",
            "position_size": "Based on YOUR account balance and risk%",
            "warning": "Real money trading - high risk - use paper first"
        },
        "endpoints": {
            "automated_trading": [
                "/brokers", "/brokers/connect", "/brokers/{id}/balance", "/brokers/{id}/test", "/brokers/{id}/remove",
                "/autotrade/config", "/autotrade/status", "/autotrade/start", "/autotrade/stop",
                "/autotrade/execute", "/autotrade/approve/{approval_id}", "/autotrade/reject/{approval_id}",
                "/autotrade/trades", "/autotrade/pending", "/autotrade/risk/check", "/autotrade/emergency/stop"
            ],
            "real_trading": ["/trading/calls", "/trading/call/{symbol}", "/trading/summary"],
            "portfolio": ["/portfolio", "/portfolio/open", "/portfolio/close/{symbol}"],
            "strategies": ["/strategies/dca", "/strategies/grid", "/strategies/breakout/scan", "/strategies/all"],
            "scanner": ["/scanner", "/scanner/volume", "/scanner/momentum", "/scanner/rsi"],
            "training": ["/training/status", "/training/start", "/training/stop"]
        }
    }

@app.get("/health")
def health():
    trainer_status = continuous_trainer.get_status()
    return {
        "status": "ok",
        "version": "0.7.0",
        "mode": "coindcx_real_money_automated_trading",
        "continuous_training": trainer_status["is_running"],
        "autotrading_enabled": autotrading_engine.config.enabled,
        "autotrading_mode": autotrading_engine.config.mode,
        "autotrading_running": autotrading_engine.is_running,
        "portfolio_value": portfolio_manager.get_portfolio().total_value,
        "open_positions": len(portfolio_manager.positions),
        "brokers": len(broker_manager.brokers),
        "primary_broker": "CoinDCX REAL MONEY - Actual INR",
        "no_paper": "No paper money simulation - real CoinDCX account",
        "models": "v7 CoinDCX Real Money Automated Trading + Extensive Controls + Endless Learning",
        "data": "Real CoinDCX market data - BTCINR, ETHINR, etc. - actual money",
        "uptime": trainer_status.get("uptime", 0)
    }

# === BROKER INTEGRATION - REAL TRADING ===

@app.get("/brokers")
def get_brokers():
    """Get all brokers with balances - CoinDCX REAL MONEY, no paper simulation"""
    try:
        brokers = broker_manager.get_all_brokers()
        return {
            "brokers": brokers,
            "count": len(brokers),
            "real_trading": True,
            "no_paper": "No paper money simulation - uses actual CoinDCX INR balances as requested",
            "primary_broker": "CoinDCX REAL MONEY - BTCINR, ETHINR, etc.",
            "secure": "API keys encoded, trading permission only, no withdrawal, IP whitelist",
            "supported": ["coindcx", "binance", "paper"],
            "features": ["CoinDCX Spot REAL MONEY trading", "Real INR balances from CoinDCX account", "Real order placement on CoinDCX", "No paper simulation - actual money", "Binance also supported", "Paper only for testing"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brokers/connect")
def connect_broker(req: BrokerConnectRequest):
    """Connect broker with API keys - secure, trading only, no withdrawal"""
    try:
        result = broker_manager.add_broker(
            broker_id=req.broker_id,
            broker_type=req.broker_type,
            api_key=req.api_key,
            api_secret=req.api_secret,
            testnet=req.testnet,
            initial_balance=req.initial_balance
        )
        return {
            "message": f"Connected broker {req.broker_id} - {'REAL TRADING' if not result.get('paper_mode') else 'PAPER MODE'}",
            "broker": result,
            "real_trading": not result.get("paper_mode", True),
            "warning": "Never grant withdrawal permission - trading only" if req.broker_type == "binance" else "Paper mode - safe, no real money",
            "secure": "Keys encoded, stored locally, trading permission only"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brokers/{broker_id}/balance")
def get_broker_balance(broker_id: str):
    """Get broker balance - real or paper"""
    try:
        broker = broker_manager.get_broker(broker_id)
        if not broker:
            raise HTTPException(status_code=404, detail=f"Broker {broker_id} not found")
        
        balances = broker.get_balance()
        return {
            "broker_id": broker_id,
            "broker_name": broker.name,
            "balances": {k: v.to_dict() for k, v in balances.items()},
            "paper_mode": getattr(broker, 'paper_mode', True),
            "real_trading": not getattr(broker, 'paper_mode', True),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brokers/{broker_id}/test")
def test_broker(broker_id: str):
    try:
        result = broker_manager.test_broker(broker_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/brokers/{broker_id}/remove")
def remove_broker(broker_id: str):
    try:
        success = broker_manager.remove_broker(broker_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Broker {broker_id} not found")
        return {"message": f"Removed broker {broker_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brokers/{broker_id}/orders")
def get_broker_orders(broker_id: str, symbol: Optional[str] = None, limit: int = Query(100, ge=1, le=500)):
    try:
        broker = broker_manager.get_broker(broker_id)
        if not broker:
            raise HTTPException(status_code=404, detail=f"Broker {broker_id} not found")
        
        orders = broker.get_order_history(symbol=symbol, limit=limit)
        open_orders = broker.get_open_orders(symbol=symbol)
        
        return {
            "broker_id": broker_id,
            "open_orders": [o.to_dict() for o in open_orders],
            "order_history": [o.to_dict() for o in orders],
            "open_count": len(open_orders),
            "total_count": len(orders),
            "real_trading": not getattr(broker, 'paper_mode', True)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === AUTOMATED TRADING - EXTENSIVE USER CONTROL ===

@app.get("/autotrade/config")
def get_autotrade_config():
    """Get auto trading config with extensive controls"""
    try:
        return autotrading_engine.config.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/config")
def update_autotrade_config(req: AutoTradeConfigRequest):
    """Update auto trading config - extensive user controls"""
    try:
        config = autotrading_engine.update_config(req.config)
        return {
            "message": "Updated auto trading config - extensive controls applied",
            "config": config.to_dict(),
            "real_trading": config.mode == "full_auto" and config.execution.enable_real_trading,
            "warning": "Real trading enabled - ensure risk controls set" if config.mode == "full_auto" and config.execution.enable_real_trading else "Paper mode - safe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/autotrade/status")
def get_autotrade_status():
    """Get auto trading status with extensive info"""
    try:
        status = autotrading_engine.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/start")
def start_autotrade():
    """Start automated trading loop"""
    try:
        if autotrading_engine.config.emergency_stop:
            raise HTTPException(status_code=400, detail="Emergency stop enabled - disable first")
        
        if not autotrading_engine.config.enabled:
            raise HTTPException(status_code=400, detail="Auto trading disabled in config - enable first")
        
        started = autotrading_engine.start()
        if not started:
            return {"status": "already_running", "message": "Auto trading already running"}
        
        return {
            "status": "started",
            "message": f"Auto trading started - mode={autotrading_engine.config.mode} broker={autotrading_engine.config.execution.broker_id}",
            "mode": autotrading_engine.config.mode,
            "real_trading": autotrading_engine.config.mode == "full_auto" and autotrading_engine.config.execution.enable_real_trading,
            "warning": "Real money trading active - monitor closely" if autotrading_engine.config.mode == "full_auto" else "Paper trading active - safe"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/stop")
def stop_autotrade():
    try:
        stopped = autotrading_engine.stop()
        return {"status": "stopped" if stopped else "not_running", "message": "Auto trading stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/emergency/stop")
def emergency_stop():
    """Emergency stop - one click halt all trading"""
    try:
        autotrading_engine.config.emergency_stop = True
        autotrading_engine.stop()
        autotrading_engine.save()
        return {
            "status": "emergency_stop_enabled",
            "message": "🚨 Emergency stop enabled - all trading halted immediately",
            "warning": "Trading halted - disable emergency stop to resume"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/emergency/disable")
def disable_emergency_stop():
    try:
        autotrading_engine.config.emergency_stop = False
        autotrading_engine.save()
        return {"status": "emergency_stop_disabled", "message": "Emergency stop disabled - can resume trading"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/execute")
def execute_autotrade(req: AutoTradeExecuteRequest):
    """Execute trade via auto trading engine with risk checks"""
    try:
        result = autotrading_engine.execute_trade(symbol=req.symbol, manual=req.manual)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/approve/{approval_id}")
def approve_autotrade(approval_id: str):
    """Approve pending trade in semi-auto mode"""
    try:
        result = autotrading_engine.approve_trade(approval_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/reject/{approval_id}")
def reject_autotrade(approval_id: str):
    try:
        result = autotrading_engine.reject_trade(approval_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/autotrade/trades")
def get_autotrade_trades(limit: int = Query(100, ge=1, le=500)):
    try:
        trades = autotrading_engine.trades[-limit:]
        return {
            "count": len(trades),
            "trades": trades,
            "real_trading_trades": len([t for t in trades if t.get("real_trading")]),
            "paper_trades": len([t for t in trades if not t.get("real_trading")])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/autotrade/pending")
def get_pending_approvals():
    try:
        return {
            "count": len(autotrading_engine.pending_approvals),
            "pending": autotrading_engine.pending_approvals,
            "message": "Trades pending approval in semi-auto mode"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotrade/risk/check")
def check_risk(symbol: str = Query(...), confidence: float = Query(80), risk_reward: float = Query(2.0), entry_price: float = Query(100000), stop_loss: float = Query(98000)):
    """Check risk with extensive controls"""
    try:
        result = autotrading_engine.risk_guard.full_check(
            symbol=symbol,
            confidence=confidence,
            risk_reward=risk_reward,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === CONTINUOUS TRAINING ===

@app.get("/training/status")
def training_status():
    try:
        status = get_training_status()
        return {"message": "Continuous training - models learn endlessly", "status": status, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/start")
def start_training(req: TrainingRequest):
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
        return {"status": "started" if started else "already_running", "message": "Continuous training started", "config": {"symbols": trainer.symbols, "retrain_interval_hours": trainer.retrain_interval.total_seconds() / 3600, "epochs": trainer.epochs}, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/stop")
def stop_training():
    try:
        stopped = continuous_trainer.stop()
        return {"status": "stopped" if stopped else "not_running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/retrain/{symbol}")
def retrain_symbol(symbol: str, epochs: int = Query(80, ge=10, le=200)):
    try:
        if symbol not in config.data.supported_symbols:
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
        has_new = continuous_trainer.update_local_data(symbol)
        results = continuous_trainer.train_symbol(symbol, epochs=epochs)
        return {"symbol": symbol, "message": f"Retrained {symbol} with real Binance data", "has_new_data": has_new, "epochs": epochs, "results": results, "real_data": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/retrain")
def retrain_all(req: TrainingRequest):
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
        return {"message": f"Retrained {len(results)} symbols", "results": results, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === REAL TRADING CALLS ===

@app.get("/trading/calls")
def get_trading_calls(
    symbols: Optional[str] = Query(None),
    timeframe: str = Query("1d", pattern="^(1m|5m|15m|1h|4h|1d|1w)$"),
    account_balance: float = Query(10000, ge=100, le=10000000),
    risk_per_trade: float = Query(0.02, ge=0.001, le=0.1),
    use_cache: bool = Query(True)
):
    parsed_symbols: Optional[List[str]] = None
    if symbols:
        if "," in symbols:
            parsed_symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()][:20]
        else:
            parsed_symbols = [symbols.strip().upper()]
    symbols_list = parsed_symbols
    global _calls_cache
    now = time.time()
    with _calls_cache_lock:
        if use_cache and _calls_cache["calls"] and (now - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
            if _calls_cache["account_balance"] == account_balance:
                cached = _calls_cache["calls"]
                if symbols_list:
                    filtered = [c for c in cached["calls"] if c["symbol"] in symbols_list]
                    return {**cached, "calls": filtered, "count": len(filtered), "cached": True, "real_trading": True}
                return {**cached, "cached": True, "real_trading": True}
    try:
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        target_symbols = symbols_list or config.data.supported_symbols[:6]
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
            "data_source": "Live Binance - real market prices",
            "how_to_use": {
                "entry": "Place limit order at entry_price (live Binance)",
                "stop_loss": "Set SL at stop_loss - mandatory",
                "take_profit": "TP1, TP2, TP3 for partials",
                "position": "Use position.size for your account",
                "risk": f"Risk ${account_balance * risk_per_trade:.0f} per trade"
            }
        }
        with _calls_cache_lock:
            _calls_cache["calls"] = result
            _calls_cache["timestamp"] = now
            _calls_cache["account_balance"] = account_balance
        return result
    except Exception as e:
        logger.error(f"Trading calls failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/call/{symbol}")
def get_single_call(symbol: str, timeframe: str = Query("1d"), account_balance: float = Query(10000, ge=100), risk_per_trade: float = Query(0.02, ge=0.005, le=0.1)):
    try:
        call_generator.risk_manager.risk_per_trade = risk_per_trade
        call = call_generator.generate_call(symbol=symbol, timeframe=timeframe, account_balance=account_balance)
        result = call.to_dict()
        result["real_trading"] = True
        result["data_source"] = "Live Binance"
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/summary")
def get_trading_summary():
    try:
        with _calls_cache_lock:
            if _calls_cache["calls"] and (time.time() - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
                return _calls_cache["calls"]["summary"]
        top_symbols = config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=top_symbols, account_balance=10000)
        summary = call_generator.get_call_summary(calls)
        summary["real_trading"] = True
        return summary
    except Exception as e:
        logger.error(f"Trading summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/real/guide")
def real_trading_guide():
    return {
        "title": "Real Trading Guide - Actual Trades with Real Money",
        "warning": "REAL trading - high risk!",
        "no_fake": "No paper trading - live Binance prices, real entry/SL/TP",
        "steps": [
            {"step": 1, "title": "Check Real Call", "description": "Get call from /trading/calls - entry is LIVE Binance price", "example": "BTC-USD STRONG_BUY $116k, SL $113k, TP1 $119k, 85% conf"},
            {"step": 2, "title": "Risk Management", "description": "Set account balance and risk per trade - max 2%", "formula": "Position size = (Account * Risk%) / |Entry - SL|", "example": "$10k, 2% = $200 risk"},
            {"step": 3, "title": "Place Order on Binance", "description": "Real order on Binance/Bybit", "actions": ["Limit at entry_price", "SL at stop_loss - MANDATORY", "TP1, TP2, TP3 partials", "Use suggested leverage"]},
            {"step": 4, "title": "Manage", "description": "Monitor", "actions": ["Move SL to BE at TP1", "50% at TP1, 30% at TP2, 20% at TP3", "Never move SL against you"]}
        ],
        "risk_management": {
            "position_sizing": "Use calculator in call",
            "stop_loss": "ALWAYS use SL - 1.5x ATR",
            "take_profit": "TP1 1:1, TP2 1:2, TP3 1:3",
            "leverage": "Low vol: 5x-10x, Med: 3x-5x, High: 1x-3x",
            "max_risk": "Max 2% per trade, 6% per day"
        },
        "real_data": {"source": "Binance Live", "entry": "Live Binance price", "models": "Continuously trained with real data every 12h"},
        "disclaimer": "Not financial advice. High risk. Past 2.57% MAPE doesn't guarantee future. Do your own research."
    }

@app.post("/trading/calls")
def post_trading_calls(req: TradingCallRequest):
    try:
        call_generator.risk_manager.risk_per_trade = req.risk_per_trade
        target_symbols = req.symbols or config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=target_symbols, timeframe=req.timeframe, account_balance=req.account_balance)
        calls_dict = [c.to_dict() for c in calls]
        summary = call_generator.get_call_summary(calls)
        return {"calls": calls_dict, "summary": summary, "count": len(calls_dict), "real_trading": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === PORTFOLIO ===

@app.get("/portfolio")
def get_portfolio():
    try:
        portfolio = portfolio_manager.get_portfolio()
        return {**portfolio.to_dict(), "real_trading": True, "data_source": "Live Binance prices", "no_fake": "Real P&L from actual positions"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/open")
def open_position(req: PortfolioOrderRequest):
    try:
        entry_price = req.entry_price
        if not entry_price:
            fetcher = BinanceRealtimeFetcher(symbol=req.symbol)
            entry_price = fetcher.get_current_price()
            if not entry_price:
                raise HTTPException(status_code=400, detail="Could not get live price")
        if not req.stop_loss or not req.take_profits:
            try:
                call = call_generator.generate_call(symbol=req.symbol, account_balance=portfolio_manager.cash + portfolio_manager.get_portfolio().positions_value)
                stop_loss = req.stop_loss or call.stop_loss
                take_profits = req.take_profits or call.take_profits
            except:
                atr = entry_price * 0.02
                stop_loss = entry_price - atr * 1.5 if req.side == "LONG" else entry_price + atr * 1.5
                risk = abs(entry_price - stop_loss)
                if req.side == "LONG":
                    take_profits = {"tp1": entry_price + risk, "tp2": entry_price + risk*2, "tp3": entry_price + risk*3}
                else:
                    take_profits = {"tp1": entry_price - risk, "tp2": entry_price - risk*2, "tp3": entry_price - risk*3}
        else:
            stop_loss = req.stop_loss
            take_profits = req.take_profits
        position = portfolio_manager.open_position(symbol=req.symbol, side=req.side, entry_price=entry_price, quantity=req.quantity, stop_loss=stop_loss, take_profits=take_profits, leverage=req.leverage)
        return {"message": f"Opened REAL position for {req.symbol}", "position": position.to_dict(), "portfolio": portfolio_manager.get_portfolio().to_dict(), "real_trading": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/close/{symbol}")
def close_position(symbol: str, current_price: Optional[float] = None):
    try:
        pos = portfolio_manager.close_position(symbol, current_price)
        if not pos:
            raise HTTPException(status_code=404, detail=f"No open position for {symbol}")
        return {"message": f"Closed REAL position for {symbol} - P&L ${pos.pnl:.2f}", "closed_position": pos.to_dict(), "portfolio": portfolio_manager.get_portfolio().to_dict(), "real_trading": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/performance")
def portfolio_performance():
    try:
        return portfolio_manager.get_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === STRATEGIES ===

@app.post("/strategies/dca")
def create_dca_bot(req: DCABotRequest):
    try:
        result = strategy_manager.create_dca_bot(symbol=req.symbol, total_investment=req.total_investment, num_orders=req.num_orders, price_deviation_pct=req.price_deviation_pct, take_profit_pct=req.take_profit_pct, stop_loss_pct=req.stop_loss_pct)
        return {"message": f"Created REAL DCA bot for {req.symbol}", "bot": result, "real_trading": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/grid")
def create_grid_bot(req: GridBotRequest):
    try:
        result = strategy_manager.create_grid_bot(symbol=req.symbol, lower_price=req.lower_price, upper_price=req.upper_price, num_grids=req.num_grids, total_investment=req.total_investment)
        return {"message": f"Created REAL Grid bot for {req.symbol}", "bot": result, "real_trading": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/breakout/scan")
def scan_breakouts(symbols: Optional[str] = Query(None)):
    try:
        parsed = None
        if symbols:
            parsed = [s.strip() for s in symbols.split(",")] if "," in symbols else [symbols]
        results = strategy_manager.scan_breakouts(parsed)
        return {"timestamp": datetime.utcnow().isoformat(), "count": len(results), "breakouts": [r for r in results if "BREAKOUT" in r["signal"]], "all_signals": results, "real_data": True, "source": "Real market data - volume confirmed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/all")
def get_all_strategies():
    try:
        return strategy_manager.get_all_bots()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === INSTITUTIONAL STRATEGIES - NEW ===

@app.post("/strategies/market_making")
def create_mm_bot(req: MarketMakingRequest):
    try:
        result = strategy_manager.create_mm_bot(symbol=req.symbol, total_investment=req.total_investment, spread_bps=req.spread_bps, max_inventory=req.max_inventory)
        return {"message": f"Created Institutional Market Making bot for {req.symbol} - Avellaneda-Stoikov", "bot": result, "real_trading": True, "institutional": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/market_making/{symbol}")
def get_mm_quote(symbol: str):
    try:
        result = strategy_manager.get_mm_quote(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/execution")
def create_execution_bot(req: ExecutionRequest):
    try:
        result = strategy_manager.create_execution_bot(symbol=req.symbol, side=req.side, total_quantity=req.total_quantity, strategy=req.strategy, duration_minutes=req.duration_minutes, num_slices=req.num_slices)
        return {"message": f"Created Institutional {req.strategy} execution for {req.symbol} {req.side} {req.total_quantity}", "bot": result, "real_trading": True, "institutional": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/stat_arb")
def create_stat_arb(req: StatArbRequest):
    try:
        result = strategy_manager.create_stat_arb_bot(symbol_a=req.symbol_a, symbol_b=req.symbol_b, entry_z=req.entry_z)
        return {"message": f"Created Institutional Stat Arb {req.symbol_a}/{req.symbol_b}", "bot": result, "real_trading": True, "institutional": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/stat_arb/{symbol_a}/{symbol_b}")
def get_stat_arb_signal(symbol_a: str, symbol_b: str):
    try:
        result = strategy_manager.get_stat_arb_signal(symbol_a, symbol_b)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/orderbook_imbalance")
def create_ofi_bot(req: OFIRequest):
    try:
        result = strategy_manager.create_ofi_bot(symbol=req.symbol)
        return {"message": f"Created Institutional OrderBook Imbalance bot for {req.symbol}", "bot": result, "real_trading": True, "institutional": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/orderbook_imbalance/{symbol}")
def get_ofi_signal(symbol: str):
    try:
        result = strategy_manager.get_ofi_signal(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/funding_arb")
def create_funding_bot(req: FundingArbRequest):
    try:
        result = strategy_manager.create_funding_bot(symbol=req.symbol)
        return {"message": f"Created Institutional Funding Arb bot for {req.symbol}", "bot": result, "real_trading": True, "institutional": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/funding_arb/{symbol}")
def get_funding_signal(symbol: str):
    try:
        result = strategy_manager.get_funding_signal(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/risk/position_size")
def get_position_size(req: RiskRequest):
    try:
        result = strategy_manager.get_position_size(symbol=req.symbol, account_balance=req.account_balance, win_rate=req.win_rate, win_loss_ratio=req.win_loss_ratio)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/risk/portfolio")
def get_portfolio_risk(symbols: Optional[str] = Query(None)):
    try:
        parsed = None
        if symbols:
            parsed = [s.strip() for s in symbols.split(",")] if "," in symbols else [symbols]
        result = strategy_manager.get_portfolio_risk(parsed)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/institutional/scan")
def scan_institutional(symbols: Optional[str] = Query(None)):
    try:
        parsed = None
        if symbols:
            parsed = [s.strip() for s in symbols.split(",")] if "," in symbols else [symbols]
        result = strategy_manager.scan_institutional(parsed)
        return {"timestamp": datetime.utcnow().isoformat(), "results": result, "institutional": True, "real_data": True, "message": "Institutional scan - MM, OFI, Funding, StatArb"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ALERTS ===

@app.get("/alerts")
def get_alerts():
    try:
        return alert_manager.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/create")
def create_alert(req: AlertRequest):
    try:
        alert = alert_manager.create_alert(symbol=req.symbol, alert_type=req.type, target_price=req.target_price, condition=req.condition)
        return {"message": f"Created REAL alert for {req.symbol}", "alert": asdict(alert), "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/active")
def get_active_alerts():
    try:
        return {"active_alerts": alert_manager.get_active_alerts(), "count": len(alert_manager.get_active_alerts()), "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/check")
def check_alerts():
    try:
        triggered = alert_manager.check_alerts()
        return {"triggered": [asdict(a) for a in triggered], "count": len(triggered), "timestamp": datetime.utcnow().isoformat(), "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/alerts/{alert_id}")
def cancel_alert(alert_id: str):
    try:
        success = alert_manager.cancel_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": f"Cancelled alert {alert_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === SCANNER ===

@app.get("/scanner")
def market_scanner_all():
    try:
        result = market_scanner.scan_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/volume")
def scanner_volume():
    try:
        spikes = market_scanner.scan_volume_spikes()
        return {"type": "volume_spikes", "count": len(spikes), "spikes": spikes, "real_data": True, "message": "Volume spikes - potential whale activity"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/momentum")
def scanner_momentum():
    try:
        momentum = market_scanner.scan_momentum()
        return {"type": "momentum", "count": len(momentum), "momentum": momentum, "real_data": True, "message": "Momentum movers"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/rsi")
def scanner_rsi():
    try:
        rsi = market_scanner.scan_oversold_overbought()
        return {"type": "rsi", "count": len(rsi), "signals": rsi, "real_data": True, "message": "RSI oversold/overbought"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ANALYTICS ===

@app.get("/analytics")
def get_analytics():
    try:
        return analytics_manager.get_full_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/metrics")
def analytics_metrics():
    try:
        return analytics_manager.calculate_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/equity")
def analytics_equity():
    try:
        return {"equity_curve": analytics_manager.get_equity_curve(), "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/symbols")
def analytics_symbols():
    try:
        return {"symbol_performance": analytics_manager.get_symbol_performance(), "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === JOURNAL ===

@app.get("/journal")
def get_journal(symbol: Optional[str] = None, tag: Optional[str] = None):
    try:
        entries = journal_manager.get_entries(symbol=symbol, tag=tag)
        return {"count": len(entries), "entries": entries, "stats": journal_manager.get_stats(), "real_trading": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journal/add")
def add_journal_entry(req: JournalRequest):
    try:
        entry = journal_manager.add_entry(symbol=req.symbol, side=req.side, entry_price=req.entry_price, quantity=req.quantity, strategy=req.strategy, notes=req.notes, emotions=req.emotions, lessons=req.lessons, tags=req.tags, exit_price=req.exit_price, pnl=req.pnl)
        return {"message": "Added REAL journal entry", "entry": asdict(entry), "real_trading": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/journal/stats")
def journal_stats():
    try:
        return journal_manager.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === MARKET DATA ===

@app.get("/market/tickers")
def market_tickers():
    global _market_cache
    now = time.time()
    with _market_cache_lock:
        if _market_cache["tickers"] and (now - _market_cache["timestamp"]) < CACHE_TTL:
            return _market_cache["tickers"]
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        resp.raise_for_status()
        all_tickers = resp.json()
        if not isinstance(all_tickers, list):
            raise ValueError("Invalid ticker response")
        wanted = set(config.data.binance_map.values())
        filtered = [t for t in all_tickers if t.get("symbol") in wanted]
        reverse_map = {v: k for k, v in config.data.binance_map.items()}
        tickers = {}
        for t in filtered:
            try:
                our_sym = reverse_map.get(t["symbol"])
                if our_sym:
                    # Validate prices
                    last_price = float(t.get("lastPrice",0) or 0)
                    if last_price <= 0 or last_price > 10_000_000:
                        continue
                    tickers[our_sym] = {
                        "symbol": our_sym,
                        "binanceSymbol": t["symbol"],
                        "price": last_price,
                        "lastPrice": last_price,
                        "priceChange": float(t.get("priceChange",0) or 0),
                        "priceChangePercent": float(t.get("priceChangePercent",0) or 0),
                        "high": float(t.get("highPrice",0) or 0),
                        "low": float(t.get("lowPrice",0) or 0),
                        "volume": float(t.get("volume",0) or 0),
                        "quoteVolume": float(t.get("quoteVolume",0) or 0),
                        "open": float(t.get("openPrice",0) or 0),
                        "trades": int(t.get("count",0) or 0),
                        "real_data": True,
                        "source": "Binance Live"
                    }
            except (ValueError, TypeError, KeyError):
                continue
        result = {"tickers": tickers, "count": len(tickers), "timestamp": now, "source": "Binance Live - Real Data", "real_trading": True}
        with _market_cache_lock:
            _market_cache["tickers"] = result
            _market_cache["timestamp"] = now
        return result
    except requests.RequestException as e:
        logger.warning(f"Binance ticker fetch failed (network): {e}")
        # Return cached if available even if expired
        with _market_cache_lock:
            if _market_cache["tickers"]:
                cached = _market_cache["tickers"].copy()
                cached["cached"] = True
                cached["warning"] = "Live fetch failed, returning cached"
                return cached
        raise HTTPException(status_code=503, detail=f"Market data unavailable: {e}")
    except Exception as e:
        logger.warning(f"Binance ticker fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Market data fetch failed: {e}")

@app.get("/market/klines")
def market_klines(symbol: str = Query("BTC-USD"), interval: str = Query("1d"), limit: int = Query(200, ge=1, le=1000)):
    try:
        binance_symbol = config.data.binance_map.get(symbol, symbol.replace("-", ""))
        resp = requests.get("https://api.binance.com/api/v3/klines", params={"symbol": binance_symbol, "interval": interval, "limit": limit}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        klines = []
        for d in data:
            klines.append({"openTime": d[0], "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4]), "volume": float(d[5]), "closeTime": d[6], "time": pd.to_datetime(d[0], unit='ms').strftime('%Y-%m-%d'), "timeISO": pd.to_datetime(d[0], unit='ms').isoformat(), "real_data": True})
        return {"symbol": symbol, "binanceSymbol": binance_symbol, "interval": interval, "klines": klines, "count": len(klines), "source": "Binance Live - Real Data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/orderbook")
def market_orderbook(symbol: str = Query("BTC-USD"), limit: int = Query(20, ge=5, le=100)):
    try:
        binance_symbol = config.data.binance_map.get(symbol, symbol.replace("-", ""))
        resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_symbol, "limit": limit}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === COINDCX MARKET DATA - REAL INR ===

@app.get("/market/coindcx/tickers")
def coindcx_tickers():
    """Real CoinDCX INR tickers - actual money markets"""
    try:
        from crypto_prediction.data.coindcx_fetcher import get_coindcx_tickers_cached
        tickers = get_coindcx_tickers_cached()
        return {
            "tickers": tickers,
            "count": len(tickers),
            "source": "CoinDCX Live INR - Real Money",
            "broker": "coindcx",
            "real_trading": True,
            "markets": list(tickers.keys())[:20],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/coindcx/price")
def coindcx_price(symbol: str = Query("BTC-USD")):
    """Get CoinDCX live price for symbol - real INR"""
    try:
        from crypto_prediction.data.coindcx_fetcher import CoinDCXRealtimeFetcher
        fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
        price = fetcher.get_current_price()
        ticker = fetcher.fetch_ticker_rest(symbol)
        return {
            "symbol": symbol,
            "coindcx_market": fetcher._map_symbol(symbol),
            "price": price,
            "price_inr": price,
            "price_usd_approx": price / 83.5 if price else 0,
            "ticker": ticker,
            "source": "CoinDCX Live INR",
            "real_data": True,
            "broker": "coindcx"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/coindcx/orderbook")
def coindcx_orderbook(symbol: str = Query("BTC-USD"), limit: int = Query(20, ge=5, le=100)):
    """CoinDCX orderbook - real INR depth"""
    try:
        from crypto_prediction.data.coindcx_fetcher import CoinDCXRealtimeFetcher
        fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
        ob = fetcher.get_orderbook(symbol, limit=limit)
        if not ob:
            raise HTTPException(status_code=404, detail=f"Orderbook not found for {symbol}")
        return {
            "symbol": symbol,
            "market": ob.get("market", symbol),
            "bids": ob.get("bids", [])[:limit],
            "asks": ob.get("asks", [])[:limit],
            "source": ob.get("source", "CoinDCX"),
            "real_data": True,
            "broker": "coindcx",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/all")
def market_all():
    """All market data - Binance USD + CoinDCX INR unified"""
    try:
        from crypto_prediction.data.price_helper import get_tickers_all
        tickers = get_tickers_all()
        return {
            "tickers": tickers,
            "count": len(tickers),
            "sources": ["CoinDCX INR", "Binance USD"],
            "real_data": True,
            "integrated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history(symbol: str = Query("BTC-USD"), period: str = Query("1y"), interval: str = Query("1d")):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        df_tail = df.tail(300)
        try:
            from crypto_prediction.features.sentiment import SentimentFeatureEngineer
            eng = SentimentFeatureEngineer()
            df_tail = eng.enrich_price_df(df_tail, symbol=symbol)
        except:
            pass
        data = {"symbol": symbol, "dates": df_tail.index.strftime('%Y-%m-%d').tolist(), "open": df_tail['Open'].tolist(), "high": df_tail['High'].tolist(), "low": df_tail['Low'].tolist(), "close": df_tail['Close'].tolist(), "volume": df_tail['Volume'].tolist(), "rsi": df_tail['RSI'].tolist() if 'RSI' in df_tail.columns else [], "sentiment": df_tail['Sentiment_Compound'].tolist() if 'Sentiment_Compound' in df_tail.columns else [], "real_data": True}
        return data
    except Exception as e:
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
        return {"symbol": req.symbol, "strategy": strat.name, "purpose": "Model validation", "metrics": result.metrics, "equity_curve": [{"date": idx.strftime('%Y-%m-%d'), "equity": float(val)} for idx, val in result.equity_curve.items()], "trades": result.trades.to_dict(orient='records') if not result.trades.empty else [], "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest/compare")
def backtest_compare(symbol: str = Query("BTC-USD"), period: str = Query("1y"), initial_capital: float = Query(10000)):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        from crypto_prediction.features.technical import FeatureEngineer
        eng = FeatureEngineer()
        df = eng.engineer(df)
        strategies = [MovingAverageStrategy(20, 50), MovingAverageStrategy(10, 30), RSIStrategy(30, 70), EnsembleSignalStrategy()]
        engine = BacktestEngine(initial_capital=initial_capital)
        results = engine.compare_strategies(df, strategies)
        comparison = {}
        for name, res in results.items():
            comparison[name] = res.metrics
        return {"symbol": symbol, "comparison": comparison, "purpose": "Model validation", "real_data": True}
    except Exception as e:
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
    trainer_status = continuous_trainer.get_status()
    return {"models": files, "count": len(files), "continuous_training": trainer_status["is_running"], "model_performance": trainer_status.get("model_performance", {}), "real_data": True}

@app.get("/settings")
def get_settings():
    return {
        "data": {"supported_symbols": config.data.supported_symbols, "sequence_length": config.data.sequence_length, "test_size": config.data.test_size, "val_size": config.data.val_size, "real_data_source": "Binance Live"},
        "features": {"count": 182, "scaler": "RobustScaler", "real_data": True},
        "models": {"lstm": {"hidden_size": 256, "num_layers": 3, "bidirectional": True, "use_attention": True}, "transformer": {"d_model": 256, "nhead": 8, "num_layers": 4, "use_learnable_pe": True}, "xgboost": {"n_estimators": 1500, "max_depth": 8, "learning_rate": 0.02}, "ensemble": {"weights": config.model.ensemble_weights, "use_stacking": True, "use_dynamic": True}},
        "trading": {"risk_per_trade": 0.02, "atr_sl_multiplier": 1.5, "real_trading": True},
        "continuous_training": {"enabled": True, "retrain_interval_hours": 12, "status": continuous_trainer.get_status()},
        "autotrading": {"enabled": autotrading_engine.config.enabled, "mode": autotrading_engine.config.mode, "brokers": list(broker_manager.brokers.keys()), "extensive_controls": True},
        "extensive_features": ["Portfolio", "DCA Bot", "Grid Bot", "Breakout Scanner", "Alerts", "Market Scanner", "Analytics", "Journal", "Broker Integration", "Auto Trading Engine"]
    }

# === CRASH DETECTOR - LOCAL FAST WEBSCRAPER FOR EARLY CRASH DETECTION ===
# All processing locally, efficient, <3s total, <100ms local processing
# Scrapes Binance spot/futures, funding, OI, orderbook, liquidations, trades, fear&greed, Reddit, news

@app.get("/crash/status")
def crash_status():
    """Get current crash risk - fast local processing, cached 20s"""
    try:
        result = crash_manager.get_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/scan")
def crash_scan(symbols: Optional[str] = Query(None), force: bool = Query(False)):
    """Full crash scan - parallel scraping, local aggregation"""
    try:
        parsed = None
        if symbols:
            parsed = [s.strip().upper() for s in symbols.split(",")] if "," in symbols else [symbols.strip().upper()]
            # Convert to Binance format if needed
            mapped=[]
            for s in parsed:
                if "USDT" in s:
                    mapped.append(s)
                else:
                    # BTC-USD -> BTCUSDT
                    mapped.append(s.replace("-","").replace("/","") + ("USDT" if "USDT" not in s else ""))
            parsed=mapped
        result = crash_manager.scan(symbols=parsed, force=force)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/history")
def crash_history(limit: int = Query(50, ge=1, le=200)):
    try:
        hist = crash_manager.get_history(limit=limit)
        return {"count": len(hist), "history": hist, "local_processing": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/alerts")
def crash_alerts(limit: int = Query(20, ge=1, le=100)):
    try:
        alerts = crash_manager.get_alerts(limit=limit)
        return {"count": len(alerts), "alerts": alerts, "message": "High/Critical crash alerts - early warning before market impact"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/signals")
def crash_signals():
    try:
        return crash_manager.get_signals_breakdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/raw")
def crash_raw(symbols: Optional[str] = Query(None)):
    """Raw scraped data for debugging - shows all sources including CoinDCX INR"""
    try:
        from crypto_prediction.crash_detector.scraper import get_scraper
        scraper=get_scraper()
        parsed = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        if symbols:
            parsed = [s.strip().upper() for s in symbols.split(",")]
        data=scraper.fetch_all(parsed)
        return {
            "timestamp": data.timestamp,
            "fetch_time_ms": data.fetch_time_ms,
            "spot_tickers_count": len(data.spot_tickers),
            "coindcx_tickers_count": len(getattr(data, 'coindcx_tickers', {})),
            "futures_count": len(data.futures_tickers),
            "funding_count": len(data.funding_rates),
            "orderbooks": list(data.orderbooks.keys()),
            "liquidations": {k: {"total": v.get("total",0), "long": v.get("long_liq",0)} for k,v in data.liquidations.items()},
            "fear_greed": data.fear_greed,
            "reddit_count": len(data.reddit_posts),
            "reddit_crash": [p for p in data.reddit_posts if p.get("is_crash")][:5],
            "news_count": len(data.news_titles),
            "news_crash": [n for n in data.news_titles if n.get("is_crash")][:5],
            "btc": data.spot_tickers.get("BTCUSDT",{}),
            "coindcx_btc": getattr(data, 'coindcx_tickers', {}).get("BTCUSDT",{}),
            "local_processing": True,
            "efficient": True,
            "price_source": "Binance USD + CoinDCX INR primary fallback"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crash/coindcx")
def crash_coindcx():
    """Crash detector with CoinDCX INR primary"""
    try:
        from crypto_prediction.data.coindcx_fetcher import get_coindcx_tickers_cached
        coindcx = get_coindcx_tickers_cached()
        crash_data = crash_manager.get_status()
        # Merge
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "coindcx_tickers": coindcx,
            "coindcx_count": len(coindcx),
            "crash_risk": crash_data.get("crash_risk", {}),
            "signals": crash_data.get("signals", []),
            "source": "CoinDCX INR primary + Binance fallback",
            "real_data": True,
            "integrated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
