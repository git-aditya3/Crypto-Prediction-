"""
XGBoost model for crypto prediction
"""
import numpy as np
import xgboost as xgb
from typing import Dict, Optional
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class XGBoostModel(BaseModel):
    def __init__(self, n_estimators: int = None, max_depth: int = None, learning_rate: float = None,
                 subsample: float = None, colsample_bytree: float = None, random_state: int = 42):
        super().__init__(name="xgboost")
        self.n_estimators = n_estimators or config.model.xgb_n_estimators
        self.max_depth = max_depth or config.model.xgb_max_depth
        self.learning_rate = learning_rate or config.model.xgb_learning_rate
        self.subsample = subsample or config.model.xgb_subsample
        self.colsample_bytree = colsample_bytree or config.model.xgb_colsample_bytree
        self.random_state = random_state

        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            n_jobs=-1,
            early_stopping_rounds=20,
            eval_metric='rmse'
        )
        self.feature_importance_ = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None, **kwargs):
        logger.info(f"Training XGBoost | n_est={self.n_estimators} max_depth={self.max_depth}")
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)

        self.is_fitted = True
        # Feature importance
        self.feature_importance_ = self.model.feature_importances_
        logger.info(f"XGBoost best_iteration: {getattr(self.model, 'best_iteration', 'N/A')}")
        return {"best_iteration": getattr(self.model, 'best_iteration', self.n_estimators)}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        return self.model.predict(X)

    def get_feature_importance(self, feature_names=None):
        if self.feature_importance_ is None:
            return None
        import pandas as pd
        names = feature_names if feature_names is not None else [f"f{i}" for i in range(len(self.feature_importance_))]
        df = pd.DataFrame({
            'feature': names,
            'importance': self.feature_importance_
        }).sort_values('importance', ascending=False)
        return df

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7) -> np.ndarray:
        """
        For XGBoost, last_sequence is expected to be (n_features,) or (seq_len, n_features)
        We use last row as base and autoregress
        """
        if last_sequence.ndim == 2:
            current = last_sequence[-1].copy()
        else:
            current = last_sequence.copy()

        preds = []
        for _ in range(steps):
            pred = self.predict(current.reshape(1, -1))[0]
            preds.append(pred)
            # Simplistic: keep same features for next step
            # In advanced version, you'd update lag features
        return np.array(preds)
