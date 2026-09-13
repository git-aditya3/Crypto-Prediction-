"""
Unified price helper - respects INR vs USD symbols
- INR symbols: CoinDCX primary, Binance fallback converted to INR
- USD/USDT symbols: Binance primary, CoinDCX fallback converted to USD
Fixed: avoids circular recursion, direct REST calls, validation
"""
from typing import Optional, Dict
from ..utils.logger import get_logger

logger = get_logger(__name__)

def _get_binance_price_direct(symbol: str) -> float:
    try:
        from ..config import get_config
        import requests
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
        resp = requests.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", params={"symbol": binance_sym}, timeout=3)
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
        if binance_sym != sym.replace("-",""):
            try:
                resp2 = requests.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", params={"symbol": sym.replace("-","").replace("/","").replace("_","")}, timeout=3)
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
        logger.debug(f"Direct Binance price failed {symbol}: {e}")
    return 0.0

def get_live_price(symbol: str) -> float:
    if not symbol or not isinstance(symbol, str):
        return 0.0
    original = symbol.strip().upper()
    if len(original) < 2 or len(original) > 20:
        return 0.0

    is_inr = "INR" in original

    if is_inr:
        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol=original)
            price = fetcher.get_current_price()
            if price and 0 < price < 200_000_000:
                return float(price)
        except Exception as e:
            logger.debug(f"CoinDCX price helper failed {original}: {e}")

        try:
            binance_price = _get_binance_price_direct(original)
            if binance_price and binance_price > 0:
                inr_price = binance_price * 83.5
                if 0 < inr_price < 200_000_000:
                    return float(inr_price)
        except Exception as e:
            logger.debug(f"Binance direct INR fallback failed {original}: {e}")

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
                                return float(p_inr)
                except Exception as e:
                    logger.debug(f"Cache read failed {original}: {e}")
        except Exception as e:
            logger.debug(f"Historical INR price helper failed {original}: {e}")

        return 0.0
    else:
        try:
            binance_price = _get_binance_price_direct(original)
            if binance_price and binance_price > 0:
                return float(binance_price)
        except Exception as e:
            logger.debug(f"Binance direct price helper failed {original}: {e}")

        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol=original)
            price_inr = fetcher.get_current_price()
            if price_inr and 0 < price_inr < 200_000_000:
                usd_price = float(price_inr) / 83.5
                if 0 < usd_price < 10_000_000:
                    return usd_price
        except Exception as e:
            logger.debug(f"CoinDCX fallback for USD failed {original}: {e}")

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
                            return float(p)
                except Exception as e:
                    logger.debug(f"Cache read failed {original}: {e}")
        except Exception as e:
            logger.debug(f"Historical USD price helper failed {original}: {e}")

        return 0.0

def get_tickers_all() -> Dict:
    result: Dict = {}
    try:
        from .coindcx_fetcher import get_coindcx_tickers_cached
        coindcx = get_coindcx_tickers_cached()
        if isinstance(coindcx, dict):
            result.update(coindcx)
    except Exception as e:
        logger.debug(f"CoinDCX tickers all failed: {e}")

    try:
        from ..config import get_config
        import requests
        cfg = get_config()
        resp = requests.get(cfg.realtime.rest_url + "/api/v3/ticker/24hr", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                for t in data[:60]:
                    try:
                        if not isinstance(t, dict):
                            continue
                        sym = t.get("symbol","")
                        if not sym or not isinstance(sym, str) or not sym.endswith("USDT"):
                            continue
                        if sym not in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT","LINKUSDT","LTCUSDT","BCHUSDT","UNIUSDT","SHIBUSDT","ETCUSDT","XLMUSDT","FILUSDT","TRXUSDT","ATOMUSDT"]:
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
                                "source": "Binance",
                                "real_data": True
                            }
                    except (ValueError, TypeError):
                        continue
                    except Exception as e:
                        logger.debug(f"Binance ticker parse failed: {e}")
                        continue
    except requests.RequestException as e:
        logger.debug(f"Binance tickers network failed: {e}")
    except Exception as e:
        logger.debug(f"Binance tickers all failed: {e}")

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
            logger.debug(f"CoinDCX orderbook helper failed {symbol}: {e}")

        try:
            from ..config import get_config
            import requests
            cfg = get_config()
            base = symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
            usd_sym = base + "-USD" if len(base)>=2 else "BTC-USD"
            binance_sym = cfg.data.binance_map.get(usd_sym.upper(), usd_sym.replace("-","").replace("/","").replace("_",""))
            resp = requests.get(cfg.realtime.rest_url + "/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
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
                        return {"bids": bids, "asks": asks, "market": symbol, "source": "Binance converted to INR"}
        except requests.RequestException as e:
            logger.debug(f"Binance orderbook helper network failed {symbol}: {e}")
        except Exception as e:
            logger.debug(f"Binance orderbook helper failed {symbol}: {e}")
    else:
        try:
            from ..config import get_config
            import requests
            cfg = get_config()
            binance_sym = cfg.data.binance_map.get(symbol.upper(), symbol.replace("-","").replace("/","").replace("_",""))
            resp = requests.get(cfg.realtime.rest_url + "/api/v3/depth", params={"symbol": binance_sym, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    return data
        except Exception as e:
            logger.debug(f"Binance orderbook helper failed {symbol}: {e}")

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
                    return {"bids": bids, "asks": asks, "market": symbol, "source": "CoinDCX converted to USD"}
                return ob
        except Exception as e:
            logger.debug(f"CoinDCX orderbook fallback failed {symbol}: {e}")

    return None
