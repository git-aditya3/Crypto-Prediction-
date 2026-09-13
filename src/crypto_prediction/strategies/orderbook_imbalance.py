"""
Institutional Order Book Imbalance & OFI
Fixed: error handling, OFI logic, validation, NaN handling
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

    def __post_init__(self):
        if self.depth <= 0 or self.depth > 50:
            self.depth = 10
        if self.imbalance_threshold <= 0:
            self.imbalance_threshold = 0.3
        if self.ofi_threshold <= 0:
            self.ofi_threshold = 0.5

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
    def __init__(self, cfg: OFIConfig):
        self.config = cfg
        self.prev_bids = None
        self.prev_asks = None
        self.signals_history = []
        self.created_at = datetime.utcnow().isoformat()
        self._last_mid = 0.0

    def fetch_orderbook(self, symbol: str) -> Optional[Dict]:
        try:
            import requests
            binance_sym = config.data.binance_map.get(symbol, symbol.replace('-','').replace('/',''))
            resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": max(20, self.config.depth*2)}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                # Validate
                if 'bids' in data and 'asks' in data:
                    return data
            else:
                logger.debug(f"Orderbook HTTP {resp.status_code} for {symbol}")
        except requests.RequestException as e:
            logger.debug(f"Orderbook fetch failed {symbol}: {e}")
        except Exception as e:
            logger.debug(f"Orderbook unexpected error {symbol}: {e}")
        return None

    def calculate_imbalance(self, orderbook) -> tuple:
        try:
            bids = orderbook.get('bids', [])[:self.config.depth]
            asks = orderbook.get('asks', [])[:self.config.depth]
            if not bids or not asks:
                return 0.0, 0.0, 0.0, 0.0

            def safe_vol(levels):
                vol=0.0
                for lvl in levels:
                    try:
                        if len(lvl) > 1:
                            vol+=float(lvl[1])
                    except (ValueError, IndexError):
                        continue
                return vol

            bid_vol = safe_vol(bids)
            ask_vol = safe_vol(asks)
            total = bid_vol + ask_vol
            imbalance = (bid_vol - ask_vol) / total if total > 0 else 0.0

            # Weighted by distance
            weighted_bid = 0.0
            weighted_ask = 0.0
            for i, b in enumerate(bids):
                try:
                    weighted_bid += float(b[1]) / (i+1)
                except Exception:
                    continue
            for i, a in enumerate(asks):
                try:
                    weighted_ask += float(a[1]) / (i+1)
                except Exception:
                    continue
            weighted_total = weighted_bid + weighted_ask
            weighted_imb = (weighted_bid - weighted_ask) / weighted_total if weighted_total > 0 else 0.0

            # Bound
            imbalance = max(-1.0, min(1.0, imbalance))
            weighted_imb = max(-1.0, min(1.0, weighted_imb))

            return imbalance, weighted_imb, bid_vol, ask_vol
        except Exception as e:
            logger.debug(f"Imbalance calc failed: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def calculate_ofi(self, curr_bids, curr_asks) -> float:
        try:
            if self.prev_bids is None or self.prev_asks is None:
                self.prev_bids = curr_bids
                self.prev_asks = curr_asks
                return 0.0

            ofi = 0.0
            levels = min(len(curr_bids), len(self.prev_bids), 5, len(curr_asks), len(self.prev_asks))

            for i in range(levels):
                try:
                    curr_bid_price = float(curr_bids[i][0])
                    prev_bid_price = float(self.prev_bids[i][0])
                    curr_bid_qty = float(curr_bids[i][1])
                    prev_bid_qty = float(self.prev_bids[i][1])

                    if curr_bid_price > prev_bid_price:
                        ofi += curr_bid_qty
                    elif curr_bid_price == prev_bid_price:
                        ofi += curr_bid_qty - prev_bid_qty
                    else:
                        ofi -= prev_bid_qty

                    curr_ask_price = float(curr_asks[i][0])
                    prev_ask_price = float(self.prev_asks[i][0])
                    curr_ask_qty = float(curr_asks[i][1])
                    prev_ask_qty = float(self.prev_asks[i][1])

                    if curr_ask_price < prev_ask_price:
                        ofi -= curr_ask_qty
                    elif curr_ask_price == prev_ask_price:
                        ofi -= curr_ask_qty - prev_ask_qty
                    else:
                        ofi += prev_ask_qty
                except (ValueError, IndexError) as e:
                    logger.debug(f"OFI level {i} parse failed: {e}")
                    continue

            self.prev_bids = curr_bids
            self.prev_asks = curr_asks

            # Normalize with tanh to [-1,1]
            try:
                normalized = float(np.tanh(ofi / 10.0))
                if not np.isfinite(normalized):
                    return 0.0
                return normalized
            except Exception:
                return 0.0
        except Exception as e:
            logger.debug(f"OFI calc failed: {e}")
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
                mid_price=self._last_mid,
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
                mid_price=self._last_mid,
                timestamp=datetime.utcnow().isoformat()
            )

        try:
            imbalance, weighted_imb, bid_vol, ask_vol = self.calculate_imbalance(ob)
            ofi = self.calculate_ofi(bids, asks)

            try:
                bid_price = float(bids[0][0])
                ask_price = float(asks[0][0])
                if bid_price <= 0 or ask_price <= 0 or bid_price >= ask_price:
                    mid = self._last_mid or bid_price or ask_price
                else:
                    mid = (bid_price + ask_price) / 2
                    self._last_mid = mid
            except Exception:
                mid = self._last_mid

            combined = (imbalance + weighted_imb + ofi) / 3.0
            # Bound combined
            combined = max(-1.0, min(1.0, combined))

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
                mid_price=float(mid) if mid else 0.0,
                timestamp=datetime.utcnow().isoformat()
            )
            self.signals_history.append(asdict(sig))
            if len(self.signals_history) > 100:
                self.signals_history = self.signals_history[-100:]
            return sig
        except Exception as e:
            logger.warning(f"OFI signal generation failed {self.config.symbol}: {e}")
            return OrderBookSignal(
                symbol=self.config.symbol,
                signal="ERROR",
                imbalance=0.0,
                ofi=0.0,
                bid_pressure=0.0,
                ask_pressure=0.0,
                mid_price=self._last_mid,
                timestamp=datetime.utcnow().isoformat()
            )

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
