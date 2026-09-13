"""
DCA Bot - Dollar Cost Averaging for real trading
Accumulates position over time, reduces entry risk
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

from ..config import get_config
from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class DCAOrder:
    symbol: str
    price: float
    quantity: float
    timestamp: str
    type: str = "BUY"

@dataclass
class DCABotConfig:
    symbol: str
    total_investment: float
    num_orders: int
    price_deviation_pct: float  # e.g., 1% between orders
    take_profit_pct: float
    stop_loss_pct: float
    timeframe: str = "1d"
    status: str = "ACTIVE"

class DCABot:
    """
    DCA Bot for real trading - accumulates at different prices
    """
    def __init__(self, config: DCABotConfig):
        self.config = config
        self.orders: List[DCAOrder] = []
        self.avg_entry = 0
        self.total_quantity = 0
        self.total_invested = 0
        self.created_at = datetime.utcnow().isoformat()
    
    def get_live_price(self, symbol: str) -> float:
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price()
            if price and price > 0 and price < 10_000_000:
                return float(price)
            return 0
        except Exception as e:
            logger.debug(f"DCA live price failed {symbol}: {e}")
            return 0
    
    def generate_dca_levels(self, current_price: float) -> List[Dict]:
        """Generate DCA levels below current price for real trading"""
        levels = []
        investment_per_order = self.config.total_investment / self.config.num_orders
        
        for i in range(self.config.num_orders):
            # Each order lower than previous by deviation
            price = current_price * (1 - (i * self.config.price_deviation_pct / 100))
            quantity = investment_per_order / price
            
            levels.append({
                "order_num": i+1,
                "price": price,
                "quantity": quantity,
                "investment": investment_per_order,
                "deviation_from_current": -i * self.config.price_deviation_pct,
                "type": "LIMIT_BUY",
                "real_trading": True
            })
        
        return levels
    
    def calculate_take_profit(self, avg_entry: float) -> Dict[str, float]:
        """Calculate TP levels for DCA - real trading"""
        return {
            "tp1": avg_entry * (1 + self.config.take_profit_pct / 100 * 0.5),
            "tp2": avg_entry * (1 + self.config.take_profit_pct / 100),
            "tp3": avg_entry * (1 + self.config.take_profit_pct / 100 * 1.5)
        }
    
    def calculate_stop_loss(self, avg_entry: float) -> float:
        return avg_entry * (1 - self.config.stop_loss_pct / 100)
    
    def to_dict(self):
        current_price = self.get_live_price(self.config.symbol)
        levels = self.generate_dca_levels(current_price) if current_price else []
        
        avg_entry = self.avg_entry or (current_price if current_price else 0)
        
        return {
            "config": asdict(self.config),
            "dca_levels": levels,
            "levels": levels,
            "avg_entry": avg_entry,
            "total_quantity": self.total_quantity,
            "total_invested": self.total_invested,
            "current_price": current_price,
            "live_price": current_price,
            "take_profits": self.calculate_take_profit(avg_entry) if avg_entry else {},
            "stop_loss": self.calculate_stop_loss(avg_entry) if avg_entry else 0,
            "pnl": (current_price - avg_entry) * self.total_quantity if current_price and avg_entry else 0,
            "pnl_pct": (current_price - avg_entry) / avg_entry * 100 if current_price and avg_entry else 0,
            "orders": [asdict(o) for o in self.orders],
            "created_at": self.created_at,
            "real_trading": True,
            "strategy": "DCA - Dollar Cost Averaging for real accumulation"
        }
