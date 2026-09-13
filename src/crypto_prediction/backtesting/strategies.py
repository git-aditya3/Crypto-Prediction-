"""
Trading strategies for backtesting
"""
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return Series of signals: 1=buy, -1=sell, 0=hold, indexed same as df"""
        pass

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__(name=f"MA_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        short_ma = df['Close'].rolling(self.short_window).mean()
        long_ma = df['Close'].rolling(self.long_window).mean()
        # Buy when short crosses above long
        signals[(short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))] = 1
        # Sell when short crosses below long
        signals[(short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))] = -1
        return signals

class RSIStrategy(BaseStrategy):
    def __init__(self, rsi_low: float = 30, rsi_high: float = 70):
        super().__init__(name=f"RSI_{rsi_low}_{rsi_high}")
        self.rsi_low = rsi_low
        self.rsi_high = rsi_high

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        if 'RSI' not in df.columns:
            return signals
        signals[df['RSI'] < self.rsi_low] = 1
        signals[df['RSI'] > self.rsi_high] = -1
        return signals

class PredictionStrategy(BaseStrategy):
    def __init__(self, prediction_col: str = "Predicted", threshold: float = 0.01):
        super().__init__(name=f"Pred_{prediction_col}_{threshold}")
        self.prediction_col = prediction_col
        self.threshold = threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        if self.prediction_col not in df.columns:
            # Try to find prediction column
            pred_cols = [c for c in df.columns if 'pred' in c.lower() or 'forecast' in c.lower()]
            if not pred_cols:
                return signals
            self.prediction_col = pred_cols[0]

        # Predicted return
        pred_return = (df[self.prediction_col] - df['Close']) / df['Close']
        signals[pred_return > self.threshold] = 1
        signals[pred_return < -self.threshold] = -1
        return signals

class EnsembleSignalStrategy(BaseStrategy):
    def __init__(self, sentiment_col: str = "Sentiment_Compound", pred_col: str = "Predicted", rsi_col: str = "RSI"):
        super().__init__(name="Ensemble_Signal")
        self.sentiment_col = sentiment_col
        self.pred_col = pred_col
        self.rsi_col = rsi_col

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        score = pd.Series(0.0, index=df.index)

        if self.pred_col in df.columns:
            pred_ret = (df[self.pred_col] - df['Close']) / df['Close']
            score += np.clip(pred_ret * 10, -1, 1)  # scale

        if self.sentiment_col in df.columns:
            score += df[self.sentiment_col] * 0.5

        if self.rsi_col in df.columns:
            # RSI: low = bullish
            score += (50 - df[self.rsi_col]) / 50 * 0.3

        signals[score > 0.5] = 1
        signals[score < -0.5] = -1
        return signals
