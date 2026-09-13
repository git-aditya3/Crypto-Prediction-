"""
FastAPI v5 - Extensive Real Trading Platform + Continuous Training
- Real trading calls for actual trades, no fake simulation
- Continuous self-training with live Binance data
- Portfolio, Strategies (DCA, Grid, Breakout), Alerts, Scanner, Analytics, Journal
- Max performance models v4
"""
from fastapi import FastAPI, HTTPException, Query, Body
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
from crypto_prediction.portfolio.manager import get_portfolio_manager
from crypto_prediction.strategies.manager import get_strategy_manager
from crypto_prediction.alerts.manager import get_alert_manager
from crypto_prediction.scanner.manager import get_market_scanner
from crypto_prediction.analytics.manager import get_analytics_manager
from crypto_prediction.journal.manager import get_journal_manager
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API v5 - Extensive Real Trading Platform",
    description="""
    🚀 v5 Extensive Real Trading Platform - No Fake Simulation
    
    **Core:**
    - 🔄 Continuous Training: Models learn endlessly from live Binance data (every 12h)
    - 💰 Real Trading Calls: Live Binance entry, ATR SL, 1:1/2/3 TP, position sizing for REAL money
    - 🧠 Models v4 Max Perf: LSTM Bidir+Attn+Huber+AdamW, Transformer Learnable PE+Attn Pool, XGBoost 1500 trees, ARIMA SARIMAX, Ensemble Dynamic+Stacking
    - 📊 182 Features, RobustScaler, Sentiment, Real-time Binance
    
    **Extensive Features:**
    - 💼 Portfolio: Real holdings, P&L, allocation, performance (win rate, profit factor, Sharpe)
    - 🤖 Strategies: DCA Bot, Grid Bot, Breakout Scanner for real trading
    - 🚨 Alerts: Price above/below, signal buy/sell, volume spike - real market
    - 🔍 Scanner: Volume spikes, momentum, RSI oversold/overbought - real opportunities
    - 📈 Analytics: Equity curve, drawdown, symbol performance, real P&L
    - 📓 Journal: Log real trades with notes/emotions/lessons
    - ⚡ Real-time: Binance tickers, klines, orderbook, live prices
    - 🎯 Risk: Position sizing, leverage, max drawdown protection, daily loss limit
    
    **No Fake:** Only real Binance market data, real trading calls for actual trades
    """,
    version="0.5.0"
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
portfolio_manager = get_portfolio_manager()
strategy_manager = get_strategy_manager()
alert_manager = get_alert_manager()
market_scanner = get_market_scanner()
analytics_manager = get_analytics_manager()
journal_manager = get_journal_manager()

_market_cache = {"tickers": None, "timestamp": 0}
_calls_cache = {"calls": None, "timestamp": 0, "account_balance": 10000}
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

class PortfolioOrderRequest(BaseModel):
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: Optional[Dict[str, float]] = None
    leverage: str = "1x"

class AlertRequest(BaseModel):
    symbol: str
    type: str  # PRICE_ABOVE, PRICE_BELOW, SIGNAL_BUY, etc.
    target_price: Optional[float] = None
    condition: str = ""

class JournalRequest(BaseModel):
    symbol: str
    side: str
    entry_price: float
    quantity: float
    strategy: str = "AI Ensemble"
    notes: str = ""
    emotions: str = ""
    lessons: str = ""
    tags: List[str] = []
    exit_price: Optional[float] = None
    pnl: float = 0

class DCABotRequest(BaseModel):
    symbol: str
    total_investment: float
    num_orders: int = 5
    price_deviation_pct: float = 1.0
    take_profit_pct: float = 5.0
    stop_loss_pct: float = 3.0

