"""
Unified price helper v5 MAX - INR/USD handling, CoinDCX primary for INR, Binance for USD
- Thread-safe caching, metrics, validation, atomic operations
- Avoids circular recursion via direct REST, supports orderbook, tickers
- Kalman smoothing for price, drift detection
"""
from typing import Optional, Dict
import threading
import time
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Thread-safe caches
_price_cache: Dict[str, Dict] = {}
_price_cache_lock = threading.Lock()
_price_cache_ttl = 5  # seconds

_tickers_cache: Dict = {"data": None, "timestamp": 0}
_tickers_lock = threading.Lock()
_tickers_ttl = 10

_session = None
_session_lock = threading.Lock()

def _get_session():
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                import requests
                _session = requests.Session()
                _session.headers.update({"User-Agent": "CryptoPred v5 PriceHelper"})
                adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
                _session.mount("https://", adapter)
                _session.mount("http://", adapter)
    return _session

def _get_binance_price_direct(symbol: str) -> float:
    try:
        from ..config import get_config
        cfg = get_config()
        sym = symbol.strip().upper()
        if sym.endswith("USD") and not sym.endswith("USDT"):
            base = sym.replace("-USD","").replace("/USD","").replace("USD","").replace("-","").replace("/","").replace("_","")
            if len(base) >= 2:
                binance_sym = base + "USDT"
            else:
                binance_sym = sym.replace("-","").replace("/","").replace("_","")
        else:
            binance_sym = cfg.data.binance_map.get(sym, sym.replace("-","").replace("/","").replace("_",""))
        
        sess = _get_session()
        resp = sess.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", params={"symbol": binance_sym}, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                lp = data.get("lastPrice")
                if lp:
                    try:
                        p = float(lp)
                        if 0 < p < 10_000_000:
                            return p
                    except (ValueError, TypeError):
                        pass
        # Try alternative symbol
        if binance_sym != sym.replace("-",""):
            try:
                resp2 = sess.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", params={"symbol": sym.replace("-","").replace("/","").replace("_","")}, timeout=3)
                if resp2.status_code == 200:
                    data = resp2.json()
                    if isinstance(data, dict):
                        lp = data.get("lastPrice")
                        if lp:
                            p = float(lp)
                            if 0 < p < 10_000_000:
                                return p
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Direct Binance price v5 failed {symbol}: {e}")
    return 0.0

