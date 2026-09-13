"""
Performance Optimization - Max Results Models
Advanced techniques for maximum accuracy with real market data
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
import torch
import torch.nn as nn

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class WalkForwardValidator:
    """
    Walk-forward validation for real market data - no lookahead bias
    Trains on past, validates on future - simulates real trading
    """
    def __init__(self, n_splits: int = 5, test_size: float = 0.2):
        self.n_splits = n_splits
        self.test_size = test_size
    
    def split(self, df: pd.DataFrame):
        """Generate walk-forward splits"""
        n = len(df)
        test_len = int(n * self.test_size)
        train_len = n - test_len
        
        # Walk-forward: expanding window
        splits = []
        for i in range(self.n_splits):
            # Train on increasing data, test on next chunk
            train_end = int(train_len * (0.5 + 0.5 * (i+1) / self.n_splits))
            test_start = train_end
            test_end = min(test_start + test_len // self.n_splits, n)
            
            if test_end > test_start:
                splits.append((list(range(0, train_end)), list(range(test_start, test_end))))
        
        return splits
    
    def evaluate_model(self, model, X: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> Dict:
        """Evaluate with walk-forward - real market simulation"""
        splits = self.split(df)
        scores = []
        
        for train_idx, test_idx in splits:
            try:
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                # Train
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                # Metrics on real data
                mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                
                scores.append({"mape": mape, "rmse": rmse})
            except Exception as e:
                logger.warning(f"Walk-forward split failed: {e}")
                continue
        
        if scores:
            avg_mape = np.mean([s["mape"] for s in scores])
            avg_rmse = np.mean([s["rmse"] for s in scores])
            return {"mape": avg_mape, "rmse": avg_rmse, "splits": len(scores)}
        return {"mape": 100, "rmse": 1e6, "splits": 0}

class DataAugmentation:
    """
    Data augmentation for crypto - improves robustness with real market noise
    """
    @staticmethod
    def add_noise(X: np.ndarray, noise_level: float = 0.01) -> np.ndarray:
        """Add Gaussian noise - simulates real market volatility"""
        noise = np.random.normal(0, noise_level, X.shape)
        return X + noise
    
    @staticmethod
    def time_warp(X: np.ndarray, warp_factor: float = 0.1) -> np.ndarray:
        """Time warping - simulates different market speeds"""
        # Simple implementation: stretch/compress sequences
        batch, seq_len, features = X.shape
        warped = np.zeros_like(X)
        
        for i in range(batch):
            # Random warp
            warp = np.random.uniform(1-warp_factor, 1+warp_factor)
            new_len = int(seq_len * warp)
            new_len = max(1, min(new_len, seq_len))
            
            # Interpolate
            for f in range(features):
                x = X[i, :, f]
                x_new = np.interp(
                    np.linspace(0, len(x)-1, seq_len),
                    np.linspace(0, len(x)-1, new_len),
                    x[:new_len] if new_len <= len(x) else np.pad(x, (0, new_len-len(x)), mode='edge')
                )
                warped[i, :, f] = x_new
        
        return warped
    
    @staticmethod
    def augment_training_data(X: np.ndarray, y: np.ndarray, augmentation_factor: int = 2) -> Tuple[np.ndarray, np.ndarray]:
        """Augment training data for better generalization"""
        augmented_X = [X]
        augmented_y = [y]
        
        for _ in range(augmentation_factor - 1):
            # Add noise
            X_noisy = DataAugmentation.add_noise(X, noise_level=0.01)
            augmented_X.append(X_noisy)
            augmented_y.append(y)
        
        return np.concatenate(augmented_X, axis=0), np.concatenate(augmented_y, axis=0)

class AdvancedEnsembleV4:
    """
    Advanced Ensemble v4 - Maximum performance
    - Dynamic weighting based on recent walk-forward performance
    - Stacking with Ridge + LightGBM meta-learner
    - Confidence-weighted predictions
    - Real market data focus
    """
    def __init__(self, models: Dict, use_walk_forward: bool = True):
        self.models = models
        self.use_walk_forward = use_walk_forward
        self.weights = {}
        self.meta_learner = None
        self.performance_history = {}
        self.confidence_scores = {}
    
    def compute_dynamic_weights(self, X_val: Dict[str, np.ndarray], y_val: np.ndarray) -> Dict[str, float]:
        """Compute weights based on recent validation performance - real data"""
        performances = {}
        
        for name, model in self.models.items():
            try:
                X = X_val.get(name)
                if X is None:
                    continue
                
                y_pred = model.predict(X)
                min_len = min(len(y_val), len(y_pred))
                y_true = y_val[-min_len:]
                y_pred = y_pred[-min_len:]
                
                # MAPE on real data
                mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
                # Directional accuracy - important for real trading
                true_dir = np.sign(np.diff(y_true))
                pred_dir = np.sign(np.diff(y_pred))
                dir_acc = np.mean(true_dir == pred_dir) * 100 if len(true_dir) > 0 else 50
                
                # Combined score: lower MAPE + higher DirAcc = better
                # For real trading, directional accuracy is crucial
                score = (100 - mape) * 0.7 + dir_acc * 0.3
                performances[name] = {"mape": mape, "dir_acc": dir_acc, "score": score}
                
                logger.info(f"  {name}: MAPE {mape:.2f}% DirAcc {dir_acc:.1f}% Score {score:.1f}")
                
            except Exception as e:
                logger.warning(f"Failed to evaluate {name}: {e}")
                performances[name] = {"mape": 100, "dir_acc": 50, "score": 0}
        
        # Inverse MAPE weighting + DirAcc bonus for real trading
        if performances:
            # Higher score = better
            total_score = sum(max(0, p["score"]) for p in performances.values())
            if total_score > 0:
                weights = {k: max(0, v["score"]) / total_score for k, v in performances.items()}
            else:
                # Equal weighting if all fail
                weights = {k: 1/len(performances) for k in performances.keys()}
            
            # Boost best model slightly for max performance
            best_model = max(performances.items(), key=lambda x: x[1]["score"])
            weights[best_model[0]] *= 1.2  # 20% boost to best
            
            # Renormalize
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            self.performance_history = performances
            self.weights = weights
            
            logger.info(f"Dynamic weights (max performance): {weights}")
            return weights
        
        # Fallback to equal weights
        return {k: 1/len(self.models) for k in self.models.keys()}
    
    def train_meta_learner(self, X_val: Dict[str, np.ndarray], y_val: np.ndarray):
        """Train stacking meta-learner with Ridge regression"""
        try:
            from sklearn.linear_model import Ridge
            from sklearn.ensemble import GradientBoostingRegressor
            
            # Collect predictions
            preds = {}
            for name, model in self.models.items():
                X = X_val.get(name)
                if X is None:
                    continue
                try:
                    p = model.predict(X)
                    preds[name] = p
                except Exception:
                    continue
            
            if len(preds) < 2:
                logger.warning("Not enough models for stacking")
                return
            
            # Align lengths
            min_len = min(len(p) for p in preds.values())
            min_len = min(min_len, len(y_val))
            
            meta_X = np.column_stack([preds[name][-min_len:] for name in preds.keys()])
            meta_y = y_val[-min_len:]
            
            # Ridge meta-learner - robust, prevents overfitting
            self.meta_learner = Ridge(alpha=1.0)
            self.meta_learner.fit(meta_X, meta_y)
            
            logger.info(f"Meta-learner trained: coefs {self.meta_learner.coef_}, intercept {self.meta_learner.intercept_:.4f}")
            
        except Exception as e:
            logger.warning(f"Meta-learner training failed: {e}")
            self.meta_learner = None
    
    def predict(self, X_dict: Dict[str, np.ndarray], return_confidence: bool = False) -> np.ndarray:
        """Predict with dynamic weighting and confidence"""
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
            raise ValueError("No predictions from models")
        
        # Align
        min_len = min(len(p) for p in predictions.values())
        aligned = {k: v[-min_len:] for k, v in predictions.items()}
        
        # Use meta-learner if available
        if self.meta_learner is not None:
            try:
                meta_X = np.column_stack([aligned[name] for name in aligned.keys()])
                if meta_X.shape[1] == len(self.meta_learner.coef_):
                    stacked = self.meta_learner.predict(meta_X)
                    if return_confidence:
                        # Confidence based on model agreement
                        std = np.std(meta_X, axis=1)
                        confidence = 1 / (1 + std)  # Higher agreement = higher confidence
                        return stacked, confidence
                    return stacked
            except Exception as e:
                logger.warning(f"Stacking failed, using weighted average: {e}")
        
        # Dynamic weighted average - max performance
        weights = self.weights or {k: 1/len(aligned) for k in aligned.keys()}
        ensemble = np.zeros(min_len)
        total_weight = 0
        
        for name, pred in aligned.items():
            w = weights.get(name, 0)
            ensemble += w * pred
            total_weight += w
        
        if total_weight > 0:
            ensemble /= total_weight
        
        if return_confidence:
            # Confidence based on model agreement and individual confidences
            meta_X = np.column_stack([aligned[name] for name in aligned.keys()])
            std = np.std(meta_X, axis=1)
            # Lower std = higher confidence
            confidence = np.clip(1 - std / (np.mean(np.abs(meta_X), axis=1) + 1e-8), 0, 1)
            return ensemble, confidence
        
        return ensemble

class ModelOptimizer:
    """
    Model optimization for max results with real market data
    """
    @staticmethod
    def optimize_lstm_hyperparams() -> Dict:
        """Optimized LSTM hyperparams for crypto - max performance"""
        return {
            "hidden_size": 256,  # Larger for more capacity
            "num_layers": 3,  # Deeper
            "dropout": 0.25,  # Lower dropout for more learning, but still regularized
            "bidirectional": True,  # Both directions
            "use_attention": True,  # Attention mechanism
            "learning_rate": 0.0005,  # Lower for stability
            "weight_decay": 1e-4,  # Regularization
            "batch_size": 32,
            "epochs": 100,  # More epochs
            "patience": 15,  # Early stopping patience
            "use_augmentation": True,  # Data augmentation
            "loss": "huber"  # Robust to outliers
        }
    
    @staticmethod
    def optimize_transformer_hyperparams() -> Dict:
        """Optimized Transformer hyperparams - max performance"""
        return {
            "d_model": 256,
            "nhead": 8,
            "num_layers": 4,
            "dim_feedforward": 512,
            "dropout": 0.15,  # Lower for crypto
            "use_learnable_pe": True,  # Learnable positional encoding
            "use_attention_pooling": True,  # Attention pooling vs last token
            "learning_rate": 0.0003,
            "weight_decay": 1e-4,
            "batch_size": 32,
            "epochs": 100,
            "patience": 15,
            "loss": "huber"
        }
    
    @staticmethod
    def optimize_xgboost_hyperparams() -> Dict:
        """Optimized XGBoost hyperparams - max performance for crypto"""
        return {
            "n_estimators": 1500,  # More trees
            "max_depth": 8,  # Deeper
            "learning_rate": 0.02,  # Lower for better generalization
            "subsample": 0.9,  # Stochastic
            "colsample_bytree": 0.8,
            "colsample_bylevel": 0.8,
            "reg_alpha": 0.1,  # L1
            "reg_lambda": 1.0,  # L2
            "min_child_weight": 3,
            "gamma": 0.05,  # Lower for more splits
            "max_delta_step": 1,  # For imbalanced
            "tree_method": "hist"  # Faster
        }

def compute_real_trading_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    """
    Compute metrics that matter for REAL trading - not just academic
    """
    # Basic regression
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
    
    # Directional accuracy - crucial for real trading
    true_returns = np.diff(y_true) / y_true[:-1]
    pred_returns = np.diff(y_pred) / y_pred[:-1]
    true_dir = np.sign(true_returns)
    pred_dir = np.sign(pred_returns)
    dir_acc = np.mean(true_dir == pred_dir) * 100 if len(true_dir) > 0 else 50
    
    # Profitability simulation - real trading metric
    # If we go long when predicted up, short when predicted down
    strategy_returns = []
    for i in range(len(true_dir)):
        if pred_dir[i] == 1:  # Predicted up, go long
            strategy_returns.append(true_returns[i])
        elif pred_dir[i] == -1:  # Predicted down, go short
            strategy_returns.append(-true_returns[i])
        else:
            strategy_returns.append(0)
    
    avg_return = np.mean(strategy_returns) * 100 if strategy_returns else 0
    win_rate = np.mean([r > 0 for r in strategy_returns]) * 100 if strategy_returns else 50
    
    # Sharpe-like ratio for real trading
    if len(strategy_returns) > 1 and np.std(strategy_returns) > 0:
        sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
    else:
        sharpe = 0
    
    return {
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "directional_accuracy": dir_acc,
        "avg_return": avg_return,
        "win_rate": win_rate,
        "sharpe": sharpe,
        "real_trading_score": dir_acc * 0.5 + win_rate * 0.3 + (100 - min(mape, 100)) * 0.2
    }
