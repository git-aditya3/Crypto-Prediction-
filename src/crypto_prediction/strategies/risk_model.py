"""
Institutional Risk Model v5 MAX - VaR, CVaR, Kelly, Drawdown Control, metrics, pooling, thread-safe
- Fixed var_size formula, correlation NaN handling, validation, versioning
- Session pooling, cache, metrics, CoinDCX INR aware
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import threading
import numpy as np
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)
VERSION = "v5_max"

@dataclass
class RiskConfig:
    confidence: float = 0.95
    lookback_days: int = 60
    max_drawdown_pct: float = 10.0
    max_position_pct: float = 20.0
    kelly_fraction: float = 0.5

    def __post_init__(self):
        if not 0.5 <= self.confidence <= 0.99:
            self.confidence = 0.95
        if self.lookback_days < 20:
            self.lookback_days = 60
        if self.lookback_days > 365:
            self.lookback_days = 365
        if self.max_drawdown_pct <= 0:
            self.max_drawdown_pct = 10.0
        if self.max_position_pct <= 0 or self.max_position_pct > 100:
            self.max_position_pct = 20.0
        if not 0.1 <= self.kelly_fraction <= 1.0:
            self.kelly_fraction = 0.5

class InstitutionalRiskModel:
    def __init__(self, cfg: RiskConfig = None):
        self.config = cfg or RiskConfig()
        self._lock = threading.Lock()
        self._metrics = {
            "var_calculations": 0,
            "cvar_calculations": 0,
            "position_sizings": 0,
            "portfolio_risks": 0,
            "errors": 0
        }
        self._returns_cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300
        import time
        self._cache_times = {}

    def get_live_price(self, symbol: str) -> float:
        try:
            from ..data.price_helper import get_live_price as unified_price
            price = unified_price(symbol)
            if price and price > 0:
                return float(price)
            return 0
        except Exception:
            return 0

    def fetch_returns(self, symbol: str) -> Optional[pd.Series]:
        if not symbol or not isinstance(symbol, str):
            return None
        # Cache check
        import time
        with self._cache_lock:
            if symbol in self._returns_cache:
                ts = self._cache_times.get(symbol, 0)
                if time.time() - ts < self._cache_ttl:
                    return self._returns_cache[symbol]
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            if df.empty or len(df) < 10:
                return None
            returns = df['Close'].pct_change().dropna().tail(self.config.lookback_days)
            if returns.empty:
                return None
            returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
            if returns.empty:
                return None
            with self._cache_lock:
                self._returns_cache[symbol] = returns
                self._cache_times[symbol] = time.time()
            return returns
        except Exception as e:
            logger.debug(f"Returns fetch failed v5 {symbol}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return None

    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        with self._lock:
            self._metrics["var_calculations"] += 1
        try:
            if returns is None or len(returns) < 10:
                return 0.02
            clean = returns[np.isfinite(returns)]
            if len(clean) < 10:
                return 0.02
            var = np.percentile(clean, (1-confidence)*100)
            result = float(abs(var))
            return max(0.001, min(result, 0.20))
        except Exception as e:
            logger.debug(f"VaR v5 calc failed: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return 0.02

    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        with self._lock:
            self._metrics["cvar_calculations"] += 1
        try:
            if returns is None or len(returns) < 10:
                return 0.03
            clean = returns[np.isfinite(returns)]
            if len(clean) < 10:
                return 0.03
            var_threshold = np.percentile(clean, (1-confidence)*100)
            tail = clean[clean <= var_threshold]
            if tail.empty:
                return self.calculate_var(returns, confidence) * 1.5
            cvar = tail.mean()
            if not np.isfinite(cvar):
                return self.calculate_var(returns, confidence) * 1.5
            result = float(abs(cvar))
            return max(0.001, min(result, 0.30))
        except Exception as e:
            logger.debug(f"CVaR v5 calc failed: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return 0.03

    def kelly_criterion(self, win_rate: float, win_loss_ratio: float) -> float:
        try:
            if win_loss_ratio <= 0 or not np.isfinite(win_loss_ratio):
                return 0.0
            if not 0 <= win_rate <= 1:
                win_rate = 0.55
            if not np.isfinite(win_rate):
                win_rate = 0.55
            kelly = win_rate - (1-win_rate) / win_loss_ratio
            if not np.isfinite(kelly):
                return 0.02
            kelly = kelly * self.config.kelly_fraction
            kelly = max(0, min(kelly, self.config.max_position_pct/100))
            return float(kelly)
        except Exception as e:
            logger.debug(f"Kelly v5 calc failed: {e}")
            return 0.02

    def calculate_drawdown(self, equity_curve: List[float]) -> Dict:
        try:
            if not equity_curve or len(equity_curve) < 2:
                return {"max_drawdown_pct": 0, "current_drawdown_pct": 0, "is_breached": False, "version": "v5_max"}
            equity = np.array(equity_curve, dtype=float)
            equity = equity[np.isfinite(equity)]
            if len(equity) < 2:
                return {"max_drawdown_pct": 0, "current_drawdown_pct": 0, "is_breached": False, "version": "v5_max"}
            peak = np.maximum.accumulate(equity)
            peak = np.where(peak == 0, 1, peak)
            drawdown = (equity - peak) / peak * 100
            max_dd = float(np.min(drawdown)) if len(drawdown) else 0
            current_dd = float(drawdown[-1]) if len(drawdown) else 0
            if not np.isfinite(max_dd):
                max_dd = 0
            if not np.isfinite(current_dd):
                current_dd = 0
            return {
                "max_drawdown_pct": max_dd,
                "current_drawdown_pct": current_dd,
                "is_breached": abs(current_dd) > self.config.max_drawdown_pct,
                "version": "v5_max"
            }
        except Exception as e:
            logger.debug(f"Drawdown v5 calc failed: {e}")
            return {"max_drawdown_pct": 0, "current_drawdown_pct": 0, "is_breached": False, "version": "v5_max"}

    def portfolio_risk(self, symbols: List[str]) -> Dict:
        with self._lock:
            self._metrics["portfolio_risks"] += 1
        try:
            from ..data.fetcher import CryptoDataFetcher
            returns_dict = {}
            for sym in symbols[:5]:
                r = self.fetch_returns(sym)
                if r is not None and len(r) >= 20:
                    returns_dict[sym] = r

            if len(returns_dict) < 2:
                return {
                    "avg_correlation": 0.0,
                    "correlation_risk": "low",
                    "var_portfolio": 0.02,
                    "cvar_portfolio": 0.03,
                    "diversification": "high",
                    "num_assets": len(returns_dict),
                    "warning": "Need at least 2 assets for correlation v5",
                    "version": "v5_max"
                }

            df = pd.DataFrame(returns_dict).dropna()
            if df.empty or len(df) < 10:
                return {"avg_correlation": 0.0, "correlation_risk": "low", "var_portfolio": 0.02, "cvar_portfolio": 0.03, "diversification": "high", "num_assets": len(returns_dict), "version": "v5_max"}

            corr = df.corr()
            mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
            corr_values = corr.values[mask]
            corr_values = corr_values[np.isfinite(corr_values)]
            if len(corr_values) == 0:
                avg_corr = 0.0
            else:
                avg_corr = float(np.mean(corr_values))
                if not np.isfinite(avg_corr):
                    avg_corr = 0.0
            avg_corr = max(-1.0, min(1.0, avg_corr))

            portfolio_returns = df.mean(axis=1)
            var_p = self.calculate_var(portfolio_returns, self.config.confidence)
            cvar_p = self.calculate_cvar(portfolio_returns, self.config.confidence)

            if avg_corr > 0.7:
                risk_level = "high"
                diversification = "low"
            elif avg_corr > 0.4:
                risk_level = "medium"
                diversification = "medium"
            else:
                risk_level = "low"
                diversification = "high"

            return {
                "avg_correlation": avg_corr,
                "correlation_risk": risk_level,
                "var_portfolio": var_p,
                "cvar_portfolio": cvar_p,
                "diversification": diversification,
                "num_assets": len(returns_dict),
                "corr_matrix": corr.round(3).to_dict() if len(returns_dict) <= 5 else {},
                "version": "v5_max"
            }
        except Exception as e:
            logger.warning(f"Portfolio risk v5 failed: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return {"error": str(e), "var_portfolio": 0.02, "cvar_portfolio": 0.03, "avg_correlation": 0.0, "version": "v5_max"}

    def position_size(self, symbol: str, account_balance: float, win_rate: float = 0.55, win_loss_ratio: float = 1.5) -> Dict:
        with self._lock:
            self._metrics["position_sizings"] += 1
        try:
            if account_balance <= 0:
                raise ValueError("account_balance must be >0")

            returns = self.fetch_returns(symbol)
            var = self.calculate_var(returns, self.config.confidence) if returns is not None else 0.02
            cvar = self.calculate_cvar(returns, self.config.confidence) if returns is not None else 0.03
            kelly = self.kelly_criterion(win_rate, win_loss_ratio)

            try:
                from ..data.price_helper import get_live_price as unified_price
                current_price = unified_price(symbol)
                if not current_price or current_price <= 0:
                    current_price = self.get_live_price(symbol)
                if not current_price or current_price <= 0:
                    from ..data.fetcher import CryptoDataFetcher
                    f = CryptoDataFetcher(symbol=symbol)
                    df = f.load_or_fetch(symbol=symbol)
                    current_price = float(df['Close'].iloc[-1]) if not df.empty else 100000
            except Exception:
                current_price = 100000

            var_based_pct = 0.02 / max(var, 0.01)
            var_based_pct = max(0.01, min(var_based_pct, self.config.max_position_pct/100))
            var_size = account_balance * var_based_pct

            kelly_size = account_balance * kelly

            recommended = min(
                (var_size * 0.6 + kelly_size * 0.4),
                account_balance * self.config.max_position_pct / 100
            )
            recommended = max(account_balance * 0.01, recommended)

            return {
                "symbol": symbol,
                "account_balance": account_balance,
                "current_price": current_price,
                "var_95": var,
                "cvar_95": cvar,
                "kelly_pct": kelly * 100,
                "kelly_size": kelly_size,
                "var_size": var_size,
                "var_based_pct": var_based_pct * 100,
                "recommended_size": float(recommended),
                "recommended_pct": float(recommended / account_balance * 100) if account_balance else 0,
                "recommended_quantity": float(recommended / current_price) if current_price else 0,
                "max_position_pct": self.config.max_position_pct,
                "method": "Institutional VaR + Kelly + Drawdown Control v5 MAX",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "v5_max"
            }
        except Exception as e:
            logger.warning(f"Position size v5 failed {symbol}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            safe_size = account_balance * 0.05 if account_balance > 0 else 500
            return {
                "symbol": symbol,
                "account_balance": account_balance,
                "var_95": 0.02,
                "cvar_95": 0.03,
                "kelly_pct": 2.0,
                "kelly_size": safe_size,
                "var_size": safe_size,
                "recommended_size": safe_size,
                "recommended_pct": 5.0,
                "max_position_pct": self.config.max_position_pct,
                "method": "Fallback v5 - 5% due to error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "v5_max"
            }

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "version": "v5_max"}

    def to_dict(self):
        return {
            "config": asdict(self.config),
            "type": "risk_model",
            "strategy": "Institutional Risk - VaR, CVaR, Kelly, Drawdown v5 MAX",
            "institutional": True,
            "version": "v5_max",
            "metrics": self.get_metrics()
        }
