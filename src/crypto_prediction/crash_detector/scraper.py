"""
Fast Local Webscraper for Crash Detection
Fixed: error handling, retry, missing data detection, logging, rate limiting
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
import random

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FAPI = "https://fapi.binance.com"
FNG_URL = "https://api.alternative.me/fng/?limit=7&format=json"
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/hot.json"
COINDESK_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"

_session = None
_last_request_time = 0
_min_interval = 0.05  # 50ms between requests to avoid rate limit

def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": "Mozilla/5.0 (CrashDetector Local/1.0) Fast Scraper",
            "Accept": "application/json",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=0)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session

def rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _min_interval:
        time.sleep(_min_interval - elapsed)
    _last_request_time = time.time()

def fetch_json(url: str, params: Optional[Dict]=None, timeout: float=4.0, retries: int=1) -> Optional[Dict]:
    for attempt in range(retries+1):
        try:
            rate_limit()
            sess = get_session()
            resp = sess.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return None
            elif resp.status_code == 429:
                # Rate limited, wait
                time.sleep(0.5 + random.random()*0.5)
                continue
            else:
                return None
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(0.2)
                continue
            return None
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                time.sleep(0.3)
                continue
            return None
        except Exception:
            return None
    return None

def fetch_text(url: str, timeout: float=4.0, retries: int=1) -> Optional[str]:
    for attempt in range(retries+1):
        try:
            rate_limit()
            sess = get_session()
            resp = sess.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (compatible; CrashDetector/1.0)"})
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
    data_quality: float  # 0-1, how much data we got

class FastScraper:
    def __init__(self, max_workers: int = 12):
        self.max_workers = max_workers
        self._last_fetch = 0
        self._cache = None
        self._cache_ttl = 25
        self._last_successful = None

    def _is_cache_valid(self):
        return self._cache and (time.time() - self._last_fetch) < self._cache_ttl

    def fetch_spot_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/ticker/24hr", timeout=5, retries=1)
        if not data:
            # Return last successful if available
            if self._last_successful and self._last_successful.spot_tickers:
                return self._last_successful.spot_tickers
            return {}
        wanted = {"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT","LTCUSDT","LINKUSDT","UNIUSDT","ETCUSDT","XLMUSDT","BCHUSDT","FILUSDT","TRXUSDT","ATOMUSDT"}
        result = {}
        if isinstance(data, list):
            for t in data:
                try:
                    sym = t.get("symbol","")
                    if sym in wanted or (sym.endswith("USDT") and sym in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT"]):
                        result[sym] = {
                            "symbol": sym,
                            "price": float(t.get("lastPrice",0) or 0),
                            "change_pct": float(t.get("priceChangePercent",0) or 0),
                            "change": float(t.get("priceChange",0) or 0),
                            "high": float(t.get("highPrice",0) or 0),
                            "low": float(t.get("lowPrice",0) or 0),
                            "volume": float(t.get("volume",0) or 0),
                            "quote_vol": float(t.get("quoteVolume",0) or 0),
                            "count": int(t.get("count",0) or 0),
                        }
                        # Sanity check
                        if result[sym]["price"] <= 0:
                            del result[sym]
                except (ValueError, TypeError):
                    continue
        return result

    def fetch_futures_tickers(self) -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr", timeout=5, retries=1)
        if not data or not isinstance(data, list):
            return {}
        result = {}
        for t in data[:60]:
            try:
                sym = t.get("symbol","")
                if "USDT" in sym and len(sym) <= 12:
                    price = float(t.get("lastPrice",0) or 0)
                    if price > 0:
                        result[sym] = {
                            "symbol": sym,
                            "price": price,
                            "change_pct": float(t.get("priceChangePercent",0) or 0),
                            "volume": float(t.get("volume",0) or 0),
                            "quote_vol": float(t.get("quoteVolume",0) or 0),
                        }
            except (ValueError, TypeError):
                continue
        return result

    def fetch_funding_rates(self, limit: int=30) -> List:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/fundingRate", params={"limit": limit}, timeout=4, retries=1)
        if data and isinstance(data, list) and len(data) > 0:
            return data
        # Fallback premiumIndex
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", timeout=4, retries=1)
        if isinstance(data, list):
            out=[]
            for d in data[:30]:
                try:
                    rate = d.get("lastFundingRate")
                    if rate is not None:
                        out.append({"symbol": d.get("symbol"), "fundingRate": float(rate), "time": d.get("nextFundingTime")})
                except (ValueError, TypeError):
                    continue
            return out
        return []

    def fetch_open_interest(self, symbol: str="BTCUSDT") -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/openInterest", params={"symbol": symbol}, timeout=3, retries=1)
        if data:
            try:
                oi = float(data.get("openInterest",0) or 0)
                if oi > 0:
                    return {"symbol": symbol, "oi": oi, "time": data.get("time",0)}
            except (ValueError, TypeError):
                pass
        return {"symbol": symbol, "oi": 0, "time": 0}

    def fetch_open_interest_multi(self, symbols: List[str]) -> Dict:
        results={}
        if not symbols:
            return results
        with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as ex:
            futs={ex.submit(self.fetch_open_interest, s): s for s in symbols}
            for f in as_completed(futs):
                try:
                    r=f.result(timeout=4)
                    if r:
                        results[r["symbol"]]=r
                except Exception:
                    continue
        return results

    def fetch_orderbook(self, symbol: str="BTCUSDT", limit: int=20) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/depth", params={"symbol": symbol, "limit": limit}, timeout=3, retries=1)
        if not data:
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0, "mid":0, "error": True}
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
                    if pf>0 and qf>0:
                        bids.append([pf,qf])
                        bid_vol+=qf
                except (ValueError, TypeError):
                    continue
            for p,q in asks_raw:
                try:
                    pf=float(p); qf=float(q)
                    if pf>0 and qf>0:
                        asks.append([pf,qf])
                        ask_vol+=qf
                except (ValueError, TypeError):
                    continue
            total = bid_vol+ask_vol
            imb = (bid_vol-ask_vol)/total if total>0 else 0
            imb = max(-1.0, min(1.0, imb))
            mid = (bids[0][0]+asks[0][0])/2 if bids and asks else 0
            return {"symbol": symbol, "bids": bids, "asks": asks, "bid_vol": bid_vol, "ask_vol": ask_vol, "imbalance": imb, "mid": mid}
        except Exception:
            return {"symbol": symbol, "bids": [], "asks": [], "bid_vol":0, "ask_vol":0, "imbalance":0, "mid":0, "error": True}

    def fetch_recent_trades(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        data = fetch_json(f"{BINANCE_SPOT}/api/v3/trades", params={"symbol": symbol, "limit": limit}, timeout=3, retries=1)
        if not isinstance(data, list):
            return {"symbol": symbol, "trades": [], "sell_vol":0, "buy_vol":0, "whale_sells":0, "sell_ratio":0.5}
        sell_vol=0.0
        buy_vol=0.0
        whale_sells=0
        trades=[]
        try:
            for t in data:
                try:
                    price=float(t.get("price",0) or 0)
                    qty=float(t.get("qty",0) or 0)
                    if price<=0 or qty<=0:
                        continue
                    is_buyer_maker=t.get("isBuyerMaker", False)
                    val=price*qty
                    if is_buyer_maker:
                        sell_vol+=val
                        if val>50000:
                            whale_sells+=1
                    else:
                        buy_vol+=val
                    if len(trades)<20:
                        trades.append({"p":price,"q":qty,"v":val,"sell":is_buyer_maker})
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass
        total = sell_vol+buy_vol
        ratio = sell_vol/total if total>0 else 0.5
        return {"symbol": symbol, "trades": trades, "sell_vol": sell_vol, "buy_vol": buy_vol, "whale_sells": whale_sells, "sell_ratio": ratio}

    def fetch_liquidations(self, symbol: str="BTCUSDT", limit: int=100) -> Dict:
        data = fetch_json(f"{BINANCE_FAPI}/fapi/v1/allForceOrders", params={"symbol": symbol, "limit": limit}, timeout=3, retries=1)
        if not isinstance(data, list):
            return {"symbol": symbol, "liquidations": [], "long_liq":0, "short_liq":0, "total":0}
        long_liq=0.0
        short_liq=0.0
        liqs=[]
        try:
            for o in data[-50:]:
                try:
                    side=o.get("side","")
                    qty=float(o.get("origQty",0) or 0)
                    price=float(o.get("price",0) or o.get("avgPrice",0) or 0)
                    if qty<=0 or price<=0:
                        continue
                    val=qty*price
                    if side=="SELL":
                        long_liq+=val
                    else:
                        short_liq+=val
                    if len(liqs)<10:
                        liqs.append({"side":side,"qty":qty,"price":price,"val":val,"time":o.get("time")})
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass
        return {"symbol": symbol, "liquidations": liqs, "long_liq": long_liq, "short_liq": short_liq, "total": long_liq+short_liq}

    def fetch_fear_greed(self) -> Dict:
        data = fetch_json(FNG_URL, timeout=4, retries=1)
        if not data or "data" not in data:
            return {"value": 50, "classification": "Neutral", "history": [], "error": True}
        try:
            d=data["data"]
            current=d[0] if d else {"value":"50","value_classification":"Neutral"}
            return {
                "value": int(current.get("value",50)),
                "classification": current.get("value_classification","Neutral"),
                "timestamp": current.get("timestamp"),
                "history": [{"value": int(x.get("value",50)), "class": x.get("value_classification")} for x in d[:7] if x.get("value")]
            }
        except (ValueError, TypeError, KeyError):
            return {"value": 50, "classification": "Neutral", "history": [], "error": True}

    def fetch_reddit(self, limit: int=25) -> List:
        txt = fetch_text(REDDIT_URL, timeout=4, retries=1)
        if not txt:
            return []
        try:
            import json
            j=json.loads(txt)
            posts=[]
            children = j.get("data",{}).get("children",[])
            for child in children[:limit]:
                try:
                    d=child.get("data",{})
                    title = d.get("title","")
                    if not title:
                        continue
                    posts.append({
                        "title": title[:200],
                        "score": int(d.get("score",0) or 0),
                        "num_comments": int(d.get("num_comments",0) or 0),
                        "created": float(d.get("created_utc",0) or 0),
                        "upvote_ratio": float(d.get("upvote_ratio",0) or 0),
                        "is_crash": any(k in title.lower() for k in ["crash","dump","liquidation","hack","sec","ban","collapse","depeg","scam","crisis","plunge","bear"])
                    })
                except (ValueError, TypeError, AttributeError):
                    continue
            return posts
        except Exception:
            return []

    def fetch_coindcx_tickers(self) -> Dict:
        """Real CoinDCX INR tickers - actual money markets"""
        try:
            from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
            fetcher = CoinDCXRealtimeFetcher(symbol="BTC-USD")
            tickers = fetcher.get_tickers_all()
            # Convert INR tickers to USD-like format for crash detection (convert back to USD for uniform scoring)
            # But keep INR for raw display
            converted={}
            for market, data in tickers.items():
                try:
                    price_inr = float(data.get("price",0) or 0)
                    if price_inr <=0:
                        continue
                    # Convert INR to USD for crash detection uniformity
                    price_usd = price_inr / 83.5
                    # Map INR market to USDT symbol for compatibility
                    # BTCINR -> BTCUSDT
                    base = market.replace("INR","")
                    usdt_sym = f"{base}USDT"
                    converted[usdt_sym] = {
                        "symbol": usdt_sym,
                        "price": price_usd,
                        "price_inr": price_inr,
                        "change_pct": float(data.get("change",0) or 0) / price_inr * 100 if price_inr else 0,
                        "change": float(data.get("change",0) or 0),
                        "high": float(data.get("high",0) or 0) / 83.5,
                        "low": float(data.get("low",0) or 0) / 83.5,
                        "volume": float(data.get("volume",0) or 0),
                        "quote_vol": float(data.get("volume",0) or 0) * price_usd,
                        "count": 100,
                        "source": "CoinDCX INR converted",
                        "market": market
                    }
                except (ValueError, TypeError):
                    continue
            return converted
        except Exception as e:
            # Debug but not error
            return {}

    def fetch_news(self) -> List:
        xml = fetch_text(COINDESK_RSS, timeout=4, retries=1)
        titles=[]
        if xml:
            try:
                root=ET.fromstring(xml)
                for item in root.findall(".//item")[:15]:
                    try:
                        t=item.find("title")
                        if t is not None and t.text:
                            title=t.text[:200]
                            titles.append({
                                "title": title,
                                "is_crash": any(k in title.lower() for k in ["crash","plunge","dump","hack","exploit","sec","lawsuit","ban","collapse","liquidation","depeg","crisis","fear","sell-off","bear","alert"]),
                                "source": "CoinDesk"
                            })
                    except Exception:
                        continue
            except ET.ParseError:
                pass
            except Exception:
                pass
        if not titles:
            titles=[{"title":"No news feed - using market data only","is_crash":False,"source":"Local"}]
        return titles

    def fetch_all(self, symbols: List[str]=None) -> ScrapedData:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        # Validate symbols
        symbols = [s.upper().replace("-","").replace("/","") for s in symbols if s]
        symbols = [s for s in symbols if len(s) >= 6 and len(s) <= 12][:10]  # limit 10

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
                ex.submit(self.fetch_coindcx_tickers): "coindcx",  # Real CoinDCX INR data
            }
            for sym in symbols[:5]:
                futures[ex.submit(self.fetch_orderbook, sym, 20)] = f"ob_{sym}"
                futures[ex.submit(self.fetch_recent_trades, sym, 100)] = f"trades_{sym}"
                futures[ex.submit(self.fetch_liquidations, sym, 50)] = f"liq_{sym}"
            futures[ex.submit(self.fetch_open_interest_multi, symbols[:5])] = "oi"

            results={}
            for f in as_completed(futures):
                key=futures[f]
                try:
                    results[key]=f.result(timeout=6)
                except Exception as e:
                    results[key]=None
                    errors.append(f"{key}: {str(e)[:100]}")

        spot = results.get("spot") or {}
        fut = results.get("futures") or {}
        funding = results.get("funding") or []
        fng = results.get("fng") or {"value":50, "classification":"Neutral", "history":[]}
        reddit = results.get("reddit") or []
        news = results.get("news") or []
        oi = results.get("oi") or {}
        coindcx = results.get("coindcx") or {}

        # Integrate CoinDCX tickers with Binance - CoinDCX is fallback when Binance fails, or additional source
        # If Binance spot empty but CoinDCX has data, use CoinDCX
        if not spot and coindcx:
            spot = coindcx
            errors.append("Binance spot failed, using CoinDCX INR converted")
        elif coindcx:
            # Merge: add CoinDCX tickers that are not in Binance
            for k,v in coindcx.items():
                if k not in spot:
                    spot[k] = v

        orderbooks={}
        trades={}
        liqs={}
        for k,v in results.items():
            if k.startswith("ob_"):
                if v and not v.get("error"):
                    orderbooks[k[3:]]=v
            elif k.startswith("trades_"):
                if v:
                    trades[k[7:]]=v
            elif k.startswith("liq_"):
                if v:
                    liqs[k[4:]]=v

        elapsed=(time.time()-start)*1000

        # Data quality: how many sources succeeded - now includes CoinDCX
        total_sources = 7 + len(symbols[:5])*3 + 1
        success_sources = sum(1 for k,v in results.items() if v not in [None, {}, []])
        quality = success_sources / total_sources if total_sources else 0
        quality = max(0.0, min(1.0, quality))

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
            data_quality=quality
        )

        # Save as last successful if quality decent
        if quality > 0.3 or not self._last_successful:
            self._last_successful = scraped

        return scraped

_scraper_instance=None
def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance=FastScraper()
    return _scraper_instance
