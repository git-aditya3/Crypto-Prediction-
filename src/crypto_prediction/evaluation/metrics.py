"""
Evaluation metrics v5 MAX for crypto prediction - comprehensive
- RMSE, MAE, MAPE, R2, directional accuracy, Sharpe, Sortino, max drawdown, Calmar, profit factor
- Confidence intervals, prediction intervals, quantile losses
- Versioning, robust handling
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score
from typing import Dict, List, Optional
import math

def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def mae(y_true, y_pred) -> float:
    return float(mean_absolute_error(y_true, y_pred))

def mape(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = np.abs(y_true) > 1e-8
    if np.sum(mask) == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / (y_true[mask] + 1e-8))) * 100)

def smape(y_true, y_pred) -> float:
    """Symmetric MAPE - more robust"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2 + 1e-8
    return float(np.mean(np.abs(y_true - y_pred) / denom) * 100)

def directional_accuracy(y_true, y_pred) -> float:
    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()
    if len(y_true) < 2:
        return 50.0
    true_dir = np.sign(np.diff(y_true))
    pred_dir = np.sign(np.diff(y_pred))
    # Handle zeros
    true_dir = np.where(true_dir == 0, 1, true_dir)
    pred_dir = np.where(pred_dir == 0, 1, pred_dir)
    return float(np.mean(true_dir == pred_dir) * 100)

def directional_accuracy_with_threshold(y_true, y_pred, threshold: float = 0.001) -> float:
    """Directional accuracy ignoring small moves < threshold"""
    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()
    if len(y_true) < 2:
        return 50.0
    true_returns = np.diff(y_true) / (y_true[:-1] + 1e-8)
    pred_returns = np.diff(y_pred) / (y_true[:-1] + 1e-8)
    # Only consider moves > threshold
    mask = np.abs(true_returns) > threshold
    if np.sum(mask) == 0:
        return 50.0
    true_dir = np.sign(true_returns[mask])
    pred_dir = np.sign(pred_returns[mask])
    return float(np.mean(true_dir == pred_dir) * 100)

def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    returns = np.array(returns).ravel()
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free_rate / 252
    std = np.std(excess)
    if std < 1e-8:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(252))

def sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    returns = np.array(returns).ravel()
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free_rate / 252
    downside = excess[excess < 0]
    if len(downside) == 0 or np.std(downside) < 1e-8:
        return float(np.mean(excess) * np.sqrt(252) / 1e-8) if np.mean(excess) > 0 else 0.0
    return float(np.mean(excess) / np.std(downside) * np.sqrt(252))

def max_drawdown(prices: np.ndarray) -> float:
    prices = np.array(prices).ravel()
    if len(prices) < 2:
        return 0.0
    peak = np.maximum.accumulate(prices)
    drawdown = (prices - peak) / (peak + 1e-8)
    return float(np.min(drawdown) * 100)

def max_drawdown_duration(prices: np.ndarray) -> int:
    """Max drawdown duration in periods"""
    prices = np.array(prices).ravel()
    if len(prices) < 2:
        return 0
    peak = np.maximum.accumulate(prices)
    # Find periods where price < peak
    drawdown = prices < peak
    max_duration = 0
    current = 0
    for is_dd in drawdown:
        if is_dd:
            current += 1
            max_duration = max(max_duration, current)
        else:
            current = 0
    return int(max_duration)

def calmar_ratio(returns: np.ndarray, prices: np.ndarray) -> float:
    """Calmar = annualized return / |max drawdown|"""
    returns = np.array(returns).ravel()
    if len(returns) < 2:
        return 0.0
    ann_return = np.mean(returns) * 252
    mdd = abs(max_drawdown(prices) / 100) + 1e-8
    return float(ann_return / mdd)

def profit_factor(returns: np.ndarray) -> float:
    """Profit factor = gross profit / gross loss"""
    returns = np.array(returns).ravel()
    if len(returns) == 0:
        return 0.0
    profits = returns[returns > 0]
    losses = returns[returns < 0]
    gross_profit = np.sum(profits) if len(profits) > 0 else 0
    gross_loss = abs(np.sum(losses)) if len(losses) > 0 else 1e-8
    return float(gross_profit / gross_loss)

def win_rate(returns: np.ndarray) -> float:
    returns = np.array(returns).ravel()
    if len(returns) == 0:
        return 0.0
    return float(np.mean(returns > 0) * 100)

