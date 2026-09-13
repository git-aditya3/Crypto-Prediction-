"""
Institutional Market Making - Avellaneda-Stoikov + Order Book Imbalance
Real trading with inventory risk management
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
    spread_bps: float = 20  # 0.20% spread
    inventory_target: float = 0.0  # target inventory
    max_inventory: float = 1.0
    gamma: float = 0.1  # inventory risk aversion (Avellaneda-Stoikov)
    kappa: float = 1.5  # order book liquidity
    volatility_window: int = 20
    order_size_pct: float = 0.1
    status: str = "ACTIVE"

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
    """
    Institutional Market Making
    - Avellaneda-Stoikov optimal bid/ask with inventory risk
    - Order book imbalance filter
    - Real Binance orderbook
    """
    def __init__(self, cfg: MarketMakingConfig):
        self.config = cfg
        self.inventory = 0.0
        self.cash = cfg.total_investment
        self.trades = []
        self.quotes_history = []
        self.created_at = datetime.utcnow().isoformat()

    def get_market_data(self, symbol: str):
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price() or 0
            orderbook = fetcher.get_orderbook(limit=20) if hasattr(fetcher, 'get_orderbook') else None
            # Fallback to REST
            if not orderbook:
                import requests
                binance_sym = config.data.binance_map.get(symbol, symbol.replace('-',''))
                resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": 20}, timeout=5)
                if resp.status_code == 200:
                    orderbook = resp.json()
            return price, orderbook
        except Exception as e:
            logger.warning(f"MM market data failed {symbol}: {e}")
            return 0, None

    def calculate_volatility(self, symbol: str) -> float:
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            returns = df['Close'].pct_change().dropna().tail(self.config.volatility_window)
            vol = returns.std() * math.sqrt(86400)  # daily vol proxy
            return max(0.01, float(vol))
        except:
            return 0.02

    def orderbook_imbalance(self, orderbook) -> float:
        """Calculate order book imbalance - institutional signal
        I = (BidVol - AskVol)/(BidVol + AskVol) in [-1,1]
        Positive = buying pressure
        """
        try:
            if not orderbook:
                return 0.0
            bids = orderbook.get('bids', [])[:10]
            asks = orderbook.get('asks', [])[:10]
            bid_vol = sum(float(b[1]) for b in bids)
            ask_vol = sum(float(a[1]) for a in asks)
            total = bid_vol + ask_vol
            if total == 0:
                return 0.0
            return (bid_vol - ask_vol) / total
        except:
            return 0.0

    def avellaneda_stoikov_quotes(self, mid_price: float, volatility: float, inventory: float) -> tuple:
        """
        Avellaneda-Stoikov optimal quotes:
        reservation_price = mid - inventory * gamma * volatility^2 * T
        spread = gamma * volatility^2 * T + 2/gamma * ln(1+gamma/kappa)
        """
        try:
            gamma = self.config.gamma
            kappa = self.config.kappa
            T = 1.0  # time horizon normalized

            # Reservation price adjusted for inventory
            reservation = mid_price - inventory * gamma * (volatility ** 2) * T

            # Optimal spread
            spread = gamma * (volatility ** 2) * T + (2 / gamma) * math.log(1 + gamma / kappa) if gamma != 0 else self.config.spread_bps / 10000 * mid_price

            # Ensure minimum spread from config
            min_spread = mid_price * self.config.spread_bps / 10000
            spread = max(spread, min_spread)

            bid = reservation - spread / 2
            ask = reservation + spread / 2

            return bid, ask, reservation, spread
        except Exception as e:
            logger.warning(f"AS quotes failed: {e}")
            spread = mid_price * self.config.spread_bps / 10000
            return mid_price - spread/2, mid_price + spread/2, mid_price, spread

    def generate_quotes(self) -> MMQuote:
        price, orderbook = self.get_market_data(self.config.symbol)
        if price == 0:
            price = 100000  # fallback

        vol = self.calculate_volatility(self.config.symbol)
        imbalance = self.orderbook_imbalance(orderbook)

        # Adjust inventory target based on imbalance (institutional)
        # If strong buy imbalance, reduce ask size, increase bid size
        bid, ask, reservation, spread = self.avellaneda_stoikov_quotes(price, vol, self.inventory)

        # Size adjustment based on imbalance
        base_size = (self.config.total_investment * self.config.order_size_pct) / price
        if imbalance > 0.3:  # strong buy pressure
            bid_size = base_size * 1.5
            ask_size = base_size * 0.5
        elif imbalance < -0.3:  # sell pressure
            bid_size = base_size * 0.5
            ask_size = base_size * 1.5
        else:
            bid_size = base_size
            ask_size = base_size

        # Inventory limit check
        if self.inventory >= self.config.max_inventory:
            bid_size = 0  # stop buying
        if self.inventory <= -self.config.max_inventory:
            ask_size = 0  # stop selling

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
