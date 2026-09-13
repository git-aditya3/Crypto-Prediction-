"""
Base Broker - Abstract interface for real trading execution
Supports Spot and Futures, market/limit orders, risk controls
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import uuid

@dataclass
class Order:
    id: str
    symbol: str
    side: str  # BUY, SELL
    type: str  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT, TRAILING_STOP, OCO
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED, REJECTED
    filled_price: Optional[float] = None
    filled_quantity: float = 0
    fee: float = 0
    timestamp: str = ""
    strategy: str = ""
    real_trading: bool = True
    broker: str = ""
    take_profits: Optional[Dict[str, float]] = None
    stop_loss: Optional[float] = None
    leverage: str = "1x"
    trailing_pct: Optional[float] = None
    client_order_id: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class Balance:
    asset: str
    free: float
    locked: float
    total: float

    def to_dict(self):
        return asdict(self)

class BaseBroker(ABC):
    """Abstract broker for real trading"""

    def __init__(self, name: str):
        self.name = name
        self.connected = False

    @abstractmethod
    def connect(self, api_key: str, api_secret: str, testnet: bool = False) -> bool:
        pass

    @abstractmethod
    def get_balance(self) -> Dict[str, Balance]:
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: float = None, stop_price: float = None,
                    take_profits: Dict[str, float] = None, stop_loss: float = None,
                    leverage: str = "1x", trailing_pct: float = None,
                    strategy: str = "") -> Order:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        pass

    @abstractmethod
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        pass

    @abstractmethod
    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        pass

    def test_connection(self) -> Dict:
        try:
            balances = self.get_balance()
            return {"connected": True, "balances": len(balances), "broker": self.name, "real_data": True}
        except Exception as e:
            return {"connected": False, "error": str(e), "broker": self.name}
