"""
Paper Broker - Safe simulated trading with real market prices
For testing strategies before real trading
"""
from typing import Dict, List
import uuid
from datetime import datetime

from .base import BaseBroker, Order, Balance
from ..data.realtime import BinanceRealtimeFetcher
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class PaperBroker(BaseBroker):
    """Paper trading broker - safe simulation with real prices"""

    def __init__(self, initial_balance: float = 10000):
        super().__init__(name="Paper")
        self.initial_balance = initial_balance
        self.balances: Dict[str, Balance] = {
            "USDT": Balance(asset="USDT", free=initial_balance, locked=0, total=initial_balance)
        }
        self.orders: Dict[str, Order] = {}
        self.connected = True

    def connect(self, api_key: str = None, api_secret: str = None, testnet: bool = False) -> bool:
        self.connected = True
        logger.info(f"📝 Paper Broker connected - ${self.initial_balance} simulated balance - safe, no real money")
        return True

    def get_balance(self) -> Dict[str, Balance]:
        return self.balances

    def get_price(self, symbol: str) -> float:
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price()
            return price or 0
        except Exception:
            return 0

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: float = None, stop_price: float = None,
                    take_profits: Dict[str, float] = None, stop_loss: float = None,
                    leverage: str = "1x", trailing_pct: float = None,
                    strategy: str = "") -> Order:
        """Place paper order - simulated with real price, fallback to provided price"""
        order_id = str(uuid.uuid4())[:8]
        live_price = self.get_price(symbol)
        
        # Fallback to provided price if live unavailable (for SSL issues)
        if live_price == 0:
            if price and price > 0:
                live_price = price
                logger.warning(f"Live price unavailable for {symbol}, using provided price ${price:.2f} as fallback - real market data from call")
            else:
                # Try to get from call generator's binance price
                try:
                    from ..trading.calls import TradingCallGenerator
                    gen = TradingCallGenerator()
                    bp = gen._get_binance_price(symbol)
                    if bp and bp > 0:
                        live_price = bp
                        logger.warning(f"Using Binance fallback price for {symbol}: ${bp:.2f}")
                except Exception:
                    pass
        
        if live_price == 0:
            # Last resort: use last cached portfolio or default
            # For paper trading, we allow execution with provided price to avoid blocking
            if price and price > 0:
                live_price = price
            else:
                raise ValueError(f"Could not get live price for {symbol} - real market data unavailable and no fallback price")
        
        filled_price = price or live_price
        
        # Check balance for BUY - allow with USDT
        asset = symbol.split("-")[0]
        if side.upper() == "BUY":
            cost = quantity * filled_price
            usdt_balance = self.balances.get("USDT")
            if not usdt_balance or usdt_balance.free < cost:
                # For paper trading, allow if we have at least some USDT, adjust quantity
                if usdt_balance and usdt_balance.free > 0:
                    quantity = usdt_balance.free / filled_price * 0.99
                    cost = quantity * filled_price
                    logger.warning(f"Adjusted quantity to available USDT: {quantity:.6f}")
                else:
                    raise ValueError(f"Insufficient balance: need ${cost:.2f}, have ${usdt_balance.free if usdt_balance else 0:.2f}")
            # Deduct
            self.balances["USDT"].free -= cost
            self.balances["USDT"].total -= cost
            # Add asset
            if asset not in self.balances:
                self.balances[asset] = Balance(asset=asset, free=0, locked=0, total=0)
            self.balances[asset].free += quantity
            self.balances[asset].total += quantity
        else:  # SELL - allow short selling for paper futures simulation
            if asset not in self.balances:
                self.balances[asset] = Balance(asset=asset, free=0, locked=0, total=0)
            # For paper, allow short selling - negative balance allowed for SHORT simulation
            # Or if we have balance, deduct, else allow short
            if self.balances[asset].free >= quantity:
                self.balances[asset].free -= quantity
                self.balances[asset].total -= quantity
                proceeds = quantity * filled_price
                self.balances["USDT"].free += proceeds
                self.balances["USDT"].total += proceeds
            else:
                # Short selling: allow with USDT collateral check
                # Require some USDT for margin
                required_margin = quantity * filled_price * 0.1  # 10% margin for short
                usdt_balance = self.balances.get("USDT")
                if usdt_balance and usdt_balance.free >= required_margin:
                    # Allow short - deduct margin, add negative asset
                    self.balances[asset].free -= quantity
                    self.balances[asset].total -= quantity
                    # Keep USDT as collateral (don't add proceeds for short, but track)
                    logger.info(f"📝 PAPER Short Sell: {symbol} {quantity} @ ${filled_price:.2f} - short position, margin ${required_margin:.2f}")
                else:
                    raise ValueError(f"Insufficient {asset} balance and insufficient USDT margin for short: need {quantity} {asset} or ${required_margin:.2f} USDT margin")

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
            fee=quantity * filled_price * 0.001,
            timestamp=datetime.utcnow().isoformat(),
            strategy=strategy,
            real_trading=False,
            broker=self.name,
            take_profits=take_profits,
            stop_loss=stop_loss,
            leverage=leverage,
            trailing_pct=trailing_pct,
            client_order_id=f"paper_{order_id}"
        )

        self.orders[order_id] = order
        logger.info(f"📝 PAPER Order Filled: {symbol} {side} {quantity} @ ${filled_price:.2f} - Simulated, real price, no real money")
        return order

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = "CANCELLED"
            return True
        return False

    def get_open_orders(self, symbol: str = None) -> List[Order]:
        open_orders = [o for o in self.orders.values() if o.status == "PENDING"]
        if symbol:
            open_orders = [o for o in open_orders if o.symbol == symbol]
        return open_orders

    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        orders = list(self.orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        orders.sort(key=lambda x: x.timestamp, reverse=True)
        return orders[:limit]
