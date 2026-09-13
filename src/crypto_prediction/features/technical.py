"""
Technical indicators and feature engineering
"""
import pandas as pd
import numpy as np
from typing import List
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class TechnicalIndicators:
    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window=window).mean()

    @staticmethod
    def ema(series: pd.Series, window: int) -> pd.Series:
        return series.ewm(span=window, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, window: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = TechnicalIndicators.ema(series, fast)
        ema_slow = TechnicalIndicators.ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(series: pd.Series, window: int = 20, std: float = 2.0):
        sma = TechnicalIndicators.sma(series, window)
        rolling_std = series.rolling(window=window).std()
        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)
        return upper, sma, lower

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14):
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        return atr

    @staticmethod
    def stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3):
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        return k_percent, d_percent

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series):
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv


class FeatureEngineer:
    def __init__(self):
        self.cfg = config.features
        self.ti = TechnicalIndicators()

    def add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Returns'] = df['Close'].pct_change()
        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['Price_Range'] = df['High'] - df['Low']
        df['Price_Change'] = df['Close'] - df['Open']
        df['High_Low_Pct'] = (df['High'] - df['Low']) / df['Close']
        df['Volatility'] = df['Returns'].rolling(window=20).std()
        df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
        return df

    def add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Volume_SMA_20'] = self.ti.sma(df['Volume'], 20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        df['OBV'] = self.ti.obv(df['Close'], df['Volume'])
        df['Volume_Change'] = df['Volume'].pct_change()
        return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # SMA
        for w in self.cfg.sma_windows:
            df[f'SMA_{w}'] = self.ti.sma(df['Close'], w)
            df[f'Close_SMA_{w}_Ratio'] = df['Close'] / df[f'SMA_{w}']
        
        # EMA
        for w in self.cfg.ema_windows:
            df[f'EMA_{w}'] = self.ti.ema(df['Close'], w)

        # MACD
        macd_line, signal_line, hist = self.ti.macd(df['Close'], self.cfg.macd_fast, self.cfg.macd_slow, self.cfg.macd_signal)
        df['MACD'] = macd_line
        df['MACD_Signal'] = signal_line
        df['MACD_Hist'] = hist

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.ti.bollinger_bands(df['Close'], self.cfg.bb_window, self.cfg.bb_std)
        df['BB_Upper'] = bb_upper
        df['BB_Middle'] = bb_middle
        df['BB_Lower'] = bb_lower
        df['BB_Width'] = (bb_upper - bb_lower) / bb_middle
        df['BB_Position'] = (df['Close'] - bb_lower) / (bb_upper - bb_lower)

        # ATR
        df['ATR'] = self.ti.atr(df['High'], df['Low'], df['Close'], self.cfg.atr_window)

        return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['RSI'] = self.ti.rsi(df['Close'], self.cfg.rsi_window)
        
        k, d = self.ti.stochastic_oscillator(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = k
        df['Stoch_D'] = d

        # Rate of Change
        df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100
        df['Momentum'] = df['Close'] - df['Close'].shift(10)

        return df

    def add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for lag in self.cfg.lag_periods:
            df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
            df[f'Returns_Lag_{lag}'] = df['Returns'].shift(lag)
            df[f'Volume_Lag_{lag}'] = df['Volume'].shift(lag)
            df[f'RSI_Lag_{lag}'] = df['RSI'].shift(lag) if 'RSI' in df.columns else np.nan
        return df

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        # Cyclical encoding
        df['DayOfWeek_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
        df['DayOfWeek_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        return df

    def engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full feature engineering pipeline"""
        logger.info(f"Starting feature engineering on {len(df)} rows")
        df = df.copy()
        df.sort_index(inplace=True)

        if self.cfg.use_price_features:
            df = self.add_price_features(df)
        
        if self.cfg.use_technical_indicators:
            df = self.add_trend_indicators(df)
            df = self.add_momentum_indicators(df)
        
        if self.cfg.use_volume_features:
            df = self.add_volume_features(df)

        if self.cfg.use_lag_features:
            df = self.add_lag_features(df)

        df = self.add_time_features(df)

        # Target: next day close price and direction
        df['Target_Close'] = df['Close'].shift(-1)
        df['Target_Returns'] = df['Returns'].shift(-1)
        df['Target_Direction'] = (df['Target_Returns'] > 0).astype(int)

        # Multi-horizon targets
        for h in [3, 7]:
            df[f'Target_Close_{h}d'] = df['Close'].shift(-h)

        logger.info(f"Feature engineering complete: {df.shape[1]} features, {len(df)} rows")
        return df

    def get_feature_columns(self, df: pd.DataFrame, exclude_targets: bool = True) -> List[str]:
        exclude = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target_Close', 'Target_Returns', 'Target_Direction']
        exclude += [c for c in df.columns if c.startswith('Target_')]
        if exclude_targets:
            return [c for c in df.columns if c not in exclude]
        return list(df.columns)