class GridBotRequest(BaseModel):
    symbol: str
    lower_price: float
    upper_price: float
    num_grids: int = 10
    total_investment: float = 1000

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 API v5 Starting - Extensive Real Trading + Continuous Training")
    try:
        continuous_trainer.start(run_immediately=False)
        logger.info("✅ Continuous training started - endless learning with live data")
    except Exception as e:
        logger.warning(f"Could not start continuous training: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API v5")
    try:
        continuous_trainer.stop()
    except:
        pass

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API v5 - Extensive Real Trading Platform - No Fake Simulation",
        "version": "0.5.0",
        "tagline": "Real trading calls for actual money + Models train endlessly with live data + Extensive bot features",
        "features": {
            "core": [
                "🔄 Continuous Training - Endless self-learning with live Binance data",
                "💰 Real Trading Calls - Live entry/SL/TP for REAL money, no paper simulation",
                "🧠 LSTM v3 - Bidir+Attention+Huber+AdamW",
                "🤖 Transformer v3 - Learnable PE+Attn Pool+Pre-LN",
                "🌲 XGBoost v3 - 1500 trees, depth 8, regularized",
                "📈 ARIMA v3 - SARIMAX weekly",
                "🎯 Ensemble v3 - Dynamic inverse MAPE + Ridge stacking"
            ],
            "extensive": [
                "💼 Portfolio - Real holdings, P&L, allocation, win rate, profit factor, Sharpe",
                "🤖 DCA Bot - Dollar Cost Averaging for real accumulation",
                "📊 Grid Bot - Profits from ranging markets, real grid levels",
                "💥 Breakout Scanner - Volume confirmed breakouts",
                "🚨 Alerts - Price, signal, volume spike alerts with live checking",
                "🔍 Market Scanner - Volume spikes, momentum, RSI oversold/overbought",
                "📈 Analytics - Equity curve, drawdown, symbol performance, real P&L",
                "📓 Journal - Log real trades with notes/emotions/lessons",
                "⚡ Real-time - Binance tickers, klines, orderbook",
                "🛡️ Risk - Position sizing, leverage, max DD protection"
            ]
        },
        "real_trading": {
            "entry": "Live Binance price NOW",
            "stop_loss": "ATR 1.5x real risk",
            "take_profit": "TP1 1:1, TP2 1:2, TP3 1:3 real profit",
            "position_size": "Based on YOUR account balance",
            "warning": "Real money trading - high risk"
        },
        "continuous_training": {
            "status": "Models retrain every 12h with real Binance data",
            "data_source": "Binance Live - real market data",
            "no_fake": "No synthetic data - only real OHLCV",
            "endless": "Training loop runs forever"
        },
        "endpoints": {
            "real_trading": ["/trading/calls", "/trading/call/{symbol}", "/trading/summary", "/trading/real/guide"],
            "portfolio": ["/portfolio", "/portfolio/open", "/portfolio/close/{symbol}", "/portfolio/performance"],
            "strategies": ["/strategies/dca", "/strategies/grid", "/strategies/breakout/scan", "/strategies/all"],
            "alerts": ["/alerts", "/alerts/create", "/alerts/active", "/alerts/check"],
            "scanner": ["/scanner", "/scanner/volume", "/scanner/momentum", "/scanner/rsi"],
            "analytics": ["/analytics", "/analytics/equity", "/analytics/metrics", "/analytics/symbols"],
            "journal": ["/journal", "/journal/add", "/journal/stats"],
            "training": ["/training/status", "/training/start", "/training/stop", "/training/retrain/{symbol}"],
            "market": ["/market/tickers", "/market/klines", "/market/orderbook", "/realtime/price"]
        }
    }

@app.get("/health")
def health():
    trainer_status = continuous_trainer.get_status()
    return {
        "status": "ok",
        "version": "0.5.0",
        "mode": "extensive_real_trading",
        "continuous_training": trainer_status["is_running"],
        "portfolio_value": portfolio_manager.get_portfolio().total_value,
        "open_positions": len(portfolio_manager.positions),
        "active_alerts": len([a for a in alert_manager.alerts.values() if a.status == "ACTIVE"]),
        "models": "v5 Extensive - Real Trading + Endless Learning",
        "data": "Real Binance market data - no fake simulation",
        "uptime": trainer_status.get("uptime", 0)
    }

# === CONTINUOUS TRAINING ===

