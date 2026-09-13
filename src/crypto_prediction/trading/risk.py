"""
Risk management for trading calls
- Stop loss / Take profit calculation
- Position sizing
- Risk/reward ratio
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from ..config import get_config

config = get_config()

class RiskManager:
    def __init__(self, risk_per_trade: float = 0.02, atr_multiplier_sl: float = 1.5, atr_multiplier_tp: float = 3.0):
        self.risk_per_trade = risk_per_trade  # 2% per trade
        self.atr_mult_sl = atr_multiplier_sl
        self.atr_mult_tp = atr_multiplier_tp

    def calculate_stop_loss(self, entry_price: float, atr: float, signal: str, atr_multiplier: float = None) -> float:
        mult = atr_multiplier or self.atr_mult_sl
        if signal in ["BUY", "STRONG_BUY", "LONG"]:
            return entry_price - (atr * mult)
        else:
            return entry_price + (atr * mult)

    def calculate_take_profits(self, entry_price: float, stop_loss: float, signal: str) -> Dict[str, float]:
        """Calculate multiple TP levels based on risk"""
        risk = abs(entry_price - stop_loss)
        if signal in ["BUY", "STRONG_BUY", "LONG"]:
            return {
                "tp1": entry_price + risk * 1.0,  # 1:1
                "tp2": entry_price + risk * 2.0,  # 1:2
                "tp3": entry_price + risk * 3.0,  # 1:3
            }
        else:
            return {
                "tp1": entry_price - risk * 1.0,
                "tp2": entry_price - risk * 2.0,
                "tp3": entry_price - risk * 3.0,
            }

    def calculate_position_size(self, account_balance: float, entry_price: float, stop_loss: float) -> Dict:
        risk_amount = account_balance * self.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        if price_diff == 0:
            return {"size": 0, "risk_amount": 0, "risk_pct": 0}
        
        # Position size in units
        size = risk_amount / price_diff
        # Position value
        position_value = size * entry_price
        
        return {
            "size": float(size),
            "position_value": float(position_value),
            "risk_amount": float(risk_amount),
            "risk_pct": float(self.risk_per_trade * 100),
            "leverage_suggestion": self._suggest_leverage(price_diff / entry_price)
        }

    def _suggest_leverage(self, volatility_pct: float) -> str:
        """Suggest leverage based on volatility"""
        if volatility_pct < 0.02:
            return "5x-10x (Low volatility)"
        elif volatility_pct < 0.05:
            return "3x-5x (Medium volatility)"
        else:
            return "1x-3x (High volatility - use low leverage)"

    def calculate_risk_reward(self, entry: float, sl: float, tp: float) -> float:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0
        return reward / risk

    def get_risk_level(self, confidence: float, volatility: float) -> str:
        """Determine overall risk level"""
        if confidence > 80 and volatility < 0.03:
            return "LOW"
        elif confidence > 60 and volatility < 0.05:
            return "MEDIUM"
        else:
            return "HIGH"
