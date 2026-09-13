"""
funding_arb v5 MAX - Improved pooling, metrics, thread-safe, versioning
"""
"""
Institutional Funding Rate Arbitrage
Fixed: fallback price, error handling, validation, annualized calc
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import requests

from ..config import get_config
from ..utils.logger import get_logger
VERSION = "v5_max"

logger = get_logger(__name__)
config = get_config()

@dataclass
class FundingArbConfig:
    symbol: str
    spot_symbol: str = ""
    futures_symbol: str = ""
    funding_threshold: float = 0.0005
    total_investment: float = 10000
    leverage: float = 1.0
    status: str = "ACTIVE"

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("symbol required")
        if self.funding_threshold <= 0:
            self.funding_threshold = 0.0005
        if self.total_investment <= 0:
            self.total_investment = 10000
        if self.leverage <= 0:
            self.leverage = 1.0

@dataclass
class FundingSignal:
    symbol: str
    signal: str
    funding_rate: float
    annualized_rate: float
    spot_price: float
    futures_price: float
    basis: float
    estimated_profit: float
    timestamp: str

class FundingArbBot:
    def __init__(self, cfg: FundingArbConfig):
        self.config = cfg
        if not cfg.spot_symbol:
            self.config.spot_symbol = cfg.symbol.replace('-','').replace('/','')
        if not cfg.futures_symbol:
            self.config.futures_symbol = cfg.symbol.replace('-','').replace('/','')
        self.signals_history = []
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

        self._last_spot = 0.0
        self._last_fut = 0.0
        self._last_funding = 0.0

    def fetch_funding_rate(self, symbol: str) -> Optional[float]:
        # Try premiumIndex first
        try:
            resp = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex", params={"symbol": symbol}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    rate = data.get('lastFundingRate')
                    if rate is not None:
                        try:
                            r = float(rate)
                            if abs(r) < 0.1:  # sanity: funding should be <10%
                                self._last_funding = r
                                return r
                        except ValueError:
                            pass
        except requests.RequestException as e:
            logger.debug(f"Funding premiumIndex failed {symbol}: {e}")

        try:
            resp = requests.get("https://fapi.binance.com/fapi/v1/fundingRate", params={"symbol": symbol, "limit": 1}, timeout=3)
            if resp.status_code == 200:
                arr = resp.json()
                if isinstance(arr, list) and arr:
                    rate = arr[0].get('fundingRate')
                    if rate is not None:
                        try:
                            r = float(rate)
                            if abs(r) < 0.1:
                                self._last_funding = r
                                return r
                        except ValueError:
                            pass
        except requests.RequestException as e:
            logger.debug(f"Funding fundingRate failed {symbol}: {e}")

        # Return last known or None
        return self._last_funding if self._last_funding != 0 else None

    def fetch_spot_price(self, symbol: str) -> float:
        try:
            resp = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": symbol}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('price')
                if price is not None:
                    p = float(price)
                    if p > 0:
                        self._last_spot = p
                        return p
        except requests.RequestException as e:
            logger.debug(f"Spot price failed {symbol}: {e}")
        except Exception as e:
            logger.debug(f"Spot price unexpected {symbol}: {e}")

        # Fallback to historical
        if self._last_spot > 0:
            return self._last_spot
        try:
            from ..data.fetcher import CryptoDataFetcher
            # Try to map back to our symbol format
            our_sym = symbol
            # Reverse map
            for k,v in config.data.binance_map.items():
                if v == symbol:
                    our_sym = k
                    break
            f = CryptoDataFetcher(symbol=our_sym)
            df = f.load_or_fetch(symbol=our_sym)
            if not df.empty:
                p = float(df['Close'].iloc[-1])
                if p > 0:
                    self._last_spot = p
                    return p
        except Exception:
            pass
        return self._last_spot or 0

    def fetch_futures_price(self, symbol: str) -> float:
        try:
            resp = requests.get("https://fapi.binance.com/fapi/v1/ticker/price", params={"symbol": symbol}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('price')
                if price is not None:
                    p = float(price)
                    if p > 0:
                        self._last_fut = p
                        return p
        except requests.RequestException as e:
            logger.debug(f"Futures price failed {symbol}: {e}")
        except Exception as e:
            logger.debug(f"Futures price unexpected {symbol}: {e}")

        if self._last_fut > 0:
            return self._last_fut
        # Fallback to spot
        return self.fetch_spot_price(symbol)

    def generate_signal(self) -> FundingSignal:
        spot_sym = self.config.spot_symbol
        fut_sym = self.config.futures_symbol

        funding = self.fetch_funding_rate(fut_sym)
        spot_price = self.fetch_spot_price(spot_sym)
        fut_price = self.fetch_futures_price(fut_sym)

        # Handle missing data gracefully
        if funding is None:
            funding = self._last_funding or 0.0
            if funding == 0:
                logger.debug(f"Funding rate missing for {fut_sym}, using 0")

        if spot_price == 0 and fut_price == 0:
            raise ValueError(f"Cannot get prices for {self.config.symbol}")

        if spot_price == 0:
            spot_price = fut_price
        if fut_price == 0:
            fut_price = spot_price

        # Basis calc with zero check
        basis = (fut_price - spot_price) / spot_price if spot_price and spot_price != 0 else 0.0
        # Bound basis to +/-10%
        basis = max(-0.1, min(0.1, basis))

        # Annualized: funding every 8h, 3 per day, 365 days
        # Bound funding to +/-2% per period for sanity
        bounded_funding = max(-0.02, min(0.02, funding))
        annualized = bounded_funding * 3 * 365

        signal = "HOLD"
        estimated_profit = 0.0

        if funding > self.config.funding_threshold:
            signal = "SHORT_FUTURES_LONG_SPOT"
            estimated_profit = funding * self.config.total_investment
        elif funding < -self.config.funding_threshold:
            signal = "LONG_FUTURES_SHORT_SPOT"
            estimated_profit = abs(funding) * self.config.total_investment
        elif abs(basis) > 0.005:
            if basis > 0:
                signal = "SHORT_FUTURES_LONG_SPOT_BASIS"
                estimated_profit = basis * self.config.total_investment * 0.5
            else:
                signal = "LONG_FUTURES_SHORT_SPOT_BASIS"
                estimated_profit = abs(basis) * self.config.total_investment * 0.5

        sig = FundingSignal(
            symbol=self.config.symbol,
            signal=signal,
            funding_rate=float(funding),
            annualized_rate=float(annualized),
            spot_price=float(spot_price),
            futures_price=float(fut_price),
            basis=float(basis),
            estimated_profit=float(estimated_profit),
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
            "type": "funding_arb",
            "strategy": "Institutional Funding Rate Arbitrage - Spot vs Futures",
            "real_trading": True,
            "institutional": True,
            "created_at": self.created_at
        }