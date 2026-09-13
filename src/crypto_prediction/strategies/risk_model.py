"""
Institutional Risk Model - VaR, CVaR, Kelly, Drawdown Control
Real trading risk management
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RiskConfig:
    confidence: float = 0.95
    lookback_days: int = 60
    max_drawdown_pct: float = 10.0
    max_position_pct: float = 20.0
    kelly_fraction: float = 0.5  # half-kelly for safety

class InstitutionalRiskModel:
    """
    Institutional Risk:
    - VaR (Value at Risk) historical
    - CVaR (Conditional VaR)
    - Kelly Criterion for position sizing
    - Drawdown control
    - Correlation risk
    - Real market data
    """
    def __init__(self, cfg: RiskConfig = None):
        self.config = cfg or RiskConfig()

    def fetch_returns(self, symbol: str) -> Optional[pd.Series]:
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            returns = df['Close'].pct_change().dropna().tail(self.config.lookback_days)
            return returns
        except Exception as e:
            logger.warning(f"Returns fetch failed {symbol}: {e}")
            return None

    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Historical VaR"""
        try:
            if returns is None or len(returns) < 10:
                return 0.02
            var = np.percentile(returns, (1-confidence)*100)
            return float(abs(var))
        except:
            return 0.02

    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Conditional VaR - expected loss beyond VaR"""
        try:
            if returns is None or len(returns) < 10:
                return 0.03
            var = np.percentile(returns, (1-confidence)*100)
            cvar = returns[returns <= var].mean()
            return float(abs(cvar)) if not np.isnan(cvar) else self.calculate_var(returns, confidence) * 1.5
        except:
            return 0.03

    def kelly_criterion(self, win_rate: float, win_loss_ratio: float) -> float:
        """
        Kelly % = W - (1-W)/R
        W = win rate, R = win/loss ratio
        """
        try:
            if win_loss_ratio <= 0:
                return 0.0
            kelly = win_rate - (1-win_rate) / win_loss_ratio
            # Half-kelly for safety
            kelly = kelly * self.config.kelly_fraction
            # Bound 0- max_position
            kelly = max(0, min(kelly, self.config.max_position_pct/100))
            return float(kelly)
        except:
            return 0.02

    def calculate_drawdown(self, equity_curve: List[float]) -> Dict:
        try:
            equity = np.array(equity_curve)
            peak = np.maximum.accumulate(equity)
            drawdown = (equity - peak) / peak * 100
            max_dd = float(np.min(drawdown)) if len(drawdown) else 0
            current_dd = float(drawdown[-1]) if len(drawdown) else 0
            return {
                "max_drawdown_pct": max_dd,
                "current_drawdown_pct": current_dd,
                "is_breached": abs(current_dd) > self.config.max_drawdown_pct
            }
        except:
            return {"max_drawdown_pct": 0, "current_drawdown_pct": 0, "is_breached": False}

    def portfolio_risk(self, symbols: List[str]) -> Dict:
        """Portfolio level risk with correlation"""
        try:
            from ..data.fetcher import CryptoDataFetcher
            returns_dict = {}
            for sym in symbols[:5]:  # limit
                r = self.fetch_returns(sym)
                if r is not None:
                    returns_dict[sym] = r

            if len(returns_dict) < 2:
                return {"correlation_risk": "low", "diversification": "high", "var_portfolio": 0.02}

            df = pd.DataFrame(returns_dict).dropna()
            corr = df.corr()
            avg_corr = float(corr.values[np.triu_indices_from(corr.values, k=1)].mean()) if corr.shape[0] > 1 else 0

            # Portfolio VaR - simplified
            portfolio_returns = df.mean(axis=1)
            var_p = self.calculate_var(portfolio_returns, self.config.confidence)
            cvar_p = self.calculate_cvar(portfolio_returns, self.config.confidence)

            risk_level = "low"
            if avg_corr > 0.7:
                risk_level = "high"
            elif avg_corr > 0.4:
                risk_level = "medium"

            return {
                "avg_correlation": avg_corr,
                "correlation_risk": risk_level,
                "var_portfolio": var_p,
                "cvar_portfolio": cvar_p,
                "diversification": "low" if avg_corr > 0.7 else "high" if avg_corr < 0.3 else "medium",
                "num_assets": len(returns_dict)
            }
        except Exception as e:
            logger.warning(f"Portfolio risk failed: {e}")
            return {"error": str(e), "var_portfolio": 0.02}

    def position_size(self, symbol: str, account_balance: float, win_rate: float = 0.55, win_loss_ratio: float = 1.5) -> Dict:
        returns = self.fetch_returns(symbol)
        var = self.calculate_var(returns, self.config.confidence) if returns is not None else 0.02
        cvar = self.calculate_cvar(returns, self.config.confidence) if returns is not None else 0.03
        kelly = self.kelly_criterion(win_rate, win_loss_ratio)

        # Risk-based size: don't risk more than VaR
        max_risk_amount = account_balance * 0.02  # 2% max risk
        # Position size based on VaR
        var_size = max_risk_amount / (var * 10000) if var else account_balance * 0.1

        # Kelly size
        kelly_size = account_balance * kelly

        # Conservative: take minimum
        recommended = min(var_size, kelly_size, account_balance * self.config.max_position_pct/100)

        return {
            "symbol": symbol,
            "account_balance": account_balance,
            "var_95": var,
            "cvar_95": cvar,
            "kelly_pct": kelly * 100,
            "kelly_size": kelly_size,
            "var_size": var_size,
            "recommended_size": float(recommended),
            "recommended_pct": float(recommended / account_balance * 100) if account_balance else 0,
            "max_position_pct": self.config.max_position_pct,
            "method": "Institutional VaR + Kelly + Drawdown Control",
            "timestamp": datetime.utcnow().isoformat()
        }

    def to_dict(self):
        return {
            "config": asdict(self.config),
            "type": "risk_model",
            "strategy": "Institutional Risk - VaR, CVaR, Kelly, Drawdown",
            "institutional": True
        }
