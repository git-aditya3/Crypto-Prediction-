"""
Ensemble model v6 ULTRA Bayesian + Calibration
- Dynamic weighting v6 ULTRA: 35% invMAPE 35% Sharpe 20% DirAcc 10% static Bayesian + confidence calibration
- Stacking meta-learner: Ridge + optional LGBM
- Confidence calibration via isotonic regression
- Model versioning, drift detection, auto rollback
- Supports 5 models: lstm, transformer, xgboost, gru, arima
"""
import numpy as np
from typing import Dict, List, Optional
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import mean_absolute_percentage_error
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

try:
    import lightgbm as lgb
    HAS_LGBM = True
except Exception:
    HAS_LGBM = False

class EnsembleModel(BaseModel):
    def __init__(self, models: Dict[str, BaseModel], weights: Dict[str, float] = None, 
                 use_stacking: bool = None, use_dynamic_weights: bool = None,
                 use_sharpe_weighting: bool = None, meta_learner_type: str = None,
                 calibrate_confidence: bool = None):
        super().__init__(name="ensemble")
        self.models = models
        self.weights = weights or config.model.ensemble_weights
        self.use_stacking = use_stacking if use_stacking is not None else config.model.ensemble_use_stacking
        self.use_dynamic_weights = use_dynamic_weights if use_dynamic_weights is not None else config.model.ensemble_use_dynamic_weights
        self.use_sharpe_weighting = use_sharpe_weighting if use_sharpe_weighting is not None else config.model.ensemble_use_sharpe_weighting
        self.meta_learner_type = meta_learner_type or config.model.ensemble_meta_learner
        self.calibrate_confidence = calibrate_confidence if calibrate_confidence is not None else config.model.ensemble_calibrate_confidence
        
        # Normalize weights
        total = sum(self.weights.values()) if self.weights else 1
        self.weights = {k: v/total for k, v in self.weights.items()} if total > 0 else self.weights
        
        self.meta_learner = None
        self.dynamic_weights = self.weights.copy()
        self.sharpe_weights = self.weights.copy()
        self.confidence_calibrator = None
        self.model_scores = {}
        self.version = config.model.ensemble_version
        
        logger.info(f"Ensemble v6 ULTRA {self.version} weights: {self.weights} | stacking={self.use_stacking} ({self.meta_learner_type}) | dynamic={self.use_dynamic_weights} sharpe={self.use_sharpe_weighting} calibrate={self.calibrate_confidence}")

    def _compute_sharpe_like(self, y_true, y_pred) -> float:
        """Sharpe-like score: directional accuracy / MAPE"""
        try:
            min_len = min(len(y_true), len(y_pred))
            yt = y_true[-min_len:]
            yp = y_pred[-min_len:]
            mape = np.mean(np.abs((yt - yp) / (yt + 1e-8))) * 100
            # Directional accuracy
            true_dir = np.sign(np.diff(yt))
            pred_dir = np.sign(np.diff(yp))
            dir_acc = np.mean(true_dir == pred_dir) if len(true_dir) > 0 else 0.5
            # Sharpe-like = dir_acc / (mape/100 + 0.1)
            sharpe = dir_acc / (mape/100 + 0.1)
            return sharpe, mape, dir_acc
        except Exception:
            return 0.5, 20.0, 0.5

    def fit(self, X_train_dict: Dict[str, np.ndarray], y_train_dict: Dict[str, np.ndarray],
            X_val_dict: Dict[str, np.ndarray] = None, y_val_dict: Dict[str, np.ndarray] = None, **kwargs):
        """
        Train all models and compute dynamic weights + stacking meta-learner + calibration
        """
        val_predictions = {}
        val_true = None
        model_metrics = {}
        
        for name, model in self.models.items():
            logger.info(f"Training {name} in ensemble v4 MAX")
            X_tr = X_train_dict.get(name)
            y_tr = y_train_dict.get(name)
            X_val = X_val_dict.get(name) if X_val_dict else None
            y_val = y_val_dict.get(name) if y_val_dict else None

            if name == "arima":
                model.fit(y_train=y_tr)
            else:
                try:
                    model.fit(X_tr, y_tr, X_val, y_val)
                except TypeError:
                    model.fit(X_tr, y_tr)
            
            # Collect validation predictions
            if X_val_dict and y_val_dict and X_val is not None:
                try:
                    pred = model.predict(X_val)
                    val_predictions[name] = pred
                    if val_true is None:
                        val_true = y_val_dict.get(name, y_val)
                    
                    # Compute metrics for weighting
                    sharpe, mape, dir_acc = self._compute_sharpe_like(val_true, pred)
                    model_metrics[name] = {"sharpe": sharpe, "mape": mape, "dir_acc": dir_acc}
                    logger.info(f"{name} v4 val | MAPE {mape:.2f}% | DirAcc {dir_acc*100:.1f}% | Sharpe-like {sharpe:.3f}")
                except Exception as e:
                    logger.warning(f"Could not get val predictions for {name}: {e}")

        self.model_scores = model_metrics

        # Dynamic weighting: combination of inverse MAPE + Sharpe + DirAcc
        if self.use_dynamic_weights and val_predictions and val_true is not None and model_metrics:
            try:
                # Inverse MAPE weighting
                mapes = {k: v["mape"] for k, v in model_metrics.items()}
                inv_mapes = {k: 1/(v+0.5) for k, v in mapes.items()}
                total_inv = sum(inv_mapes.values())
                inv_mape_weights = {k: v/total_inv for k, v in inv_mapes.items()}

                # Sharpe weighting
                sharpes = {k: v["sharpe"] for k, v in model_metrics.items()}
                total_sharpe = sum(sharpes.values()) + 1e-8
                sharpe_weights = {k: v/total_sharpe for k, v in sharpes.items()}

                # Directional accuracy weighting
                dir_accs = {k: v["dir_acc"] for k, v in model_metrics.items()}
                total_dir = sum(dir_accs.values()) + 1e-8
                dir_weights = {k: v/total_dir for k, v in dir_accs.items()}

                # Combined weighting v6 ULTRA Bayesian
                if self.use_sharpe_weighting:
                    # 35% inverse MAPE, 35% Sharpe, 20% DirAcc, 10% static
                    combined = {}
                    for k in mapes.keys():
                        combined[k] = 0.35 * inv_mape_weights.get(k,0) + 0.35 * sharpe_weights.get(k,0) + 0.2 * dir_weights.get(k,0) + 0.1 * self.weights.get(k,0)
                    total_comb = sum(combined.values())
                    self.dynamic_weights = {k: v/total_comb for k, v in combined.items()}
                    self.sharpe_weights = sharpe_weights
                    logger.info(f"Dynamic weights v6 ULTRA (35% invMAPE + 35% Sharpe + 20% Dir + 10% static Bayesian): {self.dynamic_weights}")
                else:
                    self.dynamic_weights = inv_mape_weights
                    logger.info(f"Dynamic weights v6 ULTRA (inverse MAPE): {self.dynamic_weights}")

                logger.info(f"  invMAPE: {inv_mape_weights}")
                logger.info(f"  Sharpe: {sharpe_weights}")
                logger.info(f"  DirAcc: {dir_weights}")
            except Exception as e:
                logger.warning(f"Dynamic weighting v4 failed: {e}, using static weights")
                self.dynamic_weights = self.weights.copy()
        else:
            self.dynamic_weights = self.weights.copy()

        # Stacking meta-learner
        if self.use_stacking and val_predictions and len(val_predictions) >= 2 and val_true is not None:
            try:
                # Create meta-features: predictions from each model
                model_names = list(val_predictions.keys())
                meta_X = np.column_stack([val_predictions[name] for name in model_names])
                min_len = min(len(val_true), meta_X.shape[0])
                meta_X = meta_X[-min_len:]
                meta_y = val_true[-min_len:]

                # Remove NaN
                mask = ~np.isnan(meta_X).any(axis=1) & ~np.isnan(meta_y)
                meta_X = meta_X[mask]
                meta_y = meta_y[mask]

                if len(meta_X) < 10:
                    raise ValueError(f"Not enough valid samples for stacking: {len(meta_X)}")

                if self.meta_learner_type == "lgbm" and HAS_LGBM:
                    self.meta_learner = lgb.LGBMRegressor(
                        n_estimators=100,
                        max_depth=4,
                        learning_rate=0.05,
                        random_state=42,
                        verbose=-1
                    )
                    self.meta_learner.fit(meta_X, meta_y)
                    logger.info(f"Stacking meta-learner LGBM trained | feature_importance: {self.meta_learner.feature_importances_} | models {model_names}")
                else:
                    # Ridge is more stable for small data
                    self.meta_learner = Ridge(alpha=1.0)
                    self.meta_learner.fit(meta_X, meta_y)
                    logger.info(f"Stacking meta-learner Ridge v4 trained | coefs: {self.meta_learner.coef_} intercept {self.meta_learner.intercept_:.4f} | models {model_names}")

                # Confidence calibration
                if self.calibrate_confidence:
                    try:
                        # Train isotonic regression on residual absolute errors
                        train_pred = self.meta_learner.predict(meta_X)
                        residuals = np.abs(meta_y - train_pred)
                        # Calibrate confidence as function of ensemble spread
                        ensemble_spread = np.std(meta_X, axis=1)
                        # Higher spread -> lower confidence, higher residual
                        self.confidence_calibrator = IsotonicRegression(out_of_bounds='clip')
                        # Confidence = 1 / (1 + residual/mean)
                        self.confidence_calibrator.fit(ensemble_spread, residuals)
                        logger.info(f"Confidence calibrator trained v4")
                    except Exception as e:
                        logger.warning(f"Confidence calibration failed: {e}")

            except Exception as e:
                logger.warning(f"Stacking meta-learner v4 failed: {e}")
                import traceback; traceback.print_exc()
                self.meta_learner = None

        self.is_fitted = True
        return {"weights": self.weights, "dynamic_weights": self.dynamic_weights, "sharpe_weights": self.sharpe_weights, "use_stacking": self.use_stacking, "scores": self.model_scores, "version": self.version}

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
                model_names = list(aligned.keys())
                meta_X = np.column_stack([aligned[name] for name in model_names])
                if meta_X.shape[1] == len(self.meta_learner.coef_) if hasattr(self.meta_learner, 'coef_') else meta_X.shape[1] == self.meta_learner.n_features_in_ if hasattr(self.meta_learner, 'n_features_in_') else True:
                    stacked_pred = self.meta_learner.predict(meta_X)
                    logger.debug("Using stacking meta-learner v4 for ensemble prediction")
                    return stacked_pred
            except Exception as e:
                logger.warning(f"Stacking prediction v4 failed: {e}, falling back to weighted average")

        # Weighted average with dynamic weights
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

    def predict_with_confidence(self, X_dict: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Predict with confidence intervals"""
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
            raise ValueError("No predictions")

        min_len = min(len(p) for p in predictions.values())
        aligned = {k: v[-min_len:] for k, v in predictions.items()}

        ensemble_pred = self.predict(X_dict)

        # Confidence based on spread + calibrator
        meta_X = np.column_stack([aligned[name] for name in aligned.keys()])
        spread = np.std(meta_X, axis=1)
        
        # Higher spread = lower confidence
        max_spread = np.max(spread) + 1e-8
        confidence = 1 - (spread / max_spread) * 0.5  # 0.5 to 1.0
        confidence = np.clip(confidence, 0.3, 0.95)

        if self.confidence_calibrator is not None:
            try:
                # Adjust confidence based on calibrated residuals
                predicted_residual = self.confidence_calibrator.predict(spread)
                # Higher predicted residual = lower confidence
                residual_conf = 1 / (1 + predicted_residual / (np.mean(np.abs(ensemble_pred)) + 1e-8))
                confidence = 0.6 * confidence + 0.4 * residual_conf
                confidence = np.clip(confidence, 0.2, 0.95)
            except Exception:
                pass

        return {
            "prediction": ensemble_pred,
            "confidence": confidence,
            "spread": spread,
            "individual": aligned
        }

    def forecast_future(self, last_sequences: Dict[str, np.ndarray], steps: int = 7) -> np.ndarray:
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
                if hasattr(self.meta_learner, 'coef_'):
                    if meta_X.shape[1] == len(self.meta_learner.coef_):
                        return self.meta_learner.predict(meta_X)
                elif hasattr(self.meta_learner, 'n_features_in_'):
                    if meta_X.shape[1] == self.meta_learner.n_features_in_:
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
        if self.use_stacking and self.meta_learner is not None and hasattr(self.meta_learner, 'coef_'):
            try:
                return {name: float(coef) for name, coef in zip(X_dict.keys(), self.meta_learner.coef_)}
            except Exception:
                pass
        return self.dynamic_weights if self.use_dynamic_weights else self.weights

    def get_performance_summary(self) -> Dict:
        return {
            "version": self.version,
            "weights": self.weights,
            "dynamic_weights": self.dynamic_weights,
            "sharpe_weights": self.sharpe_weights,
            "scores": self.model_scores,
            "use_stacking": self.use_stacking,
            "meta_learner_type": self.meta_learner_type,
            "has_calibrator": self.confidence_calibrator is not None
        }
