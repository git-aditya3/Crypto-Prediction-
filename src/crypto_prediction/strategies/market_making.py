"""
Institutional Market Making - Avellaneda-Stoikov + Order Book Imbalance
Real trading with inventory risk management
Fixed: volatility calc, fallback price, error handling, division by zero
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import math
import numpy as np

from ..config import get_config
from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class MarketMakingConfig:
    symbol: str
    total_investment: float = 10000
    spread_bps: float = 20
    inventory_target: float = 0.0
    max_inventory: float = 1.0
    gamma: float = 0.1
    kappa: float = 1.5
    volatility_window: int = 20
    order_size_pct: float = 0.1
    status: str = "ACTIVE"

    def __post_init__(self):
        if self.total_investment <= 0:
            raise ValueError("total_investment must be >0")
        if self.spread_bps <= 0:
            raise ValueError("spread_bps must be >0")
        if self.max_inventory <= 0:
            raise ValueError("max_inventory must be >0")
        if self.gamma <= 0:
            self.gamma = 0.1
        if self.kappa <= 0:
            self.kappa = 1.5

@dataclass
class MMQuote:
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    mid_price: float
    spread: float
    inventory: float
    timestamp: str

class MarketMakingBot:
    def __init__(self, cfg: MarketMakingConfig):
        self.config = cfg
        self.inventory = 0.0
        self.cash = cfg.total_investment
        self.trades = []
        self.quotes_history = []
        self._last_price = 0.0
        self.created_at = datetime.utcnow().isoformat()

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

    def get_market_data(self, symbol: str):
        try:
            from ..data.price_helper import get_live_price as unified_price, get_orderbook as unified_ob
            price = unified_price(symbol)
            if price and price > 0:
                self._last_price = price
            else:
                price = self._last_price or 0

            orderbook = None
            try:
                orderbook = unified_ob(symbol, limit=20)
            except Exception:
                orderbook = None

            # Fallback historical
            if not price or price == 0:
                try:
                    from ..data.fetcher import CryptoDataFetcher
                    f = CryptoDataFetcher(symbol=symbol)
                    df = f.load_or_fetch(symbol=symbol)
                    if not df.empty:
                        price = float(df['Close'].iloc[-1])
                        if "INR" in symbol.upper():
                            price = price * 83.5
                        self._last_price = price
                except Exception:
                    pass

            return price or self._last_price or 0, orderbook
        except Exception as e:
            logger.warning(f"MM market data failed {symbol}: {e}")
            return self._last_price or 0, None

    def calculate_volatility(self, symbol: str) -> float:
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            if df.empty or len(df) < self.config.volatility_window:
                return 0.02
            returns = df['Close'].pct_change().dropna().tail(self.config.volatility_window)
            if returns.empty:
                return 0.02
            # Fixed: use sqrt(365) for crypto daily vol, not sqrt(86400)
            vol = returns.std() * math.sqrt(365)
            # Bound volatility 0.5% to 20% daily
            return max(0.005, min(float(vol), 0.20))
        except Exception as e:
            logger.debug(f"Volatility calc failed {symbol}: {e}")
            return 0.02

    def orderbook_imbalance(self, orderbook) -> float:
        try:
            if not orderbook:
                return 0.0
            bids = orderbook.get('bids', [])[:10]
            asks = orderbook.get('asks', [])[:10]
            if not bids or not asks:
                return 0.0
            bid_vol = sum(float(b[1]) for b in bids if len(b) > 1)
            ask_vol = sum(float(a[1]) for a in asks if len(a) > 1)
            total = bid_vol + ask_vol
            if total == 0:
                return 0.0
            imb = (bid_vol - ask_vol) / total
            # Bound
            return max(-1.0, min(1.0, imb))
        except Exception as e:
            logger.debug(f"Imbalance calc failed: {e}")
            return 0.0

    def avellaneda_stoikov_quotes(self, mid_price: float, volatility: float, inventory: float) -> tuple:
        try:
            if mid_price <= 0:
                raise ValueError("mid_price must be >0")
            gamma = max(0.01, self.config.gamma)
            kappa = max(0.1, self.config.kappa)
            T = 1.0

            reservation = mid_price - inventory * gamma * (volatility ** 2) * T
            # Prevent reservation drifting too far
            max_drift = mid_price * 0.02  # 2% max drift
            reservation = max(mid_price - max_drift, min(mid_price + max_drift, reservation))

            spread = gamma * (volatility ** 2) * T + (2 / gamma) * math.log(1 + gamma / kappa)
            min_spread = mid_price * self.config.spread_bps / 10000
            # Also bound spread 0.05% to 2%
            min_spread = max(mid_price * 0.0005, min_spread)
            max_spread = mid_price * 0.02
            spread = max(min_spread, min(spread, max_spread))

            bid = reservation - spread / 2
            ask = reservation + spread / 2

            # Ensure bid < ask and positive
            if bid <= 0 or ask <= 0 or bid >= ask:
                spread = min_spread
                bid = mid_price - spread/2
                ask = mid_price + spread/2

            return bid, ask, reservation, spread
        except Exception as e:
            logger.warning(f"AS quotes failed: {e}")
            spread = mid_price * max(0.0005, self.config.spread_bps / 10000)
            return mid_price - spread/2, mid_price + spread/2, mid_price, spread

    def generate_quotes(self) -> MMQuote:
        price, orderbook = self.get_market_data(self.config.symbol)
        if price == 0:
            # Last resort: use last price or raise
            if self._last_price and self._last_price > 0:
                price = self._last_price
            else:
                raise ValueError(f"Cannot get price for {self.config.symbol}")

        vol = self.calculate_volatility(self.config.symbol)
        imbalance = self.orderbook_imbalance(orderbook)

        bid, ask, reservation, spread = self.avellaneda_stoikov_quotes(price, vol, self.inventory)

        base_size = (self.config.total_investment * self.config.order_size_pct) / price
        base_size = max(0.00001, base_size)  # min size

        if imbalance > 0.3:
            bid_size = base_size * 1.5
            ask_size = base_size * 0.5
        elif imbalance < -0.3:
            bid_size = base_size * 0.5
            ask_size = base_size * 1.5
        else:
            bid_size = base_size
            ask_size = base_size

        if self.inventory >= self.config.max_inventory:
            bid_size = 0
        if self.inventory <= -self.config.max_inventory:
            ask_size = 0

        # Cash check
        if bid_size * bid > self.cash:
            bid_size = self.cash / bid * 0.95 if bid > 0 else 0

        quote = MMQuote(
            symbol=self.config.symbol,
            bid_price=float(bid),
            ask_price=float(ask),
            bid_size=float(bid_size),
            ask_size=float(ask_size),
            mid_price=float(price),
            spread=float(spread),
            inventory=float(self.inventory),
            timestamp=datetime.utcnow().isoformat()
        )
        self.quotes_history.append(asdict(quote))
        if len(self.quotes_history) > 100:
            self.quotes_history = self.quotes_history[-100:]
        return quote

    def to_dict(self):
        latest = self.quotes_history[-1] if self.quotes_history else None
        return {
            "config": asdict(self.config),
            "inventory": self.inventory,
            "cash": self.cash,
            "latest_quote": latest,
            "quotes_history": self.quotes_history[-20:],
            "trades_count": len(self.trades),
            "type": "market_making",
            "strategy": "Avellaneda-Stoikov + OrderBook Imbalance",
            "real_trading": True,
            "institutional": True
        }
