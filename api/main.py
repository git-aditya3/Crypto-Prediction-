"""
FastAPI for Crypto Prediction - v2 with Sentiment, Realtime, Transformer, Backtesting
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.config import get_config
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.features.sentiment import SentimentFeatureEngineer, SentimentAnalyzer, fetch_sentiment
from crypto_prediction.data.realtime import BinanceRealtimeFetcher, RealtimeManager
from crypto_prediction.backtesting.engine import BacktestEngine
from crypto_prediction.backtesting.strategies import MovingAverageStrategy, RSIStrategy, PredictionStrategy, EnsembleSignalStrategy
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API v2",
    description="End-to-end crypto forecasting: LSTM, Transformer (TFT), XGBoost, ARIMA, Sentiment, Realtime Binance, Backtesting",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global realtime manager
realtime_manager: Optional[RealtimeManager] = None

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
    strategy: str = "ma"  # ma, rsi, prediction, ensemble
    period: str = "1y"
    initial_capital: float = 10000

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API v2",
        "version": "0.2.0",
        "features": ["LSTM", "Transformer", "XGBoost", "ARIMA", "Ensemble", "Sentiment", "Realtime Binance", "Backtesting", "React Frontend"],
        "supported_symbols": config.data.supported_symbols,
        "endpoints": ["/predict", "/forecast", "/signal", "/history", "/sentiment", "/realtime/price", "/realtime/start", "/backtest", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}

@app.get("/history")
def get_history(symbol: str = Query("BTC-USD"), period: str = Query("1y"), interval: str = Query("1d")):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        df_tail = df.tail(300)
        # Enrich with sentiment?
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
        # Also get 24h ticker
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
        # Enrich features for strategies
        from crypto_prediction.features.technical import FeatureEngineer
        eng = FeatureEngineer()
        df = eng.engineer(df)

        # Choose strategy
        if req.strategy == "ma":
            strat = MovingAverageStrategy(short_window=20, long_window=50)
        elif req.strategy == "rsi":
            strat = RSIStrategy(rsi_low=30, rsi_high=70)
        elif req.strategy == "prediction":
            # Use predictor if available
            try:
                predictor = CryptoPredictor(symbol=req.symbol)
                fc = predictor.forecast(steps=len(df), period=req.period)
                # Use ensemble forecast as prediction col
                if 'ensemble' in fc:
                    # Align
                    pred_series = pd.Series(fc['ensemble'], index=pd.to_datetime(fc['dates']))
                    # Merge
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
