"""
Crash Detector Manager - Fixed: thread safety, validation, persistence
"""
import time
import threading
from typing import List, Dict
from collections import deque
from datetime import datetime
from .detector import get_crash_detector, CrashReport

class CrashManager:
    def __init__(self, max_history: int=200):
        self.detector = get_crash_detector()
        self.history = deque(maxlen=max_history)
        self.last_report = None
        self.alerts = deque(maxlen=100)
        self._last_scan = 0
        self._cache_ttl = 20
        self._lock = threading.Lock()

    def scan(self, symbols: List[str]=None, force: bool=False) -> Dict:
        with self._lock:
            now=time.time()
            if not force and self.last_report and (now - self._last_scan) < self._cache_ttl:
                d=self.last_report.to_dict()
                d["cached"]=True
                return d

            # Validate symbols
            if symbols:
                if not isinstance(symbols, list):
                    symbols = [symbols]
                symbols = [str(s).upper().strip() for s in symbols if s]
                symbols = symbols[:10]  # limit

            try:
                report: CrashReport = self.detector.scan(symbols)
            except Exception as e:
                # Return last report if scan fails
                if self.last_report:
                    d=self.last_report.to_dict()
                    d["cached"]=True
                    d["error"]=str(e)
                    d["warning"]="Scan failed, returning cached"
                    return d
                # Create minimal report
                report = CrashReport(
                    timestamp=datetime.utcnow().isoformat(),
                    crash_risk=20.0,
                    level="LOW",
                    confidence=30.0,
                    signals=[],
                    summary=f"Scan failed: {e} - using fallback",
                    action="⚠️ Scan failed - check manually, set tight SL",
                    btc_price=0,
                    btc_change=0,
                    fetch_time_ms=0,
                    processing_time_ms=0,
                    data_quality=0.0,
                    warnings=[f"Scan failed: {e}"],
                    raw={}
                )

            self.last_report=report
            try:
                self.history.append(report.to_dict())
            except Exception:
                pass
            self._last_scan=now

            if report.level in ["HIGH","CRITICAL"]:
                try:
                    self.alerts.append({
                        "timestamp": report.timestamp,
                        "level": report.level,
                        "risk": report.crash_risk,
                        "btc_change": report.btc_change,
                        "summary": report.summary,
                        "action": report.action,
                        "data_quality": report.data_quality
                    })
                except Exception:
                    pass

            out=report.to_dict()
            out["cached"]=False
            return out

    def get_status(self) -> Dict:
        with self._lock:
            if not self.last_report:
                # Release lock to avoid deadlock when calling scan
                pass
            else:
                d=self.last_report.to_dict()
                d["cached"]=True
                d["history_count"]=len(self.history)
                d["alerts_count"]=len(self.alerts)
                return d
        # Outside lock
        return self.scan()

    def get_history(self, limit: int=50) -> List[Dict]:
        try:
            limit = max(1, min(200, int(limit)))
        except (ValueError, TypeError):
            limit=50
        with self._lock:
            return list(self.history)[-limit:][::-1]

    def get_alerts(self, limit: int=20) -> List[Dict]:
        try:
            limit = max(1, min(100, int(limit)))
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
                    "btc_change": self.last_report.btc_change
                }
        # Outside lock, trigger scan
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
            "btc_change": result.get("btc_change")
        }

_manager=None
_manager_lock=threading.Lock()
def get_crash_manager():
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager=CrashManager()
    return _manager