@app.get("/training/status")
def training_status():
    try:
        status = get_training_status()
        return {
            "message": "Continuous training - models learn endlessly from real market data",
            "status": status,
            "real_data": True
        }
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
        return {
            "status": "started" if started else "already_running",
            "message": "Continuous training started - endless learning with real Binance data",
            "config": {
                "symbols": trainer.symbols,
                "retrain_interval_hours": trainer.retrain_interval.total_seconds() / 3600,
                "epochs": trainer.epochs
            },
            "real_data": True
        }
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
        return {
            "symbol": symbol,
            "message": f"Retrained {symbol} with real Binance data",
            "has_new_data": has_new,
            "epochs": epochs,
            "results": results,
            "real_data": True
        }
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
        return {"message": f"Retrained {len(results)} symbols with real data", "results": results, "real_data": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === REAL TRADING CALLS ===

@app.get("/trading/calls")
def get_trading_calls(
    symbols: Optional[str] = Query(None, description="Filter symbols comma-separated"),
    timeframe: str = Query("1d"),
    account_balance: float = Query(10000, ge=100, le=10000000),
    risk_per_trade: float = Query(0.02, ge=0.005, le=0.1),
    use_cache: bool = Query(True)
):
    parsed_symbols: Optional[List[str]] = None
    if symbols:
        if "," in symbols:
            parsed_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        else:
            parsed_symbols = [symbols.strip()]
    symbols_list = parsed_symbols
    global _calls_cache
    now = time.time()
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
        if _calls_cache["calls"] and (time.time() - _calls_cache["timestamp"]) < CALLS_CACHE_TTL:
            return _calls_cache["calls"]["summary"]
        top_symbols = config.data.supported_symbols[:6]
        calls = call_generator.generate_all_calls(symbols=top_symbols, account_balance=10000)
        summary = call_generator.get_call_summary(calls)
        summary["real_trading"] = True
        return summary
    except Exception as e:
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
        "real_data": {
            "source": "Binance Live",
            "entry": "Live Binance price",
            "models": "Continuously trained with real data every 12h"
        },
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

# === PORTFOLIO - REAL TRADING ===

@app.get("/portfolio")
def get_portfolio():
    """Get real portfolio with live P&L - real money tracking"""
    try:
        portfolio = portfolio_manager.get_portfolio()
        return {
            **portfolio.to_dict(),
            "real_trading": True,
            "data_source": "Live Binance prices",
            "no_fake": "Real P&L from actual positions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/open")
def open_position(req: PortfolioOrderRequest):
    """Open real position - actual trade tracking"""
    try:
        # Get live price if not provided
        entry_price = req.entry_price
        if not entry_price:
            fetcher = BinanceRealtimeFetcher(symbol=req.symbol)
            entry_price = fetcher.get_current_price()
            if not entry_price:
                raise HTTPException(status_code=400, detail="Could not get live price")
        
        # Get trading call for SL/TP if not provided
        if not req.stop_loss or not req.take_profits:
            try:
                call = call_generator.generate_call(symbol=req.symbol, account_balance=portfolio_manager.cash + portfolio_manager.get_portfolio().positions_value)
                stop_loss = req.stop_loss or call.stop_loss
                take_profits = req.take_profits or call.take_profits
            except:
                # Fallback
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
        
        position = portfolio_manager.open_position(
            symbol=req.symbol,
            side=req.side,
            entry_price=entry_price,
            quantity=req.quantity,
            stop_loss=stop_loss,
            take_profits=take_profits,
            leverage=req.leverage
        )
        
        return {
            "message": f"Opened REAL position for {req.symbol} - actual trade tracking",
            "position": position.to_dict(),
            "portfolio": portfolio_manager.get_portfolio().to_dict(),
            "real_trading": True,
            "warning": "Real position tracking - use proper risk management"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/close/{symbol}")
def close_position(symbol: str, current_price: Optional[float] = None):
    """Close real position"""
    try:
        pos = portfolio_manager.close_position(symbol, current_price)
        if not pos:
            raise HTTPException(status_code=404, detail=f"No open position for {symbol}")
        
        return {
            "message": f"Closed REAL position for {symbol} - P&L ${pos.pnl:.2f}",
            "closed_position": pos.to_dict(),
            "portfolio": portfolio_manager.get_portfolio().to_dict(),
            "real_trading": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/performance")
def portfolio_performance():
    """Get portfolio performance - real trading metrics"""
    try:
        return portfolio_manager.get_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === STRATEGIES - REAL TRADING BOTS ===

@app.post("/strategies/dca")
def create_dca_bot(req: DCABotRequest):
    """Create DCA bot for real trading - dollar cost averaging"""
    try:
        result = strategy_manager.create_dca_bot(
            symbol=req.symbol,
            total_investment=req.total_investment,
            num_orders=req.num_orders,
            price_deviation_pct=req.price_deviation_pct,
            take_profit_pct=req.take_profit_pct,
            stop_loss_pct=req.stop_loss_pct
        )
        return {
            "message": f"Created REAL DCA bot for {req.symbol} - real accumulation strategy",
            "bot": result,
            "real_trading": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/grid")
def create_grid_bot(req: GridBotRequest):
    """Create Grid bot for real trading - ranging market profits"""
    try:
        result = strategy_manager.create_grid_bot(
            symbol=req.symbol,
            lower_price=req.lower_price,
            upper_price=req.upper_price,
            num_grids=req.num_grids,
            total_investment=req.total_investment
        )
        return {
            "message": f"Created REAL Grid bot for {req.symbol} - profits from volatility",
            "bot": result,
            "real_trading": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/breakout/scan")
def scan_breakouts(symbols: Optional[str] = Query(None)):
    """Scan for breakouts with volume confirmation - real opportunities"""
    try:
        parsed = None
        if symbols:
            parsed = [s.strip() for s in symbols.split(",")] if "," in symbols else [symbols]
        
        results = strategy_manager.scan_breakouts(parsed)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(results),
            "breakouts": [r for r in results if "BREAKOUT" in r["signal"]],
            "all_signals": results,
            "real_data": True,
            "source": "Real market data - volume confirmed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/all")
def get_all_strategies():
    """Get all active strategy bots - real trading"""
    try:
        return strategy_manager.get_all_bots()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ALERTS - REAL MARKET ALERTS ===

@app.get("/alerts")
def get_alerts():
    try:
        return alert_manager.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/create")
def create_alert(req: AlertRequest):
    try:
        alert = alert_manager.create_alert(
            symbol=req.symbol,
            alert_type=req.type,
            target_price=req.target_price,
            condition=req.condition
        )
        return {
            "message": f"Created REAL alert for {req.symbol}",
            "alert": asdict(alert),
            "real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/active")
def get_active_alerts():
    try:
        return {
            "active_alerts": alert_manager.get_active_alerts(),
            "count": len(alert_manager.get_active_alerts()),
            "real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/check")
def check_alerts():
    try:
        triggered = alert_manager.check_alerts()
        return {
            "triggered": [asdict(a) for a in triggered],
            "count": len(triggered),
            "timestamp": datetime.utcnow().isoformat(),
            "real_data": True
        }
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

# === MARKET SCANNER - REAL OPPORTUNITIES ===

@app.get("/scanner")
def market_scanner_all():
    """Full market scan - real opportunities from live Binance data"""
    try:
        result = market_scanner.scan_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/volume")
def scanner_volume():
    try:
        spikes = market_scanner.scan_volume_spikes()
        return {
            "type": "volume_spikes",
            "count": len(spikes),
            "spikes": spikes,
            "real_data": True,
            "message": "Volume spikes - potential whale activity, real trading opportunities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/momentum")
def scanner_momentum():
    try:
        momentum = market_scanner.scan_momentum()
        return {
            "type": "momentum",
            "count": len(momentum),
            "momentum": momentum,
            "real_data": True,
            "message": "Momentum movers - real market movers"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scanner/rsi")
def scanner_rsi():
    try:
        rsi = market_scanner.scan_oversold_overbought()
        return {
            "type": "rsi",
            "count": len(rsi),
            "signals": rsi,
            "real_data": True,
            "message": "RSI oversold/overbought - real reversal signals"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ANALYTICS - REAL PERFORMANCE ===

@app.get("/analytics")
def get_analytics():
    """Full analytics - real trading performance"""
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
        return {
            "equity_curve": analytics_manager.get_equity_curve(),
            "real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/symbols")
def analytics_symbols():
    try:
        return {
            "symbol_performance": analytics_manager.get_symbol_performance(),
            "real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === JOURNAL - REAL TRADING JOURNAL ===

@app.get("/journal")
def get_journal(symbol: Optional[str] = None, tag: Optional[str] = None):
    try:
        entries = journal_manager.get_entries(symbol=symbol, tag=tag)
        return {
            "count": len(entries),
            "entries": entries,
            "stats": journal_manager.get_stats(),
            "real_trading": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journal/add")
def add_journal_entry(req: JournalRequest):
    try:
        entry = journal_manager.add_entry(
            symbol=req.symbol,
            side=req.side,
            entry_price=req.entry_price,
            quantity=req.quantity,
            strategy=req.strategy,
            notes=req.notes,
            emotions=req.emotions,
            lessons=req.lessons,
            tags=req.tags,
            exit_price=req.exit_price,
            pnl=req.pnl
        )
        return {
            "message": "Added REAL journal entry - for actual trading improvement",
            "entry": asdict(entry),
            "real_trading": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/journal/stats")
def journal_stats():
    try:
        return journal_manager.get_stats()
    except Exception as e:
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
            "real_data": True
        }
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
        return {
            "symbol": req.symbol,
            "strategy": strat.name,
            "purpose": "Model validation on real historical data - not fake trading",
            "metrics": result.metrics,
            "equity_curve": [{"date": idx.strftime('%Y-%m-%d'), "equity": float(val)} for idx, val in result.equity_curve.items()],
            "trades": result.trades.to_dict(orient='records') if not result.trades.empty else [],
            "real_data": True
        }
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
            "real_data_source": "Binance Live"
        },
        "features": {"count": 182, "scaler": "RobustScaler", "real_data": True},
        "models": {
            "lstm": {"hidden_size": 256, "num_layers": 3, "bidirectional": True, "use_attention": True},
            "transformer": {"d_model": 256, "nhead": 8, "num_layers": 4, "use_learnable_pe": True},
            "xgboost": {"n_estimators": 1500, "max_depth": 8, "learning_rate": 0.02},
            "ensemble": {"weights": config.model.ensemble_weights, "use_stacking": True, "use_dynamic": True}
        },
        "trading": {"risk_per_trade": 0.02, "atr_sl_multiplier": 1.5, "real_trading": True},
        "continuous_training": {"enabled": True, "retrain_interval_hours": 12, "status": continuous_trainer.get_status()},
        "extensive_features": ["Portfolio", "DCA Bot", "Grid Bot", "Breakout Scanner", "Alerts", "Market Scanner", "Analytics", "Journal"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
