"""
CoinDCX Data Fetcher v5 MAX - Real INR market data + historical + orderbook + metrics
- Comprehensive mapping, validation, thread-safe caching, retry, metrics
- Historical klines via CoinDCX, ticker, orderbook, trade history
- Binance fallback converted to INR, no circular recursion
"""
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime
import threading
import random

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CoinDCXRealtimeFetcher:
    def __init__(self, symbol: str = "BTC-USD"):
        self.symbol = symbol
        self.coindcx_market = self._map_symbol(symbol)
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        self._last_price = 0.0
        self._last_fetch = 0
        self._cache_ttl = 5
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "CoinDCXFetcher v5 MAX Real Trading"})
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
        self._session.mount("https://", adapter)
        self._lock = threading.Lock()
        self._metrics = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "last_price": 0
        }

    def _map_symbol(self, symbol: str) -> str:
        if not symbol or not isinstance(symbol, str):
            return "BTCINR"
        sym = symbol.strip().upper()
        mapping = {
            "BTC-USD": "BTCINR", "BTC/USD": "BTCINR", "BTCUSDT": "BTCINR", "BTC": "BTCINR",
            "ETH-USD": "ETHINR", "ETH/USD": "ETHINR", "ETHUSDT": "ETHINR", "ETH": "ETHINR",
            "BNB-USD": "BNBINR", "BNB/USD": "BNBINR", "BNBUSDT": "BNBINR", "BNB": "BNBINR",
            "SOL-USD": "SOLINR", "SOL/USD": "SOLINR", "SOLUSDT": "SOLINR", "SOL": "SOLINR",
            "XRP-USD": "XRPINR", "XRP/USD": "XRPINR", "XRPUSDT": "XRPINR", "XRP": "XRPINR",
            "ADA-USD": "ADAINR", "ADA/USD": "ADAINR", "ADAUSDT": "ADAINR", "ADA": "ADAINR",
            "DOGE-USD": "DOGEINR", "DOGE/USD": "DOGEINR", "DOGEUSDT": "DOGEINR", "DOGE": "DOGEINR",
            "AVAX-USD": "AVAXINR", "AVAX/USD": "AVAXINR", "AVAXUSDT": "AVAXINR", "AVAX": "AVAXINR",
            "MATIC-USD": "MATICINR", "MATIC/USD": "MATICINR", "MATICUSDT": "MATICINR", "MATIC": "MATICINR",
            "DOT-USD": "DOTINR", "DOT/USD": "DOTINR", "DOTUSDT": "DOTINR", "DOT": "DOTINR",
            "LINK-USD": "LINKINR", "LINK/USD": "LINKINR", "LINKUSDT": "LINKINR", "LINK": "LINKINR",
            "LTC-USD": "LTCINR", "LTC/USD": "LTCINR", "LTCUSDT": "LTCINR", "LTC": "LTCINR",
            "BCH-USD": "BCHINR", "BCH/USD": "BCHINR", "BCHUSDT": "BCHINR", "BCH": "BCHINR",
            "UNI-USD": "UNIINR", "UNI/USD": "UNIINR", "UNIUSDT": "UNIINR", "UNI": "UNIINR",
            "SHIB-USD": "SHIBINR", "SHIB/USD": "SHIBINR", "SHIBUSDT": "SHIBINR", "SHIB": "SHIBINR",
            "BTCINR": "BTCINR", "ETHINR": "ETHINR", "BNBINR": "BNBINR", "SOLINR": "SOLINR",
            "XRPINR": "XRPINR", "ADAINR": "ADAINR", "DOGEINR": "DOGEINR", "AVAXINR": "AVAXINR",
            "MATICINR": "MATICINR", "DOTINR": "DOTINR", "LINKINR": "LINKINR", "LTCINR": "LTCINR",
            "BCHINR": "BCHINR", "UNIINR": "UNIINR", "SHIBINR": "SHIBINR",
            "ETC-USD": "ETCINR", "XLM-USD": "XLMINR", "FIL-USD": "FILINR", "TRX-USD": "TRXINR", "ATOM-USD": "ATOMINR",
            "ETCINR": "ETCINR", "XLMINR": "XLMINR", "FILINR": "FILINR", "TRXINR": "TRXINR", "ATOMINR": "ATOMINR",
        }
        if sym in mapping:
            return mapping[sym]
        if sym in mapping.values():
            return sym
        if "INR" in sym:
            cleaned = sym.replace("-","").replace("/","").replace("_","").upper()
            return cleaned
        cleaned = sym.replace("-","").replace("/","").replace("_","").replace("USD","INR").replace("USDT","INR").upper()
        if not cleaned.endswith("INR"):
            cleaned = cleaned + "INR"
        return cleaned

    def _is_cache_valid(self):
        return (time.time() - self._last_fetch) < self._cache_ttl and self._last_price > 0

    def fetch_ticker_rest(self, symbol: str = None) -> Dict:
        target_market = self.coindcx_market
        if symbol:
            try:
                target_market = self._map_symbol(symbol)
            except Exception:
                target_market = self.coindcx_market

        for attempt in range(2):
            try:
                self._metrics["requests"] += 1
                resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        for ticker in data:
                            if ticker.get("market") == target_market:
                                return ticker
                        for ticker in data:
                            if ticker.get("market","").upper() == target_market.upper():
                                return ticker
                # Fallback to trade_history
                try:
                    resp2 = self._session.get(f"{self.public_url}/market_data/trade_history", params={"pair": f"I-{target_market}"}, timeout=5)
                    if resp2.status_code == 200:
                        data = resp2.json()
                        if isinstance(data, list) and len(data) > 0:
                            last = data[0]
                            price = last.get("p") or last.get("price")
                            if price:
                                return {"market": target_market, "last_price": price, "volume": last.get("q",0)}
                except Exception as e:
                    logger.debug(f"CoinDCX trade_history v5 fallback failed {target_market}: {e}")
            except requests.RequestException as e:
                logger.debug(f"CoinDCX ticker v5 fetch failed {target_market} attempt {attempt}: {e}")
                self._metrics["errors"] += 1
                if attempt < 1:
                    time.sleep(0.3)
                    continue
            except Exception as e:
                logger.debug(f"CoinDCX ticker v5 unexpected {target_market}: {e}")
                self._metrics["errors"] += 1
        return {}

    def fetch_ohlcv(self, interval: str = "1d", limit: int = 500) -> Optional[Dict]:
        """Fetch historical OHLCV from CoinDCX - v5 new"""
        try:
            # CoinDCX doesn't have direct klines, use Binance converted
            import pandas as pd
            # Map to USD for Binance
            base = self.symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
            usd_sym = base + "-USD" if len(base) >=2 else "BTC-USD"
            binance_sym = config.data.binance_map.get(usd_sym, base + "USDT")
            url = f"{config.realtime.rest_url}/api/v3/klines"
            params = {"symbol": binance_sym, "interval": interval, "limit": limit}
            resp = self._session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data, columns=[
                        "open_time", "Open", "High", "Low", "Close", "Volume",
                        "close_time", "quote_volume", "trades", "taker_buy_base",
                        "taker_buy_quote", "ignore"
                    ])
                    # Convert to INR
                    for col in ["Open","High","Low","Close"]:
                        df[col] = pd.to_numeric(df[col], errors='coerce') * 83.5
                    df["Volume"] = pd.to_numeric(df["Volume"], errors='coerce')
                    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
                    df.set_index("open_time", inplace=True)
                    return df
        except Exception as e:
            logger.debug(f"CoinDCX OHLCV v5 failed {self.coindcx_market}: {e}")
        return None

    def get_current_price(self) -> Optional[float]:
        with self._lock:
            if self._is_cache_valid():
                self._metrics["cache_hits"] += 1
                return self._last_price

        # Try CoinDCX ticker with retry
        for attempt in range(2):
            try:
                ticker = self.fetch_ticker_rest()
                price_raw = ticker.get("last_price") or ticker.get("lastPrice") or ticker.get("price") or ticker.get("last_price_inr")
                if price_raw is not None:
                    try:
                        p = float(price_raw)
                        if 0 < p < 200_000_000:
                            with self._lock:
                                self._last_price = p
                                self._last_fetch = time.time()
                                self._metrics["last_price"] = p
                            return p
                    except (ValueError, TypeError):
                        pass
            except Exception as e:
                logger.debug(f"CoinDCX price v5 parse failed {self.coindcx_market} attempt {attempt}: {e}")
                if attempt < 1:
                    time.sleep(0.2)

        # Direct Binance REST fallback
        try:
            usd_symbol = self.symbol
            if "INR" in self.symbol.upper():
                base = self.symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
                if len(base) >= 2:
                    usd_symbol = f"{base}-USD"
            binance_sym = config.data.binance_map.get(usd_symbol.upper(), usd_symbol.replace("-","").replace("/","").replace("_",""))
            resp = self._session.get(f"{config.realtime.rest_url}/api/v3/ticker/24hr", params={"symbol": binance_sym}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    lp = data.get("lastPrice")
                    if lp:
                        try:
                            binance_price = float(lp)
                            if 0 < binance_price < 10_000_000:
                                inr_price = binance_price * 83.5
                                with self._lock:
                                    self._last_price = inr_price
                                    self._last_fetch = time.time()
                                    self._metrics["last_price"] = inr_price
                                return inr_price
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.debug(f"Binance REST fallback v5 for CoinDCX failed {self.coindcx_market}: {e}")

        # Last resort: cached file
        try:
            from pathlib import Path
            import pandas as pd
            usd_sym = self.symbol
            if "INR" in usd_sym.upper():
                base = usd_sym.upper().replace("INR","")
                usd_sym = f"{base}-USD"
            cache_path = config.project_root / "data" / "raw" / f"{usd_sym.replace('-','_')}_1d.csv"
            if cache_path.exists():
                try:
                    df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    if not df.empty:
                        p = float(df['Close'].iloc[-1]) * 83.5
                        if 0 < p < 200_000_000:
                            with self._lock:
                                self._last_price = p
                                self._last_fetch = time.time()
                            return p
                except Exception:
                    pass
        except Exception:
            pass

        with self._lock:
            return self._last_price if self._last_price > 0 else None

    def get_tickers_all(self) -> Dict:
        try:
            resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                result = {}
                if isinstance(data, list):
                    for ticker in data:
                        try:
                            market = ticker.get("market","")
                            if not market or "INR" not in market:
                                continue
                            price_raw = ticker.get("last_price",0) or 0
                            try:
                                price = float(price_raw)
                            except (ValueError, TypeError):
                                continue
                            if price <= 0 or price > 200_000_000:
                                continue
                            change_raw = ticker.get("change_24_hour",0) or 0
                            try:
                                change = float(change_raw)
                            except (ValueError, TypeError):
                                change = 0.0
                            change_pct = 0.0
                            try:
                                if price > 0:
                                    change_pct = (change / price * 100) if abs(change) < price*2 else 0.0
                            except Exception:
                                change_pct = 0.0
                            high_raw = ticker.get("high",0) or 0
                            low_raw = ticker.get("low",0) or 0
                            vol_raw = ticker.get("volume",0) or 0
                            try:
                                high = float(high_raw)
                            except (ValueError, TypeError):
                                high = 0.0
                            try:
                                low = float(low_raw)
                            except (ValueError, TypeError):
                                low = 0.0
                            try:
                                vol = float(vol_raw)
                            except (ValueError, TypeError):
                                vol = 0.0
                            result[market] = {
                                "market": market,
                                "price": price,
                                "last_price": price,
                                "change": change,
                                "change_pct": change_pct,
                                "high": high,
                                "low": low,
                                "volume": vol,
                                "real_data": True,
                                "source": "CoinDCX Live INR v5",
                                "broker": "coindcx",
                                "version": "v5_max"
                            }
                        except (ValueError, TypeError):
                            continue
                        except Exception as e:
                            logger.debug(f"Ticker parse v5 failed: {e}")
                            continue
                return result
        except requests.RequestException as e:
            logger.debug(f"CoinDCX all tickers v5 network failed: {e}")
        except Exception as e:
            logger.warning(f"CoinDCX all tickers v5 failed: {e}")
        return {}

    def get_orderbook(self, symbol: str = None, limit: int = 20) -> Optional[Dict]:
        target_market = self.coindcx_market
        if symbol:
            try:
                target_market = self._map_symbol(symbol)
            except Exception:
                pass
        try:
            limit = max(5, min(100, int(limit)))
        except (ValueError, TypeError):
            limit = 20

        for attempt in range(2):
            try:
                resp = self._session.get(f"{self.public_url}/market_data/orderbook", params={"pair": f"I-{target_market}"}, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                        bids = data.get("bids",[])[:limit]
                        asks = data.get("asks",[])[:limit]
                        valid_bids=[]
                        valid_asks=[]
                        for b in bids:
                            try:
                                if len(b) >= 2:
                                    p = float(b[0]); q = float(b[1])
                                    if p > 0 and q > 0 and p < 200_000_000:
                                        valid_bids.append([p,q])
                            except (ValueError, TypeError, IndexError):
                                continue
                        for a in asks:
                            try:
                                if len(a) >= 2:
                                    p = float(a[0]); q = float(a[1])
                                    if p > 0 and q > 0 and p < 200_000_000:
                                        valid_asks.append([p,q])
                            except (ValueError, TypeError, IndexError):
                                continue
                        if valid_bids and valid_asks:
                            return {"bids": valid_bids, "asks": valid_asks, "market": target_market, "source": "CoinDCX v5", "version": "v5_max"}
            except requests.RequestException as e:
                logger.debug(f"CoinDCX orderbook v5 network failed {target_market} attempt {attempt}: {e}")
                if attempt < 1:
                    time.sleep(0.2)
                    continue
            except Exception as e:
                logger.debug(f"CoinDCX orderbook v5 failed {target_market}: {e}")

        # Fallback Binance with INR conversion
        try:
            usd_symbol = self.symbol
            if symbol:
                usd_symbol = symbol
            if "INR" in usd_symbol.upper():
                base = usd_symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
                if len(base) >= 2:
                    usd_symbol = f"{base}-USD"
            binance_sym = config.data.binance_map.get(usd_symbol.upper(), usd_symbol.replace("-","").replace("/","").replace("_",""))
            resp = self._session.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                ob = resp.json()
                if isinstance(ob, dict) and 'bids' in ob and 'asks' in ob:
                    inr_rate = 83.5
                    bids=[]
                    asks=[]
                    for p,q in ob.get("bids",[])[:limit]:
                        try:
                            pf = float(p); qf = float(q)
                            if pf > 0 and qf > 0:
                                bids.append([pf*inr_rate, qf])
                        except (ValueError, TypeError):
                            continue
                    for p,q in ob.get("asks",[])[:limit]:
                        try:
                            pf = float(p); qf = float(q)
                            if pf > 0 and qf > 0:
                                asks.append([pf*inr_rate, qf])
                        except (ValueError, TypeError):
                            continue
                    if bids and asks:
                        return {"bids": bids, "asks": asks, "market": target_market, "source": "Binance v5 converted to INR", "version": "v5_max"}
        except Exception as e:
            logger.debug(f"Binance orderbook fallback v5 for CoinDCX failed {target_market}: {e}")
        return None

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "market": self.coindcx_market, "symbol": self.symbol, "version": "v5_max"}

# Global cache
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
    except Exception as e:
        logger.debug(f"CoinDCX cached v5 fetch failed: {e}")
        with _coindcx_cache_lock:
            return _coindcx_tickers_cache["data"] or {}

def get_coindcx_price(symbol: str) -> float:
    try:
        fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
        price = fetcher.get_current_price()
        return price or 0.0
    except Exception:
        return 0.0
