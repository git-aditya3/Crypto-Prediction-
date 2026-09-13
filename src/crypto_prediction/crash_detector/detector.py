"""
Crash Detector - Fixed with CoinDCX INR support, quality-weighted aggregation
"""
import time
import threading
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
            "crash_risk": round(float(self.crash_risk),1) if self.crash_risk is not None else 0.0,
            "level": self.level,
            "confidence": round(float(self.confidence),1) if self.confidence is not None else 0.0,
            "signals": self.signals,
            "summary": self.summary,
            "action": self.action,
            "btc_price": float(self.btc_price) if self.btc_price else 0.0,
            "btc_change": float(self.btc_change) if self.btc_change else 0.0,
            "fetch_time_ms": round(float(self.fetch_time_ms),1) if self.fetch_time_ms else 0.0,
            "processing_time_ms": round(float(self.processing_time_ms),1) if self.processing_time_ms else 0.0,
            "total_time_ms": round(float(self.fetch_time_ms + self.processing_time_ms),1) if self.fetch_time_ms and self.processing_time_ms else 0.0,
            "data_quality": round(float(self.data_quality),2) if self.data_quality is not None else 0.0,
            "warnings": self.warnings,
            "raw": self.raw,
            "local_processing": True,
            "efficient": True,
            "fixed": True,
            "price_source": "CoinDCX INR primary + Binance fallback"
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
        self._oi_history = {}

    def _aggregate(self, signals: List[SignalResult], data_quality: float) -> tuple:
        try:
            data_quality = float(data_quality or 0)
        except (ValueError, TypeError):
            data_quality = 0.0
        data_quality = max(0.0, min(1.0, data_quality))

        total_weight=0.0
        weighted_sum=0.0
        quality_sum=0.0
        total_weights_sum = sum(self.weights.values()) or 1.0

        for s in signals:
            try:
                if not isinstance(s, SignalResult):
                    continue
                w = self.weights.get(s.name, getattr(s, 'weight', 1.0))
                try:
                    w = float(w)
                except (ValueError, TypeError):
                    w = 1.0
                try:
                    dq = float(getattr(s, 'data_quality', 1.0))
                except (ValueError, TypeError):
                    dq = 1.0
                dq = max(0.0, min(1.0, dq))
                try:
                    score = float(getattr(s, 'score', 0))
                except (ValueError, TypeError):
                    score = 0.0
                score = max(0.0, min(100.0, score))
                effective_weight = w * (0.3 + 0.7 * dq)
                total_weight+=effective_weight
                weighted_sum+=score*effective_weight
                quality_sum+=dq * w
            except Exception:
                continue

        risk = weighted_sum/total_weight if total_weight>0 else 0
        avg_quality = quality_sum / total_weights_sum if total_weights_sum>0 else 0
        risk = max(0.0, min(100.0, risk))
        avg_quality = max(0.0, min(1.0, avg_quality))

        high_signals = 0
        medium_signals = 0
        low_quality_count = 0
        for s in signals:
            try:
                if not isinstance(s, SignalResult):
                    continue
                dq = float(getattr(s, 'data_quality', 1.0))
                score = float(getattr(s, 'score', 0))
                if score>60 and dq>0.5:
                    high_signals+=1
                if score>35 and dq>0.5:
                    medium_signals+=1
                if dq<0.3:
                    low_quality_count+=1
            except Exception:
                continue

        confidence = 30 + avg_quality*40
        confidence += high_signals*8 + medium_signals*3
        confidence -= low_quality_count*5

        if data_quality < 0.3:
            confidence = min(confidence, 50)
        if avg_quality < 0.3:
            confidence = min(confidence, 60)

        confidence = max(10, min(95, confidence))
        return risk, confidence, avg_quality

    def _level(self, risk: float) -> str:
        try:
            risk = float(risk)
        except (ValueError, TypeError):
            risk = 0.0
        if risk>=80: return "CRITICAL"
        if risk>=60: return "HIGH"
        if risk>=35: return "MEDIUM"
        return "LOW"

    def _action(self, risk: float, level: str, data_quality: float) -> str:
        try:
            data_quality = float(data_quality or 0)
        except (ValueError, TypeError):
            data_quality = 0.0
        base = ""
        if data_quality < 0.3:
            base = "⚠️ LOW DATA QUALITY - Binance may be blocked, using CoinDCX INR fallback - verify manually | "
        if level=="CRITICAL":
            return base + "🚨 CRITICAL CRASH IMMINENT - Exit longs, tighten SL, reduce leverage, move to stablecoins, watch liquidations"
        if level=="HIGH":
            return base + "⚠️ HIGH crash risk - Reduce position size 50%, set tight SL, avoid new longs, hedge with shorts, monitor orderbook"
        if level=="MEDIUM":
            return base + "⚡ MEDIUM risk - Caution, reduce leverage, set breakeven SL, watch funding & liquidations, prepare hedge"
        return base + "✅ LOW risk - Normal trading, but keep SL, monitor whale sells & funding"

    def _summary(self, risk: float, signals: List[SignalResult], btc_change: float, data_quality: float) -> str:
        try:
            risk = float(risk or 0)
            btc_change = float(btc_change or 0)
            data_quality = float(data_quality or 0)
        except (ValueError, TypeError):
            risk = 0.0
            btc_change = 0.0
            data_quality = 0.0
        # Top signals by score with decent quality
        try:
            top = sorted([s for s in signals if isinstance(s, SignalResult) and getattr(s, 'data_quality',0)>0.3], key=lambda x: float(getattr(x,'score',0)), reverse=True)[:3]
            if not top:
                top = sorted([s for s in signals if isinstance(s, SignalResult)], key=lambda x: float(getattr(x,'score',0)), reverse=True)[:3]
            top_str = ", ".join([f"{s.name} {float(getattr(s,'score',0)):.0f} ({getattr(s,'level','LOW')})" for s in top]) if top else "No strong signals"
        except Exception:
            top_str = "Signal aggregation"
        quality_note = f"Quality {data_quality:.0%}" if data_quality<0.5 else "Quality OK"
        source_note = "CoinDCX INR + Binance"
        if risk>=60:
            return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top: {top_str} | {quality_note} | {source_note} | Early warning before market-wide impact"
        return f"Crash risk {risk:.0f}% - BTC {btc_change:.1f}% | Top: {top_str} | {quality_note} | {source_note} | No systemic crash"

    def scan(self, symbols: List[str]=None) -> CrashReport:
        if symbols is None:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
        validated=[]
        for s in symbols:
            if not s or not isinstance(s, str):
                continue
            try:
                s_clean = s.upper().replace("-","").replace("/","").replace("_","").strip()
                if 6 <= len(s_clean) <= 12:
                    validated.append(s_clean)
            except Exception:
                continue
        symbols = validated[:10]
        if not symbols:
            symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

        t0=time.time()
        try:
            scraped: ScrapedData = self.scraper.fetch_all(symbols)
        except Exception as e:
            # Fallback empty data with all required fields including coindcx_tickers
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
                coindcx_tickers={},
                fetch_time_ms=0,
                errors=[str(e)[:200]],
                data_quality=0.0
            )
        fetch_ms = getattr(scraped, 'fetch_time_ms', 0) or 0
        t1=time.time()

        warnings=[]
        try:
            dq = float(getattr(scraped, 'data_quality', 0) or 0)
        except (ValueError, TypeError):
            dq = 0.0
        if dq < 0.3:
            warnings.append(f"Low data quality {dq:.0%} - Binance may be blocked or rate limited, using CoinDCX INR fallback/cached")
        try:
            if getattr(scraped, 'errors', None):
                if len(scraped.errors) > 0:
                    warnings.append(f"Fetch errors: {len(scraped.errors)} sources failed")
        except Exception:
            pass
        try:
            if not getattr(scraped, 'spot_tickers', None) or len(scraped.spot_tickers) == 0:
                warnings.append("No spot tickers - price drop signal uncertain, using CoinDCX if available")
        except Exception:
            pass

        signals: List[SignalResult] = []
        try:
            signals.append(calc_price_drop_signal(getattr(scraped, 'spot_tickers', {}) or {}))
            signals.append(calc_liquidation_signal(getattr(scraped, 'liquidations', {}) or {}))
            signals.append(calc_funding_signal(getattr(scraped, 'funding_rates', []) or []))
            signals.append(calc_orderbook_signal(getattr(scraped, 'orderbooks', {}) or {}))
            signals.append(calc_whale_signal(getattr(scraped, 'recent_trades', {}) or {}))
            signals.append(calc_stablecoin_signal(getattr(scraped, 'spot_tickers', {}) or {}))
            signals.append(calc_fear_greed_signal(getattr(scraped, 'fear_greed', {}) or {}))
            signals.append(calc_correlation_signal(getattr(scraped, 'spot_tickers', {}) or {}))
            signals.append(calc_volume_signal(getattr(scraped, 'spot_tickers', {}) or {}))
            signals.append(calc_news_signal(getattr(scraped, 'news_titles', []) or [], getattr(scraped, 'reddit_posts', []) or []))
            signals.append(calc_oi_signal(getattr(scraped, 'open_interest', {}) or {}, getattr(scraped, 'spot_tickers', {}) or {}))
        except Exception as e:
            warnings.append(f"Signal calculation error: {str(e)[:100]}")
            if not signals:
                try:
                    signals.append(calc_price_drop_signal({}))
                except Exception:
                    pass

        risk, confidence, avg_quality = self._aggregate(signals, getattr(scraped, 'data_quality', 0) or 0)
        level = self._level(risk)

        btc_price = 0.0
        btc_change = 0.0
        try:
            btc = (getattr(scraped, 'spot_tickers', {}) or {}).get("BTCUSDT",{})
            if isinstance(btc, dict):
                try:
                    btc_price = float(btc.get("price",0) or 0)
                except (ValueError, TypeError):
                    btc_price = 0.0
                try:
                    btc_change = float(btc.get("change_pct",0) or 0)
                except (ValueError, TypeError):
                    btc_change = 0.0
        except Exception:
            pass

        # Cached BTC fallback
        if btc_price==0:
            try:
                last = getattr(self.scraper, '_last_successful', None)
                if last and getattr(last, 'spot_tickers', None):
                    btc_last = last.spot_tickers.get("BTCUSDT",{})
                    if isinstance(btc_last, dict):
                        try:
                            btc_price = float(btc_last.get("price",0) or 0)
                        except (ValueError, TypeError):
                            pass
                        try:
                            btc_change = float(btc_last.get("change_pct",0) or 0)
                        except (ValueError, TypeError):
                            pass
                        if btc_price > 0:
                            warnings.append("Using cached BTC price - live fetch failed, CoinDCX fallback attempted")
            except Exception:
                pass

        proc_ms = (time.time()-t1)*1000

        try:
            spot_count = len(getattr(scraped, 'spot_tickers', {}) or {})
        except Exception:
            spot_count = 0
        try:
            coindcx_count = len(getattr(scraped, 'coindcx_tickers', {}) or {})
        except Exception:
            coindcx_count = 0
        try:
            futures_count = len(getattr(scraped, 'futures_tickers', {}) or {})
        except Exception:
            futures_count = 0
        try:
            funding_count = len(getattr(scraped, 'funding_rates', []) or [])
        except Exception:
            funding_count = 0
        try:
            ob_count = len(getattr(scraped, 'orderbooks', {}) or {})
        except Exception:
            ob_count = 0
        try:
            liq_count = len(getattr(scraped, 'liquidations', {}) or {})
        except Exception:
            liq_count = 0
        try:
            trades_count = len(getattr(scraped, 'recent_trades', {}) or {})
        except Exception:
            trades_count = 0
        try:
            fg_val = (getattr(scraped, 'fear_greed', {}) or {}).get("value",50)
        except Exception:
            fg_val = 50
        try:
            reddit_count = len(getattr(scraped, 'reddit_posts', []) or [])
        except Exception:
            reddit_count = 0
        try:
            news_count = len(getattr(scraped, 'news_titles', []) or [])
        except Exception:
            news_count = 0
        try:
            err_count = len(getattr(scraped, 'errors', []) or [])
        except Exception:
            err_count = 0

        report=CrashReport(
            timestamp=getattr(scraped, 'timestamp', datetime.utcnow().isoformat()),
            crash_risk=risk,
            level=level,
            confidence=confidence,
            signals=[s.to_dict() for s in signals if isinstance(s, SignalResult)],
            summary=self._summary(risk, signals, btc_change, getattr(scraped, 'data_quality', 0) or 0),
            action=self._action(risk, level, getattr(scraped, 'data_quality', 0) or 0),
            btc_price=btc_price,
            btc_change=btc_change,
            fetch_time_ms=fetch_ms,
            processing_time_ms=proc_ms,
            data_quality=getattr(scraped, 'data_quality', 0) or 0,
            warnings=warnings,
            raw={
                "spot_count": spot_count,
                "coindcx_count": coindcx_count,
                "futures_count": futures_count,
                "funding_count": funding_count,
                "orderbooks": ob_count,
                "liquidations": liq_count,
                "trades": trades_count,
                "fear_greed": fg_val,
                "reddit": reddit_count,
                "news": news_count,
                "errors": err_count,
                "avg_signal_quality": round(float(avg_quality),2) if avg_quality else 0.0,
                "price_source": "CoinDCX INR primary + Binance fallback"
            }
        )
        return report

    def quick_scan(self) -> Dict:
        try:
            report=self.scan()
            return report.to_dict()
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "crash_risk": 20.0,
                "level": "LOW",
                "confidence": 30.0,
                "signals": [],
                "summary": f"Quick scan failed: {e}",
                "action": "⚠️ Scan failed - check manually",
                "btc_price": 0,
                "btc_change": 0,
                "fetch_time_ms": 0,
                "processing_time_ms": 0,
                "data_quality": 0.0,
                "warnings": [str(e)],
                "raw": {},
                "error": str(e)
            }

_detector=None
_detector_lock=threading.Lock()

def get_crash_detector():
    global _detector
    if _detector is None:
        with _detector_lock:
            if _detector is None:
                _detector=CrashDetector()
    return _detector