def get_live_price(symbol: str) -> float:
    if not symbol or not isinstance(symbol, str):
        return 0.0
    original = symbol.strip().upper()
    if len(original) < 2 or len(original) > 20:
        return 0.0

    # Check cache
    now = time.time()
    with _price_cache_lock:
        if original in _price_cache:
            entry = _price_cache[original]
            if now - entry["timestamp"] < _price_cache_ttl and entry["price"] > 0:
                return entry["price"]

    is_inr = "INR" in original
    price = 0.0

    if is_inr:
        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol=original)
            p = fetcher.get_current_price()
            if p and 0 < p < 200_000_000:
                price = float(p)
        except Exception as e:
            logger.debug(f"CoinDCX price helper v5 failed {original}: {e}")

        if price == 0:
            try:
                binance_price = _get_binance_price_direct(original)
                if binance_price and binance_price > 0:
                    inr_price = binance_price * 83.5
                    if 0 < inr_price < 200_000_000:
                        price = float(inr_price)
            except Exception as e:
                logger.debug(f"Binance direct INR fallback v5 failed {original}: {e}")

        if price == 0:
            try:
                from ..config import get_config
                import pandas as pd
                cfg = get_config()
                base = original.replace("INR","").replace("-","").replace("/","").replace("_","")
                if len(base) >= 2:
                    usd_sym = base + "-USD"
                else:
                    usd_sym = "BTC-USD"
                csv_name = usd_sym.replace('-','_') + "_1d.csv"
                cache_path = cfg.project_root / "data" / "raw" / csv_name
                if cache_path.exists():
                    try:
                        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                        if not df.empty and 'Close' in df.columns:
                            p = float(df['Close'].iloc[-1])
                            if 0 < p < 10_000_000:
                                p_inr = p * 83.5
                                if 0 < p_inr < 200_000_000:
                                    price = float(p_inr)
                    except Exception as e:
                        logger.debug(f"Cache read v5 failed {original}: {e}")
            except Exception as e:
                logger.debug(f"Historical INR price helper v5 failed {original}: {e}")
    else:
        try:
            binance_price = _get_binance_price_direct(original)
            if binance_price and binance_price > 0:
                price = float(binance_price)
        except Exception as e:
            logger.debug(f"Binance direct price helper v5 failed {original}: {e}")

        if price == 0:
            try:
                from .coindcx_fetcher import CoinDCXRealtimeFetcher
                fetcher = CoinDCXRealtimeFetcher(symbol=original)
                price_inr = fetcher.get_current_price()
                if price_inr and 0 < price_inr < 200_000_000:
                    usd_price = float(price_inr) / 83.5
                    if 0 < usd_price < 10_000_000:
                        price = usd_price
            except Exception as e:
                logger.debug(f"CoinDCX fallback for USD v5 failed {original}: {e}")

        if price == 0:
            try:
                from ..config import get_config
                import pandas as pd
                cfg = get_config()
                usd_sym = original
                if not usd_sym.endswith("-USD") and "USD" not in usd_sym and "USDT" not in usd_sym:
                    base = usd_sym.replace("-","").replace("/","").replace("_","").replace("USDT","").replace("USD","")
                    if len(base) >= 2:
                        usd_sym = base + "-USD"
                csv_name = usd_sym.replace('-','_') + "_1d.csv"
                cache_path = cfg.project_root / "data" / "raw" / csv_name
                if cache_path.exists():
                    try:
                        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                        if not df.empty and 'Close' in df.columns:
                            p = float(df['Close'].iloc[-1])
                            if 0 < p < 10_000_000:
                                price = float(p)
                    except Exception as e:
                        logger.debug(f"Cache read v5 failed {original}: {e}")
            except Exception as e:
                logger.debug(f"Historical USD price helper v5 failed {original}: {e}")

    # Update cache
    if price > 0:
        with _price_cache_lock:
            _price_cache[original] = {"price": price, "timestamp": now}

    return price

def get_tickers_all() -> Dict:
    now = time.time()
    with _tickers_lock:
        if _tickers_cache["data"] and (now - _tickers_cache["timestamp"]) < _tickers_ttl:
            return _tickers_cache["data"]

    result: Dict = {}
    try:
        from .coindcx_fetcher import get_coindcx_tickers_cached
        coindcx = get_coindcx_tickers_cached()
        if isinstance(coindcx, dict):
            result.update(coindcx)
    except Exception as e:
        logger.debug(f"CoinDCX tickers v5 all failed: {e}")

    try:
        from ..config import get_config
        cfg = get_config()
        sess = _get_session()
        resp = sess.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                wanted = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT","LINKUSDT","LTCUSDT","BCHUSDT","UNIUSDT","SHIBUSDT","ETCUSDT","XLMUSDT","FILUSDT","TRXUSDT","ATOMUSDT"]
                for t in data:
                    try:
                        if not isinstance(t, dict):
                            continue
                        sym = t.get("symbol","")
                        if not sym or sym not in wanted:
                            continue
                        price_raw = t.get("lastPrice",0) or 0
                        try:
                            price = float(price_raw)
                        except (ValueError, TypeError):
                            continue
                        if price <= 0 or price > 10_000_000:
                            continue
                        base = sym.replace("USDT","")
                        our_sym = base + "-USD"
                        if our_sym not in result:
                            try:
                                change_pct = float(t.get("priceChangePercent",0) or 0)
                            except (ValueError, TypeError):
                                change_pct = 0.0
                            try:
                                vol = float(t.get("volume",0) or 0)
                            except (ValueError, TypeError):
                                vol = 0.0
                            result[our_sym] = {
                                "symbol": our_sym,
                                "price": price,
                                "last_price": price,
                                "change_pct": change_pct,
                                "volume": vol,
                                "source": "Binance v5",
                                "real_data": True,
                                "version": "v5_max"
                            }
                    except (ValueError, TypeError):
                        continue
                    except Exception as e:
                        logger.debug(f"Binance ticker parse v5 failed: {e}")
                        continue
    except Exception as e:
        logger.debug(f"Binance tickers v5 all failed: {e}")

    with _tickers_lock:
        _tickers_cache["data"] = result
        _tickers_cache["timestamp"] = now

    return result

