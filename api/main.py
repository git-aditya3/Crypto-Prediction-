"""
FastAPI for Crypto Prediction
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.config import get_config
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

app = FastAPI(
    title="Crypto Prediction API",
    description="End-to-end cryptocurrency price forecasting with LSTM, XGBoost, ARIMA ensemble",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastResponse(BaseModel):
    symbol: str
    current_price: Optional[float]
    dates: List[str]
    lstm: Optional[List[float]] = None
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

@app.get("/")
def root():
    return {
        "message": "Crypto Prediction API",
        "version": "0.1.0",
        "supported_symbols": config.data.supported_symbols,
        "endpoints": ["/predict", "/forecast", "/signal", "/history", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/history")
def get_history(symbol: str = Query("BTC-USD"), period: str = Query("1y"), interval: str = Query("1d")):
    try:
        fetcher = CryptoDataFetcher(symbol=symbol)
        df = fetcher.load_or_fetch(symbol=symbol)
        # Limit to period
        # Return last 200 points for chart
        df_tail = df.tail(200)
        data = {
            "symbol": symbol,
            "dates": df_tail.index.strftime('%Y-%m-%d').tolist(),
            "open": df_tail['Open'].tolist(),
            "high": df_tail['High'].tolist(),
            "low": df_tail['Low'].tolist(),
            "close": df_tail['Close'].tolist(),
            "volume": df_tail['Volume'].tolist()
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
        if not fc or len(fc) <= 2:  # only dates and current
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

@app.get("/symbols")
def list_symbols():
    return {"symbols": config.data.supported_symbols}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.api.host, port=config.api.port, reload=config.api.reload)
