"""
Crash Detector Manager - History, Alerts, Fast Local
"""
import time
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
        self._cache_ttl = 20  # seconds

    def scan(self, symbols: List[str]=None, force: bool=False) -> Dict:
        now=time.time()
        if not force and self.last_report and (now - self._last_scan) < self._cache_ttl:
            d=self.last_report.to_dict()
            d["cached"]=True
            return d
        report: CrashReport = self.detector.scan(symbols)
        self.last_report=report
        self.history.append(report.to_dict())
        self._last_scan=now

        # Auto alert if HIGH/CRITICAL
        if report.level in ["HIGH","CRITICAL"]:
            self.alerts.append({
                "timestamp": report.timestamp,
                "level": report.level,
                "risk": report.crash_risk,
                "btc_change": report.btc_change,
                "summary": report.summary,
                "action": report.action
            })
        out=report.to_dict()
        out["cached"]=False
        return out

    def get_status(self) -> Dict:
        if not self.last_report:
            return self.scan()
        d=self.last_report.to_dict()
        d["cached"]=True
        d["history_count"]=len(self.history)
        d["alerts_count"]=len(self.alerts)
        return d

    def get_history(self, limit: int=50) -> List[Dict]:
        return list(self.history)[-limit:][::-1]

    def get_alerts(self, limit: int=20) -> List[Dict]:
        return list(self.alerts)[-limit:][::-1]

    def get_signals_breakdown(self) -> Dict:
        if not self.last_report:
            self.scan()
        return {
            "timestamp": self.last_report.timestamp,
            "crash_risk": self.last_report.crash_risk,
            "level": self.last_report.level,
            "signals": self.last_report.signals,
            "btc_price": self.last_report.btc_price,
            "btc_change": self.last_report.btc_change
        }

_manager=None
def get_crash_manager():
    global _manager
    if _manager is None:
        _manager=CrashManager()
    return _manager
