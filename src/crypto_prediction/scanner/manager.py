"""
Market Scanner - Scans real market for opportunities
Volume spikes, momentum, breakouts, oversold/overbought
Real Binance data, no fake
"""
from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime
import requests

from ..config import get_config
from ..data.fetcher import CryptoDataFetcher
from ..features.technical import FeatureEngineer
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class MarketScanner:
    def __init__(self):
        self.engineer = FeatureEngineer()
    
    def fetch_tickers(self) -> Dict:
        """Fetch real Binance tickers"""
        try:
            resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
            resp.raise_for_status()
            all_tickers = resp.json()
            
            wanted = set(config.data.binance_map.values())
            filtered = [t for t in all_tickers if t["symbol"] in wanted]
            
            reverse_map = {v: k for k, v in config.data.binance_map.items()}
            tickers = {}
            for t in filtered:
                our_sym = reverse_map.get(t["symbol"])
                if our_sym:
                    tickers[our_sym] = {
                        "symbol": our_sym,
                        "price": float(t["lastPrice"]),
                        "change_pct": float(t["priceChangePercent"]),
                        "volume": float(t["volume"]),
                        "quote_volume": float(t["quoteVolume"]),
                        "high": float(t["highPrice"]),
                        "low": float(t["lowPrice"]),
                        "trades": t["count"]
                    }
            return tickers
        except Exception as e:
            logger.warning(f"Ticker fetch failed: {e}")
            return {}
    
    def scan_volume_spikes(self, tickers: Dict = None) -> List[Dict]:
        """Scan for volume spikes - real whale activity"""
        tickers = tickers or self.fetch_tickers()
        spikes = []
        
        for symbol, data in tickers.items():
            try:
                fetcher = CryptoDataFetcher(symbol=symbol)
                df = fetcher.load_or_fetch(symbol=symbol)
                
                recent_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
                vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
                
                if vol_ratio > 2.0:  # 2x average volume
                    spikes.append({
                        "symbol": symbol,
                        "type": "VOLUME_SPIKE",
                        "current_volume": recent_vol,
                        "avg_volume": avg_vol,
                        "ratio": vol_ratio,
                        "price": data["price"],
                        "change_pct": data["change_pct"],
                        "signal": "High volume - potential breakout, real trading opportunity",
                        "timestamp": datetime.utcnow().isoformat(),
                        "real_data": True
                    })
            except Exception as e:
                logger.warning(f"Volume scan failed for {symbol}: {e}")
        
        spikes.sort(key=lambda x: x["ratio"], reverse=True)
        return spikes
    
    def scan_momentum(self, tickers: Dict = None) -> List[Dict]:
        """Scan for momentum - real market movers"""
        tickers = tickers or self.fetch_tickers()
        momentum = []
        
        for symbol, data in tickers.items():
            try:
                change = data["change_pct"]
                if abs(change) > 5:  # 5%+ move
                    momentum.append({
                        "symbol": symbol,
                        "type": "MOMENTUM",
                        "change_pct": change,
                        "price": data["price"],
                        "volume": data["volume"],
                        "signal": f"{'Bullish' if change > 0 else 'Bearish'} momentum {change:.2f}% - real trading",
                        "strength": "STRONG" if abs(change) > 10 else "MODERATE",
                        "timestamp": datetime.utcnow().isoformat(),
                        "real_data": True
                    })
            except Exception:
                continue
        
        momentum.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
        return momentum
    
    def scan_oversold_overbought(self) -> List[Dict]:
        """Scan RSI for oversold/overbought - real trading signals"""
        results = []
        symbols = config.data.supported_symbols[:6]
        
        for symbol in symbols:
            try:
                fetcher = CryptoDataFetcher(symbol=symbol)
                df = fetcher.load_or_fetch(symbol=symbol)
                engineered = self.engineer.engineer(df)
                
                if 'RSI' not in engineered.columns:
                    continue
                
                rsi = engineered['RSI'].iloc[-1]
                price = df['Close'].iloc[-1]
                
                if rsi < 30:
                    results.append({
                        "symbol": symbol,
                        "type": "OVERSOLD",
                        "rsi": float(rsi),
                        "price": float(price),
                        "signal": f"Oversold RSI {rsi:.1f} - potential reversal BUY for real trading",
                        "action": "BUY",
                        "timestamp": datetime.utcnow().isoformat(),
                        "real_data": True
                    })
                elif rsi > 70:
                    results.append({
                        "symbol": symbol,
                        "type": "OVERBOUGHT",
                        "rsi": float(rsi),
                        "price": float(price),
                        "signal": f"Overbought RSI {rsi:.1f} - potential pullback SELL for real trading",
                        "action": "SELL",
                        "timestamp": datetime.utcnow().isoformat(),
                        "real_data": True
                    })
            except Exception as e:
                logger.warning(f"RSI scan failed for {symbol}: {e}")
        
        return results
    
    def scan_all(self) -> Dict:
        """Full market scan - real opportunities"""
        tickers = self.fetch_tickers()
        
        volume_spikes = self.scan_volume_spikes(tickers)
        momentum = self.scan_momentum(tickers)
        rsi_signals = self.scan_oversold_overbought()
        
        # Combine and rank
        all_opportunities = []
        
        for v in volume_spikes:
            all_opportunities.append({**v, "priority": 1, "category": "Volume"})
        for m in momentum:
            all_opportunities.append({**m, "priority": 2, "category": "Momentum"})
        for r in rsi_signals:
            all_opportunities.append({**r, "priority": 3, "category": "RSI"})
        
        # Sort by priority and strength
        all_opportunities.sort(key=lambda x: (x["priority"], -abs(x.get("change_pct", 0) or x.get("rsi", 50) - 50)))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_opportunities": len(all_opportunities),
            "volume_spikes": volume_spikes,
            "momentum": momentum,
            "rsi_signals": rsi_signals,
            "top_opportunities": all_opportunities[:10],
            "all": all_opportunities,
            "real_data": True,
            "source": "Binance Live - Real Market Data",
            "no_fake": "All signals from real market data"
        }

def get_market_scanner():
    return MarketScanner()
