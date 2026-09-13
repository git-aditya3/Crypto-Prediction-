"""
Backtesting metrics
"""
import numpy as np
import pandas as pd
from typing import Dict

def compute_backtest_metrics(equity_curve: pd.Series, trades: pd.DataFrame = None, risk_free_rate: float = 0.02) -> Dict[str, float]:
    returns = equity_curve.pct_change().dropna()
    
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100 if len(equity_curve) > 0 else 0
    # Annualized (assuming daily)
    n_days = len(equity_curve)
    annualized_return = ((1 + total_return/100) ** (252 / n_days) - 1) * 100 if n_days > 0 else 0

    volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0
    sharpe = (returns.mean() * 252 - risk_free_rate) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0

    # Max drawdown
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_dd = drawdown.min() * 100

    # Win rate
    win_rate = 0
    avg_win = 0
    avg_loss = 0
    profit_factor = 0
    if trades is not None and not trades.empty:
        wins = trades[trades['pnl'] > 0]
        losses = trades[trades['pnl'] <= 0]
        win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0

    return {
        "total_return_pct": float(total_return),
        "annualized_return_pct": float(annualized_return),
        "volatility_pct": float(volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown_pct": float(max_dd),
        "win_rate_pct": float(win_rate),
        "avg_win": float(avg_win),
        "avg_loss": float(avg_loss),
        "profit_factor": float(profit_factor),
        "num_trades": int(len(trades)) if trades is not None else 0,
        "final_equity": float(equity_curve.iloc[-1]) if len(equity_curve) > 0 else 0,
        "initial_equity": float(equity_curve.iloc[0]) if len(equity_curve) > 0 else 0
    }
