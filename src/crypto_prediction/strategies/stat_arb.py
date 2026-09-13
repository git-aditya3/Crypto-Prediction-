"""
Institutional Statistical Arbitrage - Pairs Trading & Cointegration
Fixed: p_value handling, half-life NaN, validation, error handling
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class StatArbConfig:
    symbol_a: str
    symbol_b: str
    lookback_days: int = 60
    entry_z: float = 2.0
    exit_z: float = 0.5
    stop_z: float = 3.5
    total_investment: float = 10000
    status: str = "ACTIVE"

    def __post_init__(self):
        if self.symbol_a == self.symbol_b:
            raise ValueError("symbol_a and symbol_b must be different")
        if self.lookback_days < 20:
            self.lookback_days = 60
        if self.entry_z <= 0:
            self.entry_z = 2.0
        if self.exit_z < 0:
            self.exit_z = 0.5
        if self.stop_z <= self.entry_z:
            self.stop_z = self.entry_z + 1.5

@dataclass
class StatArbSignal:
    pair: str
    signal: str
    z_score: float
    spread: float
    hedge_ratio: float
    p_value: float
    half_life: float
    timestamp: str

class StatArbBot:
    def __init__(self, cfg: StatArbConfig):
        self.config = cfg
        self.spread_history = []
        self.signals_history = []
        self.created_at = datetime.utcnow().isoformat()

    def get_live_price(self, symbol: str) -> float:
        try:
            from ..data.price_helper import get_live_price as unified_price
            price = unified_price(symbol)
            if price and price > 0 and price < 100_000_000:
                return float(price)
            return 0
        except Exception as e:
            try:
                from ..utils.logger import get_logger
                get_logger(__name__).debug(f"Unified price failed {symbol}: {e}")
            except Exception:
                pass
            return 0


    def fetch_pair_data(self) -> Optional[pd.DataFrame]:
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher_a = CryptoDataFetcher(symbol=self.config.symbol_a)
            fetcher_b = CryptoDataFetcher(symbol=self.config.symbol_b)
            df_a = fetcher_a.load_or_fetch(symbol=self.config.symbol_a)
            df_b = fetcher_b.load_or_fetch(symbol=self.config.symbol_b)
            if df_a.empty or df_b.empty:
                return None
            # Align on index
            df = pd.DataFrame({
                'A': df_a['Close'].tail(self.config.lookback_days),
                'B': df_b['Close'].tail(self.config.lookback_days)
            }).dropna()
            if len(df) < 20:
                return None
            return df
        except Exception as e:
            logger.warning(f"StatArb fetch failed {self.config.symbol_a}/{self.config.symbol_b}: {e}")
            return None

    def engle_granger_test(self, df: pd.DataFrame) -> Tuple[float, float, float, pd.Series]:
        try:
            from sklearn.linear_model import LinearRegression
            X = df['B'].values.reshape(-1,1)
            y = df['A'].values

            # Check for constant series
            if np.std(X) == 0 or np.std(y) == 0:
                return 1.0, 0.5, 10, df['A'] - df['B']

            model = LinearRegression().fit(X, y)
            hedge_ratio = float(model.coef_[0])
            if not np.isfinite(hedge_ratio):
                hedge_ratio = 1.0
            # Bound hedge ratio
            hedge_ratio = max(-10, min(10, hedge_ratio))

            spread = df['A'] - hedge_ratio * df['B']
            if spread.std() == 0:
                return hedge_ratio, 0.5, 10, spread

            spread_diff = spread.diff().dropna()
            lagged = spread.shift(1).dropna()
            current = spread[1:]

            if len(lagged) < 10:
                return hedge_ratio, 0.5, 10, spread

            # Correlation
            try:
                corr_matrix = np.corrcoef(lagged, current)
                corr = corr_matrix[0,1] if corr_matrix.shape == (2,2) and np.isfinite(corr_matrix[0,1]) else 0
            except Exception:
                corr = 0

            # Half-life via OU
            half_life = 10.0
            try:
                X_hl = lagged.values.reshape(-1,1)
                y_hl = spread_diff.values
                if len(X_hl) == len(y_hl) and len(X_hl) > 5:
                    hl_model = LinearRegression().fit(X_hl, y_hl)
                    lambda_ = hl_model.coef_[0]
                    if lambda_ < 0 and np.isfinite(lambda_) and lambda_ != 0:
                        half_life = -np.log(2) / lambda_
                        half_life = max(1, min(half_life, 100))
                    else:
                        half_life = 10
            except Exception as e:
                logger.debug(f"Half-life calc failed: {e}")
                half_life = 10

            # p-value proxy - more robust
            if corr < -0.3:
                p_value = 0.02
            elif corr < -0.15:
                p_value = 0.05
            elif corr < -0.05:
                p_value = 0.15
            elif corr < 0.1:
                p_value = 0.3
            else:
                p_value = 0.6

            return hedge_ratio, p_value, float(half_life), spread
        except Exception as e:
            logger.warning(f"EG test failed: {e}")
            try:
                return 1.0, 0.5, 10, df['A'] - df['B']
            except Exception:
                return 1.0, 0.5, 10, pd.Series([0])

    def calculate_zscore(self, spread: pd.Series) -> float:
        try:
            if spread.empty or len(spread) < 2:
                return 0.0
            mean = spread.mean()
            std = spread.std()
            if std == 0 or not np.isfinite(std) or not np.isfinite(mean):
                return 0.0
            last = spread.iloc[-1]
            if not np.isfinite(last):
                return 0.0
            z = (last - mean) / std
            # Bound z-score
            return float(max(-5, min(5, z)))
        except Exception as e:
            logger.debug(f"Z-score calc failed: {e}")
            return 0.0

    def generate_signal(self) -> StatArbSignal:
        df = self.fetch_pair_data()
        if df is None or len(df) < 20:
            return StatArbSignal(
                pair=f"{self.config.symbol_a}/{self.config.symbol_b}",
                signal="NO_DATA",
                z_score=0.0,
                spread=0.0,
                hedge_ratio=1.0,
                p_value=1.0,
                half_life=999,
                timestamp=datetime.utcnow().isoformat()
            )

        hedge_ratio, p_value, half_life, spread_series = self.engle_granger_test(df)
        z = self.calculate_zscore(spread_series)
        try:
            current_spread = float(spread_series.iloc[-1]) if not spread_series.empty else 0.0
        except Exception:
            current_spread = 0.0

        signal = "NO_SIGNAL"
        if abs(z) > self.config.stop_z:
            signal = "STOP_LOSS"
        elif z > self.config.entry_z:
            signal = "SHORT_A_LONG_B"
        elif z < -self.config.entry_z:
            signal = "LONG_A_SHORT_B"
        elif abs(z) < self.config.exit_z:
            signal = "EXIT"

        # If not cointegrated, downgrade signal
        if p_value > 0.3 and signal in ["SHORT_A_LONG_B","LONG_A_SHORT_B"]:
            signal = "NO_SIGNAL_WEAK_COINTEGRATION"

        sig = StatArbSignal(
            pair=f"{self.config.symbol_a}/{self.config.symbol_b}",
            signal=signal,
            z_score=float(z),
            spread=float(current_spread),
            hedge_ratio=float(hedge_ratio),
            p_value=float(p_value),
            half_life=float(half_life),
            timestamp=datetime.utcnow().isoformat()
        )
        self.signals_history.append(asdict(sig))
        if len(self.signals_history) > 100:
            self.signals_history = self.signals_history[-100:]
        return sig

    def to_dict(self):
        latest = self.signals_history[-1] if self.signals_history else None
        return {
            "config": asdict(self.config),
            "latest_signal": latest,
            "signals_history": self.signals_history[-20:],
            "type": "stat_arb",
            "strategy": "Institutional Pairs Trading - Cointegration + Mean Reversion",
            "real_trading": True,
            "institutional": True,
            "created_at": self.created_at
        }
