"""
Alert Manager - Real-time alerts for real trading
Price alerts, signal alerts, risk alerts
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..config import get_config
from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class Alert:
    id: str
    symbol: str
    type: str  # PRICE_ABOVE, PRICE_BELOW, SIGNAL_BUY, SIGNAL_SELL, RISK_HIGH, etc.
    condition: str
    target_price: Optional[float]
    current_price: float
    message: str
    status: str  # ACTIVE, TRIGGERED, CANCELLED
    created_at: str
    triggered_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class AlertManager:
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "alerts.json"
        self.alerts: Dict[str, Alert] = {}
        self.load()
    
    def load(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for alert_data in data.get("alerts", []):
                    alert = Alert(**alert_data)
                    self.alerts[alert.id] = alert
        except Exception as e:
            logger.warning(f"Failed to load alerts: {e}")
    
    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "alerts": [a.to_dict() for a in self.alerts.values()],
                "timestamp": datetime.utcnow().isoformat()
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def get_live_price(self, symbol: str) -> float:
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            return fetcher.get_current_price() or 0
        except:
            return 0
    
    def create_alert(self, symbol: str, alert_type: str, target_price: float = None, condition: str = "") -> Alert:
        import uuid
        alert_id = str(uuid.uuid4())[:8]
        live_price = self.get_live_price(symbol)
        
        messages = {
            "PRICE_ABOVE": f"{symbol} price above ${target_price} - potential breakout for real trading",
            "PRICE_BELOW": f"{symbol} price below ${target_price} - potential breakdown",
            "SIGNAL_BUY": f"{symbol} BUY signal - real trading opportunity",
            "SIGNAL_SELL": f"{symbol} SELL signal - real trading opportunity",
            "RISK_HIGH": f"{symbol} high risk detected - check position",
            "VOLUME_SPIKE": f"{symbol} volume spike - whale activity"
        }
        
        alert = Alert(
            id=alert_id,
            symbol=symbol,
            type=alert_type,
            condition=condition or f"{alert_type} {target_price}",
            target_price=target_price,
            current_price=live_price,
            message=messages.get(alert_type, f"{symbol} {alert_type} alert"),
            status="ACTIVE",
            created_at=datetime.utcnow().isoformat()
        )
        
        self.alerts[alert_id] = alert
        self.save()
        logger.info(f"Created REAL alert: {alert_id} {symbol} {alert_type} @ ${target_price}")
        return alert
    
    def check_alerts(self) -> List[Alert]:
        """Check all alerts with live prices - real market data"""
        triggered = []
        
        for alert in list(self.alerts.values()):
            if alert.status != "ACTIVE":
                continue
            
            try:
                live_price = self.get_live_price(alert.symbol)
                if live_price == 0:
                    continue
                
                should_trigger = False
                
                if alert.type == "PRICE_ABOVE" and alert.target_price and live_price >= alert.target_price:
                    should_trigger = True
                elif alert.type == "PRICE_BELOW" and alert.target_price and live_price <= alert.target_price:
                    should_trigger = True
                
                if should_trigger:
                    alert.status = "TRIGGERED"
                    alert.triggered_at = datetime.utcnow().isoformat()
                    alert.current_price = live_price
                    triggered.append(alert)
                    logger.info(f"REAL Alert triggered: {alert.id} {alert.symbol} {alert.type} live ${live_price} target ${alert.target_price}")
            
            except Exception as e:
                logger.warning(f"Failed to check alert {alert.id}: {e}")
        
        if triggered:
            self.save()
        
        return triggered
    
    def get_active_alerts(self) -> List[Dict]:
        self.check_alerts()
        return [a.to_dict() for a in self.alerts.values() if a.status == "ACTIVE"]
    
    def get_all_alerts(self) -> List[Dict]:
        return [a.to_dict() for a in self.alerts.values()]
    
    def cancel_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            self.alerts[alert_id].status = "CANCELLED"
            self.save()
            return True
        return False
    
    def to_dict(self):
        active = len([a for a in self.alerts.values() if a.status == "ACTIVE"])
        triggered = len([a for a in self.alerts.values() if a.status == "TRIGGERED"])
        return {
            "total": len(self.alerts),
            "active": active,
            "triggered": triggered,
            "alerts": [a.to_dict() for a in self.alerts.values()],
            "real_trading": True
        }

def get_alert_manager():
    return AlertManager()
