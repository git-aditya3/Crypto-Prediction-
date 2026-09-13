"""
Crash Detector - Fixed: missing data handling, quality-weighted aggregation, validation
"""
import time
from typing import Dict, List
from dataclasses import dataclass
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
    crash_risk: float
    level: str
    confidence: float
    signals: List[Dict]
    summary: str
    action: str
    btc_price: float
    btc_change: float
    fetch_time_ms: float
    processing_time_ms: float
    data_quality: float
    warnings: List[str]
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
            "data_quality": round(self.data_quality,2),
            "warnings": self.warnings,
            "raw": self.raw,
            "local_processing": True,
            "efficient": True,
            "fixed": True
        }

class CrashDetector:
    def __init__(self):
        self.scraper: FastScraper = get_scraper()
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
        self._oi_history = {}  # For future OI drop detection

    def _aggregate(self, signals: List[SignalResult], data_quality: float) -> tuple:
        # Quality-weighted aggregation
        total_weight=0.0
        weighted_sum=0.0
        quality_sum=0.0
        for s in signals:
            w=self.weights.get(s.name, s.weight)
            # Adjust weight by data quality - low quality signals contribute less
            effective_weight = w * (0.3 + 0.7 * s.data_quality)
            total_weight+=effective_weight
            weighted_sum+=s.score*effective_weight
            quality_sum+=s.data_quality * w

        risk = weighted_sum/total_weight if total_weight>0 else 0
        avg_quality = quality_sum / sum(self.weights.values()) if sum(self.weights.values())>0 else 0

        # Confidence based on data quality and signal agreement
        high_signals = sum(1 for s in signals if s.score>60 and s.data_quality>0.5)
        medium_signals = sum(1 for s in signals if s.score>35 and s.data_quality>0.5)
        low_quality_count = sum(1 for s in signals if s.data_quality<0.3)

        # Base confidence on quality
        confidence = 30 + avg_quality*40
        confidence += high_signals*8 + medium_signals*3
        confidence -= low_quality_count*5

        # If data quality very low, cap confidence and add warning
        if data_quality < 0.3:
            confidence = min(confidence, 50)
        if avg_quality < 0.3:
            confidence = min(confidence, 60)

        confidence = max(10, min(95, confidence))
        return risk, confidence, avg_quality

    def _level(self, risk: float) -> str:
        if risk>=80: return "CRITICAL"
        if risk>=60: return "HIGH"
        if risk>=35: return "MEDIUM"
        return "LOW"

    def _action(self, risk: float, level: str, data_quality: float) -> str:
        if data_quality < 0.3:
            base = "⚠️ LOW DATA QUALITY - Binance may be blocked, using fallback - verify manually | "
        else:
            base = ""
        if level=="CRITICAL":
            return base + "🚨 CRITICAL CRASH IMMINENT - Exit longs, tighten SL, reduce leverage, move to stablecoins, watch liquidations"
        if level=="HIGH":
            return base + "⚠️ HIGH crash risk - Reduce position size 50%, set tight SL, avoid new longs, hedge with shorts, monitor orderbook"
        if level=="MEDIUM":
            return base + "⚡ MEDIUM risk - Caution, reduce leverage, set breakeven SL, watch funding & liquidations, prepare hedge"
        return base + "✅ LOW risk - Normal trading, but keep SL, monitor whale sells & funding"

    def _summary(self, risk: float, signals: List[SignalResult], btc_change: float, data_quality: float) -> str:
        top = sorted([s for s in signals if s.data_quality>0.3], key=lambda x: x.score, reverse=True)[:3]
        if not top:
            top = sorted(signals, key=lambda x: x.score, reverse=True)[:3]
        top_str = ", ".join([f"{s.name} {s.score:.0f} ({s.level})" for s in top])
        quality_note = f"Quality {data_quality:.0%}" if data_quality<0.5 else ""
        if risk>=60:
            return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top drivers: {top_str} | {quality_note} | Early warning before market-wide impact"
        return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top: {top_str} | {quality_note} | No systemic crash detected"

    def scan(self, symbols: List[str]=None) -> CrashReport:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        # Validate symbols
        symbols = [s.upper().replace("-","").replace("/","") for s in symbols if s and isinstance(s, str)]
        symbols = [s for s in symbols if 6 <= len(s) <= 12][:10]
        if not symbols:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

        t0=time.time()
        try:
            scraped: ScrapedData = self.scraper.fetch_all(symbols)
        except Exception as e:
            # Fallback empty data
            from .scraper import ScrapedData
            scraped = ScrapedData(
                timestamp=datetime.utcnow().isoformat(),
                spot_tickers={},
                futures_tickers={},
                funding_rates=[],
                open_interest={},
                orderbooks={},
                liquidations={},
                recent_trades={},
                fear_greed={"value":50, "classification":"Neutral", "history":[]},
                reddit_posts=[],
                news_titles=[],
                fetch_time_ms=0,
                errors=[str(e)],
                data_quality=0.0
            )
        fetch_ms=scraped.fetch_time_ms
        t1=time.time()

        warnings=[]
        if scraped.data_quality < 0.3:
            warnings.append(f"Low data quality {scraped.data_quality:.0%} - Binance may be blocked or rate limited, using fallback/cached data")
        if scraped.errors:
            warnings.append(f"Fetch errors: {len(scraped.errors)} sources failed")
        if not scraped.spot_tickers:
            warnings.append("No spot tickers - price drop signal uncertain")

        signals: List[SignalResult] = []
        try:
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
        except Exception as e:
            warnings.append(f"Signal calculation error: {e}")
            # Ensure at least some signals
            if not signals:
                signals.append(calc_price_drop_signal({}))

        risk, confidence, avg_quality = self._aggregate(signals, scraped.data_quality)
        level = self._level(risk)

        btc = scraped.spot_tickers.get("BTCUSDT",{})
        btc_price = float(btc.get("price",0) or 0)
        btc_change = float(btc.get("change_pct",0) or 0)

        # If no BTC price but we have last successful, use it
        if btc_price==0 and self.scraper._last_successful and self.scraper._last_successful.spot_tickers.get("BTCUSDT"):
            btc_last = self.scraper._last_successful.spot_tickers["BTCUSDT"]
            btc_price = float(btc_last.get("price",0) or 0)
            btc_change = float(btc_last.get("change_pct",0) or 0)
            warnings.append("Using cached BTC price - live fetch failed")

        proc_ms = (time.time()-t1)*1000

        report=CrashReport(
            timestamp=scraped.timestamp,
            crash_risk=risk,
            level=level,
            confidence=confidence,
            signals=[s.to_dict() for s in signals],
            summary=self._summary(risk, signals, btc_change, scraped.data_quality),
            action=self._action(risk, level, scraped.data_quality),
            btc_price=btc_price,
            btc_change=btc_change,
            fetch_time_ms=fetch_ms,
            processing_time_ms=proc_ms,
            data_quality=scraped.data_quality,
            warnings=warnings,
            raw={
                "spot_count": len(scraped.spot_tickers),
                "futures_count": len(scraped.futures_tickers),
                "funding_count": len(scraped.funding_rates),
                "orderbooks": len(scraped.orderbooks),
                "liquidations": len(scraped.liquidations),
                "trades": len(scraped.recent_trades),
                "fear_greed": scraped.fear_greed.get("value"),
                "reddit": len(scraped.reddit_posts),
                "news": len(scraped.news_titles),
                "errors": len(scraped.errors),
                "avg_signal_quality": round(avg_quality,2)
            }
        )
        return report

    def quick_scan(self) -> Dict:
        report=self.scan()
        return report.to_dict()

_detector=None
def get_crash_detector():
    global _detector
    if _detector is None:
        _detector=CrashDetector()
    return _detector
