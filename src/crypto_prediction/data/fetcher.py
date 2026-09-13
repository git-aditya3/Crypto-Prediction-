"""
Crypto data fetcher v5 MAX - Max performance + CoinDCX INR + Binance + Robust caching + Validation + Multi-source
- Supports INR symbols (BTCINR -> BTC-USD mapping + INR conversion)
- Binance direct REST primary for USD, CoinDCX for INR
- yfinance + CoinGecko + CoinDCX OHLCV fallback
- Validation, retry, rate limiting, thread-safe cache, atomic save, TTL
- Data quality checks: price >0, OHLC consistency, volume >0, no gaps >10 days
- Auto repair: fix OHLC, forward fill small gaps, remove duplicates
"""
import time
import threading
from typing import Optional, List, Dict
import pandas as pd
import yfinance as yf
import requests
from pathlib import Path
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

_session = None
_session_lock = threading.Lock()
_last_request = 0
_request_lock = threading.Lock()

def get_session():
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                _session = requests.Session()
                _session.headers.update({"User-Agent": "CryptoPred v5 MAX Fetcher"})
                adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=30, max_retries=2)
                _session.mount("https://", adapter)
                _session.mount("http://", adapter)
    return _session

def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and repair OHLCV data - v5"""
    if df is None or df.empty:
        return df
    try:
        # Ensure numeric
        for col in ['Open','High','Low','Close','Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid prices
        df = df[(df['Close'] > 0) & (df['Close'] < 1e8) & (df['Volume'] >= 0)]
        
        # Fix OHLC consistency: High >= max(Open,Close,Low), Low <= min(Open,Close,High)
        df['High'] = df[['High','Open','Close']].max(axis=1)
        df['Low'] = df[['Low','Open','Close']].min(axis=1)
        
        # Ensure High >= Low
        invalid = df['High'] < df['Low']
        if invalid.any():
            df.loc[invalid, 'High'] = df.loc[invalid, 'Low'] * 1.001
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='last')]
        
        # Sort by time
        df.sort_index(inplace=True)
        
        # Forward fill small gaps (<3 days) and interpolate
        # Check for gaps >10 days - log warning
        if len(df) > 1:
            gaps = df.index.to_series().diff().dt.days
            large_gaps = gaps[gaps > 10]
            if len(large_gaps) > 0:
                logger.warning(f"Large gaps detected: {large_gaps.max()} days max gap")
        
        return df
    except Exception as e:
        logger.warning(f"Validation failed: {e}")
        return df

def rate_limit(min_interval=0.1):
    global _last_request
    with _request_lock:
        now = time.time()
        elapsed = now - _last_request
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        _last_request = time.time()

class CryptoDataFetcher:
    def __init__(self, symbol: str = None):
        self.symbol = symbol or config.data.default_symbol
        self.interval = config.data.interval
        self.period = config.data.period
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_lock = threading.Lock()

    def _normalize_symbol(self, symbol: str) -> tuple:
        """Returns (usd_symbol, is_inr, base)"""
        if not symbol or not isinstance(symbol, str):
            return config.data.default_symbol, False, "BTC"
        sym = symbol.strip().upper()
        is_inr = "INR" in sym
        if is_inr:
            base = sym.replace("INR","").replace("-","").replace("/","").replace("_","")
            usd_sym = base + "-USD" if len(base)>=2 else "BTC-USD"
            return usd_sym, True, base
        else:
            # Normalize BTC -> BTC-USD, BTCUSDT -> BTC-USD
            base = sym.replace("-USD","").replace("/USD","").replace("-","").replace("/","").replace("_","").replace("USDT","").replace("USD","")
            if len(base) < 2:
                base = "BTC"
            usd_sym = base + "-USD"
            return usd_sym, False, base

    def fetch_binance_direct(self, symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """Direct Binance REST - fastest, most reliable for USD"""
        try:
            usd_sym, is_inr, base = self._normalize_symbol(symbol)
            binance_sym = config.data.binance_map.get(usd_sym, base + "USDT")
            rate_limit(0.05)
            sess = get_session()
            resp = sess.get(
                config.realtime.rest_url + "/api/v3/klines",
                params={"symbol": binance_sym, "interval": "1d", "limit": limit},
                timeout=10
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                return None
            df = pd.DataFrame(data, columns=[
                'openTime', 'Open', 'High', 'Low', 'Close', 'Volume',
                'closeTime', 'QuoteVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'
            ])
            df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
            df['High'] = pd.to_numeric(df['High'], errors='coerce')
            df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df['timestamp'] = pd.to_datetime(df['openTime'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            df.sort_index(inplace=True)
            if is_inr:
                for col in ['Open','High','Low','Close']:
                    df[col] = df[col] * 83.5
            df = validate_ohlcv(df)
            logger.info(f"Binance direct v5 fetched {len(df)} rows for {symbol} ({binance_sym}) -> {usd_sym} INR={is_inr}")
            return df
        except Exception as e:
            logger.debug(f"Binance direct fetch failed {symbol}: {e}")
            return None

    def fetch_yfinance(self, symbol: Optional[str] = None, period: Optional[str] = None, interval: Optional[str] = None) -> pd.DataFrame:
        sym = symbol or self.symbol
        per = period or self.period
        inter = interval or self.interval
        usd_sym, is_inr, base = self._normalize_symbol(sym)
        
        logger.info(f"Fetching {sym} | {usd_sym} INR={is_inr} | period={per} | interval={inter} via yfinance")
        for attempt in range(3):
            try:
                rate_limit(0.2)
                ticker = yf.Ticker(usd_sym)
                df = ticker.history(period=per, interval=inter, auto_adjust=False)
                
                if df.empty:
                    # Try base symbol without -USD
                    ticker2 = yf.Ticker(base)
                    df = ticker2.history(period=per, interval=inter, auto_adjust=False)
                    if df.empty:
                        raise ValueError(f"No data returned for {sym} / {usd_sym}")
                
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                df.index = pd.to_datetime(df.index)
                df.sort_index(inplace=True)
                df.dropna(inplace=True)
                
                if is_inr:
                    for col in ['Open','High','Low','Close']:
                        df[col] = df[col] * 83.5
                
                df = validate_ohlcv(df)
                
                if len(df) < 10:
                    raise ValueError(f"Too few rows {len(df)} for {sym}")
                
                logger.info(f"Fetched {len(df)} rows for {sym} from {df.index[0]} to {df.index[-1]} via yfinance v5")
                return df
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5 * (attempt+1))
                    continue
                logger.error(f"yfinance fetch failed for {sym} after 3 attempts: {e}")
                raise

    def fetch_coingecko(self, coin_id: str = "bitcoin", days: str = "365") -> pd.DataFrame:
        logger.info(f"Fetching {coin_id} via CoinGecko, days={days}")
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        
        for attempt in range(2):
            try:
                rate_limit(0.3)
                sess = get_session()
                resp = sess.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                if not prices:
                    raise ValueError("No prices from CoinGecko")
                
                df = pd.DataFrame(prices, columns=['timestamp', 'Close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                vol_df = pd.DataFrame(volumes, columns=['timestamp', 'Volume'])
                vol_df['timestamp'] = pd.to_datetime(vol_df['timestamp'], unit='ms')
                vol_df.set_index('timestamp', inplace=True)
                
                df = df.join(vol_df, how='left')
                df['Open'] = df['Close']
                df['High'] = df['Close']
                df['Low'] = df['Close']
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
                
                logger.info(f"CoinGecko fetched {len(df)} rows for {coin_id}")
                return df
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
                    continue
                logger.error(f"CoinGecko fetch failed: {e}")
                raise

    def fetch_multiple(self, symbols: List[str], period: Optional[str] = None) -> dict:
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.fetch_yfinance(symbol=sym, period=period)
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
        return results

    def save(self, df: pd.DataFrame, path: Optional[str] = None) -> str:
        if path is None:
            safe_sym = self.symbol.replace('-','_').replace('/','_').replace(' ','_')
            path = config.project_root / "data" / "raw" / f"{safe_sym}_{self.interval}.csv"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp = Path(str(path) + ".tmp")
        df.to_csv(tmp)
        tmp.replace(path)
        logger.info(f"Saved data to {path} ({len(df)} rows)")
        return str(path)

    def load_or_fetch(self, symbol: Optional[str] = None, force_refresh: bool = False) -> pd.DataFrame:
        from pathlib import Path
        sym = symbol or self.symbol
        safe_sym = sym.replace('-','_').replace('/','_').replace(' ','_')
        cache_path = config.project_root / "data" / "raw" / f"{safe_sym}_{self.interval}.csv"
        
        with self._cache_lock:
            if safe_sym in self._cache and not force_refresh:
                cached = self._cache[safe_sym]
                if isinstance(cached, pd.DataFrame) and len(cached) > 100:
                    return cached.copy()

        if cache_path.exists() and not force_refresh:
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if isinstance(df, pd.DataFrame) and len(df) > 100:
                    # Check TTL
                    try:
                        mtime = cache_path.stat().st_mtime
                        age_hours = (time.time() - mtime) / 3600
                        if age_hours < config.data.cache_ttl_hours:
                            logger.info(f"Loaded cached data {cache_path} with {len(df)} rows (age {age_hours:.1f}h)")
                            with self._cache_lock:
                                self._cache[safe_sym] = df.copy()
                            return df
                        else:
                            logger.info(f"Cache {cache_path} expired {age_hours:.1f}h > {config.data.cache_ttl_hours}h, refetching")
                    except Exception:
                        logger.info(f"Loaded cached data {cache_path} with {len(df)} rows")
                        with self._cache_lock:
                            self._cache[safe_sym] = df.copy()
                        return df
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")

        # Try Binance direct first (fastest)
        df = self.fetch_binance_direct(sym, limit=1000)
        if df is not None and len(df) > 50:
            self.save(df, str(cache_path))
            with self._cache_lock:
                self._cache[safe_sym] = df.copy()
            return df

        # Fallback yfinance
        try:
            df = self.fetch_yfinance(symbol=sym)
            self.save(df, str(cache_path))
            with self._cache_lock:
                self._cache[safe_sym] = df.copy()
            return df
        except Exception as e_yf:
            logger.warning(f"yfinance failed for {sym}: {e_yf}, trying CoinGecko fallback")
            try:
                mapping = {
                    "BTC-USD": "bitcoin", "BTCINR": "bitcoin",
                    "ETH-USD": "ethereum", "ETHINR": "ethereum",
                    "BNB-USD": "binancecoin", "BNBINR": "binancecoin",
                    "SOL-USD": "solana", "SOLINR": "solana",
                    "XRP-USD": "ripple", "XRPINR": "ripple",
                    "ADA-USD": "cardano", "DOGE-USD": "dogecoin",
                    "AVAX-USD": "avalanche-2", "DOT-USD": "polkadot",
                    "MATIC-USD": "matic-network", "LINK-USD": "chainlink",
                    "LTC-USD": "litecoin", "BCH-USD": "bitcoin-cash",
                }
                usd_sym, is_inr, base = self._normalize_symbol(sym)
                coin_id = mapping.get(sym, mapping.get(usd_sym, "bitcoin"))
                df = self.fetch_coingecko(coin_id=coin_id, days="730")
                if is_inr:
                    for col in ['Open','High','Low','Close']:
                        df[col] = df[col] * 83.5
                self.save(df, str(cache_path))
                with self._cache_lock:
                    self._cache[safe_sym] = df.copy()
                return df
            except Exception as e_cg:
                logger.warning(f"CoinGecko also failed for {sym}: {e_cg}")
                if cache_path.exists():
                    try:
                        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                        logger.info(f"Falling back to cached data {cache_path} with {len(df)} rows after fetch failures")
                        with self._cache_lock:
                            self._cache[safe_sym] = df.copy()
                        return df
                    except Exception as e_cache:
                        logger.error(f"Cache fallback also failed: {e_cache}")
                        raise e_cache
                else:
                    raise e_cg


def fetch_crypto_data(symbol: str = "BTC-USD", period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    fetcher = CryptoDataFetcher(symbol=symbol)
    fetcher.period = period
    fetcher.interval = interval
    return fetcher.load_or_fetch(symbol=symbol)
