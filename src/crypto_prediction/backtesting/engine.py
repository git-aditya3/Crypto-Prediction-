"""
Backtesting engine - portfolio simulation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..config import get_config
from ..utils.logger import get_logger
from .strategies import BaseStrategy
from .metrics import compute_backtest_metrics

logger = get_logger(__name__)
config = get_config()

@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    side: str  # long/short
    qty: float
    pnl: float = 0.0

@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: Dict[str, float]
    signals: pd.Series

class BacktestEngine:
    def __init__(self, initial_capital: float = None, commission: float = None, slippage: float = None):
        self.initial_capital = initial_capital or config.backtest.initial_capital
        self.commission = commission or config.backtest.commission
        self.slippage = slippage or config.backtest.slippage
        self.risk_free_rate = config.backtest.risk_free_rate

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, price_col: str = "Close") -> BacktestResult:
        """
        Simple long-only backtest:
        - signal 1 = buy with all capital (if not already in position)
        - signal -1 = sell all
        - 0 = hold
        """
        df = df.copy().sort_index()
        signals = strategy.generate_signals(df)

        capital = self.initial_capital
        position = 0.0  # amount of asset held
        entry_price = 0.0
        entry_date = None

        equity_curve = []
        trades_list: List[Trade] = []

        for date, row in df.iterrows():
            price = row[price_col]
            signal = signals.loc[date]

            # Apply slippage
            exec_price = price * (1 + self.slippage) if signal == 1 else price * (1 - self.slippage) if signal == -1 else price

            if signal == 1 and position == 0:
                # Buy
                cost = capital
                fee = cost * self.commission
                qty = (cost - fee) / exec_price
                position = qty
                entry_price = exec_price
                entry_date = date
                capital = 0

            elif signal == -1 and position > 0:
                # Sell
                proceeds = position * exec_price
                fee = proceeds * self.commission
                pnl = proceeds - fee - (entry_price * position)
                capital = proceeds - fee
                trades_list.append(Trade(
                    entry_date=entry_date,
                    exit_date=date,
                    entry_price=entry_price,
                    exit_price=exec_price,
                    side="long",
                    qty=position,
                    pnl=pnl
                ))
                position = 0
                entry_price = 0
                entry_date = None

            # Equity = capital + position value
            equity = capital + (position * price if position > 0 else 0)
            equity_curve.append((date, equity))

        # Close open position at last price
        if position > 0:
            last_price = df[price_col].iloc[-1]
            proceeds = position * last_price * (1 - self.slippage)
            fee = proceeds * self.commission
            pnl = proceeds - fee - (entry_price * position)
            capital = proceeds - fee
            trades_list.append(Trade(
                entry_date=entry_date,
                exit_date=df.index[-1],
                entry_price=entry_price,
                exit_price=last_price,
                side="long",
                qty=position,
                pnl=pnl
            ))
            # update last equity
            equity_curve[-1] = (equity_curve[-1][0], capital)

        equity_df = pd.DataFrame(equity_curve, columns=['date', 'equity']).set_index('date')['equity']
        trades_df = pd.DataFrame([t.__dict__ for t in trades_list])

        metrics = compute_backtest_metrics(equity_df, trades_df, risk_free_rate=self.risk_free_rate)

        logger.info(f"Backtest {strategy.name}: Return {metrics['total_return_pct']:.2f}% | Sharpe {metrics['sharpe_ratio']:.2f} | DD {metrics['max_drawdown_pct']:.2f}% | Trades {metrics['num_trades']}")

        return BacktestResult(equity_curve=equity_df, trades=trades_df, metrics=metrics, signals=signals)

    def run_prediction_backtest(self, df: pd.DataFrame, predictions: np.ndarray, threshold: float = 0.01) -> BacktestResult:
        """
        Backtest using prediction series aligned to df
        predictions: predicted next close prices
        """
        from .strategies import PredictionStrategy
        df = df.copy()
        # Align predictions to df index tail
        pred_series = pd.Series(predictions, index=df.index[-len(predictions):])
        df.loc[pred_series.index, 'Predicted'] = pred_series.values
        # Forward fill for earlier dates
        df['Predicted'] = df['Predicted'].ffill().bfill()

        strat = PredictionStrategy(prediction_col="Predicted", threshold=threshold)
        return self.run(df, strat)

    def compare_strategies(self, df: pd.DataFrame, strategies: List[BaseStrategy]) -> Dict[str, BacktestResult]:
        results = {}
        for strat in strategies:
            try:
                results[strat.name] = self.run(df, strat)
            except Exception as e:
                logger.warning(f"Strategy {strat.name} failed: {e}")
        return results
