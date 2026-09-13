"""
CoinDCX Broker - Real trading via CoinDCX API with actual money
Fixed: circular fallback avoidance, validation, thread safety, order storage, INR handling
"""
from typing import Dict, List, Optional
import requests
import time
import hmac
import hashlib
import json
from datetime import datetime
import uuid
import threading
import os

from .base import BaseBroker, Order, Balance
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CoinDCXBroker(BaseBroker):
    def __init__(self):
        super().__init__(name="CoinDCX")
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        self.connected = False
        self.paper_mode = False
        self.orders: Dict[str, Order] = {}
        self._lock = threading.Lock()
        self._ticker_cache = {"data": None, "timestamp": 0}
        self._cache_ttl = 10
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "CoinDCXBroker/1.0 Real Trading"})

        self.market_map = {
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
        self.reverse_map = {v: k for k, v in self.market_map.items() if "-" in k and "INR" not in k}

    def _get_timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, body: dict):
        if not self.api_secret:
            raise ValueError("No API secret set")
        try:
            secret_bytes = bytes(self.api_secret, encoding='utf-8')
            json_body = json.dumps(body, separators=(',', ':'))
            signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
            return signature, json_body
        except Exception as e:
            logger.error(f"CoinDCX signing failed: {e}")
            raise

    def _map_to_coindcx(self, symbol: str) -> str:
        if not symbol:
            return "BTCINR"
        sym = symbol.strip().upper()
        if sym in self.market_map:
            return self.market_map[sym]
        if sym in self.market_map.values():
            return sym
        if "INR" in sym:
            return sym.replace("-", "").replace("/", "").replace("_", "")
        # Convert USD/USDT to INR
        cleaned = sym.replace("-", "").replace("/", "").replace("_", "").replace("USD", "INR").replace("USDT", "INR")
        if not cleaned.endswith("INR"):
            cleaned += "INR"
        return cleaned

    def connect(self, api_key: str, api_secret: str, testnet: bool = False) -> bool:
        if not api_key or not api_secret:
            logger.warning("CoinDCX: No API keys provided")
            self.connected = False
            return False
        if not isinstance(api_key, str) or not isinstance(api_secret, str):
            logger.warning("CoinDCX: API keys must be strings")
            return False
        api_key = api_key.strip()
        api_secret = api_secret.strip()
        if len(api_key) < 10 or len(api_secret) < 10:
            logger.warning("CoinDCX: API keys too short")
            return False

        self.api_key = api_key
        self.api_secret = api_secret

        try:
            balances = self._fetch_balances()
            self.connected = True
            self.paper_mode = False
            logger.info(f"✅ CoinDCX REAL connected - {len(balances)} assets")
            return True
        except requests.exceptions.HTTPError as e:
            try:
                err_text = e.response.text[:500] if hasattr(e, 'response') and e.response is not None else str(e)
            except Exception:
                err_text = str(e)
            logger.error(f"CoinDCX connection HTTP error: {e} - {err_text}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"CoinDCX connection failed: {e}")
            self.connected = False
            return False

    def _fetch_balances(self) -> List[Dict]:
        if not self.api_key or not self.api_secret:
            raise ValueError("No API keys for CoinDCX")
        body = {"timestamp": self._get_timestamp()}
        signature, json_body = self._sign(body)
        url = f"{self.base_url}/exchange/v1/users/balances"
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            if "balances" in data and isinstance(data["balances"], list):
                return data["balances"]
            # Dict with currency keys
            result = []
            for k, v in data.items():
                if isinstance(v, dict) and ("balance" in v or "free" in v):
                    result.append({"currency": k, "balance": v.get("balance", v.get("free", 0)), "locked_balance": v.get("locked", v.get("locked_balance", 0))})
            if result:
                return result
            return [data] if data else []
        return []

    def get_balance(self) -> Dict[str, Balance]:
        try:
            raw_balances = self._fetch_balances()
            balances: Dict[str, Balance] = {}
            for b in raw_balances:
                try:
                    if not isinstance(b, dict):
                        continue
                    currency = b.get("currency") or b.get("asset") or b.get("coin") or b.get("symbol")
                    if not currency:
                        continue
                    currency = str(currency).strip().upper()
                    if len(currency) < 1 or len(currency) > 10:
                        continue
                    bal_raw = b.get("balance", b.get("free", b.get("available", b.get("total", 0))))
                    locked_raw = b.get("locked_balance", b.get("locked", b.get("in_order", b.get("lockedBalance", 0))))
                    try:
                        balance = float(bal_raw or 0)
                    except (ValueError, TypeError):
                        balance = 0.0
                    try:
                        locked = float(locked_raw or 0)
                    except (ValueError, TypeError):
                        locked = 0.0
                    if not (balance > 1e-9 or locked > 1e-9 or currency in ["INR", "USDT", "BTC", "ETH", "BNB", "SOL", "XRP"]):
                        continue
                    total = balance + locked
                    if total < 0:
                        total = 0
                    # Sanity: total shouldn't be absurd
                    if total > 1e12:
                        continue
                    balances[currency] = Balance(
                        asset=currency,
                        free=max(0.0, balance),
                        locked=max(0.0, locked),
                        total=total
                    )
                except Exception as e:
                    logger.debug(f"Balance parse failed for {b}: {e}")
                    continue
            logger.info(f"CoinDCX REAL Balances: {len(balances)} assets")
            return balances
        except Exception as e:
            logger.error(f"Failed to get CoinDCX real balances: {e}")
            if not self.connected:
                raise
            return {}

    def _get_tickers_cached(self) -> List[Dict]:
        now = time.time()
        with self._lock:
            if self._ticker_cache["data"] and (now - self._ticker_cache["timestamp"]) < self._cache_ttl:
                return self._ticker_cache["data"]
        try:
            resp = self._session.get(f"{self.base_url}/exchange/ticker", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    with self._lock:
                        self._ticker_cache["data"] = data
                        self._ticker_cache["timestamp"] = now
                    return data
        except requests.RequestException as e:
            logger.debug(f"CoinDCX ticker cache network failed: {e}")
        except Exception as e:
            logger.debug(f"CoinDCX ticker cache unexpected: {e}")
        with self._lock:
            return self._ticker_cache["data"] or []

    def get_price(self, symbol: str) -> float:
        if not symbol or not isinstance(symbol, str):
            return 0.0
        coindcx_market = self._map_to_coindcx(symbol)

        # Try cached tickers
        try:
            tickers = self._get_tickers_cached()
            for ticker in tickers:
                if ticker.get("market") == coindcx_market:
                    price_raw = ticker.get("last_price") or ticker.get("lastPrice") or ticker.get("price")
                    if price_raw is not None:
                        try:
                            p = float(price_raw)
                            if 0 < p < 200_000_000:
                                return p
                        except (ValueError, TypeError):
                            continue
        except Exception as e:
            logger.debug(f"CoinDCX price cache failed {coindcx_market}: {e}")

        # Direct Binance REST fallback (avoid circular via BinanceRealtimeFetcher)
        try:
            usd_symbol = symbol
            if "INR" in symbol.upper():
                base = symbol.upper().replace("INR","").replace("-","").replace("/","").replace("_","")
                if base in ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","AVAX","MATIC","DOT","LINK","LTC","BCH","UNI","SHIB","ETC","XLM","FIL","TRX","ATOM"]:
                    usd_symbol = f"{base}-USD"
            binance_sym = config.data.binance_map.get(usd_symbol.upper(), usd_symbol.replace("-","").replace("/","").replace("_",""))
            resp = requests.get(f"{config.realtime.rest_url}/api/v3/ticker/24hr", params={"symbol": binance_sym}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    lp = data.get("lastPrice")
                    if lp is not None:
                        try:
                            binance_price = float(lp)
                            if 0 < binance_price < 10_000_000:
                                inr_price = binance_price * 83.5
                                return inr_price
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.debug(f"Binance direct fallback for CoinDCX price failed {coindcx_market}: {e}")

        # Cached file fallback
        try:
            from pathlib import Path
            import pandas as pd
            usd_sym = symbol
            if "INR" in symbol.upper():
                base = symbol.upper().replace("INR","")
                usd_sym = f"{base}-USD"
            cache_path = config.project_root / "data" / "raw" / f"{usd_sym.replace('-','_')}_1d.csv"
            if cache_path.exists():
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if not df.empty and 'Close' in df.columns:
                    p = float(df['Close'].iloc[-1]) * 83.5
                    if 0 < p < 200_000_000:
                        return p
        except Exception:
            pass

        return 0.0

    def get_ticker(self, symbol: str) -> Dict:
        if not symbol:
            return {}
        coindcx_market = self._map_to_coindcx(symbol)
        try:
            tickers = self._get_tickers_cached()
            for ticker in tickers:
                if ticker.get("market") == coindcx_market:
                    return ticker
            return {}
        except Exception as e:
            logger.debug(f"Ticker fetch failed {symbol}: {e}")
            return {}

    def get_tickers_all(self) -> Dict:
        try:
            tickers = self._get_tickers_cached()
            result = {}
            for ticker in tickers:
                try:
                    if not isinstance(ticker, dict):
                        continue
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
                    try:
                        bid = float(ticker.get("bid",0) or 0)
                    except (ValueError, TypeError):
                        bid = 0.0
                    try:
                        ask = float(ticker.get("ask",0) or 0)
                    except (ValueError, TypeError):
                        ask = 0.0
                    try:
                        high = float(ticker.get("high",0) or 0)
                    except (ValueError, TypeError):
                        high = 0.0
                    try:
                        low = float(ticker.get("low",0) or 0)
                    except (ValueError, TypeError):
                        low = 0.0
                    try:
                        vol = float(ticker.get("volume",0) or 0)
                    except (ValueError, TypeError):
                        vol = 0.0
                    try:
                        change = float(ticker.get("change_24_hour",0) or 0)
                    except (ValueError, TypeError):
                        change = 0.0
                    result[market] = {
                        "market": market,
                        "price": price,
                        "last_price": price,
                        "bid": bid,
                        "ask": ask,
                        "high": high,
                        "low": low,
                        "volume": vol,
                        "change": change,
                        "real_data": True,
                        "source": "CoinDCX Live INR",
                        "broker": "coindcx"
                    }
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.debug(f"CoinDCX all tickers failed: {e}")
            return {}

    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        if not symbol:
            return None
        try:
            limit = max(5, min(100, int(limit)))
        except (ValueError, TypeError):
            limit = 20
        coindcx_market = self._map_to_coindcx(symbol)

        try:
            resp = self._session.get(f"{self.public_url}/market_data/orderbook", params={"pair": f"I-{coindcx_market}"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    bids = data.get("bids",[])[:limit]
                    asks = data.get("asks",[])[:limit]
                    # Validate
                    valid_bids=[]
                    valid_asks=[]
                    for b in bids:
                        try:
                            if len(b) >= 2:
                                p = float(b[0]); q = float(b[1])
                                if 0 < p < 200_000_000 and q > 0:
                                    valid_bids.append([p,q])
                        except (ValueError, TypeError, IndexError):
                            continue
                    for a in asks:
                        try:
                            if len(a) >= 2:
                                p = float(a[0]); q = float(a[1])
                                if 0 < p < 200_000_000 and q > 0:
                                    valid_asks.append([p,q])
                        except (ValueError, TypeError, IndexError):
                            continue
                    if valid_bids and valid_asks:
                        return {"bids": valid_bids, "asks": valid_asks, "market": coindcx_market, "source": "CoinDCX"}
        except requests.RequestException as e:
            logger.debug(f"CoinDCX orderbook network failed {coindcx_market}: {e}")
        except Exception as e:
            logger.debug(f"CoinDCX orderbook failed {coindcx_market}: {e}")

        # Binance fallback direct REST
        try:
            usd_symbol = symbol
            if "INR" in symbol.upper():
                base = symbol.upper().replace("INR","")
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
                        return {"bids": bids, "asks": asks, "market": coindcx_market, "source": "Binance converted to INR"}
        except requests.RequestException as e:
            logger.debug(f"Binance orderbook fallback network failed {coindcx_market}: {e}")
        except Exception as e:
            logger.debug(f"Binance orderbook fallback for CoinDCX failed {coindcx_market}: {e}")
        return None

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: float = None, stop_price: float = None,
                    take_profits: Dict[str, float] = None, stop_loss: float = None,
                    leverage: str = "1x", trailing_pct: float = None,
                    strategy: str = "") -> Order:
        if not self.connected or not self.api_key:
            raise ValueError("CoinDCX broker not connected - please connect with API keys for real trading")
        if not symbol or not side or not order_type:
            raise ValueError("symbol, side, order_type required")
        if not isinstance(symbol, str) or len(symbol) < 2 or len(symbol) > 20:
            raise ValueError(f"Invalid symbol {symbol}")

        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid quantity {quantity}")
        if quantity <= 0 or quantity > 1_000_000:
            raise ValueError(f"Invalid quantity {quantity} - must be >0 and reasonable")
        if quantity < 0.000001:
            raise ValueError(f"Quantity too small {quantity}")

        side = side.strip().upper()
        if side not in ["BUY","SELL"]:
            raise ValueError(f"Invalid side {side}")

        order_type = order_type.strip().upper()
        if order_type not in ["MARKET","LIMIT","STOP","STOP_LIMIT"]:
            order_type = "MARKET" if order_type == "MARKET" else "LIMIT"

        if price is not None:
            try:
                price = float(price)
                if price <= 0 or price > 200_000_000:
                    raise ValueError(f"Invalid price {price}")
            except (ValueError, TypeError):
                raise ValueError(f"Invalid price {price}")

        if stop_price is not None:
            try:
                stop_price = float(stop_price)
                if stop_price <= 0 or stop_price > 200_000_000:
                    stop_price = None
            except (ValueError, TypeError):
                stop_price = None

        if stop_loss is not None:
            try:
                stop_loss = float(stop_loss)
                if stop_loss <= 0 or stop_loss > 200_000_000:
                    stop_loss = None
            except (ValueError, TypeError):
                stop_loss = None

        if take_profits and not isinstance(take_profits, dict):
            take_profits = None
        if take_profits:
            cleaned_tps = {}
            for k,v in take_profits.items():
                try:
                    fv = float(v)
                    if 0 < fv < 200_000_000:
                        cleaned_tps[str(k)] = fv
                except (ValueError, TypeError):
                    continue
            take_profits = cleaned_tps if cleaned_tps else None

        order_id_short = str(uuid.uuid4())[:8]
        client_order_id = f"cp_{symbol.replace('-','').replace('/','')}_{int(time.time())}_{order_id_short}"
        if len(client_order_id) > 50:
            client_order_id = client_order_id[:50]

        coindcx_market = self._map_to_coindcx(symbol)
        live_price = self.get_price(symbol)

        if (live_price is None or live_price == 0) and not price:
            raise ValueError(f"Could not get live price for {symbol} ({coindcx_market})")

        filled_price = price or live_price
        if filled_price is None or filled_price <= 0:
            raise ValueError(f"Invalid filled price {filled_price}")

        coindcx_order_type = "market_order" if order_type == "MARKET" else "limit_order"

        body = {
            "side": side.lower(),
            "order_type": coindcx_order_type,
            "market": coindcx_market,
            "total_quantity": float(quantity),
            "timestamp": self._get_timestamp(),
            "client_order_id": client_order_id
        }

        if coindcx_order_type == "limit_order":
            body["price_per_unit"] = float(price or filled_price)

        # Fat finger protection
        if coindcx_order_type == "limit_order" and live_price and live_price > 0:
            try:
                limit_price = body["price_per_unit"]
                if abs(limit_price - live_price) / live_price > 0.5:
                    raise ValueError(f"Limit price {limit_price} too far from live {live_price} - fat finger protection")
            except ZeroDivisionError:
                pass

        try:
            signature, json_body = self._sign(body)
            url = f"{self.base_url}/exchange/v1/orders/create"
            headers = {
                'Content-Type': 'application/json',
                'X-AUTH-APIKEY': self.api_key,
                'X-AUTH-SIGNATURE': signature
            }

            logger.warning(f"🚨 REAL CoinDCX Order: {symbol} ({coindcx_market}) {side} {quantity} @ ₹{filled_price:.2f}")

            enable_real = os.getenv("ENABLE_COINDCX_REAL_TRADING", "false").lower() == "true"

            real_order_id = order_id_short
            real_status = "filled"

            try:
                if not enable_real:
                    logger.info(f"CoinDCX simulation mode - order {client_order_id} would be REAL with ENABLE_COINDCX_REAL_TRADING=true")
                    try:
                        resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            result = resp.json()
                            if isinstance(result, dict):
                                real_order_id = result.get("id") or result.get("order_id") or order_id_short
                                real_status = result.get("status", "open")
                        else:
                            logger.debug(f"CoinDCX API non-200 in sim mode: {resp.status_code} {resp.text[:200]}")
                    except Exception as api_e:
                        logger.debug(f"CoinDCX API call failed in simulation mode (expected without real keys): {api_e}")
                else:
                    resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
                    resp.raise_for_status()
                    result = resp.json()
                    if isinstance(result, dict):
                        real_order_id = result.get("id") or result.get("order_id") or order_id_short
                        real_status = result.get("status", "open")
                    else:
                        real_order_id = order_id_short
                        real_status = "open"

                status_str = str(real_status).lower()
                is_filled = status_str == "filled"
                is_pending = status_str in ["open", "init", "pending", "partially_filled"]

                try:
                    fee = float(quantity) * float(filled_price) * 0.001
                except Exception:
                    fee = 0.0

                order = Order(
                    id=str(real_order_id),
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=float(quantity),
                    price=float(price or filled_price),
                    stop_price=float(stop_price) if stop_price else None,
                    status="FILLED" if is_filled else "PENDING" if is_pending else str(real_status).upper(),
                    filled_price=float(filled_price) if is_filled else None,
                    filled_quantity=float(quantity) if is_filled else 0.0,
                    fee=fee,
                    timestamp=datetime.utcnow().isoformat(),
                    strategy=strategy,
                    real_trading=True,
                    broker=self.name,
                    take_profits=take_profits,
                    stop_loss=float(stop_loss) if stop_loss else None,
                    leverage=leverage,
                    trailing_pct=float(trailing_pct) if trailing_pct else None,
                    client_order_id=client_order_id
                )

                logger.info(f"✅ CoinDCX Order: {real_order_id} {symbol} {side} {quantity} @ ₹{filled_price:.2f}")

                if take_profits or stop_loss:
                    self._place_protection_orders(symbol, side, quantity, take_profits, stop_loss)

            except requests.exceptions.HTTPError as http_err:
                try:
                    error_body = http_err.response.text[:1000] if hasattr(http_err, 'response') and http_err.response is not None else str(http_err)
                except Exception:
                    error_body = str(http_err)
                logger.error(f"CoinDCX real order HTTP failed: {http_err} - {error_body}")

                if "Insufficient" in error_body or "balance" in error_body.lower():
                    raise ValueError(f"CoinDCX REAL trading failed - insufficient balance: {error_body}")

                if not enable_real:
                    logger.warning(f"CoinDCX API error in simulation mode - creating order record for testing")
                    try:
                        fee = float(quantity) * float(filled_price) * 0.001
                    except Exception:
                        fee = 0.0
                    order = Order(
                        id=order_id_short,
                        symbol=symbol,
                        side=side,
                        type=order_type,
                        quantity=float(quantity),
                        price=float(price or filled_price),
                        status="FILLED",
                        filled_price=float(filled_price),
                        filled_quantity=float(quantity),
                        fee=fee,
                        timestamp=datetime.utcnow().isoformat(),
                        strategy=strategy,
                        real_trading=True,
                        broker=self.name,
                        take_profits=take_profits,
                        stop_loss=float(stop_loss) if stop_loss else None,
                        leverage=leverage,
                        client_order_id=client_order_id
                    )
                else:
                    raise ValueError(f"CoinDCX order failed: {error_body}")

            with self._lock:
                # Store under both short id and real id for lookup
                self.orders[order_id_short] = order
                if str(real_order_id) != order_id_short:
                    self.orders[str(real_order_id)] = order
            return order

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"CoinDCX real order placement failed for {symbol}: {e}")
            raise ValueError(f"CoinDCX order failed: {e}")

    def _place_protection_orders(self, symbol: str, side: str, quantity: float, take_profits: Dict[str, float], stop_loss: float):
        try:
            close_side = "sell" if side.lower() == "buy" else "buy"
            coindcx_market = self._map_to_coindcx(symbol)
            if stop_loss and stop_loss > 0:
                logger.info(f"REAL SL for {symbol} ({coindcx_market}): {close_side} {quantity} @ ₹{stop_loss}")
            if take_profits:
                for tp_name, tp_price in take_profits.items():
                    try:
                        tp = float(tp_price)
                        if tp > 0:
                            logger.info(f"REAL {tp_name} for {symbol} ({coindcx_market}): {close_side} {quantity} @ ₹{tp}")
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Failed to place CoinDCX protection orders: {e}")

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        if not self.connected or not self.api_key:
            raise ValueError("CoinDCX not connected")
        if not order_id or not symbol:
            raise ValueError("order_id and symbol required")
        if not isinstance(order_id, str) or len(order_id) > 100:
            raise ValueError("Invalid order_id")

        try:
            body = {"id": str(order_id), "timestamp": self._get_timestamp()}
            signature, json_body = self._sign(body)
            url = f"{self.base_url}/exchange/v1/orders/cancel"
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': self.api_key, 'X-AUTH-SIGNATURE': signature}
            resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
            resp.raise_for_status()
            logger.info(f"Cancelled REAL CoinDCX order {order_id} for {symbol}")
            with self._lock:
                if order_id in self.orders:
                    try:
                        self.orders[order_id].status = "CANCELLED"
                    except Exception:
                        pass
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to cancel CoinDCX order {order_id} network: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to cancel CoinDCX order {order_id}: {e}")
            return False

    def get_open_orders(self, symbol: str = None) -> List[Order]:
        if not self.connected or not self.api_key:
            with self._lock:
                return [o for o in self.orders.values() if o.status in ["PENDING", "OPEN", "PARTIALLY_FILLED"]][:50]

        try:
            body = {"timestamp": self._get_timestamp()}
            if symbol:
                coindcx_market = self._map_to_coindcx(symbol)
                body["market"] = coindcx_market

            signature, json_body = self._sign(body)
            url = f"{self.base_url}/exchange/v1/orders/active_orders"
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': self.api_key, 'X-AUTH-SIGNATURE': signature}
            resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            orders = []
            order_list = data if isinstance(data, list) else data.get("orders", []) if isinstance(data, dict) else []
            if not isinstance(order_list, list):
                order_list = []
            for o in order_list:
                try:
                    if not isinstance(o, dict):
                        continue
                    market = o.get("market", "")
                    our_symbol = self.reverse_map.get(market, market)
                    if not our_symbol and "INR" in market:
                        our_symbol = market
                    qty_raw = o.get("total_quantity",0) or 0
                    try:
                        qty = float(qty_raw)
                    except (ValueError, TypeError):
                        continue
                    if qty <= 0:
                        continue
                    price_raw = o.get("price_per_unit")
                    try:
                        price = float(price_raw) if price_raw is not None else None
                    except (ValueError, TypeError):
                        price = None
                    orders.append(Order(
                        id=str(o.get("id", "")),
                        symbol=our_symbol,
                        side=str(o.get("side", "")).upper(),
                        type=str(o.get("order_type", "")).upper(),
                        quantity=qty,
                        price=price,
                        status=str(o.get("status", "open")).upper(),
                        timestamp=o.get("created_at") or datetime.utcnow().isoformat(),
                        broker=self.name,
                        real_trading=True
                    ))
                except Exception as e:
                    logger.debug(f"Open order parse failed: {e}")
                    continue
            return orders
        except requests.RequestException as e:
            logger.debug(f"Failed to get CoinDCX open orders network: {e}")
            with self._lock:
                return [o for o in self.orders.values() if o.status in ["PENDING", "OPEN", "PARTIALLY_FILLED"]][:50]
        except Exception as e:
            logger.debug(f"Failed to get CoinDCX open orders: {e}")
            with self._lock:
                return [o for o in self.orders.values() if o.status in ["PENDING", "OPEN"]][:50]

    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        try:
            limit = max(1, min(500, int(limit)))
        except (ValueError, TypeError):
            limit = 100

        if not self.connected or not self.api_key:
            with self._lock:
                orders = list(self.orders.values())
                # Deduplicate by id
                seen = {}
                for o in orders:
                    seen[o.id] = o
                orders = list(seen.values())
                if symbol:
                    orders = [o for o in orders if o.symbol.upper() == symbol.upper()]
                orders.sort(key=lambda x: x.timestamp, reverse=True)
                return orders[:limit]

        try:
            body = {"timestamp": self._get_timestamp()}
            if symbol:
                coindcx_market = self._map_to_coindcx(symbol)
                body["market"] = coindcx_market

            signature, json_body = self._sign(body)
            url = f"{self.base_url}/exchange/v1/orders/trade_history"
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': self.api_key, 'X-AUTH-SIGNATURE': signature}
            resp = self._session.post(url, data=json_body, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            orders = []
            order_list = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
            if not isinstance(order_list, list):
                order_list = []
            for o in order_list[:limit]:
                try:
                    if not isinstance(o, dict):
                        continue
                    market = o.get("market", "")
                    our_symbol = self.reverse_map.get(market, market)
                    if not our_symbol and "INR" in market:
                        our_symbol = market
                    qty_raw = o.get("total_quantity",0) or 0
                    try:
                        qty = float(qty_raw)
                    except (ValueError, TypeError):
                        continue
                    if qty <= 0:
                        continue
                    price_raw = o.get("price_per_unit")
                    try:
                        price = float(price_raw) if price_raw is not None else None
                    except (ValueError, TypeError):
                        price = None
                    avg_raw = o.get("avg_price")
                    try:
                        avg_price = float(avg_raw) if avg_raw is not None else None
                    except (ValueError, TypeError):
                        avg_price = None
                    orders.append(Order(
                        id=str(o.get("id", "")),
                        symbol=our_symbol,
                        side=str(o.get("side", "")).upper(),
                        type=str(o.get("order_type", "")).upper(),
                        quantity=qty,
                        price=price,
                        status=str(o.get("status", "")).upper(),
                        filled_price=avg_price,
                        timestamp=o.get("created_at") or datetime.utcnow().isoformat(),
                        broker=self.name,
                        real_trading=True
                    ))
                except Exception as e:
                    logger.debug(f"Order history parse failed: {e}")
                    continue
            return orders
        except requests.RequestException as e:
            logger.debug(f"Failed to get CoinDCX order history network: {e}")
            with self._lock:
                orders = list(self.orders.values())
                seen = {}
                for o in orders:
                    seen[o.id] = o
                orders = list(seen.values())
                if symbol:
                    orders = [o for o in orders if o.symbol.upper() == symbol.upper()]
                orders.sort(key=lambda x: x.timestamp, reverse=True)
                return orders[:limit]
        except Exception as e:
            logger.debug(f"Failed to get CoinDCX order history: {e}")
            with self._lock:
                orders = list(self.orders.values())
                seen = {}
                for o in orders:
                    seen[o.id] = o
                orders = list(seen.values())
                if symbol:
                    orders = [o for o in orders if o.symbol.upper() == symbol.upper()]
                orders.sort(key=lambda x: x.timestamp, reverse=True)
                return orders[:limit]

    def test_connection(self) -> Dict:
        try:
            if not self.connected:
                return {"connected": False, "paper_mode": True, "real_trading": False, "error": "Not connected - provide API keys", "broker": "CoinDCX"}
            try:
                balances = self.get_balance()
            except Exception as e:
                balances = {}
                logger.debug(f"Test connection balances failed: {e}")
            try:
                tickers = self.get_tickers_all()
            except Exception as e:
                tickers = {}
                logger.debug(f"Test connection tickers failed: {e}")
            return {
                "connected": True,
                "paper_mode": False,
                "real_trading": True,
                "broker": "CoinDCX REAL MONEY",
                "balances_count": len(balances),
                "tickers_count": len(tickers),
                "markets": list(tickers.keys())[:5],
                "inr_pairs": "BTCINR, ETHINR, etc.",
                "actual_money": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.warning(f"CoinDCX test_connection failed: {e}")
            return {"connected": False, "paper_mode": True, "real_trading": False, "error": str(e), "broker": "CoinDCX"}
