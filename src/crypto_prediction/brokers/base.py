"""
Base Broker v5 MAX - Abstract interface for real trading execution + metrics + risk
- Supports Spot/Futures, market/limit/stop/trailing/OCO, SL/TP, leverage
- Thread-safe, metrics, validation, fee calculation
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime
import threading

@dataclass
class Order:
    id: str
    symbol: str
    side: str  # BUY, SELL
    type: str  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT, TRAILING_STOP, OCO
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED, REJECTED, OPEN, PARTIALLY_FILLED
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
    version: str = "v5_max"
    metadata: Dict = field(default_factory=dict)

    def to_dict(self):
        try:
            d = asdict(self)
            # Ensure JSON serializable
            return d
        except Exception:
            return {
                "id": self.id,
                "symbol": self.symbol,
                "side": self.side,
                "type": self.type,
                "quantity": self.quantity,
                "price": self.price,
                "status": self.status,
                "broker": self.broker,
                "real_trading": self.real_trading
            }

@dataclass
class Balance:
    asset: str
    free: float
    locked: float
    total: float
    usd_value: float = 0.0
    version: str = "v5_max"

    def to_dict(self):
        try:
            return asdict(self)
        except Exception:
            return {"asset": self.asset, "free": self.free, "locked": self.locked, "total": self.total}

class BaseBroker(ABC):
    """Abstract broker v5 MAX for real trading"""

    def __init__(self, name: str):
        self.name = name
        self.connected = False
        self.paper_mode = True
        self._lock = threading.Lock()
        self._metrics = {
            "orders_placed": 0,
            "orders_filled": 0,
            "orders_cancelled": 0,
            "total_fees": 0.0,
            "errors": 0,
            "last_order_time": None
        }

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

    def get_ticker(self, symbol: str) -> Dict:
        """Optional - get ticker data"""
        return {}

    def get_tickers_all(self) -> Dict:
        """Optional - get all tickers"""
        return {}

    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Optional - get orderbook"""
        return None

    def calculate_fee(self, quantity: float, price: float, fee_rate: float = 0.001) -> float:
        try:
            return float(quantity) * float(price) * float(fee_rate)
        except Exception:
            return 0.0

    def validate_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Dict:
        """Validate order before placement - v5"""
        issues = []
        if not symbol or not isinstance(symbol, str) or len(symbol) < 2:
            issues.append(f"Invalid symbol {symbol}")
        if side.upper() not in ["BUY", "SELL"]:
            issues.append(f"Invalid side {side}")
        try:
            q = float(quantity)
            if q <= 0 or q > 1_000_000:
                issues.append(f"Invalid quantity {quantity}")
        except Exception:
            issues.append(f"Invalid quantity type {quantity}")
        
        if price is not None:
            try:
                p = float(price)
                if p <= 0 or p > 200_000_000:
                    issues.append(f"Invalid price {price}")
            except Exception:
                issues.append(f"Invalid price type {price}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "symbol": symbol,
            "version": "v5_max"
        }

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "broker": self.name, "connected": self.connected, "paper_mode": self.paper_mode, "version": "v5_max"}

    def test_connection(self) -> Dict:
        try:
            balances = self.get_balance()
            return {
                "connected": True, 
                "balances": len(balances), 
                "broker": self.name, 
                "real_data": True,
                "paper_mode": self.paper_mode,
                "metrics": self.get_metrics(),
                "version": "v5_max"
            }
        except Exception as e:
            with self._lock:
                self._metrics["errors"] += 1
            return {"connected": False, "error": str(e), "broker": self.name, "version": "v5_max"}
