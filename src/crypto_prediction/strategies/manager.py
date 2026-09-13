"""
Strategy Manager - Fixed: error handling, validation, thread safety
"""
from typing import Dict, List
import threading
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
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class StrategyManager:
    def __init__(self):
        self.dca_bots: Dict[str, DCABot] = {}
        self.grid_bots: Dict[str, GridBot] = {}
        self.breakout_bot = BreakoutBot()
        self.mm_bots: Dict[str, MarketMakingBot] = {}
        self.execution_bots: Dict[str, TWAPVWAPExecutor] = {}
        self.stat_arb_bots: Dict[str, StatArbBot] = {}
        self.ofi_bots: Dict[str, OrderBookImbalanceBot] = {}
        self.funding_bots: Dict[str, FundingArbBot] = {}
        self.risk_model = InstitutionalRiskModel()
        self._lock = threading.Lock()

    def _validate_symbol(self, symbol: str) -> str:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol must be non-empty string")
        symbol = symbol.strip().upper()
        if len(symbol) < 3 or len(symbol) > 20:
            raise ValueError(f"Invalid symbol length: {symbol}")
        return symbol

    def create_dca_bot(self, symbol: str, total_investment: float, num_orders: int = 5, 
                      price_deviation_pct: float = 1.0, take_profit_pct: float = 5.0, stop_loss_pct: float = 3.0) -> Dict:
        symbol = self._validate_symbol(symbol)
        if total_investment <= 0:
            raise ValueError("total_investment must be >0")
        if num_orders <= 0 or num_orders > 50:
            raise ValueError("num_orders must be 1-50")
        cfg = DCABotConfig(
            symbol=symbol,
            total_investment=total_investment,
            num_orders=num_orders,
            price_deviation_pct=price_deviation_pct,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct
        )
        bot = DCABot(cfg)
        with self._lock:
            self.dca_bots[symbol] = bot
        return bot.to_dict()

    def create_grid_bot(self, symbol: str, lower_price: float, upper_price: float, num_grids: int = 10, total_investment: float = 1000) -> Dict:
        symbol = self._validate_symbol(symbol)
        if lower_price <= 0 or upper_price <= 0:
            raise ValueError("Prices must be >0")
        if lower_price >= upper_price:
            raise ValueError("lower_price must be < upper_price")
        if num_grids <= 1 or num_grids > 100:
            raise ValueError("num_grids must be 2-100")
        if total_investment <= 0:
            raise ValueError("total_investment must be >0")
        cfg = GridBotConfig(
            symbol=symbol,
            lower_price=lower_price,
            upper_price=upper_price,
            num_grids=num_grids,
            total_investment=total_investment
        )
        bot = GridBot(cfg)
        with self._lock:
            self.grid_bots[symbol] = bot
        return bot.to_dict()

    def create_mm_bot(self, symbol: str, total_investment: float = 10000, spread_bps: float = 20, max_inventory: float = 1.0) -> Dict:
        symbol = self._validate_symbol(symbol)
        if total_investment <= 0:
            raise ValueError("total_investment must be >0")
        cfg = MarketMakingConfig(symbol=symbol, total_investment=total_investment, spread_bps=spread_bps, max_inventory=max_inventory)
        bot = MarketMakingBot(cfg)
        with self._lock:
            self.mm_bots[symbol] = bot
        try:
            bot.generate_quotes()
        except Exception as e:
            logger.warning(f"MM initial quote failed {symbol}: {e}")
        return bot.to_dict()

    def get_mm_quote(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        with self._lock:
            bot = self.mm_bots.get(symbol)
        if not bot:
            cfg = MarketMakingConfig(symbol=symbol)
            bot = MarketMakingBot(cfg)
            with self._lock:
                self.mm_bots[symbol] = bot
        try:
            quote = bot.generate_quotes()
            from dataclasses import asdict
            return asdict(quote)
        except Exception as e:
            logger.warning(f"MM quote failed {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "signal": "NO_DATA"}

    def create_execution_bot(self, symbol: str, side: str, total_quantity: float, strategy: str = "TWAP", duration_minutes: int = 60, num_slices: int = 12) -> Dict:
        symbol = self._validate_symbol(symbol)
        if total_quantity <= 0:
            raise ValueError("total_quantity must be >0")
        cfg = ExecutionConfig(symbol=symbol, side=side, total_quantity=total_quantity, strategy=strategy, duration_minutes=duration_minutes, num_slices=num_slices)
        bot = TWAPVWAPExecutor(cfg)
        key = f"{symbol}_{strategy.upper()}_{side.upper()}"
        with self._lock:
            self.execution_bots[key] = bot
        return bot.to_dict()

    def create_stat_arb_bot(self, symbol_a: str, symbol_b: str, entry_z: float = 2.0) -> Dict:
        symbol_a = self._validate_symbol(symbol_a)
        symbol_b = self._validate_symbol(symbol_b)
        if symbol_a == symbol_b:
            raise ValueError("Symbols must be different")
        cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b, entry_z=entry_z)
        bot = StatArbBot(cfg)
        key = f"{symbol_a}_{symbol_b}"
        with self._lock:
            self.stat_arb_bots[key] = bot
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"StatArb initial signal failed {key}: {e}")
        return bot.to_dict()

    def get_stat_arb_signal(self, symbol_a: str, symbol_b: str) -> Dict:
        symbol_a = self._validate_symbol(symbol_a)
        symbol_b = self._validate_symbol(symbol_b)
        key = f"{symbol_a}_{symbol_b}"
        with self._lock:
            bot = self.stat_arb_bots.get(key)
        if not bot:
            try:
                cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b)
                bot = StatArbBot(cfg)
                with self._lock:
                    self.stat_arb_bots[key] = bot
            except Exception as e:
                return {"error": str(e), "pair": f"{symbol_a}/{symbol_b}", "signal": "ERROR"}
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            logger.warning(f"StatArb signal failed {key}: {e}")
            return {"error": str(e), "pair": f"{symbol_a}/{symbol_b}", "signal": "ERROR"}

    def create_ofi_bot(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cfg = OFIConfig(symbol=symbol)
        bot = OrderBookImbalanceBot(cfg)
        with self._lock:
            self.ofi_bots[symbol] = bot
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"OFI initial signal failed {symbol}: {e}")
        return bot.to_dict()

    def get_ofi_signal(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        with self._lock:
            bot = self.ofi_bots.get(symbol)
        if not bot:
            cfg = OFIConfig(symbol=symbol)
            bot = OrderBookImbalanceBot(cfg)
            with self._lock:
                self.ofi_bots[symbol] = bot
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            logger.warning(f"OFI signal failed {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "signal": "ERROR"}

    def create_funding_bot(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cfg = FundingArbConfig(symbol=symbol)
        bot = FundingArbBot(cfg)
        with self._lock:
            self.funding_bots[symbol] = bot
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"Funding initial signal failed {symbol}: {e}")
        return bot.to_dict()

    def get_funding_signal(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        with self._lock:
            bot = self.funding_bots.get(symbol)
        if not bot:
            cfg = FundingArbConfig(symbol=symbol)
            bot = FundingArbBot(cfg)
            with self._lock:
                self.funding_bots[symbol] = bot
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            return asdict(sig)
        except Exception as e:
            logger.warning(f"Funding signal failed {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "signal": "ERROR"}

    def get_position_size(self, symbol: str, account_balance: float, win_rate: float = 0.55, win_loss_ratio: float = 1.5) -> Dict:
        symbol = self._validate_symbol(symbol)
        if account_balance <= 0:
            raise ValueError("account_balance must be >0")
        return self.risk_model.position_size(symbol, account_balance, win_rate, win_loss_ratio)

    def get_portfolio_risk(self, symbols: List[str] = None) -> Dict:
        if symbols:
            validated=[]
            for s in symbols:
                try:
                    validated.append(self._validate_symbol(s))
                except ValueError:
                    continue
            symbols = validated[:10]
        symbols = symbols or config.data.supported_symbols[:5]
        return self.risk_model.portfolio_risk(symbols)

    def get_all_bots(self) -> Dict:
        with self._lock:
            dca = {k: v.to_dict() for k, v in self.dca_bots.items()}
            grid = {k: v.to_dict() for k, v in self.grid_bots.items()}
            mm = {k: v.to_dict() for k, v in self.mm_bots.items()}
            exe = {k: v.to_dict() for k, v in self.execution_bots.items()}
            stat = {k: v.to_dict() for k, v in self.stat_arb_bots.items()}
            ofi = {k: v.to_dict() for k, v in self.ofi_bots.items()}
            funding = {k: v.to_dict() for k, v in self.funding_bots.items()}
            count = len(dca) + len(grid) + len(mm) + len(exe) + len(stat) + len(ofi) + len(funding)
        return {
            "dca_bots": dca,
            "grid_bots": grid,
            "mm_bots": mm,
            "execution_bots": exe,
            "stat_arb_bots": stat,
            "ofi_bots": ofi,
            "funding_bots": funding,
            "count": count,
            "real_trading": True,
            "institutional": True
        }

    def scan_breakouts(self, symbols: List[str] = None) -> List[Dict]:
        try:
            if symbols:
                symbols = [self._validate_symbol(s) for s in symbols]
            return self.breakout_bot.scan_all(symbols)
        except Exception as e:
            logger.warning(f"Breakout scan failed: {e}")
            return []

    def scan_institutional(self, symbols: List[str] = None) -> Dict:
        try:
            if symbols:
                symbols = [self._validate_symbol(s) for s in symbols]
            else:
                symbols = config.data.supported_symbols[:6]
        except Exception:
            symbols = config.data.supported_symbols[:6]

        results = {
            "market_making": [],
            "orderbook_imbalance": [],
            "funding_arb": [],
            "stat_arb": []
        }
        for sym in symbols[:3]:
            try:
                results["orderbook_imbalance"].append(self.get_ofi_signal(sym))
            except Exception as e:
                logger.debug(f"Institutional OFI scan failed {sym}: {e}")
                results["orderbook_imbalance"].append({"symbol": sym, "signal": "ERROR", "error": str(e)})
            try:
                results["funding_arb"].append(self.get_funding_signal(sym))
            except Exception as e:
                logger.debug(f"Institutional funding scan failed {sym}: {e}")
                results["funding_arb"].append({"symbol": sym, "signal": "ERROR", "error": str(e)})
            try:
                results["market_making"].append(self.get_mm_quote(sym))
            except Exception as e:
                logger.debug(f"Institutional MM scan failed {sym}: {e}")
                results["market_making"].append({"symbol": sym, "error": str(e)})

        pairs = [("BTC-USD","ETH-USD"), ("BTC-USD","BNB-USD"), ("ETH-USD","SOL-USD")]
        for a,b in pairs:
            try:
                results["stat_arb"].append(self.get_stat_arb_signal(a,b))
            except Exception as e:
                logger.debug(f"Institutional stat arb scan failed {a}/{b}: {e}")
                results["stat_arb"].append({"pair": f"{a}/{b}", "signal": "ERROR", "error": str(e)})
        return results

_strategy_manager = None
_manager_lock = threading.Lock()

def get_strategy_manager():
    global _strategy_manager
    if _strategy_manager is None:
        with _manager_lock:
            if _strategy_manager is None:
                _strategy_manager = StrategyManager()
    return _strategy_manager
