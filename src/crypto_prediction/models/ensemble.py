"""
Ensemble model combining LSTM, XGBoost, ARIMA
"""
import numpy as np
from typing import Dict, List, Optional
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class EnsembleModel(BaseModel):
    def __init__(self, models: Dict[str, BaseModel], weights: Dict[str, float] = None):
        super().__init__(name="ensemble")
        self.models = models
        self.weights = weights or config.model.ensemble_weights
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        logger.info(f"Ensemble weights: {self.weights}")

    def fit(self, X_train_dict: Dict[str, np.ndarray], y_train_dict: Dict[str, np.ndarray],
            X_val_dict: Dict[str, np.ndarray] = None, y_val_dict: Dict[str, np.ndarray] = None, **kwargs):
        """
        X_train_dict: {"lstm": (seq data), "xgboost": (flat data), "arima": y}
        """
        for name, model in self.models.items():
            logger.info(f"Training {name} in ensemble")
            X_tr = X_train_dict.get(name)
            y_tr = y_train_dict.get(name)
            X_val = X_val_dict.get(name) if X_val_dict else None
            y_val = y_val_dict.get(name) if y_val_dict else None

            if name == "arima":
                model.fit(y_train=y_tr)
            else:
                model.fit(X_tr, y_tr, X_val, y_val)

        self.is_fitted = True
        return {"weights": self.weights}

    def predict(self, X_dict: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Weighted average of predictions
        X_dict: {"lstm": X_test_seq, "xgboost": X_test_flat, "arima": steps or X_test}
        """
        predictions = {}
        for name, model in self.models.items():
            X = X_dict.get(name)
            if X is None:
                continue
            try:
                pred = model.predict(X)
                predictions[name] = pred
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")

        if not predictions:
            raise ValueError("No model predictions available")

        # Align lengths - use shortest
        min_len = min(len(p) for p in predictions.values())
        aligned = {k: v[-min_len:] if len(v) > min_len else v for k, v in predictions.items()}

        # Weighted sum
        ensemble_pred = np.zeros(min_len)
        for name, pred in aligned.items():
            w = self.weights.get(name, 0)
            ensemble_pred += w * pred

        return ensemble_pred

    def predict_single_model(self, name: str, X) -> np.ndarray:
        return self.models[name].predict(X)

    def forecast_future(self, last_sequences: Dict[str, np.ndarray], steps: int = 7) -> Dict[str, np.ndarray]:
        """
        Future forecast from each model
        last_sequences: {"lstm": (seq_len, features), "xgboost": (features,), "arima": None}
        """
        forecasts = {}
        for name, model in self.models.items():
            try:
                seq = last_sequences.get(name)
                if name == "arima":
                    forecasts[name] = model.forecast_future(steps=steps)
                else:
                    forecasts[name] = model.forecast_future(seq, steps=steps)
            except Exception as e:
                logger.warning(f"Future forecast failed for {name}: {e}")

        # Ensemble future
        if forecasts:
            min_len = min(len(v) for v in forecasts.values())
            ensemble = np.zeros(min_len)
            for name, pred in forecasts.items():
                w = self.weights.get(name, 0)
                ensemble += w * pred[-min_len:]
            forecasts['ensemble'] = ensemble

        return forecasts

    def save(self, path: str):
        import joblib
        from pathlib import Path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Save each submodel separately to avoid issues
        joblib.dump({"weights": self.weights, "model_names": list(self.models.keys())}, path)
        logger.info(f"Saved ensemble meta to {path}")
