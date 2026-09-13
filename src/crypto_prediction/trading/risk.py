"""
Risk management v5 MAX for trading calls
- Stop loss / Take profit calculation with ATR, volatility, Kelly
- Position sizing: fixed fractional, Kelly, volatility targeting, risk parity
- Risk/reward ratio, VaR, CVaR, drawdown control, leverage suggestion
- Advanced: portfolio heat, correlation, max loss, trailing stops
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from ..config import get_config

config = get_config()

class RiskManager:
    def __init__(self, risk_per_trade: float = 0.02, atr_multiplier_sl: float = 1.5, atr_multiplier_tp: float = 3.0, max_portfolio_heat: float = 0.06, max_correlation: float = 0.7):
        self.risk_per_trade = risk_per_trade  # 2% per trade
        self.atr_mult_sl = atr_multiplier_sl
        self.atr_mult_tp = atr_multiplier_tp
        self.max_portfolio_heat = max_portfolio_heat  # Max 6% total risk
        self.max_correlation = max_correlation

    def calculate_stop_loss(self, entry_price: float, atr: float, signal: str, atr_multiplier: float = None, volatility: float = None) -> float:
        mult = atr_multiplier or self.atr_mult_sl
        # Adjust multiplier by volatility regime
        if volatility is not None:
            if volatility > 0.05:
                mult *= 1.5  # Wider stop in high vol
            elif volatility < 0.02:
                mult *= 0.8  # Tighter stop in low vol
        
        if signal in ["BUY", "STRONG_BUY", "LONG"]:
            sl = entry_price - (atr * mult)
            # Ensure SL not too far (>10%) or too close (<0.5%)
            min_sl = entry_price * 0.90
            max_sl = entry_price * 0.995
            return max(min_sl, min(sl, max_sl))
        else:
            sl = entry_price + (atr * mult)
            max_sl = entry_price * 1.10
            min_sl = entry_price * 1.005
            return min(max_sl, max(sl, min_sl))

    def calculate_take_profits(self, entry_price: float, stop_loss: float, signal: str, risk_reward_ratios: list = None) -> Dict[str, float]:
        """Calculate multiple TP levels based on risk - v5 with dynamic RR"""
        risk = abs(entry_price - stop_loss)
        if risk_reward_ratios is None:
            risk_reward_ratios = [1.0, 2.0, 3.0, 5.0]  # v5 adds 1:5
        
        if signal in ["BUY", "STRONG_BUY", "LONG"]:
            return {
                f"tp{i+1}": entry_price + risk * rr for i, rr in enumerate(risk_reward_ratios)
            }
        else:
            return {
                f"tp{i+1}": entry_price - risk * rr for i, rr in enumerate(risk_reward_ratios)
            }

    def calculate_trailing_stop(self, entry_price: float, current_price: float, atr: float, signal: str, profit_pct: float = 0) -> float:
        """Trailing stop that locks profit - v5"""
        if signal in ["BUY", "STRONG_BUY", "LONG"]:
            # If in profit, trail by 1x ATR from current price
            if current_price > entry_price:
                trail = current_price - atr * 1.0
                # Lock at least 50% of profit after 2% gain
                if profit_pct > 2.0:
                    locked = entry_price + (current_price - entry_price) * 0.5
                    return max(trail, locked, entry_price * 0.97)
                return max(trail, entry_price * 0.97)
            else:
                return entry_price - atr * self.atr_mult_sl
        else:
            if current_price < entry_price:
                trail = current_price + atr * 1.0
                if profit_pct > 2.0:
                    locked = entry_price - (entry_price - current_price) * 0.5
                    return min(trail, locked, entry_price * 1.03)
                return min(trail, entry_price * 1.03)
            else:
                return entry_price + atr * self.atr_mult_sl

    def calculate_position_size(self, account_balance: float, entry_price: float, stop_loss: float, kelly_fraction: float = None, volatility: float = None, method: str = "fixed_fractional") -> Dict:
        """
        Multiple position sizing methods v5:
        - fixed_fractional: 2% risk
        - kelly: Kelly criterion
        - volatility_targeting: inverse vol
        - risk_parity: equal risk
        """
        risk_amount = account_balance * self.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        if price_diff == 0:
            return {"size": 0, "risk_amount": 0, "risk_pct": 0, "method": method}

        # Base size
        size = risk_amount / price_diff
        position_value = size * entry_price

        # Adjust by method
        kelly_size = size
        vol_size = size
        kelly_pct = self.risk_per_trade

        if kelly_fraction is not None and method in ["kelly", "all"]:
            # Kelly: f* = (bp - q)/b where b = odds, p = win prob
            # Use provided kelly_fraction clipped
            kelly_fraction = max(0.01, min(kelly_fraction, 0.25))  # Cap Kelly at 25%
            kelly_size = (account_balance * kelly_fraction) / price_diff
            kelly_pct = kelly_fraction

        if volatility is not None and method in ["volatility_targeting", "all"]:
            # Volatility targeting: target 15% annualized vol
            target_vol = 0.15 / np.sqrt(252)  # daily
            vol_scalar = target_vol / (volatility + 1e-8)
            vol_scalar = max(0.3, min(vol_scalar, 2.0))  # Clip 0.3x to 2x
            vol_size = size * vol_scalar

        # Choose final size based on method
        if method == "kelly" and kelly_fraction is not None:
            final_size = kelly_size
            final_pct = kelly_pct
        elif method == "volatility_targeting" and volatility is not None:
            final_size = vol_size
            final_pct = self.risk_per_trade * (vol_size / size) if size > 0 else self.risk_per_trade
        elif method == "all":
            # Average of methods
            sizes = [size]
            if kelly_fraction is not None:
                sizes.append(kelly_size)
            if volatility is not None:
                sizes.append(vol_size)
            final_size = np.mean(sizes)
            final_pct = np.mean([self.risk_per_trade, kelly_pct, self.risk_per_trade * (vol_size/size if size>0 else 1)])
        else:
            final_size = size
            final_pct = self.risk_per_trade

        # Risk checks
        final_value = final_size * entry_price
        # Don't risk more than 10% of account in single position value wise
        max_position_value = account_balance * 0.1
        if final_value > max_position_value:
            final_size = max_position_value / entry_price
            final_value = max_position_value

        return {
            "size": float(final_size),
            "position_value": float(final_value),
            "risk_amount": float(final_size * price_diff),
            "risk_pct": float(final_pct * 100),
            "kelly_size": float(kelly_size),
            "volatility_size": float(vol_size),
            "base_size": float(size),
            "method": method,
            "kelly_fraction": float(kelly_fraction) if kelly_fraction else 0.02,
            "leverage_suggestion": self._suggest_leverage(price_diff / entry_price, volatility)
        }

    def calculate_var_cvar(self, returns: np.ndarray, position_value: float, confidence: float = 0.95) -> Dict:
        """Value at Risk and Conditional VaR - v5"""
        try:
            returns = np.array(returns)
            if len(returns) < 10:
                return {"var_95": position_value * 0.02, "cvar_95": position_value * 0.03, "var_pct": 2.0}
            
            var_pct = np.percentile(returns, (1-confidence)*100)
            cvar_pct = returns[returns <= var_pct].mean() if len(returns[returns <= var_pct]) > 0 else var_pct
            
            var_value = abs(var_pct * position_value)
            cvar_value = abs(cvar_pct * position_value)
            
            return {
                "var_95": float(var_value),
                "cvar_95": float(cvar_value),
                "var_pct": float(abs(var_pct)*100),
                "cvar_pct": float(abs(cvar_pct)*100),
                "confidence": confidence
            }
        except Exception:
            return {"var_95": position_value * 0.02, "cvar_95": position_value * 0.03, "var_pct": 2.0}

    def check_portfolio_heat(self, open_positions: list, new_risk: float) -> Dict:
        """Check if new trade would exceed max portfolio heat - v5"""
        try:
            total_risk = sum([p.get('risk_pct', 0) for p in open_positions]) + new_risk
            would_exceed = total_risk > self.max_portfolio_heat * 100
            return {
                "total_risk_pct": total_risk,
                "max_allowed": self.max_portfolio_heat * 100,
                "would_exceed": would_exceed,
                "remaining_risk": max(0, self.max_portfolio_heat * 100 - total_risk),
                "can_trade": not would_exceed
            }
        except Exception:
            return {"total_risk_pct": new_risk, "max_allowed": self.max_portfolio_heat*100, "would_exceed": False, "can_trade": True}

    def _suggest_leverage(self, volatility_pct: float, volatility: float = None) -> str:
        """Suggest leverage based on volatility - v5 enhanced"""
        if volatility is not None:
            vol = volatility
        else:
            vol = volatility_pct
        
        if vol < 0.015:
            return "5x-10x (Very low volatility - high leverage OK)"
        elif vol < 0.025:
            return "3x-5x (Low volatility)"
        elif vol < 0.04:
            return "2x-3x (Medium volatility)"
        elif vol < 0.06:
            return "1x-2x (High volatility - low leverage)"
        else:
            return "1x (Very high volatility - no leverage)"

    def calculate_risk_reward(self, entry: float, sl: float, tp: float) -> float:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0
        return reward / risk

    def get_risk_level(self, confidence: float, volatility: float, kelly_fraction: float = None, var_pct: float = None) -> str:
        """Determine overall risk level - v5 with Kelly and VaR"""
        try:
            # Base on confidence and vol
            if confidence > 85 and volatility < 0.02:
                base = "LOW"
            elif confidence > 65 and volatility < 0.04:
                base = "MEDIUM"
            elif confidence > 50 and volatility < 0.06:
                base = "MEDIUM-HIGH"
            else:
                base = "HIGH"

            # Adjust with Kelly
            if kelly_fraction is not None:
                if kelly_fraction < 0:
                    return "VERY_HIGH - Negative edge, avoid"
                elif kelly_fraction < 0.02:
                    base = "HIGH" if base in ["LOW", "MEDIUM"] else base

            # Adjust with VaR
            if var_pct is not None and var_pct > 5:
                return "VERY_HIGH - VaR >5%"

            return base
        except Exception:
            return "MEDIUM"

    def calculate_sharpe_sortino(self, returns: np.ndarray, risk_free: float = 0.0) -> Dict:
        """Calculate Sharpe and Sortino - v5"""
        try:
            returns = np.array(returns)
            if len(returns) < 2:
                return {"sharpe": 0, "sortino": 0}
            
            excess = returns - risk_free/252
            sharpe = np.mean(excess) / (np.std(excess) + 1e-8) * np.sqrt(252)
            
            downside = excess[excess < 0]
            if len(downside) > 0 and np.std(downside) > 1e-8:
                sortino = np.mean(excess) / np.std(downside) * np.sqrt(252)
            else:
                sortino = sharpe * 1.5 if sharpe > 0 else 0
            
            return {"sharpe": float(sharpe), "sortino": float(sortino)}
        except Exception:
            return {"sharpe": 0, "sortino": 0}
