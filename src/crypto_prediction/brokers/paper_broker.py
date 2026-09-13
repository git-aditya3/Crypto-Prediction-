"""
Paper Broker v5 MAX - Safe simulated trading with real market prices + metrics + risk
- Real live prices, fee simulation, slippage, portfolio tracking, metrics
- Thread-safe, validation, supports LONG/SHORT, leverage simulation
"""
from typing import Dict, List
import uuid
from datetime import datetime
import threading

from .base import BaseBroker, Order, Balance
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class PaperBroker(BaseBroker):
    """Paper trading broker v5 MAX - safe simulation with real prices"""

    def __init__(self, initial_balance: float = 10000):
        super().__init__(name="Paper")
        self.initial_balance = initial_balance
        self.balances: Dict[str, Balance] = {
            "USDT": Balance(asset="USDT", free=initial_balance, locked=0, total=initial_balance, usd_value=initial_balance)
        }
        self.orders: Dict[str, Order] = {}
        self.connected = True
        self.paper_mode = True
        self._lock = threading.Lock()
        self._metrics = {
            "orders_placed": 0,
            "orders_filled": 0,
            "total_fees": 0.0,
            "total_pnl": 0.0,
            "win_trades": 0,
            "loss_trades": 0
        }

    def connect(self, api_key: str = None, api_secret: str = None, testnet: bool = False) -> bool:
        with self._lock:
            self.connected = True
        logger.info(f"📝 Paper Broker v5 MAX connected - ${self.initial_balance} simulated - safe, no real money | version v5_max")
        return True

    def get_balance(self) -> Dict[str, Balance]:
        with self._lock:
            # Update USD values
            for asset, bal in self.balances.items():
                if asset == "USDT" or asset == "INR":
                    bal.usd_value = bal.total
                else:
                    try:
                        price = self.get_price(asset + "-USD")
                        bal.usd_value = bal.total * price if price else bal.total
                    except Exception:
                        bal.usd_value = bal.total
            return dict(self.balances)

    def get_price(self, symbol: str) -> float:
        try:
            from ..data.price_helper import get_live_price
            price = get_live_price(symbol)
            return price or 0.0
        except Exception:
            try:
                from ..data.realtime import BinanceRealtimeFetcher
                fetcher = BinanceRealtimeFetcher(symbol=symbol)
                price = fetcher.get_current_price()
                return price or 0
            except Exception:
                return 0.0

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: float = None, stop_price: float = None,
                    take_profits: Dict[str, float] = None, stop_loss: float = None,
                    leverage: str = "1x", trailing_pct: float = None,
                    strategy: str = "") -> Order:
        with self._lock:
            validation = self.validate_order(symbol, side, quantity, price)
            if not validation["valid"]:
                raise ValueError(f"Order validation failed v5: {validation['issues']}")

        order_id = str(uuid.uuid4())[:8]
        live_price = self.get_price(symbol)
        
        if live_price == 0:
            if price and price > 0:
                live_price = price
                logger.warning(f"Paper v5 live price unavailable for {symbol}, using provided ${price:.2f}")
            else:
                try:
                    from ..trading.calls import TradingCallGenerator
                    gen = TradingCallGenerator()
                    bp = gen._get_live_price(symbol)
                    if bp and bp > 0:
                        live_price = bp
                except Exception:
                    pass
        
        if live_price == 0:
            if price and price > 0:
                live_price = price
            else:
                raise ValueError(f"Could not get live price v5 for {symbol}")

        # Slippage simulation v5
        slippage = config.backtest.slippage
        if side.upper() == "BUY":
            filled_price = live_price * (1 + slippage)
        else:
            filled_price = live_price * (1 - slippage)
        
        if price and order_type.upper() == "LIMIT":
            filled_price = price

        # Fee
        fee_rate = config.backtest.commission
        fee = quantity * filled_price * fee_rate

        asset = symbol.split("-")[0].split("/")[0].split("_")[0].upper()
        
        with self._lock:
            if side.upper() == "BUY":
                cost = quantity * filled_price + fee
                usdt_balance = self.balances.get("USDT")
                if not usdt_balance or usdt_balance.free < cost:
                    if usdt_balance and usdt_balance.free > 0:
                        quantity = (usdt_balance.free - fee) / filled_price * 0.99
                        if quantity <= 0:
                            raise ValueError(f"Insufficient USDT v5: need ${cost:.2f}, have ${usdt_balance.free:.2f}")
                        cost = quantity * filled_price + fee
                        fee = quantity * filled_price * fee_rate
                        logger.warning(f"Paper v5 adjusted quantity to {quantity:.6f}")
                    else:
                        raise ValueError(f"Insufficient USDT v5: need ${cost:.2f}, have ${usdt_balance.free if usdt_balance else 0:.2f}")
                self.balances["USDT"].free -= cost
                self.balances["USDT"].total -= cost
                if asset not in self.balances:
                    self.balances[asset] = Balance(asset=asset, free=0, locked=0, total=0)
                self.balances[asset].free += quantity
                self.balances[asset].total += quantity
            else:  # SELL
                if asset not in self.balances:
                    self.balances[asset] = Balance(asset=asset, free=0, locked=0, total=0)
                if self.balances[asset].free >= quantity:
                    self.balances[asset].free -= quantity
                    self.balances[asset].total -= quantity
                    proceeds = quantity * filled_price - fee
                    self.balances["USDT"].free += proceeds
                    self.balances["USDT"].total += proceeds
                else:
                    # Short selling
                    required_margin = quantity * filled_price * 0.1
                    usdt_balance = self.balances.get("USDT")
                    if usdt_balance and usdt_balance.free >= required_margin:
                        self.balances[asset].free -= quantity
                        self.balances[asset].total -= quantity
                        logger.info(f"📝 PAPER v5 Short: {symbol} {quantity} @ ${filled_price:.2f} margin ${required_margin:.2f}")
                    else:
                        raise ValueError(f"Insufficient {asset} v5 and USDT margin for short: need {quantity} {asset} or ${required_margin:.2f}")

            order = Order(
                id=order_id,
                symbol=symbol,
                side=side.upper(),
                type=order_type.upper(),
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                status="FILLED",
                filled_price=filled_price,
                filled_quantity=quantity,
                fee=fee,
                timestamp=datetime.utcnow().isoformat(),
                strategy=strategy,
                real_trading=False,
                broker=self.name,
                take_profits=take_profits,
                stop_loss=stop_loss,
                leverage=leverage,
                trailing_pct=trailing_pct,
                client_order_id=f"paper_v5_{order_id}",
                version="v5_max",
                metadata={"live_price": live_price, "slippage": slippage, "fee_rate": fee_rate}
            )

            self.orders[order_id] = order
            self._metrics["orders_placed"] += 1
            self._metrics["orders_filled"] += 1
            self._metrics["total_fees"] += fee
            self._metrics["last_order_time"] = datetime.utcnow().isoformat()

        logger.info(f"📝 PAPER v5 Order Filled: {symbol} {side} {quantity:.6f} @ ${filled_price:.2f} fee ${fee:.2f} - simulated real price")
        return order

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        with self._lock:
            if order_id in self.orders:
                self.orders[order_id].status = "CANCELLED"
                self._metrics["orders_cancelled"] = self._metrics.get("orders_cancelled", 0) + 1
                return True
        return False

    def get_open_orders(self, symbol: str = None) -> List[Order]:
        with self._lock:
            open_orders = [o for o in self.orders.values() if o.status in ["PENDING", "OPEN", "PARTIALLY_FILLED"]]
            if symbol:
                open_orders = [o for o in open_orders if o.symbol == symbol]
            return open_orders

    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        try:
            limit = max(1, min(500, int(limit)))
        except Exception:
            limit = 100
        with self._lock:
            orders = list(self.orders.values())
            if symbol:
                orders = [o for o in orders if o.symbol == symbol]
            orders.sort(key=lambda x: x.timestamp, reverse=True)
            return orders[:limit]

    def get_metrics(self) -> Dict:
        with self._lock:
            return {
                **self._metrics,
                "balances": len(self.balances),
                "orders": len(self.orders),
                "broker": self.name,
                "paper_mode": True,
                "version": "v5_max"
            }
