"""
Ensemble model v3 Improved Accuracy
- Dynamic weighting based on validation performance
- Stacking meta-learner (Ridge)
- Inverse error weighting
"""
import numpy as np
from typing import Dict, List, Optional
from sklearn.linear_model import Ridge
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class EnsembleModel(BaseModel):
    def __init__(self, models: Dict[str, BaseModel], weights: Dict[str, float] = None, 
                 use_stacking: bool = None, use_dynamic_weights: bool = None):
        super().__init__(name="ensemble")
        self.models = models
        self.weights = weights or config.model.ensemble_weights
        self.use_stacking = use_stacking if use_stacking is not None else config.model.ensemble_use_stacking
        self.use_dynamic_weights = use_dynamic_weights if use_dynamic_weights is not None else config.model.ensemble_use_dynamic_weights
        
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        
        self.meta_learner = None
        self.dynamic_weights = self.weights.copy()
        
        logger.info(f"Ensemble v3 weights: {self.weights} | stacking={self.use_stacking} | dynamic={self.use_dynamic_weights}")

    def fit(self, X_train_dict: Dict[str, np.ndarray], y_train_dict: Dict[str, np.ndarray],
            X_val_dict: Dict[str, np.ndarray] = None, y_val_dict: Dict[str, np.ndarray] = None, **kwargs):
        """
        Train all models and compute dynamic weights + stacking meta-learner
        """
        val_predictions = {}
        val_true = None
        
        for name, model in self.models.items():
            logger.info(f"Training {name} in ensemble v3")
            X_tr = X_train_dict.get(name)
            y_tr = y_train_dict.get(name)
            X_val = X_val_dict.get(name) if X_val_dict else None
            y_val = y_val_dict.get(name) if y_val_dict else None

            if name == "arima":
                model.fit(y_train=y_tr)
            else:
                model.fit(X_tr, y_tr, X_val, y_val)
            
            # Collect validation predictions for dynamic weighting and stacking
            if X_val_dict and y_val_dict and X_val is not None:
                try:
                    pred = model.predict(X_val)
                    val_predictions[name] = pred
                    if val_true is None:
                        val_true = y_val_dict.get(name, y_val)
                except Exception as e:
                    logger.warning(f"Could not get val predictions for {name}: {e}")

        # Dynamic weighting based on validation MAPE (inverse error)
        if self.use_dynamic_weights and val_predictions and val_true is not None:
            try:
                errors = {}
                for name, pred in val_predictions.items():
                    min_len = min(len(val_true), len(pred))
                    mape = np.mean(np.abs((val_true[-min_len:] - pred[-min_len:]) / (val_true[-min_len:] + 1e-8))) * 100
                    errors[name] = mape
                    logger.info(f"{name} val MAPE: {mape:.2f}%")
                
                # Inverse error weighting
                inv_errors = {k: 1/(v+1e-8) for k, v in errors.items()}
                total_inv = sum(inv_errors.values())
                self.dynamic_weights = {k: v/total_inv for k, v in inv_errors.items()}
                logger.info(f"Dynamic weights (inverse MAPE): {self.dynamic_weights}")
            except Exception as e:
                logger.warning(f"Dynamic weighting failed: {e}, using static weights")
                self.dynamic_weights = self.weights.copy()

        # Stacking meta-learner
        if self.use_stacking and val_predictions and len(val_predictions) >= 2:
            try:
                # Create meta-features: predictions from each model
                meta_X = np.column_stack([val_predictions[name] for name in val_predictions.keys()])
                # Align lengths
                min_len = min(len(val_true), meta_X.shape[0])
                meta_X = meta_X[-min_len:]
                meta_y = val_true[-min_len:]
                
                self.meta_learner = Ridge(alpha=1.0)
                self.meta_learner.fit(meta_X, meta_y)
                logger.info(f"Stacking meta-learner trained | coefs: {self.meta_learner.coef_}")
            except Exception as e:
                logger.warning(f"Stacking meta-learner failed: {e}")
                self.meta_learner = None

        self.is_fitted = True
        return {"weights": self.weights, "dynamic_weights": self.dynamic_weights, "use_stacking": self.use_stacking}

    def predict(self, X_dict: Dict[str, np.ndarray]) -> np.ndarray:
        predictions = {}
        for name, model in self.models.items():
            X = X_dict.get(name)
            if X is None:
                continue
            try:
                pred = model.predict(X)
                predictions[name] = pred
            except Exception as e:
                logger.warning(f"Prediction failed for {name}: {e}")

        if not predictions:
            raise ValueError("No predictions from ensemble models")

        # Align all predictions to same length
        min_len = min(len(p) for p in predictions.values())
        aligned = {k: v[-min_len:] for k, v in predictions.items()}

        # Use stacking if available
        if self.use_stacking and self.meta_learner is not None:
            try:
                # Ensure order matches training
                model_names = list(aligned.keys())
                meta_X = np.column_stack([aligned[name] for name in model_names])
                # If meta-learner was trained on different order, need to handle
                # For simplicity, use dynamic weights if order mismatch
                if meta_X.shape[1] == len(self.meta_learner.coef_):
                    stacked_pred = self.meta_learner.predict(meta_X)
                    logger.info("Using stacking meta-learner for ensemble prediction")
                    return stacked_pred
            except Exception as e:
                logger.warning(f"Stacking prediction failed: {e}, falling back to weighted average")

        # Weighted average with dynamic weights
        weights_to_use = self.dynamic_weights if self.use_dynamic_weights else self.weights
        ensemble_pred = np.zeros(min_len)
        total_weight = 0
        for name, pred in aligned.items():
            w = weights_to_use.get(name, 0)
            ensemble_pred += w * pred
            total_weight += w
        
        # Normalize if weights don't sum to 1 due to missing models
        if total_weight > 0:
            ensemble_pred /= total_weight
        
        return ensemble_pred

    def forecast_future(self, last_sequences: Dict[str, np.ndarray], steps: int = 7) -> np.ndarray:
        """Future forecast using each model's forecast_future"""
        predictions = {}
        for name, model in self.models.items():
            seq = last_sequences.get(name)
            if seq is None:
                continue
            try:
                pred = model.forecast_future(seq, steps=steps)
                predictions[name] = pred
            except Exception as e:
                logger.warning(f"Future forecast failed for {name}: {e}")

        if not predictions:
            raise ValueError("No future forecasts from ensemble models")

        min_len = min(len(p) for p in predictions.values())
        aligned = {k: v[:min_len] for k, v in predictions.items()}

        if self.use_stacking and self.meta_learner is not None:
            try:
                model_names = list(aligned.keys())
                meta_X = np.column_stack([aligned[name] for name in model_names])
                if meta_X.shape[1] == len(self.meta_learner.coef_):
                    return self.meta_learner.predict(meta_X)
            except Exception:
                pass

        weights_to_use = self.dynamic_weights if self.use_dynamic_weights else self.weights
        ensemble_pred = np.zeros(min_len)
        total_weight = 0
        for name, pred in aligned.items():
            w = weights_to_use.get(name, 0)
            ensemble_pred += w * pred
            total_weight += w
        
        if total_weight > 0:
            ensemble_pred /= total_weight
        
        return ensemble_pred

    def get_model_contributions(self, X_dict: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Get each model's contribution to ensemble - for interpretability"""
        if self.use_stacking and self.meta_learner is not None:
            return {name: float(coef) for name, coef in zip(X_dict.keys(), self.meta_learner.coef_)}
        return self.dynamic_weights if self.use_dynamic_weights else self.weights
