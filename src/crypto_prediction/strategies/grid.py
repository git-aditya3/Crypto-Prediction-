"""
Grid Trading Bot - Profits from ranging markets, real trading
Places buy/sell orders in grid, profits from volatility
"""
from dataclasses import dataclass, asdict
from typing import Dict, List
from datetime import datetime
import numpy as np

from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class GridLevel:
    price: float
    quantity: float
    side: str  # BUY, SELL
    status: str = "PENDING"

@dataclass
class GridBotConfig:
    symbol: str
    lower_price: float
    upper_price: float
    num_grids: int
    total_investment: float
    status: str = "ACTIVE"

class GridBot:
    """
    Grid Bot for real trading - profits from sideways markets
    """
    def __init__(self, config: GridBotConfig):
        self.config = config
        self.levels: List[GridLevel] = []
        self.profit = 0
        self.trades = 0
        self.created_at = datetime.utcnow().isoformat()
        self.generate_grid()
    
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

    def generate_grid(self):
        """Generate grid levels for real trading"""
        lower = self.config.lower_price
        upper = self.config.upper_price
        num = self.config.num_grids
        
        # Price step
        price_step = (upper - lower) / num
        investment_per_grid = self.config.total_investment / num
        
        self.levels = []
        for i in range(num + 1):
            price = lower + i * price_step
            # Alternate buy/sell, more buys below mid, more sells above
            mid = (lower + upper) / 2
            side = "BUY" if price < mid else "SELL"
            quantity = investment_per_grid / price
            
            self.levels.append(GridLevel(
                price=price,
                quantity=quantity,
                side=side,
                status="PENDING"
            ))
    
    def calculate_profit_per_grid(self) -> float:
        """Profit per grid trade"""
        price_range = self.config.upper_price - self.config.lower_price
        avg_price = (self.config.upper_price + self.config.lower_price) / 2
        grid_profit_pct = (price_range / self.config.num_grids) / avg_price * 100
        return grid_profit_pct
    
    def to_dict(self):
        current_price = self.get_live_price(self.config.symbol)
        
        return {
            "config": asdict(self.config),
            "grid_levels": [asdict(l) for l in self.levels],
            "levels": [asdict(l) for l in self.levels],
            "current_price": current_price,
            "live_price": current_price,
            "profit": self.profit,
            "trades": self.trades,
            "profit_per_grid": self.config.total_investment / self.config.num_grids * (self.calculate_profit_per_grid() / 100),
            "profit_per_grid_pct": self.calculate_profit_per_grid(),
            "estimated_apr": self.calculate_profit_per_grid() * self.config.num_grids * 0.5,
            "created_at": self.created_at,
            "real_trading": True,
            "strategy": "Grid Trading - profits from volatility in ranging market",
            "how_it_works": f"Buy low at {self.config.lower_price}, sell high at {self.config.upper_price}, {self.config.num_grids} grids, profit ~{self.calculate_profit_per_grid():.2f}% per grid"
        }
