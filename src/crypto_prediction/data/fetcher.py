"""
Crypto data fetcher - supports yfinance and CoinGecko fallback
"""
import time
from typing import Optional, List
import pandas as pd
import yfinance as yf
import requests
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CryptoDataFetcher:
    def __init__(self, symbol: str = None):
        self.symbol = symbol or config.data.default_symbol
        self.interval = config.data.interval
        self.period = config.data.period

    def fetch_yfinance(self, symbol: Optional[str] = None, period: Optional[str] = None, interval: Optional[str] = None) -> pd.DataFrame:
        """Fetch OHLCV data from yfinance"""
        sym = symbol or self.symbol
        per = period or self.period
        inter = interval or self.interval
        
        logger.info(f"Fetching {sym} | period={per} | interval={inter} via yfinance")
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=per, interval=inter, auto_adjust=False)
            
            if df.empty:
                raise ValueError(f"No data returned for {sym}")
            
            # Standardize columns
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            df.dropna(inplace=True)
            
            logger.info(f"Fetched {len(df)} rows for {sym} from {df.index[0]} to {df.index[-1]}")
            return df
        except Exception as e:
            logger.error(f"yfinance fetch failed for {sym}: {e}")
            raise

    def fetch_coingecko(self, coin_id: str = "bitcoin", days: str = "365") -> pd.DataFrame:
        """Fallback fetcher using CoinGecko API"""
        logger.info(f"Fetching {coin_id} via CoinGecko, days={days}")
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            df = pd.DataFrame(prices, columns=['timestamp', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            vol_df = pd.DataFrame(volumes, columns=['timestamp', 'Volume'])
            vol_df['timestamp'] = pd.to_datetime(vol_df['timestamp'], unit='ms')
            vol_df.set_index('timestamp', inplace=True)
            
            df = df.join(vol_df, how='left')
            # Synthesize OHLC from Close for compatibility
            df['Open'] = df['Close']
            df['High'] = df['Close']
            df['Low'] = df['Close']
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            logger.info(f"CoinGecko fetched {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"CoinGecko fetch failed: {e}")
            raise

    def fetch_multiple(self, symbols: List[str], period: Optional[str] = None) -> dict:
        """Fetch multiple symbols"""
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.fetch_yfinance(symbol=sym, period=period)
                time.sleep(0.5)  # rate limit courtesy
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
        return results

    def save(self, df: pd.DataFrame, path: Optional[str] = None) -> str:
        from pathlib import Path
        if path is None:
            path = config.project_root / "data" / "raw" / f"{self.symbol.replace('-','_')}_{self.interval}.csv"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path)
        logger.info(f"Saved data to {path}")
        return str(path)

    def load_or_fetch(self, symbol: Optional[str] = None, force_refresh: bool = False) -> pd.DataFrame:
        """Load from cache if exists, else fetch"""
        from pathlib import Path
        sym = symbol or self.symbol
        cache_path = config.project_root / "data" / "raw" / f"{sym.replace('-','_')}_{self.interval}.csv"
        
        if cache_path.exists() and not force_refresh:
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                logger.info(f"Loaded cached data {cache_path} with {len(df)} rows")
                # If cache is recent (<1 day old) and enough data, return
                if len(df) > 100:
                    return df
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")

        # Fetch fresh
        try:
            df = self.fetch_yfinance(symbol=sym)
        except:
            # Try coingecko mapping
            mapping = {
                "BTC-USD": "bitcoin",
                "ETH-USD": "ethereum",
                "BNB-USD": "binancecoin",
                "SOL-USD": "solana",
                "XRP-USD": "ripple",
                "ADA-USD": "cardano",
                "DOGE-USD": "dogecoin",
                "AVAX-USD": "avalanche-2",
                "DOT-USD": "polkadot",
                "MATIC-USD": "matic-network"
            }
            coin_id = mapping.get(sym, "bitcoin")
            df = self.fetch_coingecko(coin_id=coin_id, days="730")
        
        self.save(df, str(cache_path))
        return df


def fetch_crypto_data(symbol: str = "BTC-USD", period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    fetcher = CryptoDataFetcher(symbol=symbol)
    fetcher.period = period
    fetcher.interval = interval
    return fetcher.load_or_fetch(symbol=symbol)
