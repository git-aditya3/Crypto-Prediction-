"""
XGBoost model v3 Improved Accuracy
- Tuned hyperparameters
- Regularization
- Feature selection
- Early stopping 50 rounds
"""
import numpy as np
import xgboost as xgb
from typing import Dict, Optional
from sklearn.feature_selection import SelectFromModel
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class XGBoostModel(BaseModel):
    def __init__(self, n_estimators: int = None, max_depth: int = None, learning_rate: float = None,
                 subsample: float = None, colsample_bytree: float = None, 
                 reg_alpha: float = None, reg_lambda: float = None,
                 min_child_weight: int = None, gamma: float = None,
                 random_state: int = 42):
        super().__init__(name="xgboost")
        self.n_estimators = n_estimators or config.model.xgb_n_estimators
        self.max_depth = max_depth or config.model.xgb_max_depth
        self.learning_rate = learning_rate or config.model.xgb_learning_rate
        self.subsample = subsample or config.model.xgb_subsample
        self.colsample_bytree = colsample_bytree or config.model.xgb_colsample_bytree
        self.reg_alpha = reg_alpha or config.model.xgb_reg_alpha
        self.reg_lambda = reg_lambda or config.model.xgb_reg_lambda
        self.min_child_weight = min_child_weight or config.model.xgb_min_child_weight
        self.gamma = gamma or config.model.xgb_gamma
        self.random_state = random_state

        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            reg_alpha=self.reg_alpha,
            reg_lambda=self.reg_lambda,
            min_child_weight=self.min_child_weight,
            gamma=self.gamma,
            random_state=self.random_state,
            n_jobs=-1,
            early_stopping_rounds=50,
            eval_metric='rmse',
            tree_method='hist'  # Faster
        )
        self.feature_importance_ = None
        self.selected_features_mask = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None, **kwargs):
        logger.info(f"Training XGBoost v3 | n_est={self.n_estimators} depth={self.max_depth} lr={self.learning_rate} alpha={self.reg_alpha} lambda={self.reg_lambda}")
        
        # Feature selection for high-dimensional data
        if X_train.shape[1] > 50:
            logger.info(f"High dimensional data ({X_train.shape[1]} features), using feature selection")
            # Quick feature selection using initial model
            selector_model = xgb.XGBRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.1, random_state=self.random_state, n_jobs=-1
            )
            selector_model.fit(X_train, y_train)
            # Select top 80% importance or at least 50 features
            selector = SelectFromModel(selector_model, max_features=min(100, X_train.shape[1]), threshold=-np.inf)
            selector.fit(X_train, y_train)
            self.selected_features_mask = selector.get_support()
            X_train_selected = selector.transform(X_train)
            X_val_selected = selector.transform(X_val) if X_val is not None else None
            logger.info(f"Selected {X_train_selected.shape[1]} features from {X_train.shape[1]}")
        else:
            X_train_selected = X_train
            X_val_selected = X_val
        
        if X_val_selected is not None and y_val is not None:
            self.model.fit(
                X_train_selected, y_train,
                eval_set=[(X_val_selected, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train_selected, y_train)

        self.is_fitted = True
        self.feature_importance_ = self.model.feature_importances_
        logger.info(f"XGBoost v3 best_iteration: {getattr(self.model, 'best_iteration', 'N/A')} | best_score: {getattr(self.model, 'best_score', 'N/A')}")
        return {"best_iteration": getattr(self.model, 'best_iteration', self.n_estimators), "n_features_selected": X_train_selected.shape[1]}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        if self.selected_features_mask is not None:
            X = X[:, self.selected_features_mask]
        return self.model.predict(X)

    def get_feature_importance(self, feature_names=None):
        if self.feature_importance_ is None:
            return None
        import pandas as pd
        if self.selected_features_mask is not None and feature_names is not None:
            # Map back to original feature names
            selected_names = [name for i, name in enumerate(feature_names) if self.selected_features_mask[i]]
            names = selected_names
        else:
            names = feature_names if feature_names is not None else [f"f{i}" for i in range(len(self.feature_importance_))]
        df = pd.DataFrame({
            'feature': names,
            'importance': self.feature_importance_
        }).sort_values('importance', ascending=False)
        return df

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7) -> np.ndarray:
        if last_sequence.ndim == 2:
            current = last_sequence[-1].copy()
        else:
            current = last_sequence.copy()

        preds = []
        for _ in range(steps):
            pred = self.predict(current.reshape(1, -1))[0]
            preds.append(pred)
        return np.array(preds)
