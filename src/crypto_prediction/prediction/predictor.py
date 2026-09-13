"""
Prediction / inference pipeline
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..data.dataset import CryptoDataset
from ..models.lstm_model import LSTMModel
from ..models.xgboost_model import XGBoostModel
from ..models.arima_model import ARIMAModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CryptoPredictor:
    def __init__(self, symbol: str = "BTC-USD"):
        self.symbol = symbol
        self.dataset = CryptoDataset(symbol=symbol)
        self.preprocessor = None
        self.models = {}
        self._load_artifacts()

    def _load_artifacts(self):
        """Load preprocessor and models if they exist"""
        models_dir = config.project_root / "models"
        symbol_key = self.symbol.replace('-','_')

        # Preprocessor
        pre_path = models_dir / f"{symbol_key}_preprocessor.joblib"
        if pre_path.exists():
            try:
                from ..data.preprocessor import DataPreprocessor
                self.preprocessor = DataPreprocessor()
                self.preprocessor.load(str(pre_path))
                logger.info(f"Loaded preprocessor for {self.symbol}")
            except Exception as e:
                logger.warning(f"Failed to load preprocessor: {e}")

        # LSTM torch
        lstm_path = models_dir / f"{symbol_key}_lstm.pt"
        if lstm_path.exists() and self.preprocessor:
            try:
                input_size = len(self.preprocessor.feature_columns)
                self.models['lstm'] = LSTMModel.load_torch(str(lstm_path))
                logger.info("Loaded LSTM model")
            except Exception as e:
                logger.warning(f"Failed to load LSTM: {e}")

        # XGBoost
        xgb_path = models_dir / f"{symbol_key}_xgb.joblib"
        if xgb_path.exists():
            try:
                self.models['xgboost'] = XGBoostModel.load(str(xgb_path))
                logger.info("Loaded XGBoost model")
            except Exception as e:
                logger.warning(f"Failed to load XGB: {e}")

        # ARIMA
        arima_path = models_dir / f"{symbol_key}_arima.joblib"
        if arima_path.exists():
            try:
                self.models['arima'] = ARIMAModel.load(str(arima_path))
                logger.info("Loaded ARIMA model")
            except Exception as e:
                logger.warning(f"Failed to load ARIMA: {e}")

    def prepare_latest_data(self, period: str = "1y", interval: str = "1d") -> Dict:
        """Fetch latest data and prepare for prediction"""
        if self.preprocessor is None:
            # If no preprocessor, create full pipeline
            logger.info("No preprocessor found, building fresh pipeline")
            data_dict = self.dataset.get_full_pipeline(period=period, interval=interval)
            self.preprocessor = self.dataset.preprocessor
        else:
            # Fetch and engineer with existing preprocessor columns
            raw = self.dataset.load(period=period, interval=interval)
            feat = self.dataset.engineer.engineer(raw)
            cleaned = self.preprocessor.prepare_features(feat, feature_cols=self.preprocessor.feature_columns)
            # Scale
            X = self.preprocessor.feature_scaler.transform(cleaned[self.preprocessor.feature_columns].values)
            # Create sequences
            seq_len = config.data.sequence_length
            X_seq, _ = self.preprocessor.create_sequences(X, np.zeros(len(X)), seq_length=seq_len)
            data_dict = {
                'X': X,
                'X_seq': X_seq,
                'cleaned_df': cleaned,
                'raw_df': raw,
                'feature_df': feat
            }
        return data_dict

    def predict_next(self, period: str = "1y", interval: str = "1d") -> Dict:
        """Predict next price (1 step ahead)"""
        data = self.prepare_latest_data(period=period, interval=interval)
        
        results = {}
        latest_flat = data['X'][-1] if 'X' in data else data['X_test'][-1] if 'X_test' in data else None
        latest_seq = data['X_seq'][-1] if 'X_seq' in data else data['X_train_seq'][-1]

        if 'lstm' in self.models:
            try:
                pred_scaled = self.models['lstm'].predict(latest_seq.reshape(1, *latest_seq.shape))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['lstm'] = float(pred)
            except Exception as e:
                logger.warning(f"LSTM predict failed: {e}")

        if 'xgboost' in self.models:
            try:
                pred_scaled = self.models['xgboost'].predict(latest_flat.reshape(1, -1))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['xgboost'] = float(pred)
            except Exception as e:
                logger.warning(f"XGB predict failed: {e}")

        if 'arima' in self.models:
            try:
                pred = self.models['arima'].predict(steps=1)[0]
                results['arima'] = float(pred)
            except Exception as e:
                logger.warning(f"ARIMA predict failed: {e}")

        # Ensemble
        if results:
            weights = config.model.ensemble_weights
            # Only use weights for models that predicted
            total_w = sum(weights.get(k,0) for k in results.keys())
            if total_w > 0:
                ensemble = sum(results[k] * weights.get(k,0) / total_w for k in results.keys())
                results['ensemble'] = float(ensemble)

        return results

    def forecast(self, steps: int = 7, period: str = "1y", interval: str = "1d") -> Dict[str, List[float]]:
        """Forecast next N steps"""
        data = self.prepare_latest_data(period=period, interval=interval)
        
        latest_flat = data['X'][-1] if 'X' in data else None
        latest_seq = data['X_seq'][-1] if 'X_seq' in data else None
        if latest_flat is None or latest_seq is None:
            # fallback from dataset
            proc = data
            latest_flat = proc['X_test'][-1] if 'X_test' in proc else proc['X_train'][-1]
            latest_seq = proc['X_test_seq'][-1] if 'X_test_seq' in proc else proc['X_train_seq'][-1]

        forecasts = {}

        if 'lstm' in self.models:
            try:
                preds_scaled = self.models['lstm'].forecast_future(latest_seq, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['lstm'] = preds.tolist()
            except Exception as e:
                logger.warning(f"LSTM forecast failed: {e}")

        if 'xgboost' in self.models:
            try:
                preds_scaled = self.models['xgboost'].forecast_future(latest_flat, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['xgboost'] = preds.tolist()
            except Exception as e:
                logger.warning(f"XGB forecast failed: {e}")

        if 'arima' in self.models:
            try:
                preds = self.models['arima'].forecast_future(steps=steps)
                forecasts['arima'] = preds.tolist()
            except Exception as e:
                logger.warning(f"ARIMA forecast failed: {e}")

        # Ensemble forecast
        if forecasts:
            # Align all to same length
            min_len = min(len(v) for v in forecasts.values())
            aligned = {k: v[:min_len] for k, v in forecasts.items()}
            weights = config.model.ensemble_weights
            total_w = sum(weights.get(k,0) for k in aligned.keys())
            if total_w > 0:
                ensemble = np.zeros(min_len)
                for k, v in aligned.items():
                    ensemble += np.array(v) * weights.get(k,0) / total_w
                forecasts['ensemble'] = ensemble.tolist()

        # Generate future dates
        last_date = data['cleaned_df'].index[-1] if 'cleaned_df' in data else pd.Timestamp.now()
        future_dates = [last_date + timedelta(days=i+1) for i in range(steps)]
        forecasts['dates'] = [d.strftime('%Y-%m-%d') for d in future_dates]

        # Add current price
        current_price = float(data['cleaned_df']['Close'].iloc[-1]) if 'cleaned_df' in data else None
        forecasts['current_price'] = current_price
        forecasts['symbol'] = self.symbol

        return forecasts

    def get_trading_signal(self, forecast: Dict) -> Dict:
        """Generate simple trading signal based on forecast"""
        current = forecast.get('current_price')
        ensemble = forecast.get('ensemble') or forecast.get('lstm') or forecast.get('xgboost')
        
        if not current or not ensemble:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

        next_price = ensemble[0] if isinstance(ensemble, list) else ensemble
        change_pct = (next_price - current) / current * 100

        if change_pct > 2:
            signal = "STRONG_BUY"
        elif change_pct > 0.5:
            signal = "BUY"
        elif change_pct < -2:
            signal = "STRONG_SELL"
        elif change_pct < -0.5:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = min(abs(change_pct) * 20, 95)  # simplistic confidence

        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "current_price": current,
            "predicted_price": next_price,
            "change_pct": round(change_pct, 2),
            "reason": f"Predicted {change_pct:.2f}% change"
        }
