"""
Fast Local Webscraper for Crash Detection
- All processing locally, no external AI APIs
- Efficient: Session reuse, ThreadPoolExecutor parallel I/O, 3-5s timeouts, LRU cache
- Sources: Binance Spot/Futures, Funding, OI, Orderbook, Liquidations, Fear&Greed, Reddit, News RSS
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
from functools import lru_cache

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FAPI = "https://fapi.binance.com"
FNG_URL = "https://api.alternative.me/fng/?limit=7&format=json"
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/hot.json"
COINDESK_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"

# Global session for connection reuse - critical for speed
_session = None

def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": "Mozilla/5.0 (CrashDetector Local/1.0) Fast Scraper",
            "Accept": "application/json",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=1)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session

def fetch_json(url: str, params: Optional[Dict]=None, timeout: float=4.0) -> Optional[Dict]:
    try:
        sess = get_session()
        resp = sess.get(url, params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fetch_text(url: str, timeout: float=4.0) -> Optional[str]:
    try:
        sess = get_session()
        resp = sess.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
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
    fetch_time_ms: float

class FastScraper:
    def __init__(self, max_workers: int = 12):
        self.max_workers = max_workers
        self._last_fetch = 0
        self._cache = None
        self._cache_ttl = 25  # seconds for market data

    def _is_cache_valid(self):
        return self._cache and (time.time() - self._last_fetch) < self._cache_ttl

    def fetch_spot_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/ticker/24hr", timeout=5)
        if not data:
            return {}
        # Filter major symbols for speed
        wanted = {"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT","LTCUSDT","LINKUSDT","UNIUSDT","ETCUSDT","XLMUSDT","BCHUSDT","FILUSDT","TRXUSDT","ATOMUSDT","USDTUSD","USDCUSDT"}
        result = {}
        if isinstance(data, list):
            for t in data:
                sym = t.get("symbol","")
                if sym in wanted or "USDT" in sym:
                    try:
                        result[sym] = {
                            "symbol": sym,
                            "price": float(t.get("lastPrice",0)),
                            "change_pct": float(t.get("priceChangePercent",0)),
                            "change": float(t.get("priceChange",0)),
                            "high": float(t.get("highPrice",0)),
                            "low": float(t.get("lowPrice",0)),
                            "volume": float(t.get("volume",0)),
                            "quote_vol": float(t.get("quoteVolume",0)),
                            "count": int(t.get("count",0)),
                        }
                    except: continue
        return result

    def fetch_futures_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr", timeout=5)
        if not data or not isinstance(data, list):
            return {}
        result = {}
        for t in data[:50]:  # top 50 for speed
            try:
                sym = t.get("symbol","")
                if "USDT" in sym:
                    result[sym] = {
                        "symbol": sym,
                        "price": float(t.get("lastPrice",0)),
                        "change_pct": float(t.get("priceChangePercent",0)),
                        "volume": float(t.get("volume",0)),
                        "quote_vol": float(t.get("quoteVolume",0)),
                    }
            except: continue
        return result

    def fetch_funding_rates(self, limit: int=30) -> List:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/fundingRate", params={"limit": limit}, timeout=4)
        if not data:
            # fallback premiumIndex
            data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", timeout=4)
            if isinstance(data, list):
                out=[]
                for d in data[:30]:
                    try:
                        out.append({"symbol": d.get("symbol"), "fundingRate": float(d.get("lastFundingRate",0)), "time": d.get("nextFundingTime")})
                    except: continue
                return out
            return []
        return data if isinstance(data, list) else []

    def fetch_open_interest(self, symbol: str="BTCUSDT") -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/openInterest", params={"symbol": symbol}, timeout=3)
        if data:
            try:
                return {"symbol": symbol, "oi": float(data.get("openInterest",0)), "time": data.get("time")}
            except: pass
        return {"symbol": symbol, "oi": 0, "time": 0}

    def fetch_open_interest_multi(self, symbols: List[str]) -> Dict:
        results={}
        with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as ex:
            futs={ex.submit(self.fetch_open_interest, s): s for s in symbols}
            for f in as_completed(futs):
                try:
                    r=f.result()
                    results[r["symbol"]]=r
                except: pass
        return results

    def fetch_orderbook(self, symbol: str="BTCUSDT", limit: int=20) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/depth", params={"symbol": symbol, "limit": limit}, timeout=3)
        if not data:
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0}
        try:
            bids = [[float(p), float(q)] for p,q in data.get("bids",[])[:limit]]
            asks = [[float(p), float(q)] for p,q in data.get("asks",[])[:limit]]
            bid_vol = sum(q for _,q in bids)
            ask_vol = sum(q for _,q in asks)
            total = bid_vol+ask_vol
            imb = (bid_vol-ask_vol)/total if total>0 else 0
            return {"symbol": symbol, "bids": bids, "asks": asks, "bid_vol": bid_vol, "ask_vol": ask_vol, "imbalance": imb, "mid": (bids[0][0]+asks[0][0])/2 if bids and asks else 0}
        except:
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0}

    def fetch_recent_trades(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/trades", params={"symbol": symbol, "limit": limit}, timeout=3)
        if not isinstance(data, list):
            return {"symbol": symbol, "trades": [], "sell_vol":0, "buy_vol":0, "whale_sells":0}
        sell_vol=0
        buy_vol=0
        whale_sells=0
        trades=[]
        try:
            for t in data:
                price=float(t.get("price",0))
                qty=float(t.get("qty",0))
                is_buyer_maker=t.get("isBuyerMaker", False)
                val=price*qty
                if is_buyer_maker: # sell
                    sell_vol+=val
                    if val>50000: whale_sells+=1
                else:
                    buy_vol+=val
                trades.append({"p":price,"q":qty,"v":val,"sell":is_buyer_maker})
        except: pass
        return {"symbol": symbol, "trades": trades[:20], "sell_vol": sell_vol, "buy_vol": buy_vol, "whale_sells": whale_sells, "sell_ratio": sell_vol/(sell_vol+buy_vol) if (sell_vol+buy_vol)>0 else 0.5}

    def fetch_liquidations(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/allForceOrders", params={"symbol": symbol, "limit": limit}, timeout=3)
        if not isinstance(data, list):
            return {"symbol": symbol, "liquidations": [], "long_liq":0, "short_liq":0, "total":0}
        long_liq=0
        short_liq=0
        liqs=[]
        try:
            for o in data[-50:]:
                side=o.get("side","")
                qty=float(o.get("origQty",0))
                price=float(o.get("price",0) or o.get("avgPrice",0) or 0)
                val=qty*price
                if side=="SELL":
                    long_liq+=val
                else:
                    short_liq+=val
                liqs.append({"side":side,"qty":qty,"price":price,"val":val,"time":o.get("time")})
        except: pass
        return {"symbol": symbol, "liquidations": liqs[-10:], "long_liq": long_liq, "short_liq": short_liq, "total": long_liq+short_liq}

    def fetch_fear_greed(self) -> Dict:
        data = fetch_json(FNG_URL, timeout=4)
        if not data or "data" not in data:
            return {"value": 50, "classification": "Neutral", "history": []}
        try:
            d=data["data"]
            current=d[0] if d else {"value":"50","value_classification":"Neutral"}
            return {
                "value": int(current.get("value",50)),
                "classification": current.get("value_classification","Neutral"),
                "timestamp": current.get("timestamp"),
                "history": [{"value": int(x.get("value",50)), "class": x.get("value_classification")} for x in d[:7]]
            }
        except:
            return {"value": 50, "classification": "Neutral", "history": []}

    def fetch_reddit(self, limit: int=25) -> List:
        # Reddit JSON is public but rate limited - use quick fetch
        txt = fetch_text(REDDIT_URL, timeout=4)
        if not txt:
            return []
        try:
            import json
            j=json.loads(txt)
            posts=[]
            for child in j.get("data",{}).get("children",[])[:limit]:
                d=child.get("data",{})
                posts.append({
                    "title": d.get("title","")[:200],
                    "score": d.get("score",0),
                    "num_comments": d.get("num_comments",0),
                    "created": d.get("created_utc",0),
                    "upvote_ratio": d.get("upvote_ratio",0),
                    "is_crash": any(k in d.get("title","").lower() for k in ["crash","dump","liquidation","hack","sec","ban","collapse","depeg","scam","crisis"])
                })
            return posts
        except:
            return []

    def fetch_news(self) -> List:
        # Try CoinDesk RSS
        xml = fetch_text(COINDESK_RSS, timeout=4)
        titles=[]
        if xml:
            try:
                root=ET.fromstring(xml)
                for item in root.findall(".//item")[:15]:
                    t=item.find("title")
                    if t is not None and t.text:
                        title=t.text[:200]
                        titles.append({
                            "title": title,
                            "is_crash": any(k in title.lower() for k in ["crash","plunge","dump","hack","exploit","sec","lawsuit","ban","collapse","liquidation","depeg","crisis","fear","sell-off","bear"]),
                            "source": "CoinDesk"
                        })
            except: pass
        # Fallback static crash keywords if RSS fails
        if not titles:
            titles=[{"title":"No news feed - using market data only","is_crash":False,"source":"Local"}]
        return titles

    def fetch_all(self, symbols: List[str]=None) -> ScrapedData:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        start=time.time()
        # Parallel fetch core data
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures={
                ex.submit(self.fetch_spot_tickers): "spot",
                ex.submit(self.fetch_futures_tickers): "futures",
                ex.submit(self.fetch_funding_rates): "funding",
                ex.submit(self.fetch_fear_greed): "fng",
                ex.submit(self.fetch_reddit): "reddit",
                ex.submit(self.fetch_news): "news",
            }
            # Add per-symbol parallel
            for sym in symbols[:5]:
                futures[ex.submit(self.fetch_orderbook, sym, 20)] = f"ob_{sym}"
                futures[ex.submit(self.fetch_recent_trades, sym, 100)] = f"trades_{sym}"
                futures[ex.submit(self.fetch_liquidations, sym, 50)] = f"liq_{sym}"
            futures[ex.submit(self.fetch_open_interest_multi, symbols[:5])] = "oi"

            results={}
            for f in as_completed(futures):
                key=futures[f]
                try:
                    results[key]=f.result()
                except Exception as e:
                    results[key]=None

        spot = results.get("spot") or {}
        fut = results.get("futures") or {}
        funding = results.get("funding") or []
        fng = results.get("fng") or {"value":50}
        reddit = results.get("reddit") or []
        news = results.get("news") or []
        oi = results.get("oi") or {}

        orderbooks={}
        trades={}
        liqs={}
        for k,v in results.items():
            if k.startswith("ob_"):
                orderbooks[k[3:]]=v
            elif k.startswith("trades_"):
                trades[k[7:]]=v
            elif k.startswith("liq_"):
                liqs[k[4:]]=v

        elapsed=(time.time()-start)*1000

        return ScrapedData(
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
            fetch_time_ms=elapsed
        )

# Singleton for speed
_scraper_instance=None
def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance=FastScraper()
    return _scraper_instance
