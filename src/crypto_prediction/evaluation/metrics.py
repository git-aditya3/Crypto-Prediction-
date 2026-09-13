"""
Evaluation metrics for crypto prediction
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score
from typing import Dict

def rmse(y_true, y_pred) -> float:
    return np.sqrt(mean_squared_error(y_true, y_pred))

def mae(y_true, y_pred) -> float:
    return mean_absolute_error(y_true, y_pred)

def mape(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def directional_accuracy(y_true, y_pred) -> float:
    """
    Accuracy of predicting price direction (up/down)
    y_true, y_pred are price series, we compare diff signs
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    if len(y_true) < 2:
        return 0.0
    true_dir = np.sign(np.diff(y_true))
    pred_dir = np.sign(np.diff(y_pred))
    # For price prediction, compare predicted direction vs true direction of actual?
    # Alternative: pred_dir based on pred vs previous true
    # Here we use pred diff vs true diff
    return np.mean(true_dir == pred_dir) * 100

def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    excess = returns - risk_free_rate
    if np.std(excess) == 0:
        return 0.0
    return np.mean(excess) / np.std(excess) * np.sqrt(252)

def max_drawdown(prices: np.ndarray) -> float:
    peak = np.maximum.accumulate(prices)
    drawdown = (prices - peak) / peak
    return np.min(drawdown) * 100

def compute_regression_metrics(y_true, y_pred) -> Dict[str, float]:
    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()
    # Align
    min_len = min(len(y_true), len(y_pred))
    y_true = y_true[-min_len:]
    y_pred = y_pred[-min_len:]

    metrics = {
        "rmse": float(rmse(y_true, y_pred)),
        "mae": float(mae(y_true, y_pred)),
        "mape": float(mape(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "directional_accuracy": float(directional_accuracy(y_true, y_pred)),
        "mse": float(mean_squared_error(y_true, y_pred)),
    }
    return metrics

def compute_classification_metrics(y_true_dir, y_pred_dir) -> Dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true_dir, y_pred_dir) * 100)
    }

def generate_report(y_true, y_pred, symbol: str = "BTC-USD") -> str:
    metrics = compute_regression_metrics(y_true, y_pred)
    report = f"\n=== {symbol} Evaluation Report ===\n"
    for k, v in metrics.items():
        report += f"{k:25s}: {v:.4f}\n"
    return report
