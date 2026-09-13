"""
Strategy Manager - Manages all trading strategies for real trading
Includes Institutional strategies: Market Making, TWAP/VWAP, Stat Arb, OrderBook Imbalance, Funding Arb, Risk Model
"""
from typing import Dict, List
from .dca import DCABot, DCABotConfig
from .grid import GridBot, GridBotConfig
from .breakout import BreakoutBot
from .market_making import MarketMakingBot, MarketMakingConfig
from .twap_vwap import TWAPVWAPExecutor, ExecutionConfig
from .stat_arb import StatArbBot, StatArbConfig
from .orderbook_imbalance import OrderBookImbalanceBot, OFIConfig
from .funding_arb import FundingArbBot, FundingArbConfig
from .risk_model import InstitutionalRiskModel, RiskConfig
from ..config import get_config

config = get_config()

class StrategyManager:
    def __init__(self):
        self.dca_bots: Dict[str, DCABot] = {}
        self.grid_bots: Dict[str, GridBot] = {}
        self.breakout_bot = BreakoutBot()
        # Institutional
        self.mm_bots: Dict[str, MarketMakingBot] = {}
        self.execution_bots: Dict[str, TWAPVWAPExecutor] = {}
        self.stat_arb_bots: Dict[str, StatArbBot] = {}
        self.ofi_bots: Dict[str, OrderBookImbalanceBot] = {}
        self.funding_bots: Dict[str, FundingArbBot] = {}
        self.risk_model = InstitutionalRiskModel()
    
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

    # Institutional - Market Making
    def create_mm_bot(self, symbol: str, total_investment: float = 10000, spread_bps: float = 20, max_inventory: float = 1.0) -> Dict:
        cfg = MarketMakingConfig(symbol=symbol, total_investment=total_investment, spread_bps=spread_bps, max_inventory=max_inventory)
        bot = MarketMakingBot(cfg)
        self.mm_bots[symbol] = bot
        # Generate initial quote
        try:
            bot.generate_quotes()
        except:
            pass
        return bot.to_dict()

    def get_mm_quote(self, symbol: str) -> Dict:
        bot = self.mm_bots.get(symbol)
        if not bot:
            cfg = MarketMakingConfig(symbol=symbol)
            bot = MarketMakingBot(cfg)
            self.mm_bots[symbol] = bot
        try:
            quote = bot.generate_quotes()
            from dataclasses import asdict
            return asdict(quote)
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    # TWAP/VWAP
    def create_execution_bot(self, symbol: str, side: str, total_quantity: float, strategy: str = "TWAP", duration_minutes: int = 60, num_slices: int = 12) -> Dict:
        cfg = ExecutionConfig(symbol=symbol, side=side, total_quantity=total_quantity, strategy=strategy, duration_minutes=duration_minutes, num_slices=num_slices)
        bot = TWAPVWAPExecutor(cfg)
        key = f"{symbol}_{strategy}_{side}"
        self.execution_bots[key] = bot
        return bot.to_dict()

    # Stat Arb
    def create_stat_arb_bot(self, symbol_a: str, symbol_b: str, entry_z: float = 2.0) -> Dict:
        cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b, entry_z=entry_z)
        bot = StatArbBot(cfg)
        key = f"{symbol_a}_{symbol_b}"
        self.stat_arb_bots[key] = bot
        try:
            bot.generate_signal()
        except:
            pass
        return bot.to_dict()

    def get_stat_arb_signal(self, symbol_a: str, symbol_b: str) -> Dict:
        key = f"{symbol_a}_{symbol_b}"
        bot = self.stat_arb_bots.get(key)
        if not bot:
            cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b)
            bot = StatArbBot(cfg)
            self.stat_arb_bots[key] = bot
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            return {"error": str(e), "pair": f"{symbol_a}/{symbol_b}"}

    # OrderBook Imbalance
    def create_ofi_bot(self, symbol: str) -> Dict:
        cfg = OFIConfig(symbol=symbol)
        bot = OrderBookImbalanceBot(cfg)
        self.ofi_bots[symbol] = bot
        try:
            bot.generate_signal()
        except:
            pass
        return bot.to_dict()

    def get_ofi_signal(self, symbol: str) -> Dict:
        bot = self.ofi_bots.get(symbol)
        if not bot:
            cfg = OFIConfig(symbol=symbol)
            bot = OrderBookImbalanceBot(cfg)
            self.ofi_bots[symbol] = bot
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    # Funding Arb
    def create_funding_bot(self, symbol: str) -> Dict:
        cfg = FundingArbConfig(symbol=symbol)
        bot = FundingArbBot(cfg)
        self.funding_bots[symbol] = bot
        try:
            bot.generate_signal()
        except:
            pass
        return bot.to_dict()

    def get_funding_signal(self, symbol: str) -> Dict:
        bot = self.funding_bots.get(symbol)
        if not bot:
            cfg = FundingArbConfig(symbol=symbol)
            bot = FundingArbBot(cfg)
            self.funding_bots[symbol] = bot
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    # Risk
    def get_position_size(self, symbol: str, account_balance: float, win_rate: float = 0.55, win_loss_ratio: float = 1.5) -> Dict:
        return self.risk_model.position_size(symbol, account_balance, win_rate, win_loss_ratio)

    def get_portfolio_risk(self, symbols: List[str] = None) -> Dict:
        symbols = symbols or config.data.supported_symbols[:5]
        return self.risk_model.portfolio_risk(symbols)
    
    def get_all_bots(self) -> Dict:
        return {
            "dca_bots": {k: v.to_dict() for k, v in self.dca_bots.items()},
            "grid_bots": {k: v.to_dict() for k, v in self.grid_bots.items()},
            "mm_bots": {k: v.to_dict() for k, v in self.mm_bots.items()},
            "execution_bots": {k: v.to_dict() for k, v in self.execution_bots.items()},
            "stat_arb_bots": {k: v.to_dict() for k, v in self.stat_arb_bots.items()},
            "ofi_bots": {k: v.to_dict() for k, v in self.ofi_bots.items()},
            "funding_bots": {k: v.to_dict() for k, v in self.funding_bots.items()},
            "count": len(self.dca_bots) + len(self.grid_bots) + len(self.mm_bots) + len(self.execution_bots) + len(self.stat_arb_bots) + len(self.ofi_bots) + len(self.funding_bots),
            "real_trading": True,
            "institutional": True
        }
    
    def scan_breakouts(self, symbols: List[str] = None) -> List[Dict]:
        return self.breakout_bot.scan_all(symbols)

    def scan_institutional(self, symbols: List[str] = None) -> Dict:
        """Scan all institutional signals"""
        symbols = symbols or config.data.supported_symbols[:6]
        results = {
            "market_making": [],
            "orderbook_imbalance": [],
            "funding_arb": [],
            "stat_arb": []
        }
        for sym in symbols[:3]:
            try:
                results["orderbook_imbalance"].append(self.get_ofi_signal(sym))
            except:
                pass
            try:
                results["funding_arb"].append(self.get_funding_signal(sym))
            except:
                pass
            try:
                results["market_making"].append(self.get_mm_quote(sym))
            except:
                pass
        # Stat arb pairs
        pairs = [("BTC-USD","ETH-USD"), ("BTC-USD","BNB-USD"), ("ETH-USD","SOL-USD")]
        for a,b in pairs:
            try:
                results["stat_arb"].append(self.get_stat_arb_signal(a,b))
            except:
                pass
        return results

# Global
_strategy_manager = None

def get_strategy_manager():
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
