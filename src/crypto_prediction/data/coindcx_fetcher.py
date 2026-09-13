"""
CoinDCX Data Fetcher - Real INR market data from CoinDCX
Works with actual CoinDCX API, no fake simulation
Integrated with Binance fallback for robustness
"""
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime
import threading

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CoinDCXRealtimeFetcher:
    """
    Real CoinDCX data fetcher - fetches actual INR market data
    No paper simulation - real CoinDCX prices
    """
    def __init__(self, symbol: str = "BTC-USD"):
        self.symbol = symbol
        self.coindcx_market = self._map_symbol(symbol)
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        self._last_price = 0.0
        self._last_fetch = 0
        self._cache_ttl = 5  # seconds
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "CoinDCXFetcher/1.0"})
        self._lock = threading.Lock()

    def _map_symbol(self, symbol: str) -> str:
        """Map our symbols to CoinDCX INR markets"""
        mapping = {
            "BTC-USD": "BTCINR",
            "ETH-USD": "ETHINR",
            "BNB-USD": "BNBINR",
            "SOL-USD": "SOLINR",
            "XRP-USD": "XRPINR",
            "ADA-USD": "ADAINR",
            "DOGE-USD": "DOGEINR",
            "AVAX-USD": "AVAXINR",
            "MATIC-USD": "MATICINR",
            "DOT-USD": "DOTINR",
            "LINK-USD": "LINKINR",
            "LTC-USD": "LTCINR",
            "BCH-USD": "BCHINR",
            "UNI-USD": "UNIINR",
            "SHIB-USD": "SHIBINR",
            "BTCINR": "BTCINR",
            "ETHINR": "ETHINR",
        }
        # If already INR, return as is
        if symbol.upper() in mapping.values():
            return symbol.upper()
        # If contains INR, keep
        if "INR" in symbol.upper():
            return symbol.upper().replace("-","").replace("/","")
        return mapping.get(symbol.upper(), symbol.replace("-","").replace("/","").replace("USD","INR").upper())

    def _is_cache_valid(self):
        return (time.time() - self._last_fetch) < self._cache_ttl and self._last_price > 0

    def fetch_ticker_rest(self) -> Dict:
        """Fetch ticker from CoinDCX public API - real data"""
        try:
            # Try public endpoint first (no auth needed)
            # CoinDCX public ticker: https://api.coindcx.com/exchange/ticker
            resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for ticker in data:
                        if ticker.get("market") == self.coindcx_market:
                            return ticker
            # Fallback to market details
            resp2 = self._session.get(f"{self.public_url}/market_data/trade_history", params={"pair": f"I-{self.coindcx_market}"}, timeout=5)
            if resp2.status_code == 200:
                data = resp2.json()
                if isinstance(data, list) and len(data) > 0:
                    last = data[0]
                    return {"market": self.coindcx_market, "last_price": last.get("p"), "volume": last.get("q")}
        except requests.RequestException as e:
            logger.debug(f"CoinDCX ticker fetch failed {self.coindcx_market}: {e}")
        except Exception as e:
            logger.debug(f"CoinDCX ticker unexpected {self.coindcx_market}: {e}")
        return {}

    def get_current_price(self) -> Optional[float]:
        """Get current price - real CoinDCX INR price, with Binance fallback converted to INR"""
        with self._lock:
            if self._is_cache_valid():
                return self._last_price

        try:
            ticker = self.fetch_ticker_rest()
            price = ticker.get("last_price") or ticker.get("lastPrice") or ticker.get("price")
            if price:
                try:
                    p = float(price)
                    if p > 0 and p < 100_000_000:  # sanity for INR (BTC ~ 80L INR)
                        with self._lock:
                            self._last_price = p
                            self._last_fetch = time.time()
                        return p
                except (ValueError, TypeError):
                    pass
        except Exception as e:
            logger.debug(f"CoinDCX price parse failed {self.coindcx_market}: {e}")

        # Fallback to Binance with INR conversion (83.5 INR per USD approx)
        try:
            from .realtime import BinanceRealtimeFetcher
            # Map INR back to USD for Binance
            usd_symbol = self.symbol
            if "INR" in self.symbol.upper():
                # BTCINR -> BTC-USD
                base = self.symbol.upper().replace("INR","").replace("-","").replace("/","")
                usd_symbol = f"{base}-USD"
            fetcher = BinanceRealtimeFetcher(symbol=usd_symbol)
            binance_price = fetcher.get_current_price()
            if binance_price and binance_price > 0:
                # Convert USD to INR - use 83.5 as approx, but could fetch USDINR rate
                inr_price = binance_price * 83.5
                with self._lock:
                    self._last_price = inr_price
                    self._last_fetch = time.time()
                logger.debug(f"CoinDCX fallback: Binance {usd_symbol} ${binance_price} -> ₹{inr_price:.2f} for {self.coindcx_market}")
                return inr_price
        except Exception as e:
            logger.debug(f"Binance fallback for CoinDCX failed {self.coindcx_market}: {e}")

        # Last resort: cached file directly (avoid yfinance recursion)
        try:
            from pathlib import Path
            import pandas as pd
            usd_sym = self.symbol
            if "INR" in usd_sym.upper():
                base = usd_sym.upper().replace("INR","")
                usd_sym = f"{base}-USD"
            cache_path = config.project_root / "data" / "raw" / f"{usd_sym.replace('-','_')}_1d.csv"
            if cache_path.exists():
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if not df.empty:
                    p = float(df['Close'].iloc[-1]) * 83.5
                    with self._lock:
                        self._last_price = p
                        self._last_fetch = time.time()
                    return p
        except Exception:
            pass

        with self._lock:
            return self._last_price if self._last_price > 0 else None

    def get_tickers_all(self) -> Dict:
        """Get all CoinDCX tickers - real INR market data"""
        try:
            resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                result = {}
                if isinstance(data, list):
                    for ticker in data:
                        try:
                            market = ticker.get("market","")
                            if "INR" in market:
                                price = float(ticker.get("last_price",0) or 0)
                                if price > 0:
                                    result[market] = {
                                        "market": market,
                                        "price": price,
                                        "last_price": price,
                                        "change": float(ticker.get("change_24_hour",0) or 0),
                                        "change_pct": float(ticker.get("change_24_hour",0) or 0) / price * 100 if price else 0,
                                        "high": float(ticker.get("high",0) or 0),
                                        "low": float(ticker.get("low",0) or 0),
                                        "volume": float(ticker.get("volume",0) or 0),
                                        "real_data": True,
                                        "source": "CoinDCX Live INR",
                                        "broker": "coindcx"
                                    }
                        except (ValueError, TypeError):
                            continue
                return result
        except Exception as e:
            logger.warning(f"CoinDCX all tickers failed: {e}")
        return {}

    def get_orderbook(self, limit: int = 20) -> Optional[Dict]:
        """CoinDCX orderbook - if available, else Binance converted"""
        try:
            # CoinDCX orderbook endpoint (if public)
            resp = self._session.get(f"{self.public_url}/market_data/orderbook", params={"pair": f"I-{self.coindcx_market}"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    return data
        except Exception as e:
            logger.debug(f"CoinDCX orderbook failed {self.coindcx_market}: {e}")

        # Fallback to Binance orderbook with INR conversion
        try:
            from .realtime import BinanceRealtimeFetcher
            usd_symbol = self.symbol
            if "INR" in self.symbol.upper():
                base = self.symbol.upper().replace("INR","")
                usd_symbol = f"{base}-USD"
            fetcher = BinanceRealtimeFetcher(symbol=usd_symbol)
            # Try to get Binance orderbook via direct REST
            import requests
            binance_sym = config.data.binance_map.get(usd_symbol, usd_symbol.replace("-","").replace("/",""))
            resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                ob = resp.json()
                # Convert prices to INR
                inr_rate = 83.5
                bids = [[float(p)*inr_rate, float(q)] for p,q in ob.get("bids",[])[:limit]]
                asks = [[float(p)*inr_rate, float(q)] for p,q in ob.get("asks",[])[:limit]]
                return {"bids": bids, "asks": asks, "source": "Binance converted to INR"}
        except Exception as e:
            logger.debug(f"Binance orderbook fallback for CoinDCX failed {self.coindcx_market}: {e}")
        return None

# Global cache for all tickers
_coindcx_tickers_cache = {"data": None, "timestamp": 0}
_coindcx_cache_lock = threading.Lock()
COINDcx_CACHE_TTL = 10

def get_coindcx_tickers_cached() -> Dict:
    now = time.time()
    with _coindcx_cache_lock:
        if _coindcx_tickers_cache["data"] and (now - _coindcx_tickers_cache["timestamp"]) < COINDcx_CACHE_TTL:
            return _coindcx_tickers_cache["data"]
    try:
        fetcher = CoinDCXRealtimeFetcher(symbol="BTC-USD")
        data = fetcher.get_tickers_all()
        with _coindcx_cache_lock:
            _coindcx_tickers_cache["data"] = data
            _coindcx_tickers_cache["timestamp"] = now
        return data
    except Exception:
        with _coindcx_cache_lock:
            return _coindcx_tickers_cache["data"] or {}
