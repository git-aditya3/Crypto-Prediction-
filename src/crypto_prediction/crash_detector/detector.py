"""
Crash Detector - Main Engine
Local, fast, efficient aggregation of all signals into crash risk 0-100
Runs entirely locally, <100ms processing after fetch, <3s total with network
"""
import time
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

from .scraper import FastScraper, get_scraper, ScrapedData
from .signals import (
    calc_price_drop_signal, calc_liquidation_signal, calc_funding_signal,
    calc_orderbook_signal, calc_whale_signal, calc_stablecoin_signal,
    calc_fear_greed_signal, calc_correlation_signal, calc_volume_signal,
    calc_news_signal, calc_oi_signal, SignalResult
)

@dataclass
class CrashReport:
    timestamp: str
    crash_risk: float  # 0-100
    level: str  # LOW/MEDIUM/HIGH/CRITICAL
    confidence: float
    signals: List[Dict]
    summary: str
    action: str
    btc_price: float
    btc_change: float
    fetch_time_ms: float
    processing_time_ms: float
    raw: Dict

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "crash_risk": round(self.crash_risk,1),
            "level": self.level,
            "confidence": round(self.confidence,1),
            "signals": self.signals,
            "summary": self.summary,
            "action": self.action,
            "btc_price": self.btc_price,
            "btc_change": self.btc_change,
            "fetch_time_ms": round(self.fetch_time_ms,1),
            "processing_time_ms": round(self.processing_time_ms,1),
            "total_time_ms": round(self.fetch_time_ms + self.processing_time_ms,1),
            "raw": self.raw,
            "local_processing": True,
            "efficient": True
        }

class CrashDetector:
    def __init__(self):
        self.scraper: FastScraper = get_scraper()
        # Weights tuned for crash early detection - price, liquidation, orderbook, stablecoin have higher weight
        self.weights = {
            "price_drop": 1.5,
            "liquidation": 1.3,
            "orderbook": 1.2,
            "stablecoin": 1.4,
            "whale": 1.1,
            "news": 1.2,
            "funding": 1.0,
            "correlation": 1.0,
            "volume": 1.0,
            "fear_greed": 0.8,
            "open_interest": 0.9
        }

    def _aggregate(self, signals: List[SignalResult]) -> tuple:
        # Weighted average
        total_weight=0
        weighted_sum=0
        for s in signals:
            w=self.weights.get(s.name, s.weight)
            total_weight+=w
            weighted_sum+=s.score*w
        risk = weighted_sum/total_weight if total_weight else 0
        # Confidence based on data availability and signal agreement
        high_signals = sum(1 for s in signals if s.score>60)
        confidence = min(95, 50 + high_signals*10 + len([s for s in signals if s.score>0])*3)
        return risk, confidence

    def _level(self, risk: float) -> str:
        if risk>=80: return "CRITICAL"
        if risk>=60: return "HIGH"
        if risk>=35: return "MEDIUM"
        return "LOW"

    def _action(self, risk: float, level: str) -> str:
        if level=="CRITICAL":
            return "🚨 CRITICAL CRASH IMMINENT - Exit longs, tighten SL, reduce leverage, move to stablecoins, watch liquidations"
        if level=="HIGH":
            return "⚠️ HIGH crash risk - Reduce position size 50%, set tight SL, avoid new longs, hedge with shorts, monitor orderbook"
        if level=="MEDIUM":
            return "⚡ MEDIUM risk - Caution, reduce leverage, set breakeven SL, watch funding & liquidations, prepare hedge"
        return "✅ LOW risk - Normal trading, but keep SL, monitor whale sells & funding"

    def _summary(self, risk: float, signals: List[SignalResult], btc_change: float) -> str:
        top = sorted(signals, key=lambda x: x.score, reverse=True)[:3]
        top_str = ", ".join([f"{s.name} {s.score:.0f} ({s.level})" for s in top])
        if risk>=60:
            return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top drivers: {top_str} | Early warning detected before market-wide impact"
        return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top: {top_str} | No systemic crash detected"

    def scan(self, symbols: List[str]=None) -> CrashReport:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        t0=time.time()
        scraped: ScrapedData = self.scraper.fetch_all(symbols)
        fetch_ms=scraped.fetch_time_ms
        t1=time.time()

        # Calculate all signals - local processing, fast
        signals: List[SignalResult] = []
        signals.append(calc_price_drop_signal(scraped.spot_tickers))
        signals.append(calc_liquidation_signal(scraped.liquidations))
        signals.append(calc_funding_signal(scraped.funding_rates))
        signals.append(calc_orderbook_signal(scraped.orderbooks))
        signals.append(calc_whale_signal(scraped.recent_trades))
        signals.append(calc_stablecoin_signal(scraped.spot_tickers))
        signals.append(calc_fear_greed_signal(scraped.fear_greed))
        signals.append(calc_correlation_signal(scraped.spot_tickers))
        signals.append(calc_volume_signal(scraped.spot_tickers))
        signals.append(calc_news_signal(scraped.news_titles, scraped.reddit_posts))
        signals.append(calc_oi_signal(scraped.open_interest, scraped.spot_tickers))

        risk, confidence = self._aggregate(signals)
        level = self._level(risk)

        btc = scraped.spot_tickers.get("BTCUSDT",{})
        btc_price = btc.get("price",0)
        btc_change = btc.get("change_pct",0)

        proc_ms = (time.time()-t1)*1000

        report=CrashReport(
            timestamp=scraped.timestamp,
            crash_risk=risk,
            level=level,
            confidence=confidence,
            signals=[s.to_dict() for s in signals],
            summary=self._summary(risk, signals, btc_change),
            action=self._action(risk, level),
            btc_price=btc_price,
            btc_change=btc_change,
            fetch_time_ms=fetch_ms,
            processing_time_ms=proc_ms,
            raw={
                "spot_count": len(scraped.spot_tickers),
                "futures_count": len(scraped.futures_tickers),
                "funding_count": len(scraped.funding_rates),
                "orderbooks": len(scraped.orderbooks),
                "liquidations": len(scraped.liquidations),
                "trades": len(scraped.recent_trades),
                "fear_greed": scraped.fear_greed.get("value"),
                "reddit": len(scraped.reddit_posts),
                "news": len(scraped.news_titles)
            }
        )
        return report

    def quick_scan(self) -> Dict:
        """Ultra fast scan for API - returns minimal"""
        report=self.scan()
        return report.to_dict()

# Singleton
_detector=None
def get_crash_detector():
    global _detector
    if _detector is None:
        _detector=CrashDetector()
    return _detector
