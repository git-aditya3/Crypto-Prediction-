"""
Strategy Manager v5 MAX - Institutional strategies + CoinDCX INR + Thread-safe + Metrics
- DCA, Grid, Breakout, Market Making Avellaneda-Stoikov, TWAP/VWAP execution, Stat Arb, OFI, Funding Arb, Risk Model
- CoinDCX INR support, validation, error handling, metrics, caching
"""
from typing import Dict, List, Optional
import threading
import time
from datetime import datetime

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
        self._metrics = {
            "bots_created": 0,
            "signals_generated": 0,
            "scans": 0,
            "errors": 0
        }
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 10
        
        self.coindcx_map = {
            "BTC-USD": "BTCINR", "ETH-USD": "ETHINR", "BNB-USD": "BNBINR",
            "SOL-USD": "SOLINR", "XRP-USD": "XRPINR", "ADA-USD": "ADAINR",
            "DOGE-USD": "DOGEINR", "AVAX-USD": "AVAXINR", "MATIC-USD": "MATICINR",
            "DOT-USD": "DOTINR", "LINK-USD": "LINKINR", "LTC-USD": "LTCINR",
        }

    def _validate_symbol(self, symbol: str) -> str:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol must be non-empty string")
        symbol = symbol.strip().upper()
        if len(symbol) < 3 or len(symbol) > 20:
            raise ValueError(f"Invalid symbol length: {symbol}")
        if symbol.endswith("USDT") and "INR" not in symbol:
            base = symbol.replace("USDT","")
            if len(base) >= 2:
                return f"{base}-USD"
        if "/" in symbol:
            symbol = symbol.replace("/","-")
        if "INR" in symbol:
            return symbol.replace("-","")
        return symbol

    def _get_price_source(self, symbol: str) -> str:
        if "INR" in symbol.upper():
            return "CoinDCX INR primary v5 MAX"
        return "CoinDCX INR + Binance USD fallback v5 MAX"

    def _cache_get(self, key: str) -> Optional[Dict]:
        now = time.time()
        with self._cache_lock:
            if key in self._cache:
                entry = self._cache[key]
                if now - entry["timestamp"] < self._cache_ttl:
                    return entry["data"]
        return None

    def _cache_set(self, key: str, data: Dict):
        with self._cache_lock:
            self._cache[key] = {"data": data, "timestamp": time.time()}

    def create_dca_bot(self, symbol: str, total_investment: float, num_orders: int = 5, 
                      price_deviation_pct: float = 1.0, take_profit_pct: float = 5.0, stop_loss_pct: float = 3.0) -> Dict:
        symbol = self._validate_symbol(symbol)
        if total_investment <= 0:
            raise ValueError("total_investment must be >0")
        if num_orders <= 0 or num_orders > 50:
            raise ValueError("num_orders must be 1-50")
        if price_deviation_pct <= 0 or price_deviation_pct > 20:
            price_deviation_pct = 1.0
        if take_profit_pct <= 0 or take_profit_pct > 100:
            take_profit_pct = 5.0
        if stop_loss_pct <= 0 or stop_loss_pct > 50:
            stop_loss_pct = 3.0

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
            self._metrics["bots_created"] += 1
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["coindcx_support"] = True
        result["version"] = "v5_max"
        return result

    def create_grid_bot(self, symbol: str, lower_price: float, upper_price: float, num_grids: int = 10, total_investment: float = 1000) -> Dict:
        symbol = self._validate_symbol(symbol)
        try:
            lower_price = float(lower_price)
            upper_price = float(upper_price)
            num_grids = int(num_grids)
            total_investment = float(total_investment)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric parameters v5")

        if lower_price <= 0 or upper_price <= 0:
            raise ValueError("Prices must be >0 v5")
        if lower_price >= upper_price:
            raise ValueError("lower_price must be < upper_price v5")
        if num_grids <= 1 or num_grids > 100:
            raise ValueError("num_grids must be 2-100 v5")
        if total_investment <= 0:
            raise ValueError("total_investment must be >0 v5")

        if "INR" in symbol.upper() and lower_price < 1000 and symbol.upper().startswith("BTC"):
            lower_price = lower_price * 83.5
            upper_price = upper_price * 83.5

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
            self._metrics["bots_created"] += 1
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["coindcx_support"] = True
        result["version"] = "v5_max"
        return result

    def create_mm_bot(self, symbol: str, total_investment: float = 10000, spread_bps: float = 20, max_inventory: float = 1.0) -> Dict:
        symbol = self._validate_symbol(symbol)
        try:
            total_investment = float(total_investment)
            spread_bps = float(spread_bps)
            max_inventory = float(max_inventory)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric parameters v5")
        if total_investment <= 0:
            raise ValueError("total_investment must be >0 v5")
        if spread_bps <= 0 or spread_bps > 1000:
            spread_bps = 20
        if max_inventory <= 0:
            max_inventory = 1.0

        cfg = MarketMakingConfig(symbol=symbol, total_investment=total_investment, spread_bps=spread_bps, max_inventory=max_inventory)
        bot = MarketMakingBot(cfg)
        with self._lock:
            self.mm_bots[symbol] = bot
            self._metrics["bots_created"] += 1
        try:
            bot.generate_quotes()
        except Exception as e:
            logger.warning(f"MM initial quote v5 failed {symbol}: {e}")
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["coindcx_support"] = True
        result["version"] = "v5_max"
        return result

    def get_mm_quote(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cache_key = f"mm_{symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

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
            result = asdict(quote)
            result["price_source"] = self._get_price_source(symbol)
            result["coindcx_support"] = True
            result["version"] = "v5_max"
            with self._lock:
                self._metrics["signals_generated"] += 1
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"MM quote v5 failed {symbol}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return {"error": str(e), "symbol": symbol, "signal": "NO_DATA", "price_source": self._get_price_source(symbol), "version": "v5_max"}

    def create_execution_bot(self, symbol: str, side: str, total_quantity: float, strategy: str = "TWAP", duration_minutes: int = 60, num_slices: int = 12) -> Dict:
        symbol = self._validate_symbol(symbol)
        if total_quantity <= 0:
            raise ValueError("total_quantity must be >0 v5")
        try:
            total_quantity = float(total_quantity)
            duration_minutes = int(duration_minutes)
            num_slices = int(num_slices)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric parameters v5")
        side = side.upper()
        if side not in ["BUY","SELL"]:
            raise ValueError("side must be BUY or SELL v5")
        cfg = ExecutionConfig(symbol=symbol, side=side, total_quantity=total_quantity, strategy=strategy, duration_minutes=duration_minutes, num_slices=num_slices)
        bot = TWAPVWAPExecutor(cfg)
        key = f"{symbol}_{strategy.upper()}_{side.upper()}_v5"
        with self._lock:
            self.execution_bots[key] = bot
            self._metrics["bots_created"] += 1
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["version"] = "v5_max"
        return result

    def create_stat_arb_bot(self, symbol_a: str, symbol_b: str, entry_z: float = 2.0) -> Dict:
        symbol_a = self._validate_symbol(symbol_a)
        symbol_b = self._validate_symbol(symbol_b)
        if symbol_a == symbol_b:
            raise ValueError("Symbols must be different v5")
        try:
            entry_z = float(entry_z)
        except (ValueError, TypeError):
            entry_z = 2.0
        cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b, entry_z=entry_z)
        bot = StatArbBot(cfg)
        key = f"{symbol_a}_{symbol_b}_v5"
        with self._lock:
            self.stat_arb_bots[key] = bot
            self._metrics["bots_created"] += 1
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"StatArb initial signal v5 failed {key}: {e}")
        result = bot.to_dict()
        result["price_source"] = "CoinDCX INR + Binance v5 MAX"
        result["version"] = "v5_max"
        return result

    def get_stat_arb_signal(self, symbol_a: str, symbol_b: str) -> Dict:
        symbol_a = self._validate_symbol(symbol_a)
        symbol_b = self._validate_symbol(symbol_b)
        key = f"{symbol_a}_{symbol_b}_v5"
        cache_key = f"statarb_{symbol_a}_{symbol_b}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        with self._lock:
            bot = self.stat_arb_bots.get(key) or self.stat_arb_bots.get(f"{symbol_a}_{symbol_b}")
        if not bot:
            try:
                cfg = StatArbConfig(symbol_a=symbol_a, symbol_b=symbol_b)
                bot = StatArbBot(cfg)
                with self._lock:
                    self.stat_arb_bots[key] = bot
            except Exception as e:
                return {"error": str(e), "pair": f"{symbol_a}/{symbol_b}", "signal": "ERROR", "version": "v5_max"}
        try:
            sig = bot.generate_signal()
            from dataclasses import asdict
            result = asdict(sig)
            result["price_source"] = "CoinDCX INR + Binance v5 MAX"
            result["version"] = "v5_max"
            with self._lock:
                self._metrics["signals_generated"] += 1
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"StatArb signal v5 failed {key}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return {"error": str(e), "pair": f"{symbol_a}/{symbol_b}", "signal": "ERROR", "version": "v5_max"}

    def create_ofi_bot(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cfg = OFIConfig(symbol=symbol)
        bot = OrderBookImbalanceBot(cfg)
        with self._lock:
            self.ofi_bots[symbol] = bot
            self._metrics["bots_created"] += 1
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"OFI initial signal v5 failed {symbol}: {e}")
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["version"] = "v5_max"
        return result

    def get_ofi_signal(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cache_key = f"ofi_{symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

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
            result = asdict(sig)
            result["price_source"] = self._get_price_source(symbol)
            result["version"] = "v5_max"
            with self._lock:
                self._metrics["signals_generated"] += 1
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"OFI signal v5 failed {symbol}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return {"error": str(e), "symbol": symbol, "signal": "ERROR", "version": "v5_max"}

    def create_funding_bot(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cfg = FundingArbConfig(symbol=symbol)
        bot = FundingArbBot(cfg)
        with self._lock:
            self.funding_bots[symbol] = bot
            self._metrics["bots_created"] += 1
        try:
            bot.generate_signal()
        except Exception as e:
            logger.warning(f"Funding initial signal v5 failed {symbol}: {e}")
        result = bot.to_dict()
        result["price_source"] = self._get_price_source(symbol)
        result["version"] = "v5_max"
        return result

    def get_funding_signal(self, symbol: str) -> Dict:
        symbol = self._validate_symbol(symbol)
        cache_key = f"funding_{symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

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
            result = asdict(sig)
            result["price_source"] = self._get_price_source(symbol)
            result["version"] = "v5_max"
            with self._lock:
                self._metrics["signals_generated"] += 1
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"Funding signal v5 failed {symbol}: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return {"error": str(e), "symbol": symbol, "signal": "ERROR", "version": "v5_max"}

    def get_position_size(self, symbol: str, account_balance: float, win_rate: float = 0.55, win_loss_ratio: float = 1.5) -> Dict:
        symbol = self._validate_symbol(symbol)
        if account_balance <= 0:
            raise ValueError("account_balance must be >0 v5")
        result = self.risk_model.position_size(symbol, account_balance, win_rate, win_loss_ratio)
        result["price_source"] = self._get_price_source(symbol)
        result["version"] = "v5_max"
        return result

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
        result = self.risk_model.portfolio_risk(symbols)
        result["price_source"] = "CoinDCX INR + Binance v5 MAX"
        result["coindcx_support"] = True
        result["version"] = "v5_max"
        return result

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
            metrics = dict(self._metrics)
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
            "institutional": True,
            "price_source": "CoinDCX INR primary, Binance fallback v5 MAX",
            "coindcx_support": True,
            "inr_pairs": list(self.coindcx_map.values()),
            "metrics": metrics,
            "version": "v5_max"
        }

    def scan_breakouts(self, symbols: List[str] = None) -> List[Dict]:
        try:
            if symbols:
                symbols = [self._validate_symbol(s) for s in symbols]
            with self._lock:
                self._metrics["scans"] += 1
            results = self.breakout_bot.scan_all(symbols)
            for r in results:
                r["price_source"] = self._get_price_source(r.get("symbol",""))
                r["version"] = "v5_max"
            return results
        except Exception as e:
            logger.warning(f"Breakout scan v5 failed: {e}")
            with self._lock:
                self._metrics["errors"] += 1
            return []

    def scan_institutional(self, symbols: List[str] = None) -> Dict:
        try:
            if symbols:
                symbols = [self._validate_symbol(s) for s in symbols]
            else:
                symbols = config.data.supported_symbols[:6]
        except Exception:
            symbols = config.data.supported_symbols[:6]

        with self._lock:
            self._metrics["scans"] += 1

        results = {
            "market_making": [],
            "orderbook_imbalance": [],
            "funding_arb": [],
            "stat_arb": [],
            "timestamp": datetime.utcnow().isoformat(),
            "version": "v5_max"
        }
        for sym in symbols[:4]:
            try:
                results["orderbook_imbalance"].append(self.get_ofi_signal(sym))
            except Exception as e:
                logger.debug(f"Institutional OFI v5 scan failed {sym}: {e}")
                results["orderbook_imbalance"].append({"symbol": sym, "signal": "ERROR", "error": str(e), "version": "v5_max"})
            try:
                results["funding_arb"].append(self.get_funding_signal(sym))
            except Exception as e:
                logger.debug(f"Institutional funding v5 scan failed {sym}: {e}")
                results["funding_arb"].append({"symbol": sym, "signal": "ERROR", "error": str(e), "version": "v5_max"})
            try:
                results["market_making"].append(self.get_mm_quote(sym))
            except Exception as e:
                logger.debug(f"Institutional MM v5 scan failed {sym}: {e}")
                results["market_making"].append({"symbol": sym, "error": str(e), "version": "v5_max"})

        pairs = [("BTC-USD","ETH-USD"), ("BTC-USD","BNB-USD"), ("ETH-USD","SOL-USD")]
        for a,b in pairs:
            try:
                results["stat_arb"].append(self.get_stat_arb_signal(a,b))
            except Exception as e:
                logger.debug(f"Institutional stat arb v5 scan failed {a}/{b}: {e}")
                results["stat_arb"].append({"pair": f"{a}/{b}", "signal": "ERROR", "error": str(e), "version": "v5_max"})

        results["price_source"] = "CoinDCX INR primary, Binance fallback v5 MAX"
        results["coindcx_support"] = True
        results["metrics"] = dict(self._metrics)
        return results

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "version": "v5_max"}

_strategy_manager = None
_manager_lock = threading.Lock()

def get_strategy_manager():
    global _strategy_manager
    if _strategy_manager is None:
        with _manager_lock:
            if _strategy_manager is None:
                _strategy_manager = StrategyManager()
    return _strategy_manager
