"""
Institutional Order Book Imbalance & OFI (Order Flow Imbalance)
Real-time Binance orderbook signals
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class OFIConfig:
    symbol: str
    depth: int = 10
    imbalance_threshold: float = 0.3
    ofi_threshold: float = 0.5
    total_investment: float = 10000
    status: str = "ACTIVE"

@dataclass
class OrderBookSignal:
    symbol: str
    signal: str
    imbalance: float
    ofi: float
    bid_pressure: float
    ask_pressure: float
    mid_price: float
    timestamp: str

class OrderBookImbalanceBot:
    """
    Institutional Order Book Signals:
    - Book Imbalance: (BidVol - AskVol)/(BidVol+AskVol)
    - OFI: Order Flow Imbalance from bid/ask changes
    - Bid/Ask Pressure
    - Real Binance depth
    """
    def __init__(self, cfg: OFIConfig):
        self.config = cfg
        self.prev_bids = None
        self.prev_asks = None
        self.signals_history = []
        self.created_at = datetime.utcnow().isoformat()

    def fetch_orderbook(self, symbol: str) -> Optional[Dict]:
        try:
            import requests
            binance_sym = config.data.binance_map.get(symbol, symbol.replace('-',''))
            resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": self.config.depth*2}, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Orderbook fetch failed {symbol}: {e}")
        return None

    def calculate_imbalance(self, orderbook) -> tuple:
        try:
            bids = orderbook.get('bids', [])[:self.config.depth]
            asks = orderbook.get('asks', [])[:self.config.depth]
            bid_vol = sum(float(b[1]) for b in bids)
            ask_vol = sum(float(a[1]) for a in asks)
            total = bid_vol + ask_vol
            imbalance = (bid_vol - ask_vol) / total if total else 0
            # Weighted imbalance by price distance (closer levels more important)
            weighted_bid = sum(float(b[1]) / (i+1) for i, b in enumerate(bids))
            weighted_ask = sum(float(a[1]) / (i+1) for i, a in enumerate(asks))
            weighted_total = weighted_bid + weighted_ask
            weighted_imb = (weighted_bid - weighted_ask) / weighted_total if weighted_total else 0
            return imbalance, weighted_imb, bid_vol, ask_vol
        except:
            return 0,0,0,0

    def calculate_ofi(self, curr_bids, curr_asks) -> float:
        """
        OFI: Order Flow Imbalance
        OFI = sum over levels of (delta bid - delta ask)
        Positive = net buying pressure
        """
        try:
            if self.prev_bids is None or self.prev_asks is None:
                self.prev_bids = curr_bids
                self.prev_asks = curr_asks
                return 0.0

            ofi = 0.0
            # Compare top levels
            for i in range(min(len(curr_bids), len(self.prev_bids), 5)):
                try:
                    curr_bid_price = float(curr_bids[i][0])
                    prev_bid_price = float(self.prev_bids[i][0])
                    curr_bid_qty = float(curr_bids[i][1])
                    prev_bid_qty = float(self.prev_bids[i][1])

                    if curr_bid_price > prev_bid_price:
                        ofi += curr_bid_qty  # bid price up = buying
                    elif curr_bid_price == prev_bid_price:
                        ofi += curr_bid_qty - prev_bid_qty
                    else:
                        ofi -= prev_bid_qty

                    curr_ask_price = float(curr_asks[i][0])
                    prev_ask_price = float(self.prev_asks[i][0])
                    curr_ask_qty = float(curr_asks[i][1])
                    prev_ask_qty = float(self.prev_asks[i][1])

                    if curr_ask_price < prev_ask_price:
                        ofi -= curr_ask_qty  # ask price down = selling
                    elif curr_ask_price == prev_ask_price:
                        ofi -= curr_ask_qty - prev_ask_qty
                    else:
                        ofi += prev_ask_qty
                except:
                    continue

            self.prev_bids = curr_bids
            self.prev_asks = curr_asks
            # Normalize
            return float(np.tanh(ofi / 10))  # bound to [-1,1]
        except:
            return 0.0

    def generate_signal(self) -> OrderBookSignal:
        ob = self.fetch_orderbook(self.config.symbol)
        if not ob:
            return OrderBookSignal(
                symbol=self.config.symbol,
                signal="NO_DATA",
                imbalance=0.0,
                ofi=0.0,
                bid_pressure=0.0,
                ask_pressure=0.0,
                mid_price=0.0,
                timestamp=datetime.utcnow().isoformat()
            )

        bids = ob.get('bids', [])
        asks = ob.get('asks', [])
        if not bids or not asks:
            return OrderBookSignal(
                symbol=self.config.symbol,
                signal="NO_DATA",
                imbalance=0.0,
                ofi=0.0,
                bid_pressure=0.0,
                ask_pressure=0.0,
                mid_price=0.0,
                timestamp=datetime.utcnow().isoformat()
            )

        imbalance, weighted_imb, bid_vol, ask_vol = self.calculate_imbalance(ob)
        ofi = self.calculate_ofi(bids, asks)

        bid_price = float(bids[0][0])
        ask_price = float(asks[0][0])
        mid = (bid_price + ask_price) / 2

        # Combined signal
        combined = (imbalance + weighted_imb + ofi) / 3

        signal = "HOLD"
        if combined > self.config.imbalance_threshold and ofi > self.config.ofi_threshold:
            signal = "STRONG_BUY"
        elif combined > self.config.imbalance_threshold * 0.5:
            signal = "BUY"
        elif combined < -self.config.imbalance_threshold and ofi < -self.config.ofi_threshold:
            signal = "STRONG_SELL"
        elif combined < -self.config.imbalance_threshold * 0.5:
            signal = "SELL"

        sig = OrderBookSignal(
            symbol=self.config.symbol,
            signal=signal,
            imbalance=float(imbalance),
            ofi=float(ofi),
            bid_pressure=float(bid_vol),
            ask_pressure=float(ask_vol),
            mid_price=float(mid),
            timestamp=datetime.utcnow().isoformat()
        )
        self.signals_history.append(asdict(sig))
        if len(self.signals_history) > 100:
            self.signals_history = self.signals_history[-100:]
        return sig

    def to_dict(self):
        latest = self.signals_history[-1] if self.signals_history else None
        return {
            "config": asdict(self.config),
            "latest_signal": latest,
            "signals_history": self.signals_history[-20:],
            "type": "orderbook_imbalance",
            "strategy": "Institutional Order Book Imbalance + OFI",
            "real_trading": True,
            "institutional": True,
            "created_at": self.created_at
        }
