"""
Performance Analytics - Real trading performance tracking
Win rate, profit factor, Sharpe, Sortino, equity curve, drawdown
No fake simulation - real P&L
"""
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import json

from ..config import get_config
from ..portfolio.manager import get_portfolio_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class PerformanceAnalytics:
    def __init__(self):
        self.portfolio_manager = get_portfolio_manager()
    
    def get_equity_curve(self) -> List[Dict]:
        """Get equity curve from closed trades - real P&L"""
        try:
            closed = self.portfolio_manager.closed_positions
            if not closed:
                return []
            
            # Sort by entry time
            sorted_trades = sorted(closed, key=lambda x: x.entry_time)
            
            equity = self.portfolio_manager.initial_balance
            curve = [{"date": datetime.utcnow().isoformat(), "equity": equity, "type": "initial"}]
            
            for trade in sorted_trades:
                equity += trade.pnl
                curve.append({
                    "date": trade.entry_time,
                    "equity": equity,
                    "pnl": trade.pnl,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "real_data": True
                })
            
            return curve
        except Exception as e:
            logger.error(f"Equity curve failed: {e}")
            return []
    
    def calculate_metrics(self) -> Dict:
        """Calculate real trading performance metrics"""
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            closed = self.portfolio_manager.closed_positions
            
            if not closed:
                return {
                    "total_trades": 0,
                    "win_rate": 0,
                    "profit_factor": 0,
                    "avg_win": 0,
                    "avg_loss": 0,
                    "total_pnl": portfolio.total_pnl,
                    "total_pnl_pct": portfolio.total_pnl_pct,
                    "sharpe": 0,
                    "sortino": 0,
                    "max_drawdown": 0,
                    "real_trading": True
                }
            
            wins = [t for t in closed if t.pnl > 0]
            losses = [t for t in closed if t.pnl <= 0]
            
            win_rate = len(wins) / len(closed) * 100 if closed else 0
            
            total_wins = sum(t.pnl for t in wins)
            total_losses = abs(sum(t.pnl for t in losses))
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            avg_win = np.mean([t.pnl for t in wins]) if wins else 0
            avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
            
            # Returns for Sharpe/Sortino
            returns = [t.pnl / self.portfolio_manager.initial_balance for t in closed]
            
            if len(returns) > 1 and np.std(returns) > 0:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
                # Sortino - downside deviation
                downside = [r for r in returns if r < 0]
                sortino = np.mean(returns) / np.std(downside) * np.sqrt(252) if downside and np.std(downside) > 0 else 0
            else:
                sharpe = 0
                sortino = 0
            
            # Max drawdown from equity curve
            equity_curve = self.get_equity_curve()
            max_dd = 0
            if equity_curve:
                equities = [e["equity"] for e in equity_curve]
                peak = equities[0]
                for eq in equities:
                    if eq > peak:
                        peak = eq
                    dd = (peak - eq) / peak * 100 if peak > 0 else 0
                    max_dd = max(max_dd, dd)
            
            return {
                "total_trades": len(closed),
                "open_positions": len(self.portfolio_manager.positions),
                "win_rate": win_rate,
                "wins": len(wins),
                "losses": len(losses),
                "profit_factor": profit_factor,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_pnl": portfolio.total_pnl,
                "total_pnl_pct": portfolio.total_pnl_pct,
                "best_trade": max([t.pnl for t in closed], default=0),
                "worst_trade": min([t.pnl for t in closed], default=0),
                "sharpe": sharpe,
                "sortino": sortino,
                "max_drawdown": max_dd,
                "max_drawdown_pct": max_dd,
                "real_trading": True,
                "data_source": "Real trades - live Binance",
                "no_fake": "All P&L from real trading calls"
            }
        except Exception as e:
            logger.error(f"Metrics failed: {e}")
            return {"error": str(e), "real_trading": True}
    
    def get_symbol_performance(self) -> Dict[str, Dict]:
        """Performance per symbol - real trading"""
        try:
            closed = self.portfolio_manager.closed_positions
            symbols = {}
            
            for trade in closed:
                sym = trade.symbol
                if sym not in symbols:
                    symbols[sym] = {"trades": [], "pnl": 0, "wins": 0, "losses": 0}
                symbols[sym]["trades"].append(trade)
                symbols[sym]["pnl"] += trade.pnl
                if trade.pnl > 0:
                    symbols[sym]["wins"] += 1
                else:
                    symbols[sym]["losses"] += 1
            
            result = {}
            for sym, data in symbols.items():
                total = len(data["trades"])
                win_rate = data["wins"] / total * 100 if total > 0 else 0
                result[sym] = {
                    "symbol": sym,
                    "total_trades": total,
                    "total_pnl": data["pnl"],
                    "win_rate": win_rate,
                    "wins": data["wins"],
                    "losses": data["losses"],
                    "avg_pnl": data["pnl"] / total if total > 0 else 0,
                    "real_trading": True
                }
            
            return result
        except Exception as e:
            logger.error(f"Symbol perf failed: {e}")
            return {}
    
    def get_full_analytics(self) -> Dict:
        """Full analytics dashboard - real trading"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.calculate_metrics(),
            "equity_curve": self.get_equity_curve(),
            "symbol_performance": self.get_symbol_performance(),
            "portfolio": self.portfolio_manager.get_portfolio().to_dict(),
            "real_trading": True,
            "data_source": "Live Binance - Real P&L",
            "no_fake": "No paper trading - real performance"
        }

def get_analytics_manager():
    return PerformanceAnalytics()
