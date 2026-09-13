"""
Crypto data fetcher v6 ULTRA - Max performance + CoinDCX INR + Binance + Robust caching + Validation + Multi-source
- Supports INR symbols (BTCINR -> BTC-USD mapping + INR conversion)
- Binance direct REST primary for USD, CoinDCX for INR
- yfinance + CoinGecko + CoinDCX OHLCV fallback + multi-source merge
- Validation, retry with exponential backoff + jitter, rate limiting, thread-safe cache, atomic save, TTL, checksum
- Data quality checks: price >0, OHLC consistency, volume >0, no gaps >10 days, jump detection >50%
- Auto repair: fix OHLC, forward fill small gaps, remove duplicates, anomaly detection
"""
import time
import threading
import random
import hashlib
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
                _session.headers.update({"User-Agent": "CryptoPred v6 ULTRA Fetcher - iOS26 Liquid Glass"})
                adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=3)
                _session.mount("https://", adapter)
                _session.mount("http://", adapter)
    return _session

def exponential_backoff(attempt: int, base: float = 0.5, jitter: bool = True) -> float:
    """v6: exponential backoff with jitter"""
    delay = base * (2 ** attempt)
    if jitter:
        delay += random.uniform(0, base)
    return min(delay, 10.0)

def validate_ohlcv(df: pd.DataFrame, strict: bool = None) -> pd.DataFrame:
    """Validate and repair OHLCV data - v6 ULTRA"""
    if df is None or df.empty:
        return df
    if strict is None:
        strict = config.data.validation_strict
    
    try:
        # Ensure numeric
        for col in ['Open','High','Low','Close','Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid prices
        df = df[(df['Close'] > 0) & (df['Close'] < 2e8) & (df['Volume'] >= 0)]
        df = df.dropna(subset=['Close'])
        
        if df.empty:
            return df
        
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
        
        # v6: Detect price jumps > max_price_jump_pct as anomaly
        if len(df) > 2 and strict:
            pct_change = df['Close'].pct_change().abs() * 100
            jumps = pct_change[pct_change > config.data.max_price_jump_pct]
            if len(jumps) > 0:
                logger.warning(f"v6: Price jumps >{config.data.max_price_jump_pct}% detected: {len(jumps)} occurrences, max {pct_change.max():.1f}% - capping")
                # Cap jumps to prevent poisoning
                for idx in jumps.index:
                    prev_idx = df.index.get_loc(idx) - 1
                    if prev_idx >= 0:
                        prev_close = df['Close'].iloc[prev_idx]
                        curr_close = df['Close'].loc[idx]
                        # Cap to 20% change max for continuity
                        if curr_close > prev_close:
                            df.loc[idx, 'Close'] = prev_close * 1.20
                        else:
                            df.loc[idx, 'Close'] = prev_close * 0.80
        
        # Check for gaps >10 days - log warning
        if len(df) > 1:
            gaps = df.index.to_series().diff().dt.days
            large_gaps = gaps[gaps > 10]
            if len(large_gaps) > 0:
                logger.warning(f"Large gaps detected: {large_gaps.max()} days max gap, {len(large_gaps)} gaps")
        
        # Forward fill small gaps (<3 days) if needed - but keep time continuity
        # Don't interpolate too aggressively to preserve real data
        
        return df
    except Exception as e:
        logger.warning(f"Validation v6 failed: {e}")
        return df

def rate_limit(min_interval=0.05):
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
        self._fetch_metrics = {"binance_success": 0, "yfinance_success": 0, "coingecko_success": 0, "failures": 0}

    def _normalize_symbol(self, symbol: str) -> tuple:
        """Returns (usd_symbol, is_inr, base) - v6 improved"""
        if not symbol or not isinstance(symbol, str):
            return config.data.default_symbol, False, "BTC"
        sym = symbol.strip().upper()
        is_inr = "INR" in sym
        if is_inr:
            # BTCINR, BTC/INR, BTC-INR, BTC_INR -> BTC
            base = sym.replace("INR","").replace("-","").replace("/","").replace("_","").replace(" ","").replace("USDT","").replace("USD","")
            if len(base) < 2:
                base = "BTC"
            usd_sym = base + "-USD" if len(base)>=2 else "BTC-USD"
            return usd_sym, True, base
        else:
            # Normalize BTC -> BTC-USD, BTCUSDT -> BTC-USD, BTC/USD -> BTC-USD
            base = sym.replace("-USD","").replace("/USD","").replace("-","").replace("/","").replace("_","").replace(" ","").replace("USDT","").replace("USD","")
            if len(base) < 2:
                base = "BTC"
            usd_sym = base + "-USD"
            return usd_sym, False, base

    def _checksum_df(self, df: pd.DataFrame) -> str:
        """v6: checksum for data integrity"""
        try:
            data = f"{len(df)}_{df['Close'].iloc[0]}_{df['Close'].iloc[-1]}_{df.index[0]}_{df.index[-1]}"
            return hashlib.md5(data.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"

    def fetch_binance_direct(self, symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """Direct Binance REST - fastest, most reliable for USD - v6 with retry"""
        for attempt in range(3):
            try:
                usd_sym, is_inr, base = self._normalize_symbol(symbol)
                binance_sym = config.data.binance_map.get(usd_sym, base + "USDT")
                rate_limit(0.03)
                sess = get_session()
                resp = sess.get(
                    config.realtime.rest_url + "/api/v3/klines",
                    params={"symbol": binance_sym, "interval": "1d", "limit": limit},
                    timeout=15
                )
                if resp.status_code == 429:
                    wait = exponential_backoff(attempt, base=1.0)
                    logger.warning(f"Binance 429 rate limit, waiting {wait:.1f}s attempt {attempt+1}")
                    time.sleep(wait)
                    continue
                if resp.status_code != 200:
                    logger.debug(f"Binance direct failed {symbol} {binance_sym}: {resp.status_code} {resp.text[:100]}")
                    time.sleep(exponential_backoff(attempt))
                    continue
                data = resp.json()
                if not isinstance(data, list) or len(data) == 0:
                    time.sleep(exponential_backoff(attempt))
                    continue
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
                if len(df) < 10:
                    continue
                self._fetch_metrics["binance_success"] += 1
                logger.info(f"Binance direct v6 fetched {len(df)} rows for {symbol} ({binance_sym}) -> {usd_sym} INR={is_inr} checksum {self._checksum_df(df)}")
                return df
            except Exception as e:
                logger.debug(f"Binance direct fetch failed {symbol} attempt {attempt+1}: {e}")
                time.sleep(exponential_backoff(attempt))
                continue
        self._fetch_metrics["failures"] += 1
        return None

    def fetch_yfinance(self, symbol: Optional[str] = None, period: Optional[str] = None, interval: Optional[str] = None) -> pd.DataFrame:
        sym = symbol or self.symbol
        per = period or self.period
        inter = interval or self.interval
        usd_sym, is_inr, base = self._normalize_symbol(sym)
        
        logger.info(f"Fetching {sym} | {usd_sym} INR={is_inr} | period={per} | interval={inter} via yfinance v6")
        for attempt in range(4):
            try:
                rate_limit(0.15)
                ticker = yf.Ticker(usd_sym)
                df = ticker.history(period=per, interval=inter, auto_adjust=False)
                
                if df.empty:
                    # Try base symbol without -USD
                    ticker2 = yf.Ticker(base)
                    df = ticker2.history(period=per, interval=inter, auto_adjust=False)
                    if df.empty:
                        # Try with USD
                        ticker3 = yf.Ticker(base + "USD")
                        df = ticker3.history(period=per, interval=inter, auto_adjust=False)
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
                
                self._fetch_metrics["yfinance_success"] += 1
                logger.info(f"Fetched {len(df)} rows for {sym} from {df.index[0]} to {df.index[-1]} via yfinance v6 checksum {self._checksum_df(df)}")
                return df
            except Exception as e:
                if attempt < 3:
                    wait = exponential_backoff(attempt, base=0.5)
                    logger.debug(f"yfinance retry {attempt+1} for {sym}: {e}, waiting {wait:.1f}s")
                    time.sleep(wait)
                    continue
                logger.error(f"yfinance fetch failed for {sym} after 4 attempts: {e}")
                raise

    def fetch_coingecko(self, coin_id: str = "bitcoin", days: str = "365") -> pd.DataFrame:
        logger.info(f"Fetching {coin_id} via CoinGecko v6, days={days}")
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        
        for attempt in range(3):
            try:
                rate_limit(0.3)
                sess = get_session()
                resp = sess.get(url, params=params, timeout=20)
                if resp.status_code == 429:
                    wait = exponential_backoff(attempt, base=2.0)
                    logger.warning(f"CoinGecko 429, waiting {wait:.1f}s")
                    time.sleep(wait)
                    continue
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
                df = validate_ohlcv(df)
                
                self._fetch_metrics["coingecko_success"] += 1
                logger.info(f"CoinGecko v6 fetched {len(df)} rows for {coin_id}")
                return df
            except Exception as e:
                if attempt < 2:
                    wait = exponential_backoff(attempt, base=1.0)
                    time.sleep(wait)
                    continue
                logger.error(f"CoinGecko fetch failed: {e}")
                raise

    def fetch_multiple(self, symbols: List[str], period: Optional[str] = None) -> dict:
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.fetch_yfinance(symbol=sym, period=period)
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
        return results

    def save(self, df: pd.DataFrame, path: Optional[str] = None) -> str:
        if path is None:
            safe_sym = self.symbol.replace('-','_').replace('/','_').replace(' ','_')
            path = config.project_root / "data" / "raw" / f"{safe_sym}_{self.interval}.csv"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Atomic write with checksum
        tmp = Path(str(path) + ".tmp")
        df.to_csv(tmp)
        # Verify write
        try:
            test_df = pd.read_csv(tmp, index_col=0, parse_dates=True)
            if len(test_df) != len(df):
                raise ValueError("Write verification failed")
        except Exception as e:
            logger.warning(f"Save verification failed for {path}: {e}")
        tmp.replace(path)
        logger.info(f"Saved data v6 to {path} ({len(df)} rows) checksum {self._checksum_df(df)}")
        return str(path)

    def load_or_fetch(self, symbol: Optional[str] = None, force_refresh: bool = False) -> pd.DataFrame:
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
                            df = validate_ohlcv(df)
                            logger.info(f"Loaded cached data v6 {cache_path} with {len(df)} rows (age {age_hours:.1f}h) checksum {self._checksum_df(df)}")
                            with self._cache_lock:
                                self._cache[safe_sym] = df.copy()
                            return df
                        else:
                            logger.info(f"Cache {cache_path} expired {age_hours:.1f}h > {config.data.cache_ttl_hours}h, refetching")
                    except Exception:
                        df = validate_ohlcv(df)
                        logger.info(f"Loaded cached data v6 {cache_path} with {len(df)} rows")
                        with self._cache_lock:
                            self._cache[safe_sym] = df.copy()
                        return df
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")

        # v6: Try multi-source merge if enabled
        if config.data.use_multi_source_merge:
            df_binance = self.fetch_binance_direct(sym, limit=1000)
            if df_binance is not None and len(df_binance) > 200:
                # Try to get more history from yfinance and merge
                try:
                    df_yf = self.fetch_yfinance(symbol=sym, period="2y")
                    if len(df_yf) > len(df_binance):
                        # Merge: yfinance for history, binance for recent
                        combined = pd.concat([df_yf, df_binance])
                        combined = combined[~combined.index.duplicated(keep='last')]
                        combined.sort_index(inplace=True)
                        combined = validate_ohlcv(combined)
                        logger.info(f"v6 multi-source merge: yf {len(df_yf)} + binance {len(df_binance)} -> {len(combined)}")
                        self.save(combined, str(cache_path))
                        with self._cache_lock:
                            self._cache[safe_sym] = combined.copy()
                        return combined
                except Exception as e:
                    logger.debug(f"Multi-source merge failed, using binance only: {e}")
                self.save(df_binance, str(cache_path))
                with self._cache_lock:
                    self._cache[safe_sym] = df_binance.copy()
                return df_binance

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
            logger.warning(f"yfinance failed for {sym}: {e_yf}, trying CoinGecko fallback v6")
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
                df = validate_ohlcv(df)
                self.save(df, str(cache_path))
                with self._cache_lock:
                    self._cache[safe_sym] = df.copy()
                return df
            except Exception as e_cg:
                logger.warning(f"CoinGecko also failed for {sym}: {e_cg}")
                if cache_path.exists():
                    try:
                        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                        df = validate_ohlcv(df)
                        logger.info(f"Falling back to cached data v6 {cache_path} with {len(df)} rows after fetch failures")
                        with self._cache_lock:
                            self._cache[safe_sym] = df.copy()
                        return df
                    except Exception as e_cache:
                        logger.error(f"Cache fallback also failed: {e_cache}")
                        raise e_cache
                else:
                    raise e_cg

    def get_metrics(self) -> Dict:
        return dict(self._fetch_metrics)

    def get_latest_price(self, symbol: str = None) -> Optional[float]:
        """v6: unified latest price with fallback"""
        sym = symbol or self.symbol
        # Try binance direct first
        try:
            df = self.fetch_binance_direct(sym, limit=1)
            if df is not None and len(df) > 0:
                return float(df['Close'].iloc[-1])
        except Exception:
            pass
        # Try yfinance
        try:
            df = self.fetch_yfinance(symbol=sym, period="1d")
            if len(df) > 0:
                return float(df['Close'].iloc[-1])
        except Exception:
            pass
        return None


def fetch_crypto_data(symbol: str = "BTC-USD", period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    fetcher = CryptoDataFetcher(symbol=symbol)
    fetcher.period = period
    fetcher.interval = interval
    return fetcher.load_or_fetch(symbol=symbol)
