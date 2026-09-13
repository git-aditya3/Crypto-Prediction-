"""
CoinDCX Data Fetcher - Real INR market data from CoinDCX
Fixed: signature compatibility, circular fallback avoidance, comprehensive mapping, validation
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
    def __init__(self, symbol: str = "BTC-USD"):
        self.symbol = symbol
        self.coindcx_market = self._map_symbol(symbol)
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        self._last_price = 0.0
        self._last_fetch = 0
        self._cache_ttl = 5
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "CoinDCXFetcher/1.0 Real Trading"})
        self._lock = threading.Lock()

    def _map_symbol(self, symbol: str) -> str:
        """Comprehensive mapping to CoinDCX INR markets"""
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
        }
        if sym in mapping:
            return mapping[sym]
        if sym in mapping.values():
            return sym
        if "INR" in sym:
            cleaned = sym.replace("-", "").replace("/", "").replace("_", "").upper()
            return cleaned
        # Default: replace USD with INR
        cleaned = sym.replace("-", "").replace("/", "").replace("_", "").replace("USD", "INR").replace("USDT", "INR").upper()
        # Ensure ends with INR
        if not cleaned.endswith("INR"):
            cleaned = cleaned + "INR"
        return cleaned

    def _is_cache_valid(self):
        return (time.time() - self._last_fetch) < self._cache_ttl and self._last_price > 0

    def fetch_ticker_rest(self, symbol: str = None) -> Dict:
        """Fetch ticker from CoinDCX public API - supports optional symbol param for API compatibility"""
        target_market = self.coindcx_market
        if symbol:
            try:
                target_market = self._map_symbol(symbol)
            except Exception:
                target_market = self.coindcx_market

        try:
            resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for ticker in data:
                        if ticker.get("market") == target_market:
                            return ticker
                    # If not found, try case-insensitive
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
                logger.debug(f"CoinDCX trade_history fallback failed {target_market}: {e}")
        except requests.RequestException as e:
            logger.debug(f"CoinDCX ticker fetch failed {target_market}: {e}")
        except Exception as e:
            logger.debug(f"CoinDCX ticker unexpected {target_market}: {e}")
        return {}

    def get_current_price(self) -> Optional[float]:
        """Get current price - real CoinDCX INR, with direct Binance REST fallback (no circular via BinanceRealtimeFetcher)"""
        with self._lock:
            if self._is_cache_valid():
                return self._last_price

        # Try CoinDCX ticker
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
                        return p
                except (ValueError, TypeError):
                    pass
        except Exception as e:
            logger.debug(f"CoinDCX price parse failed {self.coindcx_market}: {e}")

        # Direct Binance REST fallback (avoid circular via BinanceRealtimeFetcher.get_current_price)
        try:
            usd_symbol = self.symbol
            if "INR" in self.symbol.upper():
                base = self.symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
                if len(base) >= 2:
                    usd_symbol = f"{base}-USD"
            binance_sym = config.data.binance_map.get(usd_symbol.upper(), usd_symbol.replace("-","").replace("/","").replace("_",""))
            # Direct REST call, not via fetcher class
            resp = requests.get(f"{config.realtime.rest_url}/api/v3/ticker/24hr", params={"symbol": binance_sym}, timeout=3)
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
                                logger.debug(f"CoinDCX fallback Binance {usd_symbol} ${binance_price} -> ₹{inr_price:.2f}")
                                return inr_price
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.debug(f"Binance REST fallback for CoinDCX failed {self.coindcx_market}: {e}")

        # Last resort: cached file directly
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
                                "source": "CoinDCX Live INR",
                                "broker": "coindcx"
                            }
                        except (ValueError, TypeError):
                            continue
                        except Exception as e:
                            logger.debug(f"Ticker parse failed: {e}")
                            continue
                return result
        except requests.RequestException as e:
            logger.debug(f"CoinDCX all tickers network failed: {e}")
        except Exception as e:
            logger.warning(f"CoinDCX all tickers failed: {e}")
        return {}

    def get_orderbook(self, symbol: str = None, limit: int = 20) -> Optional[Dict]:
        """CoinDCX orderbook - supports symbol param for compatibility, else uses self.symbol"""
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

        try:
            resp = self._session.get(f"{self.public_url}/market_data/orderbook", params={"pair": f"I-{target_market}"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    # Validate
                    bids = data.get("bids",[])[:limit]
                    asks = data.get("asks",[])[:limit]
                    # Ensure valid numbers
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
                        return {"bids": valid_bids, "asks": valid_asks, "market": target_market, "source": "CoinDCX"}
        except requests.RequestException as e:
            logger.debug(f"CoinDCX orderbook network failed {target_market}: {e}")
        except Exception as e:
            logger.debug(f"CoinDCX orderbook failed {target_market}: {e}")

        # Fallback to Binance orderbook with INR conversion - direct REST, no circular via fetcher class
        try:
            usd_symbol = self.symbol
            if symbol:
                usd_symbol = symbol
            if "INR" in usd_symbol.upper():
                base = usd_symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
                if len(base) >= 2:
                    usd_symbol = f"{base}-USD"
            binance_sym = config.data.binance_map.get(usd_symbol.upper(), usd_symbol.replace("-","").replace("/","").replace("_",""))
            resp = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
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
                        return {"bids": bids, "asks": asks, "market": target_market, "source": "Binance converted to INR"}
        except requests.RequestException as e:
            logger.debug(f"Binance orderbook fallback network failed {target_market}: {e}")
        except Exception as e:
            logger.debug(f"Binance orderbook fallback for CoinDCX failed {target_market}: {e}")
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
    except Exception as e:
        logger.debug(f"CoinDCX cached fetch failed: {e}")
        with _coindcx_cache_lock:
            return _coindcx_tickers_cache["data"] or {}
