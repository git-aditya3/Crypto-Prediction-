"""
Strategy Manager - Manages all trading strategies for real trading
"""
from typing import Dict, List
from .dca import DCABot, DCABotConfig
from .grid import GridBot, GridBotConfig
from .breakout import BreakoutBot
from ..config import get_config

config = get_config()

class StrategyManager:
    def __init__(self):
        self.dca_bots: Dict[str, DCABot] = {}
        self.grid_bots: Dict[str, GridBot] = {}
        self.breakout_bot = BreakoutBot()
    
    def create_dca_bot(self, symbol: str, total_investment: float, num_orders: int = 5, 
                      price_deviation_pct: float = 1.0, take_profit_pct: float = 5.0, stop_loss_pct: float = 3.0) -> Dict:
        cfg = DCABotConfig(
            symbol=symbol,
            total_investment=total_investment,
            num_orders=num_orders,
            price_deviation_pct=price_deviation_pct,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct
        )
        bot = DCABot(cfg)
        self.dca_bots[symbol] = bot
        return bot.to_dict()
    
    def create_grid_bot(self, symbol: str, lower_price: float, upper_price: float, num_grids: int = 10, total_investment: float = 1000) -> Dict:
        cfg = GridBotConfig(
            symbol=symbol,
            lower_price=lower_price,
            upper_price=upper_price,
            num_grids=num_grids,
            total_investment=total_investment
        )
        bot = GridBot(cfg)
        self.grid_bots[symbol] = bot
        return bot.to_dict()
    
    def get_all_bots(self) -> Dict:
        return {
            "dca_bots": {k: v.to_dict() for k, v in self.dca_bots.items()},
            "grid_bots": {k: v.to_dict() for k, v in self.grid_bots.items()},
            "count": len(self.dca_bots) + len(self.grid_bots),
            "real_trading": True
        }
    
    def scan_breakouts(self, symbols: List[str] = None) -> List[Dict]:
        return self.breakout_bot.scan_all(symbols)

# Global
_strategy_manager = None

def get_strategy_manager():
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
