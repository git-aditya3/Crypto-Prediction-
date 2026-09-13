"""
Real-time crypto data ingestion via Binance WebSocket + REST fallback
Supports live streaming, buffering, and integration with prediction pipeline
"""
import asyncio
import json
import time
from collections import deque
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading
import queue

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
        self.buffer = deque(maxlen=self.buffer_size)  # stores trade dicts
        self.ohlcv_buffer = deque(maxlen=self.buffer_size)  # 1m candles
        self.callbacks: List[Callable] = []
        self.running = False
        self.ws_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # REST fallback
        self.rest_url = config.realtime.rest_url

    def fetch_ohlcv_rest(self, interval: str = "1m", limit: int = 500) -> pd.DataFrame:
        """Fetch recent OHLCV via REST"""
        try:
            url = f"{self.rest_url}/api/v3/klines"
            params = {"symbol": self.binance_symbol, "interval": interval, "limit": limit}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
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
        except Exception as e:
            logger.error(f"REST fetch failed: {e}")
            raise

    def fetch_ticker_rest(self) -> Dict:
        try:
            url = f"{self.rest_url}/api/v3/ticker/24hr"
            params = {"symbol": self.binance_symbol}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Ticker fetch failed: {e}")
            return {}

    # ---- WebSocket via websockets library (async) ----
    async def _ws_handler(self):
        import websockets
        uri = f"{config.realtime.ws_url}/{self.binance_symbol.lower()}@trade"
        kline_uri = f"{config.realtime.ws_url}/{self.binance_symbol.lower()}@kline_1m"

        logger.info(f"Connecting to Binance WS: {uri}")

        while self.running:
            try:
                async with websockets.connect(uri, ping_interval=20) as ws:
                    logger.info(f"WS connected for {self.binance_symbol}")
                    async for msg in ws:
                        if not self.running:
                            break
                        try:
                            data = json.loads(msg)
                            trade = {
                                "symbol": data.get('s'),
                                "price": float(data.get('p', 0)),
                                "qty": float(data.get('q', 0)),
                                "time": pd.to_datetime(data.get('T', 0), unit='ms'),
                                "is_buyer_maker": data.get('m', False)
                            }
                            self.buffer.append(trade)
                            # callbacks
                            for cb in self.callbacks:
                                try:
                                    cb(trade)
                                except Exception as e:
                                    logger.warning(f"Callback failed: {e}")
                        except Exception as e:
                            logger.warning(f"WS message parse failed: {e}")
            except Exception as e:
                logger.warning(f"WS connection lost: {e}, reconnecting in {config.realtime.reconnect_interval}s")
                await asyncio.sleep(config.realtime.reconnect_interval)

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._ws_handler())

    def start(self):
        if self.running:
            return
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.ws_thread.start()
        logger.info(f"Started realtime fetcher for {self.symbol} ({self.binance_symbol})")

    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info("Stopped realtime fetcher")

    def add_callback(self, cb: Callable):
        self.callbacks.append(cb)

    def get_latest_trades(self, n: int = 100) -> List[Dict]:
        return list(self.buffer)[-n:]

    def get_current_price(self) -> Optional[float]:
        try:
            if self.buffer:
                price = self.buffer[-1].get('price')
                if price and price > 0 and price < 10_000_000:
                    return float(price)
        except Exception as e:
            logger.debug(f"Buffer price read failed: {e}")
        # fallback REST
        try:
            ticker = self.fetch_ticker_rest()
            lp = ticker.get('lastPrice', 0)
            if lp:
                p = float(lp)
                if p > 0 and p < 10_000_000:
                    return p
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"REST price parse failed: {e}")
        except Exception as e:
            logger.debug(f"REST price failed: {e}")
        return None

    def to_dataframe(self) -> pd.DataFrame:
        if not self.buffer:
            return pd.DataFrame()
        df = pd.DataFrame(list(self.buffer))
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        return df

# ---- Manager for multiple symbols ----
class RealtimeManager:
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or config.data.supported_symbols[:3]
        self.fetchers: Dict[str, BinanceRealtimeFetcher] = {}
        for sym in self.symbols:
            self.fetchers[sym] = BinanceRealtimeFetcher(symbol=sym)

    def start_all(self):
        for f in self.fetchers.values():
            f.start()

    def stop_all(self):
        for f in self.fetchers.values():
            f.stop()

    def get_prices(self) -> Dict[str, float]:
        return {sym: fetcher.get_current_price() for sym, fetcher in self.fetchers.items()}

# ---- Integration with prediction pipeline ----
class LivePredictor:
    def __init__(self, symbol: str = "BTC-USD"):
        from ..prediction.predictor import CryptoPredictor
        self.symbol = symbol
        self.fetcher = BinanceRealtimeFetcher(symbol=symbol)
        self.predictor = CryptoPredictor(symbol=symbol)
        self.price_history = deque(maxlen=1000)

        self.fetcher.add_callback(self._on_trade)

    def _on_trade(self, trade: Dict):
        self.price_history.append(trade)
        # Optionally trigger prediction every N trades

    def start(self):
        self.fetcher.start()

    def stop(self):
        self.fetcher.stop()

    def get_live_signal(self) -> Dict:
        current_price = self.fetcher.get_current_price()
        # Get forecast from stored models (1d)
        try:
            forecast = self.predictor.forecast(steps=1, period="1y")
            signal = self.predictor.get_trading_signal(forecast)
            # Override current price with live
            if current_price:
                signal['live_price'] = current_price
                # Recalc change
                pred = signal['predicted_price']
                signal['live_change_pct'] = (pred - current_price) / current_price * 100 if current_price else 0
            return signal
        except Exception as e:
            logger.warning(f"Live signal failed: {e}")
            return {"symbol": self.symbol, "live_price": current_price, "signal": "HOLD", "reason": str(e)}