def compute_regression_metrics(y_true, y_pred, y_true_prices: Optional[np.ndarray] = None) -> Dict[str, float]:
    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()
    min_len = min(len(y_true), len(y_pred))
    y_true = y_true[-min_len:]
    y_pred = y_pred[-min_len:]

    # Basic
    metrics = {
        "rmse": rmse(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "smape": smape(y_true, y_pred),
        "r2": float(r2_score(y_true, y_pred)) if min_len > 1 else 0.0,
        "directional_accuracy": directional_accuracy(y_true, y_pred),
        "directional_accuracy_threshold": directional_accuracy_with_threshold(y_true, y_pred, threshold=0.002),
        "mse": float(mean_squared_error(y_true, y_pred)),
        "bias": float(np.mean(y_pred - y_true)),
        "std_error": float(np.std(y_true - y_pred)),
    }

    # Returns based
    try:
        true_returns = np.diff(y_true) / (y_true[:-1] + 1e-8)
        pred_returns = np.diff(y_pred) / (y_true[:-1] + 1e-8)
        metrics["sharpe"] = sharpe_ratio(true_returns)
        metrics["sortino"] = sortino_ratio(true_returns)
        metrics["max_drawdown"] = max_drawdown(y_true)
        metrics["max_drawdown_duration"] = max_drawdown_duration(y_true)
        metrics["calmar"] = calmar_ratio(true_returns, y_true)
        metrics["profit_factor"] = profit_factor(true_returns)
        metrics["win_rate"] = win_rate(true_returns)
        metrics["volatility"] = float(np.std(true_returns) * np.sqrt(252) * 100)  # annualized %
        
        # Prediction quality for returns
        if len(true_returns) > 1:
            metrics["return_correlation"] = float(np.corrcoef(true_returns, pred_returns)[0,1]) if np.std(pred_returns) > 1e-8 else 0.0
        else:
            metrics["return_correlation"] = 0.0
    except Exception:
        metrics["sharpe"] = 0.0
        metrics["sortino"] = 0.0
        metrics["max_drawdown"] = 0.0
        metrics["calmar"] = 0.0
        metrics["profit_factor"] = 0.0
        metrics["win_rate"] = 50.0

    metrics["version"] = "v5_max"
    return metrics

def compute_classification_metrics(y_true_dir, y_pred_dir) -> Dict[str, float]:
    y_true_dir = np.array(y_true_dir).ravel()
    y_pred_dir = np.array(y_pred_dir).ravel()
    min_len = min(len(y_true_dir), len(y_pred_dir))
    y_true_dir = y_true_dir[-min_len:]
    y_pred_dir = y_pred_dir[-min_len:]
    
    try:
        acc = accuracy_score(y_true_dir, y_pred_dir) * 100
    except Exception:
        acc = 50.0
    
    return {
        "accuracy": float(acc),
        "version": "v5_max"
    }

def compute_quantile_loss(y_true, y_pred, quantile: float = 0.5) -> float:
    """Quantile loss for confidence intervals"""
    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()
    min_len = min(len(y_true), len(y_pred))
    y_true = y_true[-min_len:]
    y_pred = y_pred[-min_len:]
    diff = y_true - y_pred
    loss = np.where(diff >= 0, quantile * diff, (quantile - 1) * diff)
    return float(np.mean(loss))

def generate_report(y_true, y_pred, symbol: str = "BTC-USD") -> str:
    metrics = compute_regression_metrics(y_true, y_pred)
    report = f"\n=== {symbol} Evaluation Report v5 MAX ===\n"
    report += f"Version: v5_max | Models: LSTM v4, Transformer v4, GRU v4, XGB v4, ARIMA v4, Ensemble v4\n"
    report += "-" * 60 + "\n"
    for k, v in metrics.items():
        if k == "version":
            continue
        if isinstance(v, float):
            report += f"{k:30s}: {v:12.4f}\n"
        else:
            report += f"{k:30s}: {v}\n"
    report += "-" * 60 + "\n"
    # Interpretation
    mape = metrics.get("mape", 999)
    dir_acc = metrics.get("directional_accuracy", 0)
    if mape < 5:
        report += "✅ Excellent accuracy (MAPE < 5%)\n"
    elif mape < 10:
        report += "✅ Good accuracy (MAPE < 10%)\n"
    elif mape < 15:
        report += "⚠️ Moderate accuracy (MAPE < 15%)\n"
    else:
        report += "❌ Poor accuracy (MAPE >= 15%) - needs retrain\n"
    
    if dir_acc > 60:
        report += "✅ Good directional accuracy (>60%)\n"
    elif dir_acc > 55:
        report += "⚠️ Moderate directional accuracy\n"
    else:
        report += "❌ Poor directional accuracy - random\n"
    
    return report

def compare_models(results: Dict[str, Dict]) -> Dict:
    """Compare multiple model results"""
    if not results:
        return {}
    
    comparison = {}
    for model_name, metrics in results.items():
        if isinstance(metrics, dict) and "mape" in metrics:
            comparison[model_name] = {
                "mape": metrics.get("mape", 999),
                "rmse": metrics.get("rmse", 999),
                "r2": metrics.get("r2", 0),
                "dir_acc": metrics.get("directional_accuracy", 0),
                "sharpe": metrics.get("sharpe", 0)
            }
    
    # Rank by MAPE
    ranked = sorted(comparison.items(), key=lambda x: x[1]["mape"])
    
    return {
        "comparison": comparison,
        "ranking": [name for name, _ in ranked],
        "best_model": ranked[0][0] if ranked else None,
        "best_mape": ranked[0][1]["mape"] if ranked else None,
        "version": "v5_max"
    }