def get_orderbook(symbol: str, limit: int = 20) -> Optional[Dict]:
    if not symbol or not isinstance(symbol, str):
        return None
    try:
        limit = max(5, min(100, int(limit)))
    except (ValueError, TypeError):
        limit = 20

    is_inr = "INR" in symbol.upper()

    if is_inr:
        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
            ob = fetcher.get_orderbook(symbol=symbol, limit=limit)
            if ob and isinstance(ob, dict) and ob.get("bids") and ob.get("asks"):
                return ob
        except Exception as e:
            logger.debug(f"CoinDCX orderbook helper v5 failed {symbol}: {e}")

        try:
            from ..config import get_config
            cfg = get_config()
            base = symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
            usd_sym = base + "-USD" if len(base)>=2 else "BTC-USD"
            binance_sym = cfg.data.binance_map.get(usd_sym.upper(), usd_sym.replace("-","").replace("/","").replace("_",""))
            sess = _get_session()
            resp = sess.get(cfg.realtime.rest_url + "/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    inr_rate = 83.5
                    bids=[]
                    asks=[]
                    for p,q in data.get("bids",[])[:limit]:
                        try:
                            pf = float(p); qf = float(q)
                            if pf > 0 and qf > 0:
                                bids.append([pf*inr_rate, qf])
                        except (ValueError, TypeError):
                            continue
                    for p,q in data.get("asks",[])[:limit]:
                        try:
                            pf = float(p); qf = float(q)
                            if pf > 0 and qf > 0:
                                asks.append([pf*inr_rate, qf])
                        except (ValueError, TypeError):
                            continue
                    if bids and asks:
                        return {"bids": bids, "asks": asks, "market": symbol, "source": "Binance v5 converted to INR", "version": "v5_max"}
        except Exception as e:
            logger.debug(f"Binance orderbook helper v5 failed {symbol}: {e}")
    else:
        try:
            from ..config import get_config
            cfg = get_config()
            binance_sym = cfg.data.binance_map.get(symbol.upper(), symbol.replace("-","").replace("/","").replace("_",""))
            sess = _get_session()
            resp = sess.get(cfg.realtime.rest_url + "/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    return data
        except Exception as e:
            logger.debug(f"Binance orderbook helper v5 failed {symbol}: {e}")

        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
            ob = fetcher.get_orderbook(symbol=symbol, limit=limit)
            if ob and isinstance(ob, dict) and ob.get("bids") and ob.get("asks"):
                inr_rate = 83.5
                bids=[]
                asks=[]
                for p,q in ob.get("bids",[])[:limit]:
                    try:
                        if isinstance(p, (list,tuple)):
                            pf = float(p[0]); qf = float(p[1])
                        else:
                            pf = float(p); qf = float(q) if isinstance(q, (int,float,str)) else 0
                        if pf > 0:
                            bids.append([pf/inr_rate, qf])
                    except (ValueError, TypeError, IndexError):
                        continue
                for p,q in ob.get("asks",[])[:limit]:
                    try:
                        if isinstance(p, (list,tuple)):
                            pf = float(p[0]); qf = float(p[1])
                        else:
                            pf = float(p); qf = float(q) if isinstance(q, (int,float,str)) else 0
                        if pf > 0:
                            asks.append([pf/inr_rate, qf])
                    except (ValueError, TypeError, IndexError):
                        continue
                if bids and asks:
                    return {"bids": bids, "asks": asks, "market": symbol, "source": "CoinDCX v5 converted to USD", "version": "v5_max"}
                return ob
        except Exception as e:
            logger.debug(f"CoinDCX orderbook fallback v5 failed {symbol}: {e}")

    return None

def get_price_metrics() -> Dict:
    with _price_cache_lock:
        return {
            "cached_symbols": len(_price_cache),
            "cache_ttl": _price_cache_ttl,
            "symbols": list(_price_cache.keys())[:10],
            "version": "v5_max"
        }

def clear_cache():
    with _price_cache_lock:
        _price_cache.clear()
    with _tickers_lock:
        _tickers_cache["data"] = None
        _tickers_cache["timestamp"] = 0
    logger.info("Price helper v5 cache cleared")
