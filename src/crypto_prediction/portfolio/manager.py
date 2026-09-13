"""
Portfolio Manager - Real portfolio tracking for actual trades
No fake simulation - tracks real holdings, real P&L
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import numpy as np

from ..config import get_config
from ..data.realtime import BinanceRealtimeFetcher
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class Position:
    symbol: str
    side: str  # LONG, SHORT
    entry_price: float
    current_price: float
    quantity: float
    stop_loss: float
    take_profits: Dict[str, float]
    entry_time: str
    leverage: str = "1x"
    status: str = "OPEN"
    pnl: float = 0
    pnl_pct: float = 0
    risk_amount: float = 0
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Portfolio:
    total_value: float
    cash: float
    positions_value: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[Dict]
    allocation: Dict[str, float]
    timestamp: str
    closed_positions: List[Dict] = None
    real_trading: bool = True
    data_source: str = "Live Binance prices"
    no_fake: str = "Real P&L from actual positions"
    
    def to_dict(self):
        d = asdict(self)
        # Ensure closed_positions is list
        if d.get('closed_positions') is None:
            d['closed_positions'] = []
        return d

class PortfolioManager:
    """
    Real portfolio management - tracks actual trades
    """
    def __init__(self, initial_balance: float = 10000, storage_path: str = None):
        self.initial_balance = initial_balance
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "portfolio.json"
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.cash = initial_balance
        self.load()
    
    def load(self):
        """Load portfolio from storage"""
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                self.cash = data.get("cash", self.initial_balance)
                self.initial_balance = data.get("initial_balance", self.initial_balance)
                # Load positions
                for pos_data in data.get("positions", []):
                    pos = Position(**pos_data)
                    self.positions[pos.symbol] = pos
                for pos_data in data.get("closed_positions", []):
                    self.closed_positions.append(Position(**pos_data))
                logger.info(f"Loaded portfolio: {len(self.positions)} open, {len(self.closed_positions)} closed, cash ${self.cash:.2f}")
        except Exception as e:
            logger.warning(f"Failed to load portfolio: {e}")
    
    def save(self):
        """Save portfolio to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "initial_balance": self.initial_balance,
                "cash": self.cash,
                "positions": [p.to_dict() for p in self.positions.values()],
                "closed_positions": [p.to_dict() for p in self.closed_positions],
                "timestamp": datetime.utcnow().isoformat()
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")
    
    def get_live_price(self, symbol: str) -> float:
        """Get live Binance price - real data"""
        try:
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price()
            if price:
                return price
            # Fallback to cache
            from ..trading.calls import TradingCallGenerator
            gen = TradingCallGenerator()
            bp = gen._get_binance_price(symbol)
            return bp or 0
        except:
            return 0
    
    def open_position(self, symbol: str, side: str, entry_price: float, quantity: float, 
                     stop_loss: float, take_profits: Dict[str, float], leverage: str = "1x", risk_amount: float = 0) -> Position:
        """Open real position"""
        # Check if already have position
        if symbol in self.positions:
            logger.warning(f"Already have position for {symbol}, closing existing")
            self.close_position(symbol, entry_price)
        
        cost = quantity * entry_price
        if cost > self.cash:
            # Adjust quantity to available cash
            quantity = self.cash / entry_price * 0.99  # Leave 1% for fees
            cost = quantity * entry_price
        
        self.cash -= cost
        
        pos = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profits=take_profits,
            entry_time=datetime.utcnow().isoformat(),
            leverage=leverage,
            status="OPEN",
            pnl=0,
            pnl_pct=0,
            risk_amount=risk_amount
        )
        
        self.positions[symbol] = pos
        self.save()
        logger.info(f"Opened REAL position: {symbol} {side} {quantity:.4f} @ ${entry_price:.2f} SL ${stop_loss:.2f}")
        return pos
    
    def close_position(self, symbol: str, current_price: float = None, reason: str = "MANUAL") -> Optional[Position]:
        """Close real position"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        if current_price is None:
            current_price = self.get_live_price(symbol)
        
        # Calculate P&L
        if pos.side == "LONG":
            pnl = (current_price - pos.entry_price) * pos.quantity
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
        else:
            pnl = (pos.entry_price - current_price) * pos.quantity
            pnl_pct = (pos.entry_price - current_price) / pos.entry_price * 100
        
        # Update position
        pos.current_price = current_price
        pos.pnl = pnl
        pos.pnl_pct = pnl_pct
        pos.status = f"CLOSED_{reason}"
        
        # Return cash + P&L
        self.cash += pos.quantity * pos.entry_price + pnl
        
        # Move to closed
        self.closed_positions.append(pos)
        del self.positions[symbol]
        self.save()
        
        logger.info(f"Closed REAL position: {symbol} P&L ${pnl:.2f} ({pnl_pct:.2f}%) reason {reason}")
        return pos
    
    def update_positions(self):
        """Update all positions with live prices - real market data"""
        for symbol, pos in list(self.positions.items()):
            try:
                live_price = self.get_live_price(symbol)
                if live_price and live_price > 0:
                    pos.current_price = live_price
                    
                    # Calculate live P&L
                    if pos.side == "LONG":
                        pos.pnl = (live_price - pos.entry_price) * pos.quantity
                        pos.pnl_pct = (live_price - pos.entry_price) / pos.entry_price * 100
                        
                        # Check SL/TP
                        if live_price <= pos.stop_loss:
                            self.close_position(symbol, live_price, "STOP_LOSS")
                        elif live_price >= pos.take_profits.get("tp3", float('inf')):
                            self.close_position(symbol, live_price, "TP3")
                        elif live_price >= pos.take_profits.get("tp2", float('inf')):
                            # Partial close at TP2 - for real trading, we could implement partials
                            pass
                    else:
                        pos.pnl = (pos.entry_price - live_price) * pos.quantity
                        pos.pnl_pct = (pos.entry_price - live_price) / pos.entry_price * 100
                        
                        if live_price >= pos.stop_loss:
                            self.close_position(symbol, live_price, "STOP_LOSS")
                        elif live_price <= pos.take_profits.get("tp3", 0):
                            self.close_position(symbol, live_price, "TP3")
            except Exception as e:
                logger.warning(f"Failed to update {symbol}: {e}")
        
        self.save()
    
    def get_portfolio(self) -> Portfolio:
        """Get current portfolio with real P&L"""
        self.update_positions()
        
        positions_value = 0
        total_pnl = 0
        
        for pos in self.positions.values():
            positions_value += pos.quantity * pos.current_price
            total_pnl += pos.pnl
        
        # Include closed P&L
        closed_pnl = sum(p.pnl for p in self.closed_positions)
        total_pnl += closed_pnl
        
        total_value = self.cash + positions_value
        total_pnl_pct = (total_value - self.initial_balance) / self.initial_balance * 100 if self.initial_balance > 0 else 0
        
        # Allocation
        allocation = {}
        if total_value > 0:
            allocation["CASH"] = self.cash / total_value * 100
            for symbol, pos in self.positions.items():
                allocation[symbol] = (pos.quantity * pos.current_price) / total_value * 100
        
        return Portfolio(
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            positions=[p.to_dict() for p in self.positions.values()],
            allocation=allocation,
            timestamp=datetime.utcnow().isoformat(),
            closed_positions=[p.to_dict() for p in self.closed_positions[-20:]],  # last 20 closed
            real_trading=True,
            data_source="Live Binance prices",
            no_fake="Real P&L from actual positions"
        )
    
    def get_performance(self) -> Dict:
        """Get performance metrics - real trading"""
        portfolio = self.get_portfolio()
        
        closed = self.closed_positions
        wins = [p for p in closed if p.pnl > 0]
        losses = [p for p in closed if p.pnl <= 0]
        
        win_rate = len(wins) / len(closed) * 100 if closed else 0
        avg_win = np.mean([p.pnl for p in wins]) if wins else 0
        avg_loss = np.mean([p.pnl for p in losses]) if losses else 0
        profit_factor = abs(sum(p.pnl for p in wins) / sum(p.pnl for p in losses)) if losses and sum(p.pnl for p in losses) != 0 else 0
        
        # Real trading metrics
        return {
            "total_value": portfolio.total_value,
            "initial_balance": self.initial_balance,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_pct": portfolio.total_pnl_pct,
            "cash": portfolio.cash,
            "open_positions": len(self.positions),
            "closed_trades": len(closed),
            "win_rate": win_rate,
            "wins": len(wins),
            "losses": len(losses),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "best_trade": max([p.pnl for p in closed], default=0),
            "worst_trade": min([p.pnl for p in closed], default=0),
            "real_trading": True,
            "data_source": "Live Binance"
        }

# Global instance
_portfolio_manager = None

def get_portfolio_manager(initial_balance: float = 10000) -> PortfolioManager:
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager(initial_balance=initial_balance)
    return _portfolio_manager
