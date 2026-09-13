"""
Technical indicators and feature engineering v4 MAX - 200+ features
- ADX, CCI, Williams %R, MFI, Ichimoku, Keltner, VWAP, Fibonacci
- Kalman filter smoothing, Fourier features, market regime, orderbook approximations
- Volatility clustering, efficiency ratio, trend consistency, fractal, Hurst
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
    def wma(series: pd.Series, window: int) -> pd.Series:
        weights = np.arange(1, window + 1)
        return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    @staticmethod
    def rsi(series: pd.Series, window: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        gain = gain.ewm(alpha=1/window, adjust=False).mean()
        loss = loss.ewm(alpha=1/window, adjust=False).mean()
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
        atr = tr.ewm(alpha=1/window, adjust=False).mean()
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

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14):
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = minus_dm.abs()

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/window, adjust=False).mean()

        plus_di = 100 * (plus_dm.ewm(alpha=1/window, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/window, adjust=False).mean() / atr)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.ewm(alpha=1/window, adjust=False).mean()
        return adx, plus_di, minus_di

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20):
        tp = (high + low + close) / 3
        sma = tp.rolling(window).mean()
        mad = tp.rolling(window).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
        cci = (tp - sma) / (0.015 * mad)
        return cci

    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14):
        highest_high = high.rolling(window).max()
        lowest_low = low.rolling(window).min()
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr

    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 14):
        tp = (high + low + close) / 3
        raw_money_flow = tp * volume
        positive_flow = (raw_money_flow.where(tp > tp.shift(1), 0)).rolling(window).sum()
        negative_flow = (raw_money_flow.where(tp < tp.shift(1), 0)).rolling(window).sum()
        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi

    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series):
        tenkan_sen = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun_sen = (high.rolling(26).max() + low.rolling(26).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        senkou_span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou_span = close.shift(-26)
        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span

    @staticmethod
    def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20, atr_mult: float = 2.0):
        ema = TechnicalIndicators.ema(close, window)
        atr = TechnicalIndicators.atr(high, low, close, window)
        upper = ema + (atr * atr_mult)
        lower = ema - (atr * atr_mult)
        return upper, ema, lower

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series):
        tp = (high + low + close) / 3
        vwap = (tp * volume).cumsum() / volume.cumsum()
        return vwap

    @staticmethod
    def fibonacci_levels(close: pd.Series, window: int = 50):
        recent_high = close.rolling(window).max()
        recent_low = close.rolling(window).min()
        diff = recent_high - recent_low
        fib_618 = recent_high - 0.618 * diff
        distance = (close - fib_618) / diff
        return distance

    @staticmethod
    def kalman_filter(series: pd.Series, process_var: float = 1e-5, measurement_var: float = 0.1) -> pd.Series:
        """Kalman filter smoothing - reduces noise, keeps trend"""
        try:
            n = len(series)
            if n < 10:
                return series
            x_est = series.iloc[0]
            p_est = 1.0
            smoothed = []
            for z in series.values:
                p_pred = p_est + process_var
                k_gain = p_pred / (p_pred + measurement_var)
                x_est = x_est + k_gain * (z - x_est)
                p_est = (1 - k_gain) * p_pred
                smoothed.append(x_est)
            return pd.Series(smoothed, index=series.index)
        except Exception:
            return series

    @staticmethod
    def fourier_features(series: pd.Series, n_components: int = 3) -> pd.DataFrame:
        """Fourier transform features - capture cyclical patterns"""
        try:
            values = series.fillna(method='ffill').fillna(0).values
            if len(values) < 20:
                return pd.DataFrame()
            
            fft = np.fft.fft(values)
            freqs = np.fft.fftfreq(len(values))
            
            # Get dominant frequencies
            fft_abs = np.abs(fft)
            dominant_idx = np.argsort(fft_abs)[-n_components-1:-1]  # Exclude DC
            
            features = {}
            for i, idx in enumerate(dominant_idx):
                features[f'Fourier_Freq_{i}'] = float(freqs[idx]) if idx < len(freqs) else 0
                features[f'Fourier_Amp_{i}'] = float(fft_abs[idx]) if idx < len(fft_abs) else 0
            
            # Create DataFrame with same index
            df = pd.DataFrame([features] * len(series), index=series.index)
            return df
        except Exception:
            return pd.DataFrame()

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
        df['Volatility_10'] = df['Returns'].rolling(window=10).std()
        df['Volatility_30'] = df['Returns'].rolling(window=30).std()
        df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
        df['Log_Returns_5'] = df['Log_Returns'].rolling(5).sum()
        df['Price_Acceleration'] = df['Returns'].diff()
        df['Close_SMA_20_Dist'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).mean()
        
        # v4 additions
        if self.cfg.use_kalman_filter:
            try:
                df['Close_Kalman'] = self.ti.kalman_filter(df['Close'])
                df['Close_Kalman_Diff'] = df['Close'] - df['Close_Kalman']
                df['Kalman_Trend'] = df['Close_Kalman'].diff(5) / df['Close_Kalman']
            except Exception:
                pass
        
        # Fractal dimension approximation
        try:
            df['Fractal_HL'] = (df['High'] - df['Low']) / df['Close'].rolling(10).std()
        except Exception:
            pass
        
        return df

    def add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Volume_SMA_20'] = self.ti.sma(df['Volume'], 20)
        df['Volume_EMA_20'] = self.ti.ema(df['Volume'], 20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        df['OBV'] = self.ti.obv(df['Close'], df['Volume'])
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_Std'] = df['Volume'].rolling(20).std() / df['Volume'].rolling(20).mean()
        try:
            df['VWAP'] = self.ti.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
            df['Close_VWAP_Dist'] = (df['Close'] - df['VWAP']) / df['VWAP']
        except Exception:
            pass
        df['Volume_Momentum'] = df['Volume'].pct_change(5)
        
        # v4: Volume profile
        try:
            df['Volume_Weighted_Return'] = df['Returns'] * df['Volume_Ratio']
            df['Volume_Trend'] = df['Volume'].rolling(20).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True)
        except Exception:
            pass
        
        return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for w in self.cfg.sma_windows:
            df[f'SMA_{w}'] = self.ti.sma(df['Close'], w)
            df[f'Close_SMA_{w}_Ratio'] = df['Close'] / df[f'SMA_{w}']
            df[f'SMA_{w}_Slope'] = df[f'SMA_{w}'].diff(5) / df[f'SMA_{w}']
        
        for w in self.cfg.ema_windows:
            df[f'EMA_{w}'] = self.ti.ema(df['Close'], w)
            df[f'Close_EMA_{w}_Ratio'] = df['Close'] / df[f'EMA_{w}']

        for w in [10, 20, 50]:
            df[f'WMA_{w}'] = self.ti.wma(df['Close'], w)

        macd_line, signal_line, hist = self.ti.macd(df['Close'], self.cfg.macd_fast, self.cfg.macd_slow, self.cfg.macd_signal)
        df['MACD'] = macd_line
        df['MACD_Signal'] = signal_line
        df['MACD_Hist'] = hist
        df['MACD_Hist_Slope'] = hist.diff(3)

        bb_upper, bb_middle, bb_lower = self.ti.bollinger_bands(df['Close'], self.cfg.bb_window, self.cfg.bb_std)
        df['BB_Upper'] = bb_upper
        df['BB_Middle'] = bb_middle
        df['BB_Lower'] = bb_lower
        df['BB_Width'] = (bb_upper - bb_lower) / bb_middle
        df['BB_Position'] = (df['Close'] - bb_lower) / (bb_upper - bb_lower)
        df['BB_Squeeze'] = (df['BB_Width'] < df['BB_Width'].rolling(20).mean()).astype(int)

        try:
            kc_upper, kc_middle, kc_lower = self.ti.keltner_channels(df['High'], df['Low'], df['Close'])
            df['KC_Upper'] = kc_upper
            df['KC_Lower'] = kc_lower
            df['KC_Position'] = (df['Close'] - kc_lower) / (kc_upper - kc_lower)
        except Exception:
            pass

        df['ATR'] = self.ti.atr(df['High'], df['Low'], df['Close'], self.cfg.atr_window)
        df['ATR_Pct'] = df['ATR'] / df['Close']

        if self.cfg.use_advanced_indicators:
            try:
                adx, plus_di, minus_di = self.ti.adx(df['High'], df['Low'], df['Close'], self.cfg.adx_window)
                df['ADX'] = adx
                df['Plus_DI'] = plus_di
                df['Minus_DI'] = minus_di
                df['DI_Diff'] = plus_di - minus_di
                df['ADX_Strength'] = (adx > 25).astype(int)
            except Exception:
                pass

            try:
                tenkan, kijun, senkou_a, senkou_b, chikou = self.ti.ichimoku(df['High'], df['Low'], df['Close'])
                df['Ichimoku_Tenkan'] = tenkan
                df['Ichimoku_Kijun'] = kijun
                df['Ichimoku_Senkou_A'] = senkou_a
                df['Ichimoku_Senkou_B'] = senkou_b
                df['Ichimoku_Cloud_Dist'] = (df['Close'] - (senkou_a + senkou_b)/2) / df['Close']
                df['Ichimoku_Bullish'] = (df['Close'] > senkou_a).astype(int) & (df['Close'] > senkou_b).astype(int)
            except Exception:
                pass

        return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['RSI'] = self.ti.rsi(df['Close'], self.cfg.rsi_window)
        df['RSI_SMA'] = self.ti.sma(df['RSI'], 14)
        df['RSI_Divergence'] = df['RSI'] - df['RSI_SMA']
        
        k, d = self.ti.stochastic_oscillator(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = k
        df['Stoch_D'] = d
        df['Stoch_Diff'] = k - d

        df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100
        df['ROC_5'] = ((df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5)) * 100
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        df['Momentum_5'] = df['Close'] - df['Close'].shift(5)

        if self.cfg.use_advanced_indicators:
            try:
                df['CCI'] = self.ti.cci(df['High'], df['Low'], df['Close'], self.cfg.cci_window)
                df['Williams_R'] = self.ti.williams_r(df['High'], df['Low'], df['Close'], self.cfg.williams_window)
                df['MFI'] = self.ti.mfi(df['High'], df['Low'], df['Close'], df['Volume'], self.cfg.mfi_window)
            except Exception:
                pass

            try:
                df['Fib_Dist'] = self.ti.fibonacci_levels(df['Close'])
            except Exception:
                pass

            # v4: Additional momentum
            try:
                df['RSI_Momentum'] = df['RSI'].diff(3)
                df['MFI_Momentum'] = df['MFI'].diff(3) if 'MFI' in df.columns else 0
                df['ROC_Momentum'] = df['ROC'].diff(3)
            except Exception:
                pass

        return df

    def add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for lag in self.cfg.lag_periods:
            df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
            df[f'Returns_Lag_{lag}'] = df['Returns'].shift(lag)
            df[f'Volume_Lag_{lag}'] = df['Volume'].shift(lag)
            df[f'RSI_Lag_{lag}'] = df['RSI'].shift(lag) if 'RSI' in df.columns else np.nan
            df[f'Log_Returns_Lag_{lag}'] = df['Log_Returns'].shift(lag)
            df[f'Price_Change_Lag_{lag}'] = df['Price_Change'].shift(lag)
            # v4: More lags
            df[f'ATR_Lag_{lag}'] = df['ATR'].shift(lag) if 'ATR' in df.columns else np.nan
            df[f'Volatility_Lag_{lag}'] = df['Volatility'].shift(lag) if 'Volatility' in df.columns else np.nan
        return df

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['DayOfMonth'] = df.index.day
        df['DayOfWeek_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
        df['DayOfWeek_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        df['DayOfMonth_sin'] = np.sin(2 * np.pi * df['DayOfMonth'] / 31)
        df['DayOfMonth_cos'] = np.cos(2 * np.pi * df['DayOfMonth'] / 31)
        df['Is_Month_End'] = (df.index.is_month_end).astype(int)
        df['Is_Month_Start'] = (df.index.is_month_start).astype(int)
        
        # v4: More time features
        try:
            df['Is_Weekend'] = (df['DayOfWeek'] >= 5).astype(int)
            df['WeekOfYear'] = df.index.isocalendar().week.astype(int)
            df['WeekOfYear_sin'] = np.sin(2 * np.pi * df['WeekOfYear'] / 52)
            df['WeekOfYear_cos'] = np.cos(2 * np.pi * df['WeekOfYear'] / 52)
        except Exception:
            pass
        
        return df

    def add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Volatility_Regime'] = (df['Volatility'] > df['Volatility'].rolling(50).mean()).astype(int)
        df['Volatility_Cluster'] = df['Volatility'].rolling(5).mean() / df['Volatility'].rolling(50).mean()
        df['Efficiency_Ratio'] = (df['Close'] - df['Close'].shift(10)).abs() / df['Close'].diff().abs().rolling(10).sum()
        df['Trend_Consistency'] = df['Returns'].rolling(10).apply(lambda x: (x > 0).sum() / len(x), raw=True)
        
        # v4: More volatility features
        try:
            df['Volatility_Ratio'] = df['Volatility_10'] / df['Volatility_30']
            df['Volatility_Change'] = df['Volatility'].pct_change()
            df['High_Vol_Regime'] = (df['Volatility'] > df['Volatility'].rolling(100).quantile(0.8)).astype(int)
            df['Low_Vol_Regime'] = (df['Volatility'] < df['Volatility'].rolling(100).quantile(0.2)).astype(int)
            df['GARCH_Proxy'] = df['Returns'].rolling(20).std() / df['Returns'].rolling(100).std()
        except Exception:
            pass
        
        return df

    def add_market_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """v4: Market regime detection - bull/bear/sideways"""
        df = df.copy()
        try:
            # Trend regime via SMA
            df['Bull_Market'] = (df['Close'] > df['SMA_50']).astype(int) & (df['SMA_50'] > df['SMA_200']).astype(int) if 'SMA_200' in df.columns else (df['Close'] > df['SMA_50']).astype(int)
            df['Bear_Market'] = (df['Close'] < df['SMA_50']).astype(int) & (df['SMA_50'] < df['SMA_200']).astype(int) if 'SMA_200' in df.columns else (df['Close'] < df['SMA_50']).astype(int)
            df['Sideways_Market'] = 1 - df['Bull_Market'] - df['Bear_Market']
            df['Sideways_Market'] = df['Sideways_Market'].clip(0,1)
            
            # Volatility regime
            df['High_Vol_Market'] = (df['Volatility'] > df['Volatility'].rolling(50).mean() * 1.5).astype(int)
            
            # Combined regime
            df['Regime'] = df['Bull_Market'] * 1 + df['Bear_Market'] * -1 + df['Sideways_Market'] * 0
        except Exception as e:
            logger.debug(f"Market regime features failed: {e}")
        
        return df

    def add_fourier_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """v4: Fourier features for cyclical patterns"""
        if not self.cfg.use_fourier_features:
            return df
        
        df = df.copy()
        try:
            # Simple Fourier: sin/cos of price position in recent range
            window = 50
            recent_high = df['Close'].rolling(window).max()
            recent_low = df['Close'].rolling(window).min()
            price_pos = (df['Close'] - recent_low) / (recent_high - recent_low + 1e-8)
            
            df['Fourier_Sin_1'] = np.sin(2 * np.pi * price_pos)
            df['Fourier_Cos_1'] = np.cos(2 * np.pi * price_pos)
            df['Fourier_Sin_2'] = np.sin(4 * np.pi * price_pos)
            df['Fourier_Cos_2'] = np.cos(4 * np.pi * price_pos)
            
            # Price cycle via detrended
            detrended = df['Close'] - df['SMA_20'] if 'SMA_20' in df.columns else df['Close'] - df['Close'].rolling(20).mean()
            df['Detrended_Sin'] = np.sin(2 * np.pi * detrended / detrended.rolling(20).std())
        except Exception as e:
            logger.debug(f"Fourier features failed: {e}")
        
        return df

    def engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full feature engineering pipeline v4 MAX - 200+ features"""
        logger.info(f"Starting feature engineering v4 MAX on {len(df)} rows")
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
        df = self.add_volatility_features(df)
        
        if self.cfg.use_market_regime:
            df = self.add_market_regime_features(df)
        
        if self.cfg.use_fourier_features:
            df = self.add_fourier_features(df)

        # Target: next day close price and direction
        df['Target_Close'] = df['Close'].shift(-1)
        df['Target_Returns'] = df['Returns'].shift(-1)
        df['Target_Log_Returns'] = df['Log_Returns'].shift(-1)
        df['Target_Direction'] = (df['Target_Returns'] > 0).astype(int)

        # Multi-horizon targets
        for h in [2, 3, 5, 7, 14]:
            df[f'Target_Close_{h}d'] = df['Close'].shift(-h)
            df[f'Target_Returns_{h}d'] = df['Close'].pct_change(h).shift(-h)

        logger.info(f"Feature engineering v4 MAX complete: {df.shape[1]} features, {len(df)} rows | version v4_max")
        return df

    def get_feature_columns(self, df: pd.DataFrame, exclude_targets: bool = True) -> List[str]:
        exclude = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target_Close', 'Target_Returns', 'Target_Log_Returns', 'Target_Direction']
        exclude += [c for c in df.columns if c.startswith('Target_Close_')]
        exclude += [c for c in df.columns if c.startswith('Target_Returns_')]
        if exclude_targets:
            return [c for c in df.columns if c not in exclude]
        return list(df.columns)
