"""
Real-time crypto data ingestion via Binance WebSocket + REST fallback + CoinDCX INR integration
Fixed: thread safety, CoinDCX fallback, validation, error handling
"""
import asyncio
import json
import time
from collections import deque
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading

import requests
import pandas as pd

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class BinanceRealtimeFetcher:
    def __init__(self, symbol: str = "BTC-USD", buffer_size: int = None):
        self.symbol = symbol
        self.binance_symbol = config.data.binance_map.get(symbol, "BTCUSDT")
        self.buffer_size = buffer_size or config.realtime.buffer_size
        self.buffer = deque(maxlen=self.buffer_size)
        self.ohlcv_buffer = deque(maxlen=self.buffer_size)
        self.callbacks: List[Callable] = []
        self.running = False
        self.ws_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.rest_url = config.realtime.rest_url
        self._lock = threading.Lock()
        self._last_price = 0.0

    def fetch_ohlcv_rest(self, interval: str = "1m", limit: int = 500) -> pd.DataFrame:
        try:
            url = f"{self.rest_url}/api/v3/klines"
            params = {"symbol": self.binance_symbol, "interval": interval, "limit": max(1, min(1000, limit))}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("Empty klines response")
            df = pd.DataFrame(data, columns=[
                "open_time", "Open", "High", "Low", "Close", "Volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore"
            ])
            df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
            df.set_index("open_time", inplace=True)
            df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
            logger.info(f"REST fetched {len(df)} {interval} candles for {self.binance_symbol}")
            return df
        except requests.RequestException as e:
            logger.warning(f"REST fetch network failed {self.binance_symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"REST fetch failed {self.binance_symbol}: {e}")
            raise

    def fetch_ticker_rest(self) -> Dict:
        try:
            url = f"{self.rest_url}/api/v3/ticker/24hr"
            params = {"symbol": self.binance_symbol}
            resp = requests.get(url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and data.get("symbol"):
                return data
            return {}
        except requests.RequestException as e:
            logger.debug(f"Ticker fetch network failed {self.binance_symbol}: {e}")
            return {}
        except Exception as e:
            logger.debug(f"Ticker fetch failed {self.binance_symbol}: {e}")
            return {}

    def get_orderbook(self, limit: int = 20) -> Optional[Dict]:
        """Orderbook for bots - real Binance depth"""
        try:
            limit = max(5, min(100, limit))
            resp = requests.get(f"{self.rest_url}/api/v3/depth", params={"symbol": self.binance_symbol, "limit": limit}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'bids' in data and 'asks' in data:
                    return data
        except requests.RequestException as e:
            logger.debug(f"Orderbook fetch failed {self.binance_symbol}: {e}")
        except Exception as e:
            logger.debug(f"Orderbook unexpected {self.binance_symbol}: {e}")
        return None

    async def _ws_handler(self):
        import websockets
        uri = f"{config.realtime.ws_url}/{self.binance_symbol.lower()}@trade"
        logger.info(f"Connecting to Binance WS: {uri}")

        while self.running:
            try:
                async with websockets.connect(uri, ping_interval=20, close_timeout=10) as ws:
                    logger.info(f"WS connected for {self.binance_symbol}")
                    async for msg in ws:
                        if not self.running:
                            break
                        try:
                            data = json.loads(msg)
                            price_raw = data.get('p', 0)
                            qty_raw = data.get('q', 0)
                            try:
                                price = float(price_raw)
                                qty = float(qty_raw)
                            except (ValueError, TypeError):
                                continue
                            if price <= 0 or price > 10_000_000 or qty <= 0:
                                continue
                            trade = {
                                "symbol": data.get('s'),
                                "price": price,
                                "qty": qty,
                                "time": pd.to_datetime(data.get('T', 0), unit='ms'),
                                "is_buyer_maker": data.get('m', False)
                            }
                            with self._lock:
                                self.buffer.append(trade)
                                self._last_price = price
                            for cb in self.callbacks:
                                try:
                                    cb(trade)
                                except Exception as e:
                                    logger.warning(f"Callback failed: {e}")
                        except (ValueError, TypeError, KeyError) as e:
                            logger.debug(f"WS message parse failed: {e}")
                            continue
                        except Exception as e:
                            logger.warning(f"WS message unexpected: {e}")
                            continue
            except asyncio.CancelledError:
                logger.info(f"WS handler cancelled for {self.binance_symbol}")
                break
            except Exception as e:
                logger.warning(f"WS connection lost {self.binance_symbol}: {e}, reconnecting in {config.realtime.reconnect_interval}s")
                try:
                    await asyncio.sleep(config.realtime.reconnect_interval)
                except asyncio.CancelledError:
                    break

    def _run_loop(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._ws_handler())
        except Exception as e:
            logger.error(f"WS loop failed {self.binance_symbol}: {e}")
        finally:
            try:
                self.loop.close()
            except Exception:
                pass

    def start(self):
        if self.running:
            return
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_loop, daemon=True, name=f"WS-{self.binance_symbol}")
        self.ws_thread.start()
        logger.info(f"Started realtime fetcher for {self.symbol} ({self.binance_symbol})")

    def stop(self):
        self.running = False
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception:
                pass
        if self.ws_thread:
            try:
                self.ws_thread.join(timeout=3)
            except Exception:
                pass
        logger.info(f"Stopped realtime fetcher {self.binance_symbol}")

    def add_callback(self, cb: Callable):
        if callable(cb):
            self.callbacks.append(cb)

    def get_latest_trades(self, n: int = 100) -> List[Dict]:
        try:
            n = max(1, min(1000, n))
            with self._lock:
                return list(self.buffer)[-n:]
        except Exception:
            return []

    def get_current_price(self) -> Optional[float]:
        # Try buffer first
        try:
            with self._lock:
                if self.buffer:
                    price = self.buffer[-1].get('price')
                    if price and 0 < price < 10_000_000:
                        return float(price)
                if self._last_price and 0 < self._last_price < 10_000_000:
                    return float(self._last_price)
        except Exception as e:
            logger.debug(f"Buffer price read failed {self.binance_symbol}: {e}")

        # Try Binance REST
        try:
            ticker = self.fetch_ticker_rest()
            lp = ticker.get('lastPrice')
            if lp:
                p = float(lp)
                if 0 < p < 10_000_000:
                    with self._lock:
                        self._last_price = p
                    return p
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"REST price parse failed {self.binance_symbol}: {e}")
        except Exception as e:
            logger.debug(f"REST price failed {self.binance_symbol}: {e}")

        # Try CoinDCX fallback for INR markets or when Binance blocked
        try:
            from .coindcx_fetcher import CoinDCXRealtimeFetcher
            # If symbol is USD, try to get INR then convert back, or if INR symbol use CoinDCX directly
            coindcx = CoinDCXRealtimeFetcher(symbol=self.symbol)
            inr_price = coindcx.get_current_price()
            if inr_price and inr_price > 0:
                # If original symbol is USD, convert INR back to USD
                if "USD" in self.symbol.upper() and "INR" not in self.symbol.upper():
                    usd_price = inr_price / 83.5
                    if 0 < usd_price < 10_000_000:
                        with self._lock:
                            self._last_price = usd_price
                        return usd_price
                else:
                    # INR symbol, return INR price
                    return inr_price
        except Exception as e:
            logger.debug(f"CoinDCX fallback for {self.symbol} failed: {e}")

        # Last resort: cached file directly (avoid yfinance recursion)
        try:
            from pathlib import Path
            import pandas as pd
            cache_path = config.project_root / "data" / "raw" / f"{self.symbol.replace('-','_')}_1d.csv"
            if cache_path.exists():
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if not df.empty:
                    p = float(df['Close'].iloc[-1])
                    if 0 < p < 10_000_000:
                        with self._lock:
                            self._last_price = p
                        return p
        except Exception:
            pass

        with self._lock:
            return self._last_price if self._last_price > 0 else None

    def to_dataframe(self) -> pd.DataFrame:
        try:
            with self._lock:
                if not self.buffer:
                    return pd.DataFrame()
                data = list(self.buffer)
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            if 'time' not in df.columns:
                return pd.DataFrame()
            df.set_index('time', inplace=True)
            df.sort_index(inplace=True)
            return df
        except Exception as e:
            logger.debug(f"to_dataframe failed {self.binance_symbol}: {e}")
            return pd.DataFrame()

class RealtimeManager:
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or config.data.supported_symbols[:3]
        self.fetchers: Dict[str, BinanceRealtimeFetcher] = {}
        self._lock = threading.Lock()
        for sym in self.symbols:
            try:
                self.fetchers[sym] = BinanceRealtimeFetcher(symbol=sym)
            except Exception as e:
                logger.warning(f"Failed to create fetcher for {sym}: {e}")

    def start_all(self):
        with self._lock:
            for f in self.fetchers.values():
                try:
                    f.start()
                except Exception as e:
                    logger.warning(f"Failed to start fetcher: {e}")

    def stop_all(self):
        with self._lock:
            for f in self.fetchers.values():
                try:
                    f.stop()
                except Exception as e:
                    logger.debug(f"Failed to stop fetcher: {e}")

    def get_prices(self) -> Dict[str, float]:
        result={}
        with self._lock:
            fetchers = list(self.fetchers.items())
        for sym, fetcher in fetchers:
            try:
                price = fetcher.get_current_price()
                if price and price > 0:
                    result[sym] = price
            except Exception as e:
                logger.debug(f"get_prices failed for {sym}: {e}")
                continue
        return result

    def get_coindcx_prices(self) -> Dict[str, float]:
        """Get CoinDCX INR prices for integration"""
        try:
            from .coindcx_fetcher import get_coindcx_tickers_cached
            tickers = get_coindcx_tickers_cached()
            return {k: v.get("price",0) for k,v in tickers.items() if v.get("price",0)>0}
        except Exception as e:
            logger.debug(f"get_coindcx_prices failed: {e}")
            return {}

class LivePredictor:
    def __init__(self, symbol: str = "BTC-USD"):
        from ..prediction.predictor import CryptoPredictor
        self.symbol = symbol
        self.fetcher = BinanceRealtimeFetcher(symbol=symbol)
        self.predictor = CryptoPredictor(symbol=symbol)
        self.price_history = deque(maxlen=1000)
        self._lock = threading.Lock()
        self.fetcher.add_callback(self._on_trade)

    def _on_trade(self, trade: Dict):
        try:
            with self._lock:
                self.price_history.append(trade)
        except Exception:
            pass

    def start(self):
        try:
            self.fetcher.start()
        except Exception as e:
            logger.warning(f"LivePredictor start failed {self.symbol}: {e}")

    def stop(self):
        try:
            self.fetcher.stop()
        except Exception as e:
            logger.debug(f"LivePredictor stop failed {self.symbol}: {e}")

    def get_live_signal(self) -> Dict:
        current_price = None
        try:
            current_price = self.fetcher.get_current_price()
        except Exception:
            pass

        try:
            forecast = self.predictor.forecast(steps=1, period="1y")
            signal = self.predictor.get_trading_signal(forecast)
            if current_price and current_price > 0:
                signal['live_price'] = current_price
                pred = signal.get('predicted_price', current_price)
                try:
                    signal['live_change_pct'] = (pred - current_price) / current_price * 100 if current_price else 0
                except (ZeroDivisionError, TypeError):
                    signal['live_change_pct'] = 0
                signal['real_data'] = True
                signal['source'] = "Binance Live + CoinDCX INR fallback"
            return signal
        except Exception as e:
            logger.warning(f"Live signal failed {self.symbol}: {e}")
            return {"symbol": self.symbol, "live_price": current_price, "signal": "HOLD", "reason": str(e), "real_data": False}
