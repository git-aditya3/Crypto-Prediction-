"""
Unified price helper - tries CoinDCX INR first, then Binance USD, then historical
Used by all bots, auto trading, analytics, crash detector
"""
from typing import Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

def get_live_price(symbol: str) -> float:
    """Get live price with CoinDCX primary for INR, Binance fallback"""
    if not symbol or not isinstance(symbol, str):
        return 0.0
    symbol = symbol.strip().upper()
    # Normalize: BTCINR, BTC-USD, BTC/USD, BTCUSDT etc
    original = symbol

    # Try CoinDCX if INR or mapped
    try:
        from .coindcx_fetcher import CoinDCXRealtimeFetcher
        fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
        price = fetcher.get_current_price()
        if price and price > 0 and price < 100_000_000:
            return float(price)
    except Exception as e:
        logger.debug(f"CoinDCX price helper failed {symbol}: {e}")

    # Try Binance
    try:
        from .realtime import BinanceRealtimeFetcher
        # Convert INR to USD for Binance fetcher if needed
        usd_symbol = symbol
        if "INR" in symbol:
            base = symbol.replace("INR","").replace("-","").replace("/","")
            if base in ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","AVAX","MATIC","DOT","LINK","LTC","BCH","UNI","SHIB","ETC","XLM","FIL","TRX","ATOM"]:
                usd_symbol = f"{base}-USD"
        fetcher = BinanceRealtimeFetcher(symbol=usd_symbol)
        price = fetcher.get_current_price()
        if price and price > 0 and price < 10_000_000:
            # If original was INR, convert USD to INR
            if "INR" in original.upper():
                price = price * 83.5
            return float(price)
    except Exception as e:
        logger.debug(f"Binance price helper failed {symbol}: {e}")

    # Historical fallback - try cached CSV directly to avoid yfinance recursion in sandbox
    try:
        from pathlib import Path
        from ..config import get_config
        import pandas as pd
        cfg = get_config()
        usd_sym = original
        if "INR" in original.upper():
            base = original.upper().replace("INR","")
            usd_sym = f"{base}-USD"
        # Try cache file
        cache_path = cfg.project_root / "data" / "raw" / f"{usd_sym.replace('-','_')}_1d.csv"
        if cache_path.exists():
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if not df.empty:
                    p = float(df['Close'].iloc[-1])
                    if "INR" in original.upper():
                        p = p * 83.5
                    if 0 < p < 100_000_000:
                        return p
            except Exception:
                pass
        # Last resort try fetcher but with short timeout
        try:
            from .fetcher import CryptoDataFetcher
            f = CryptoDataFetcher(symbol=usd_sym)
            # Only try if cache exists, else skip to avoid network
            if cache_path.exists():
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                if not df.empty:
                    p = float(df['Close'].iloc[-1])
                    if "INR" in original.upper():
                        p = p * 83.5
                    if 0 < p < 100_000_000:
                        return p
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"Historical price helper failed {symbol}: {e}")

    return 0.0

def get_tickers_all() -> dict:
    """Get all tickers from CoinDCX + Binance"""
    result={}
    try:
        from .coindcx_fetcher import get_coindcx_tickers_cached
        coindcx = get_coindcx_tickers_cached()
        result.update(coindcx)
    except Exception as e:
        logger.debug(f"CoinDCX tickers all failed: {e}")

    try:
        from ..config import get_config
        import requests
        cfg = get_config()
        # Binance 24hr
        resp = requests.get(f"{cfg.realtime.rest_url}/api/v3/ticker/24hr", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                for t in data[:50]:
                    try:
                        sym = t.get("symbol","")
                        if sym and sym.endswith("USDT"):
                            price = float(t.get("lastPrice",0) or 0)
                            if price > 0:
                                # Convert to our format
                                base = sym.replace("USDT","")
                                our_sym = f"{base}-USD"
                                if our_sym not in result:
                                    result[our_sym] = {
                                        "symbol": our_sym,
                                        "price": price,
                                        "last_price": price,
                                        "change_pct": float(t.get("priceChangePercent",0) or 0),
                                        "volume": float(t.get("volume",0) or 0),
                                        "source": "Binance",
                                        "real_data": True
                                    }
                    except (ValueError, TypeError):
                        continue
    except Exception as e:
        logger.debug(f"Binance tickers all failed: {e}")

    return result

def get_orderbook(symbol: str, limit: int = 20) -> Optional[dict]:
    """Orderbook with CoinDCX primary"""
    if not symbol:
        return None
    try:
        from .coindcx_fetcher import CoinDCXRealtimeFetcher
        fetcher = CoinDCXRealtimeFetcher(symbol=symbol)
        ob = fetcher.get_orderbook(symbol, limit)
        if ob and ob.get("bids") and ob.get("asks"):
            return ob
    except Exception as e:
        logger.debug(f"CoinDCX orderbook helper failed {symbol}: {e}")

    try:
        from .realtime import BinanceRealtimeFetcher
        usd_sym = symbol
        if "INR" in symbol.upper():
            base = symbol.upper().replace("INR","")
            usd_sym = f"{base}-USD"
        fetcher = BinanceRealtimeFetcher(symbol=usd_sym)
        ob = fetcher.get_orderbook(limit)
        if ob and ob.get("bids") and ob.get("asks"):
            if "INR" in symbol.upper():
                # Convert to INR
                inr_rate = 83.5
                bids=[]
                asks=[]
                for p,q in ob.get("bids",[])[:limit]:
                    try:
                        bids.append([float(p)*inr_rate, float(q)])
                    except (ValueError, TypeError):
                        continue
                for p,q in ob.get("asks",[])[:limit]:
                    try:
                        asks.append([float(p)*inr_rate, float(q)])
                    except (ValueError, TypeError):
                        continue
                return {"bids": bids, "asks": asks, "market": symbol, "source": "Binance converted to INR"}
            return ob
    except Exception as e:
        logger.debug(f"Binance orderbook helper failed {symbol}: {e}")

    return None
