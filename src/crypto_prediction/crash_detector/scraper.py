"""
Fast Local Webscraper v5 MAX for Crash Detection - CoinDCX INR + Binance + Metrics
- Parallel fetching 12 workers, rate limiting, exponential backoff, validation
- Sources: spot, futures, funding, OI, orderbook, trades, liquidations, fear&greed, Reddit, news, CoinDCX INR
- Thread-safe caching, data quality scoring, metrics, fallback logic
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import xml.etree.ElementTree as ET
import random
import threading

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FAPI = "https://fapi.binance.com"
FNG_URL = "https://api.alternative.me/fng/?limit=7&format=json"
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/hot.json"
COINDESK_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"
COINGECKO_URL = "https://api.coingecko.com/api/v3/global"

_session = None
_session_lock = threading.Lock()
_last_request_time = 0
_last_request_lock = threading.Lock()
_min_interval = 0.03  # Faster for v5

def get_session():
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                _session = requests.Session()
                _session.headers.update({
                    "User-Agent": "Mozilla/5.0 (CrashDetector v5 MAX) Fast Scraper CoinDCX",
                    "Accept": "application/json",
                })
                adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=60, max_retries=0)
                _session.mount("https://", adapter)
                _session.mount("http://", adapter)
    return _session

def rate_limit():
    global _last_request_time
    with _last_request_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < _min_interval:
            time.sleep(_min_interval - elapsed)
        _last_request_time = time.time()

def fetch_json(url: str, params: Optional[Dict]=None, timeout: float=3.0, retries: int=2) -> Optional[Dict]:
    for attempt in range(retries+1):
        try:
            rate_limit()
            sess = get_session()
            resp = sess.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except (ValueError, TypeError):
                    return None
            elif resp.status_code == 429:
                time.sleep(0.5 + random.random()*0.5)
                continue
            elif resp.status_code >= 500:
                if attempt < retries:
                    time.sleep(0.3 * (attempt+1))
                    continue
                return None
            else:
                return None
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(0.2 * (attempt+1))
                continue
            return None
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                time.sleep(0.3 * (attempt+1))
                continue
            return None
        except Exception:
            return None
    return None

def fetch_text(url: str, timeout: float=3.0, retries: int=1) -> Optional[str]:
    for attempt in range(retries+1):
        try:
            rate_limit()
            sess = get_session()
            resp = sess.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (compatible; CrashDetector v5 MAX/1.0)"})
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                time.sleep(0.5)
                continue
        except Exception:
            if attempt < retries:
                time.sleep(0.2)
                continue
            return None
    return None

@dataclass
class ScrapedData:
    timestamp: str
    spot_tickers: Dict
    futures_tickers: Dict
    funding_rates: List
    open_interest: Dict
    orderbooks: Dict
    liquidations: Dict
    recent_trades: Dict
    fear_greed: Dict
    reddit_posts: List
    news_titles: List
    coindcx_tickers: Dict
    fetch_time_ms: float
    errors: List[str]
    data_quality: float
    version: str = "v5_max"
    metrics: Dict = field(default_factory=dict)

class FastScraper:
    def __init__(self, max_workers: int = 16):
        self.max_workers = max_workers
        self._last_fetch = 0
        self._cache = None
        self._cache_ttl = 20  # Faster for v5
        self._last_successful: Optional[ScrapedData] = None
        self._lock = threading.Lock()
        self._metrics = {
            "total_fetches": 0,
            "cache_hits": 0,
            "avg_fetch_time_ms": 0,
            "data_quality_avg": 0
        }

    def _is_cache_valid(self):
        with self._lock:
            return self._cache and (time.time() - self._last_fetch) < self._cache_ttl

    def fetch_spot_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/ticker/24hr", timeout=4, retries=2)
        if not data or not isinstance(data, list):
            with self._lock:
                if self._last_successful and self._last_successful.spot_tickers:
                    return dict(self._last_successful.spot_tickers)
            return {}
        wanted = {"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT","LTCUSDT","LINKUSDT","UNIUSDT","ETCUSDT","XLMUSDT","BCHUSDT","FILUSDT","TRXUSDT","ATOMUSDT","SHIBUSDT"}
        result = {}
        for t in data:
            try:
                if not isinstance(t, dict):
                    continue
                sym = t.get("symbol","")
                if not sym or sym not in wanted:
                    continue
                try:
                    price = float(t.get("lastPrice",0) or 0)
                except (ValueError, TypeError):
                    continue
                if price <= 0 or price > 10_000_000:
                    continue
                try:
                    change_pct = float(t.get("priceChangePercent",0) or 0)
                    change = float(t.get("priceChange",0) or 0)
                    high = float(t.get("highPrice",0) or 0)
                    low = float(t.get("lowPrice",0) or 0)
                    vol = float(t.get("volume",0) or 0)
                    quote_vol = float(t.get("quoteVolume",0) or 0)
                    count = int(t.get("count",0) or 0)
                except (ValueError, TypeError):
                    change_pct = 0.0
                    change = 0.0
                    high = 0.0
                    low = 0.0
                    vol = 0.0
                    quote_vol = 0.0
                    count = 0

                result[sym] = {
                    "symbol": sym,
                    "price": price,
                    "change_pct": change_pct,
                    "change": change,
                    "high": high,
                    "low": low,
                    "volume": vol,
                    "quote_vol": quote_vol,
                    "count": count,
                    "source": "Binance v5",
                    "real_data": True,
                    "version": "v5_max"
                }
            except Exception:
                continue
        return result

    def fetch_futures_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr", timeout=4, retries=2)
        if not data or not isinstance(data, list):
            return {}
        result = {}
        for t in data[:80]:
            try:
                if not isinstance(t, dict):
                    continue
                sym = t.get("symbol","")
                if not sym or "USDT" not in sym or len(sym) > 12:
                    continue
                try:
                    price = float(t.get("lastPrice",0) or 0)
                except (ValueError, TypeError):
                    continue
                if price <= 0 or price > 10_000_000:
                    continue
                try:
                    change_pct = float(t.get("priceChangePercent",0) or 0)
                    vol = float(t.get("volume",0) or 0)
                    quote_vol = float(t.get("quoteVolume",0) or 0)
                except (ValueError, TypeError):
                    change_pct = 0.0
                    vol = 0.0
                    quote_vol = 0.0
                result[sym] = {
                    "symbol": sym,
                    "price": price,
                    "change_pct": change_pct,
                    "volume": vol,
                    "quote_vol": quote_vol,
                    "source": "Binance Futures v5",
                    "real_data": True,
                    "version": "v5_max"
                }
            except Exception:
                continue
        return result

    def fetch_funding_rates(self, limit: int=30) -> List:
        try:
            limit = max(1, min(100, int(limit)))
        except (ValueError, TypeError):
            limit = 30
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/fundingRate", params={"limit": limit}, timeout=3, retries=2)
        if data and isinstance(data, list) and len(data) > 0:
            return data
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", timeout=3, retries=2)
        if isinstance(data, list):
            out=[]
            for d in data[:30]:
                try:
                    if not isinstance(d, dict):
                        continue
                    rate = d.get("lastFundingRate")
                    if rate is None:
                        continue
                    try:
                        rate_f = float(rate)
                    except (ValueError, TypeError):
                        continue
                    out.append({"symbol": d.get("symbol"), "fundingRate": rate_f, "time": d.get("nextFundingTime"), "version": "v5_max"})
                except Exception:
                    continue
            return out
        return []

    def fetch_open_interest(self, symbol: str="BTCUSDT") -> Dict:
        if not symbol or not isinstance(symbol, str):
            symbol = "BTCUSDT"
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/openInterest", params={"symbol": symbol}, timeout=2, retries=1)
        if data and isinstance(data, dict):
            try:
                oi_raw = data.get("openInterest",0) or 0
                oi = float(oi_raw)
                if oi > 0 and oi < 1e12:
                    return {"symbol": symbol, "oi": oi, "time": data.get("time",0), "source": "Binance v5", "version": "v5_max"}
            except (ValueError, TypeError):
                pass
        return {"symbol": symbol, "oi": 0, "time": 0, "source": "Binance v5", "version": "v5_max"}

    def fetch_open_interest_multi(self, symbols: List[str]) -> Dict:
        results={}
        if not symbols or not isinstance(symbols, list):
            return results
        valid_symbols = []
        for s in symbols:
            if isinstance(s, str) and 6 <= len(s) <= 12:
                valid_symbols.append(s.upper())
        if not valid_symbols:
            return results
        with ThreadPoolExecutor(max_workers=min(10, len(valid_symbols))) as ex:
            futs={ex.submit(self.fetch_open_interest, s): s for s in valid_symbols}
            for f in as_completed(futs):
                try:
                    r=f.result(timeout=3)
                    if r and isinstance(r, dict) and r.get("oi",0) > 0:
                        results[r["symbol"]]=r
                except Exception:
                    continue
        return results

    def fetch_orderbook(self, symbol: str="BTCUSDT", limit: int=20) -> Dict:
        if not symbol or not isinstance(symbol, str):
            symbol = "BTCUSDT"
        try:
            limit = max(5, min(100, int(limit)))
        except (ValueError, TypeError):
            limit = 20
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/depth", params={"symbol": symbol, "limit": limit}, timeout=2, retries=1)
        if not data or not isinstance(data, dict):
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0, "mid":0, "error": True, "version": "v5_max"}
        try:
            bids_raw = data.get("bids",[])[:limit]
            asks_raw = data.get("asks",[])[:limit]
            bids = []
            asks = []
            bid_vol = 0.0
            ask_vol = 0.0
            for p,q in bids_raw:
                try:
                    pf=float(p); qf=float(q)
                    if pf>0 and qf>0 and pf < 10_000_000:
                        bids.append([pf,qf])
                        bid_vol+=qf
                except Exception:
                    continue
            for p,q in asks_raw:
                try:
                    pf=float(p); qf=float(q)
                    if pf>0 and qf>0 and pf < 10_000_000:
                        asks.append([pf,qf])
                        ask_vol+=qf
                except Exception:
                    continue
            total = bid_vol+ask_vol
            imb = (bid_vol-ask_vol)/total if total>0 else 0
            imb = max(-1.0, min(1.0, imb))
            mid = (bids[0][0]+asks[0][0])/2 if bids and asks else 0
            if mid <= 0 or mid > 10_000_000:
                mid = 0
            return {"symbol": symbol, "bids": bids, "asks": asks, "bid_vol": bid_vol, "ask_vol": ask_vol, "imbalance": imb, "mid": mid, "source": "Binance v5", "version": "v5_max"}
        except Exception:
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0, "mid":0, "error": True, "version": "v5_max"}

    def fetch_recent_trades(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        if not symbol or not isinstance(symbol, str):
            symbol = "BTCUSDT"
        try:
            limit = max(1, min(1000, int(limit)))
        except (ValueError, TypeError):
            limit = 100
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/trades", params={"symbol": symbol, "limit": limit}, timeout=2, retries=1)
        if not isinstance(data, list):
            return {"symbol": symbol, "trades": [], "sell_vol":0, "buy_vol":0, "whale_sells":0, "sell_ratio":0.5, "source": "Binance v5", "version": "v5_max"}
        sell_vol=0.0
        buy_vol=0.0
        whale_sells=0
        trades=[]
        try:
            for t in data:
                try:
                    if not isinstance(t, dict):
                        continue
                    price_raw = t.get("price",0) or 0
                    qty_raw = t.get("qty",0) or 0
                    try:
                        price=float(price_raw)
                        qty=float(qty_raw)
                    except (ValueError, TypeError):
                        continue
                    if price<=0 or qty<=0 or price > 10_000_000:
                        continue
                    is_buyer_maker=t.get("isBuyerMaker", False)
                    val=price*qty
                    if val <= 0 or val > 1e9:
                        continue
                    if is_buyer_maker:
                        sell_vol+=val
                        if val>50000:
                            whale_sells+=1
                    else:
                        buy_vol+=val
                    if len(trades)<20:
                        trades.append({"p":price,"q":qty,"v":val,"sell":bool(is_buyer_maker)})
                except Exception:
                    continue
        except Exception:
            pass
        total = sell_vol+buy_vol
        ratio = sell_vol/total if total>0 else 0.5
        ratio = max(0.0, min(1.0, ratio))
        return {"symbol": symbol, "trades": trades, "sell_vol": sell_vol, "buy_vol": buy_vol, "whale_sells": whale_sells, "sell_ratio": ratio, "source": "Binance v5", "version": "v5_max"}

    def fetch_liquidations(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        if not symbol or not isinstance(symbol, str):
            symbol = "BTCUSDT"
        try:
            limit = max(1, min(500, int(limit)))
        except (ValueError, TypeError):
            limit = 100
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/allForceOrders", params={"symbol": symbol, "limit": limit}, timeout=2, retries=1)
        if not isinstance(data, list):
            return {"symbol": symbol, "liquidations": [], "long_liq":0, "short_liq":0, "total":0, "source": "Binance v5", "version": "v5_max"}
        long_liq=0.0
        short_liq=0.0
        liqs=[]
        try:
            for o in data[-50:]:
                try:
                    if not isinstance(o, dict):
                        continue
                    side=o.get("side","")
                    qty_raw=o.get("origQty",0) or 0
                    price_raw=o.get("price",0) or o.get("avgPrice",0) or 0
                    try:
                        qty=float(qty_raw)
                        price=float(price_raw)
                    except (ValueError, TypeError):
                        continue
                    if qty<=0 or price<=0 or price > 10_000_000 or qty > 1e6:
                        continue
                    val=qty*price
                    if val <= 0 or val > 1e9:
                        continue
                    if side=="SELL":
                        long_liq+=val
                    else:
                        short_liq+=val
                    if len(liqs)<10:
                        liqs.append({"side":side,"qty":qty,"price":price,"val":val,"time":o.get("time")})
                except Exception:
                    continue
        except Exception:
            pass
        return {"symbol": symbol, "liquidations": liqs, "long_liq": long_liq, "short_liq": short_liq, "total": long_liq+short_liq, "source": "Binance v5", "version": "v5_max"}

    def fetch_fear_greed(self) -> Dict:
        data = fetch_json(FNG_URL, timeout=3, retries=2)
        if not data or not isinstance(data, dict) or "data" not in data:
            return {"value": 50, "classification": "Neutral", "history": [], "error": True, "source": "FNG v5", "version": "v5_max"}
        try:
            d=data.get("data",[])
            if not isinstance(d, list) or len(d) == 0:
                return {"value": 50, "classification": "Neutral", "history": [], "error": True, "source": "FNG v5", "version": "v5_max"}
            current=d[0] if d else {"value":"50","value_classification":"Neutral"}
            if not isinstance(current, dict):
                current = {"value":"50","value_classification":"Neutral"}
            try:
                val = int(current.get("value",50))
            except (ValueError, TypeError):
                val = 50
            val = max(0, min(100, val))
            hist=[]
            for x in d[:7]:
                try:
                    if not isinstance(x, dict):
                        continue
                    v_raw = x.get("value",50)
                    try:
                        v = int(v_raw)
                    except (ValueError, TypeError):
                        continue
                    v = max(0, min(100, v))
                    hist.append({"value": v, "class": x.get("value_classification","Neutral")})
                except Exception:
                    continue
            return {
                "value": val,
                "classification": current.get("value_classification","Neutral"),
                "timestamp": current.get("timestamp"),
                "history": hist,
                "source": "FNG v5",
                "real_data": True,
                "version": "v5_max"
            }
        except Exception:
            return {"value": 50, "classification": "Neutral", "history": [], "error": True, "source": "FNG v5", "version": "v5_max"}

    def fetch_reddit(self, limit: int=25) -> List:
        try:
            limit = max(1, min(100, int(limit)))
        except (ValueError, TypeError):
            limit = 25
        txt = fetch_text(REDDIT_URL, timeout=3, retries=1)
        if not txt or not isinstance(txt, str):
            return []
        try:
            import json
            j=json.loads(txt)
            if not isinstance(j, dict):
                return []
            posts=[]
            children = j.get("data",{}).get("children",[])
            if not isinstance(children, list):
                return []
            for child in children[:limit]:
                try:
                    if not isinstance(child, dict):
                        continue
                    d=child.get("data",{})
                    if not isinstance(d, dict):
                        continue
                    title = d.get("title","")
                    if not title or not isinstance(title, str):
                        continue
                    try:
                        score = int(d.get("score",0) or 0)
                        num_comments = int(d.get("num_comments",0) or 0)
                        created = float(d.get("created_utc",0) or 0)
                        upvote_ratio = float(d.get("upvote_ratio",0) or 0)
                    except (ValueError, TypeError):
                        score = 0
                        num_comments = 0
                        created = 0.0
                        upvote_ratio = 0.0
                    title_lower = title.lower()
                    is_crash = any(k in title_lower for k in ["crash","dump","liquidation","hack","sec","ban","collapse","depeg","scam","crisis","plunge","bear","alert","sell-off","bloodbath","panic","fud","fear"])
                    posts.append({
                        "title": title[:200],
                        "score": score,
                        "num_comments": num_comments,
                        "created": created,
                        "upvote_ratio": upvote_ratio,
                        "is_crash": is_crash,
                        "source": "Reddit v5",
                        "version": "v5_max"
                    })
                except Exception:
                    continue
            return posts
        except Exception:
            return []

    def fetch_coindcx_tickers(self) -> Dict:
        try:
            from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol="BTC-USD")
            tickers = fetcher.get_tickers_all()
            if not isinstance(tickers, dict) or len(tickers) == 0:
                return {}
            converted={}
            for market, data in tickers.items():
                try:
                    if not isinstance(data, dict):
                        continue
                    if not isinstance(market, str) or "INR" not in market:
                        continue
                    price_inr_raw = data.get("price",0) or 0
                    try:
                        price_inr = float(price_inr_raw)
                    except (ValueError, TypeError):
                        continue
                    if price_inr <=0 or price_inr > 200_000_000:
                        continue
                    price_usd = price_inr / 83.5
                    if price_usd <= 0 or price_usd > 10_000_000:
                        continue
                    base = market.replace("INR","").strip()
                    if len(base) < 2 or len(base) > 10:
                        continue
                    usdt_sym = f"{base}USDT"
                    try:
                        change_abs = float(data.get("change",0) or 0)
                    except (ValueError, TypeError):
                        change_abs = 0.0
                    change_pct = 0.0
                    try:
                        if price_inr > 0:
                            change_pct = change_abs / price_inr * 100
                            change_pct = max(-50.0, min(50.0, change_pct))
                    except Exception:
                        change_pct = 0.0
                    try:
                        high_inr = float(data.get("high",0) or 0)
                        high_usd = high_inr / 83.5 if high_inr > 0 else 0
                        low_inr = float(data.get("low",0) or 0)
                        low_usd = low_inr / 83.5 if low_inr > 0 else 0
                        vol = float(data.get("volume",0) or 0)
                    except (ValueError, TypeError):
                        high_usd = 0.0
                        low_usd = 0.0
                        vol = 0.0

                    converted[usdt_sym] = {
                        "symbol": usdt_sym,
                        "price": price_usd,
                        "price_inr": price_inr,
                        "change_pct": change_pct,
                        "change": change_abs,
                        "high": high_usd,
                        "low": low_usd,
                        "volume": vol,
                        "quote_vol": vol * price_usd if vol > 0 else 0,
                        "count": 100,
                        "source": "CoinDCX INR converted v5",
                        "market": market,
                        "real_data": True,
                        "version": "v5_max"
                    }
                except Exception:
                    continue
            return converted
        except Exception:
            return {}

    def fetch_news(self) -> List:
        xml = fetch_text(COINDESK_RSS, timeout=3, retries=1)
        titles=[]
        if xml and isinstance(xml, str):
            try:
                root=ET.fromstring(xml)
                for item in root.findall(".//item")[:20]:
                    try:
                        t=item.find("title")
                        if t is not None and t.text and isinstance(t.text, str):
                            title=t.text.strip()[:200]
                            if len(title) < 5:
                                continue
                            title_lower = title.lower()
                            is_crash = any(k in title_lower for k in ["crash","plunge","dump","hack","exploit","sec","lawsuit","ban","collapse","liquidation","depeg","crisis","fear","sell-off","bear","alert","warning","bloodbath","panic","fud","dump"])
                            titles.append({
                                "title": title,
                                "is_crash": is_crash,
                                "source": "CoinDesk v5",
                                "version": "v5_max"
                            })
                    except Exception:
                        continue
            except ET.ParseError:
                pass
            except Exception:
                pass
        if not titles:
            titles=[{"title":"No news feed - using market data only v5","is_crash":False,"source":"Local v5","version":"v5_max"}]
        return titles

    def fetch_global_market(self) -> Dict:
        """Fetch global market data from CoinGecko - v5 new"""
        data = fetch_json(COINGECKO_URL, timeout=3, retries=1)
        if data and isinstance(data, dict) and "data" in data:
            try:
                d = data["data"]
                return {
                    "total_market_cap_usd": d.get("total_market_cap",{}).get("usd",0),
                    "total_volume_usd": d.get("total_volume",{}).get("usd",0),
                    "market_cap_change_24h": d.get("market_cap_change_percentage_24h_usd",0),
                    "btc_dominance": d.get("market_cap_percentage",{}).get("btc",0),
                    "source": "CoinGecko v5",
                    "version": "v5_max"
                }
            except Exception:
                pass
        return {"total_market_cap_usd": 0, "source": "CoinGecko v5", "version": "v5_max"}

    def fetch_all(self, symbols: List[str]=None) -> ScrapedData:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        validated=[]
        for s in symbols:
            if not isinstance(s, str):
                continue
            s_clean = s.upper().replace("-","").replace("/","").replace("_","").strip()
            if 6 <= len(s_clean) <= 12:
                validated.append(s_clean)
        symbols = validated[:12]
        if not symbols:
            symbols = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

        start=time.time()
        errors=[]
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures={
                ex.submit(self.fetch_spot_tickers): "spot",
                ex.submit(self.fetch_futures_tickers): "futures",
                ex.submit(self.fetch_funding_rates): "funding",
                ex.submit(self.fetch_fear_greed): "fng",
                ex.submit(self.fetch_reddit): "reddit",
                ex.submit(self.fetch_news): "news",
                ex.submit(self.fetch_coindcx_tickers): "coindcx",
                ex.submit(self.fetch_global_market): "global",
            }
            for sym in symbols[:6]:
                futures[ex.submit(self.fetch_orderbook, sym, 20)] = f"ob_{sym}"
                futures[ex.submit(self.fetch_recent_trades, sym, 100)] = f"trades_{sym}"
                futures[ex.submit(self.fetch_liquidations, sym, 50)] = f"liq_{sym}"
            futures[ex.submit(self.fetch_open_interest_multi, symbols[:6])] = "oi"

            results={}
            for f in as_completed(futures):
                key=futures[f]
                try:
                    results[key]=f.result(timeout=5)
                except Exception as e:
                    results[key]=None
                    try:
                        err_msg = str(e)[:100]
                    except Exception:
                        err_msg = "Unknown error"
                    errors.append(f"{key}: {err_msg}")

        spot = results.get("spot") or {}
        if not isinstance(spot, dict):
            spot = {}
        fut = results.get("futures") or {}
        if not isinstance(fut, dict):
            fut = {}
        funding = results.get("funding") or []
        if not isinstance(funding, list):
            funding = []
        fng = results.get("fng") or {"value":50, "classification":"Neutral", "history":[]}
        if not isinstance(fng, dict):
            fng = {"value":50, "classification":"Neutral", "history":[]}
        reddit = results.get("reddit") or []
        if not isinstance(reddit, list):
            reddit = []
        news = results.get("news") or []
        if not isinstance(news, list):
            news = []
        oi = results.get("oi") or {}
        if not isinstance(oi, dict):
            oi = {}
        coindcx = results.get("coindcx") or {}
        if not isinstance(coindcx, dict):
            coindcx = {}
        global_market = results.get("global") or {}
        if not isinstance(global_market, dict):
            global_market = {}

        if not spot and coindcx:
            spot = dict(coindcx)
            errors.append("Binance spot failed, using CoinDCX INR converted as primary v5")
        elif coindcx:
            for k,v in coindcx.items():
                if k not in spot and isinstance(v, dict):
                    spot[k] = v

        orderbooks={}
        trades={}
        liqs={}
        for k,v in results.items():
            try:
                if k.startswith("ob_"):
                    if v and isinstance(v, dict) and not v.get("error"):
                        orderbooks[k[3:]]=v
                elif k.startswith("trades_"):
                    if v and isinstance(v, dict):
                        trades[k[7:]]=v
                elif k.startswith("liq_"):
                    if v and isinstance(v, dict):
                        liqs[k[4:]]=v
            except Exception:
                continue

        elapsed=(time.time()-start)*1000

        total_sources = 8 + len(symbols[:6])*3 + 1
        success_sources = 0
        for k,v in results.items():
            try:
                if v is None:
                    continue
                if isinstance(v, dict) and len(v) == 0:
                    continue
                if isinstance(v, list) and len(v) == 0:
                    continue
                success_sources += 1
            except Exception:
                continue

        quality = success_sources / total_sources if total_sources > 0 else 0
        quality = max(0.0, min(1.0, quality))

        # Metrics v5
        with self._lock:
            self._metrics["total_fetches"] += 1
            prev_avg = self._metrics["avg_fetch_time_ms"]
            total = self._metrics["total_fetches"]
            self._metrics["avg_fetch_time_ms"] = (prev_avg * (total-1) + elapsed) / total if total > 1 else elapsed
            prev_q = self._metrics["data_quality_avg"]
            self._metrics["data_quality_avg"] = (prev_q * (total-1) + quality) / total if total > 1 else quality

        scraped = ScrapedData(
            timestamp=datetime.utcnow().isoformat(),
            spot_tickers=spot,
            futures_tickers=fut,
            funding_rates=funding,
            open_interest=oi,
            orderbooks=orderbooks,
            liquidations=liqs,
            recent_trades=trades,
            fear_greed=fng,
            reddit_posts=reddit,
            news_titles=news,
            coindcx_tickers=coindcx,
            fetch_time_ms=elapsed,
            errors=errors,
            data_quality=quality,
            version="v5_max",
            metrics={
                "global_market": global_market,
                "scraper_metrics": dict(self._metrics),
                "total_sources": total_sources,
                "success_sources": success_sources
            }
        )

        with self._lock:
            if quality > 0.25 or not self._last_successful:
                self._last_successful = scraped
                self._cache = scraped
                self._last_fetch = time.time()

        return scraped

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "version": "v5_max"}

_scraper_instance=None
_scraper_lock=threading.Lock()

def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        with _scraper_lock:
            if _scraper_instance is None:
                _scraper_instance=FastScraper()
    return _scraper_instance
