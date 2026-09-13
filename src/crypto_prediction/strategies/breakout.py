"""
Breakout Strategy - Real trading for trending markets
Enters on breakout with volume confirmation
"""
from dataclasses import dataclass, asdict
from typing import Dict, List
from datetime import datetime
import pandas as pd

from ..config import get_config
from ..data.fetcher import CryptoDataFetcher
from ..features.technical import FeatureEngineer
from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class BreakoutSignal:
    symbol: str
    signal: str
    entry_price: float
    stop_loss: float
    take_profit: float
    breakout_level: float
    volume_confirmed: bool
    timestamp: str

class BreakoutBot:
    def __init__(self):
        self.engineer = FeatureEngineer()
    
    def get_live_price(self, symbol: str) -> float:
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            return fetcher.get_current_price() or 0
        except:
            return 0
    
    def detect_breakout(self, symbol: str) -> BreakoutSignal:
        """Detect breakout with real data"""
        try:
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            
            # Engineer
            engineered = self.engineer.engineer(df)
            
            # Get recent levels
            recent_high = df['High'].rolling(20).max().iloc[-1]
            recent_low = df['Low'].rolling(20).min().iloc[-1]
            current_price = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Volume confirmation
            volume_confirmed = volume > avg_volume * 1.5
            
            # Breakout logic
            if current_price > recent_high * 0.998 and volume_confirmed:  # Near breakout
                # Bullish breakout
                breakout_level = recent_high
                entry = current_price
                sl = recent_low
                tp = entry + (entry - sl) * 2  # 1:2 RR
                
                return BreakoutSignal(
                    symbol=symbol,
                    signal="BREAKOUT_BUY",
                    entry_price=float(entry),
                    stop_loss=float(sl),
                    take_profit=float(tp),
                    breakout_level=float(breakout_level),
                    volume_confirmed=volume_confirmed,
                    timestamp=datetime.utcnow().isoformat()
                )
            elif current_price < recent_low * 1.002 and volume_confirmed:
                # Bearish breakdown
                breakout_level = recent_low
                entry = current_price
                sl = recent_high
                tp = entry - (sl - entry) * 2
                
                return BreakoutSignal(
                    symbol=symbol,
                    signal="BREAKDOWN_SELL",
                    entry_price=float(entry),
                    stop_loss=float(sl),
                    take_profit=float(tp),
                    breakout_level=float(breakout_level),
                    volume_confirmed=volume_confirmed,
                    timestamp=datetime.utcnow().isoformat()
                )
            else:
                return BreakoutSignal(
                    symbol=symbol,
                    signal="NO_BREAKOUT",
                    entry_price=float(current_price),
                    stop_loss=0,
                    take_profit=0,
                    breakout_level=float(recent_high if current_price > (recent_high+recent_low)/2 else recent_low),
                    volume_confirmed=volume_confirmed,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except Exception as e:
            logger.error(f"Breakout detection failed for {symbol}: {e}")
            live_price = self.get_live_price(symbol)
            return BreakoutSignal(
                symbol=symbol,
                signal="ERROR",
                entry_price=live_price,
                stop_loss=0,
                take_profit=0,
                breakout_level=0,
                volume_confirmed=False,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def scan_all(self, symbols: List[str] = None) -> List[Dict]:
        """Scan all symbols for breakouts - real market scanner"""
        symbols = symbols or config.data.supported_symbols[:6]
        signals = []
        
        for sym in symbols:
            try:
                sig = self.detect_breakout(sym)
                signals.append(asdict(sig))
            except Exception as e:
                logger.error(f"Failed to scan {sym}: {e}")
        
        # Sort by breakout signals first
        signals.sort(key=lambda x: 0 if "BREAKOUT" in x["signal"] else 1)
        return signals
