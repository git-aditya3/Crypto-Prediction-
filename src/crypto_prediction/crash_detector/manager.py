"""
Crash Detector Manager v5 MAX - Thread-safe, validation, persistence, metrics, caching
- Fast local processing, cached 20s, history, alerts, signals breakdown
- CoinDCX INR integrated, versioning, metrics
"""
import time
import threading
from typing import List, Dict
from collections import deque
from datetime import datetime
from .detector import get_crash_detector, CrashReport

class CrashManager:
    def __init__(self, max_history: int=300):
        self.detector = get_crash_detector()
        self.history = deque(maxlen=max_history)
        self.last_report = None
        self.alerts = deque(maxlen=150)
        self._last_scan = 0
        self._cache_ttl = 15  # Faster for v5
        self._lock = threading.Lock()
        self._metrics = {
            "total_scans": 0,
            "cache_hits": 0,
            "alerts_generated": 0,
            "avg_fetch_time_ms": 0,
            "avg_processing_time_ms": 0
        }

    def scan(self, symbols: List[str]=None, force: bool=False) -> Dict:
        with self._lock:
            now=time.time()
            if not force and self.last_report and (now - self._last_scan) < self._cache_ttl:
                d=self.last_report.to_dict()
                d["cached"]=True
                self._metrics["cache_hits"] += 1
                return d

            if symbols:
                if not isinstance(symbols, list):
                    symbols = [symbols]
                symbols = [str(s).upper().strip() for s in symbols if s]
                symbols = symbols[:15]

            try:
                report: CrashReport = self.detector.scan(symbols)
            except Exception as e:
                if self.last_report:
                    d=self.last_report.to_dict()
                    d["cached"]=True
                    d["error"]=str(e)
                    d["warning"]="Scan v5 failed, returning cached"
                    d["version"] = "v5_max"
                    return d
                report = CrashReport(
                    timestamp=datetime.utcnow().isoformat(),
                    crash_risk=20.0,
                    level="LOW",
                    confidence=30.0,
                    signals=[],
                    summary=f"Scan v5 failed: {e} - using fallback",
                    action="⚠️ Scan v5 failed - check manually, set tight SL",
                    btc_price=0,
                    btc_change=0,
                    fetch_time_ms=0,
                    processing_time_ms=0,
                    data_quality=0.0,
                    warnings=[f"Scan v5 failed: {e}"],
                    raw={},
                    version="v5_max"
                )

            self.last_report=report
            try:
                self.history.append(report.to_dict())
            except Exception:
                pass
            self._last_scan=now
            self._metrics["total_scans"] += 1
            # Update avg times
            try:
                prev_fetch = self._metrics["avg_fetch_time_ms"]
                total = self._metrics["total_scans"]
                self._metrics["avg_fetch_time_ms"] = (prev_fetch * (total-1) + report.fetch_time_ms) / total if total > 1 else report.fetch_time_ms
                prev_proc = self._metrics["avg_processing_time_ms"]
                self._metrics["avg_processing_time_ms"] = (prev_proc * (total-1) + report.processing_time_ms) / total if total > 1 else report.processing_time_ms
            except Exception:
                pass

            if report.level in ["HIGH","CRITICAL"]:
                try:
                    self.alerts.append({
                        "timestamp": report.timestamp,
                        "level": report.level,
                        "risk": report.crash_risk,
                        "btc_change": report.btc_change,
                        "summary": report.summary,
                        "action": report.action,
                        "data_quality": report.data_quality,
                        "version": "v5_max"
                    })
                    self._metrics["alerts_generated"] += 1
                except Exception:
                    pass

            out=report.to_dict()
            out["cached"]=False
            out["metrics"] = dict(self._metrics)
            out["version"] = "v5_max"
            return out

    def get_status(self) -> Dict:
        with self._lock:
            if not self.last_report:
                pass
            else:
                d=self.last_report.to_dict()
                d["cached"]=True
                d["history_count"]=len(self.history)
                d["alerts_count"]=len(self.alerts)
                d["metrics"]=dict(self._metrics)
                d["version"]="v5_max"
                return d
        return self.scan()

    def get_history(self, limit: int=50) -> List[Dict]:
        try:
            limit = max(1, min(300, int(limit)))
        except (ValueError, TypeError):
            limit=50
        with self._lock:
            return list(self.history)[-limit:][::-1]

    def get_alerts(self, limit: int=20) -> List[Dict]:
        try:
            limit = max(1, min(150, int(limit)))
        except (ValueError, TypeError):
            limit=20
        with self._lock:
            return list(self.alerts)[-limit:][::-1]

    def get_signals_breakdown(self) -> Dict:
        with self._lock:
            if not self.last_report:
                pass
            else:
                return {
                    "timestamp": self.last_report.timestamp,
                    "crash_risk": self.last_report.crash_risk,
                    "level": self.last_report.level,
                    "confidence": self.last_report.confidence,
                    "data_quality": self.last_report.data_quality,
                    "warnings": self.last_report.warnings,
                    "signals": self.last_report.signals,
                    "btc_price": self.last_report.btc_price,
                    "btc_change": self.last_report.btc_change,
                    "metrics": dict(self._metrics),
                    "version": "v5_max"
                }
        result = self.scan()
        return {
            "timestamp": result.get("timestamp"),
            "crash_risk": result.get("crash_risk"),
            "level": result.get("level"),
            "confidence": result.get("confidence"),
            "data_quality": result.get("data_quality"),
            "warnings": result.get("warnings",[]),
            "signals": result.get("signals",[]),
            "btc_price": result.get("btc_price"),
            "btc_change": result.get("btc_change"),
            "metrics": result.get("metrics", {}),
            "version": "v5_max"
        }

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "history_count": len(self.history), "alerts_count": len(self.alerts), "version": "v5_max"}

_manager=None
_manager_lock=threading.Lock()
def get_crash_manager():
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager=CrashManager()
    return _manager
