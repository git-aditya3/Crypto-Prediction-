"""
Risk Guard - Extensive risk management for real automated trading
Prevents over-trading, large losses, protects capital
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .config import AutoTradingConfig
from ..portfolio.manager import get_portfolio_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str
    risk_amount: float = 0
    position_size: float = 0
    details: Dict = None

class RiskGuard:
    """Extensive risk checks before real trading"""

    def __init__(self, config: AutoTradingConfig):
        self.config = config
        self.daily_trades: List[Dict] = []
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.last_trade_time: Optional[datetime] = None
        self.portfolio_manager = get_portfolio_manager()

    def update_config(self, config: AutoTradingConfig):
        self.config = config

    def check_emergency_stop(self) -> RiskCheckResult:
        if self.config.emergency_stop:
            return RiskCheckResult(allowed=False, reason="Emergency stop enabled - trading halted")
        return RiskCheckResult(allowed=True, reason="Emergency stop not active")

    def check_enabled(self) -> RiskCheckResult:
        if not self.config.enabled:
            return RiskCheckResult(allowed=False, reason="Auto trading disabled")
        return RiskCheckResult(allowed=True, reason="Auto trading enabled")

    def check_trading_hours(self) -> RiskCheckResult:
        if not self.config.trading_hours.enabled:
            return RiskCheckResult(allowed=True, reason="24/7 trading enabled")
        
        now = datetime.utcnow()
        current_hour = now.hour
        start = self.config.trading_hours.start_hour
        end = self.config.trading_hours.end_hour
        
        if start <= current_hour < end:
            return RiskCheckResult(allowed=True, reason=f"Within trading hours {start}:00-{end}:00 UTC")
        else:
            return RiskCheckResult(allowed=False, reason=f"Outside trading hours {start}:00-{end}:00 UTC, current {current_hour}:00")

    def check_daily_loss(self) -> RiskCheckResult:
        if not self.config.risk.daily_loss_halt:
            return RiskCheckResult(allowed=True, reason="Daily loss halt disabled")
        
        # Reset daily if new day
        today = datetime.utcnow().date()
        today_trades = [t for t in self.daily_trades if datetime.fromisoformat(t["timestamp"]).date() == today]
        today_pnl = sum(t.get("pnl", 0) for t in today_trades)
        
        max_daily_loss = self.config.account_balance * (self.config.risk.max_daily_loss_pct / 100)
        
        if today_pnl <= -max_daily_loss:
            return RiskCheckResult(
                allowed=False,
                reason=f"Daily loss limit reached: ${today_pnl:.2f} <= -${max_daily_loss:.2f} ({self.config.risk.max_daily_loss_pct}%) - trading halted for today",
                details={"daily_pnl": today_pnl, "max_loss": max_daily_loss}
            )
        
        return RiskCheckResult(allowed=True, reason=f"Daily P&L ${today_pnl:.2f} within limit -${max_daily_loss:.2f}")

    def check_max_positions(self) -> RiskCheckResult:
        portfolio = self.portfolio_manager.get_portfolio()
        open_count = len(portfolio.positions)
        
        if open_count >= self.config.risk.max_positions:
            return RiskCheckResult(
                allowed=False,
                reason=f"Max positions reached: {open_count} >= {self.config.risk.max_positions}"
            )
        
        return RiskCheckResult(allowed=True, reason=f"Positions {open_count}/{self.config.risk.max_positions}")

    def check_max_drawdown(self) -> RiskCheckResult:
        portfolio = self.portfolio_manager.get_portfolio()
        drawdown_pct = -portfolio.total_pnl_pct if portfolio.total_pnl_pct < 0 else 0
        
        if drawdown_pct >= self.config.risk.max_drawdown_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"Max drawdown reached: {drawdown_pct:.2f}% >= {self.config.risk.max_drawdown_pct}% - trading halted"
            )
        
        return RiskCheckResult(allowed=True, reason=f"Drawdown {drawdown_pct:.2f}% within {self.config.risk.max_drawdown_pct}%")

    def check_consecutive_losses(self) -> RiskCheckResult:
        if self.consecutive_losses >= self.config.risk.max_consecutive_losses:
            # Check cooldown
            if self.last_trade_time:
                cooldown = timedelta(minutes=self.config.risk.cooldown_after_loss_minutes)
                if datetime.utcnow() - self.last_trade_time < cooldown:
                    return RiskCheckResult(
                        allowed=False,
                        reason=f"Max consecutive losses {self.consecutive_losses} >= {self.config.risk.max_consecutive_losses} - cooldown {self.config.risk.cooldown_after_loss_minutes}min"
                    )
                else:
                    # Reset after cooldown
                    self.consecutive_losses = 0
        
        return RiskCheckResult(allowed=True, reason=f"Consecutive losses {self.consecutive_losses}/{self.config.risk.max_consecutive_losses}")

    def check_daily_trades(self) -> RiskCheckResult:
        today = datetime.utcnow().date()
        today_count = len([t for t in self.daily_trades if datetime.fromisoformat(t["timestamp"]).date() == today])
        
        if today_count >= self.config.max_daily_trades:
            return RiskCheckResult(
                allowed=False,
                reason=f"Max daily trades reached: {today_count} >= {self.config.max_daily_trades}"
            )
        
        return RiskCheckResult(allowed=True, reason=f"Daily trades {today_count}/{self.config.max_daily_trades}")

    def check_cooldown(self) -> RiskCheckResult:
        if not self.last_trade_time:
            return RiskCheckResult(allowed=True, reason="No previous trade")
        
        cooldown = timedelta(minutes=self.config.trading_hours.cooldown_between_trades_minutes)
        elapsed = datetime.utcnow() - self.last_trade_time
        
        if elapsed < cooldown:
            remaining = cooldown - elapsed
            return RiskCheckResult(
                allowed=False,
                reason=f"Cooldown active: {remaining.total_seconds()/60:.1f}min remaining (need {self.config.trading_hours.cooldown_between_trades_minutes}min between trades)"
            )
        
        return RiskCheckResult(allowed=True, reason=f"Cooldown passed, {elapsed.total_seconds()/60:.1f}min since last trade")

    def check_symbol_allowed(self, symbol: str) -> RiskCheckResult:
        # Check blacklist
        if symbol in self.config.symbols.blacklist:
            return RiskCheckResult(allowed=False, reason=f"Symbol {symbol} in blacklist")
        
        # Check whitelist if not empty
        if self.config.symbols.whitelist and symbol not in self.config.symbols.whitelist:
            return RiskCheckResult(allowed=False, reason=f"Symbol {symbol} not in whitelist {self.config.symbols.whitelist}")
        
        # Check max per symbol
        portfolio = self.portfolio_manager.get_portfolio()
        symbol_positions = [p for p in portfolio.positions if p["symbol"] == symbol]
        if len(symbol_positions) >= self.config.symbols.max_positions_per_symbol:
            return RiskCheckResult(
                allowed=False,
                reason=f"Max positions per symbol reached for {symbol}: {len(symbol_positions)} >= {self.config.symbols.max_positions_per_symbol}"
            )
        
        return RiskCheckResult(allowed=True, reason=f"Symbol {symbol} allowed")

    def check_signal_confidence(self, confidence: float) -> RiskCheckResult:
        threshold = self.config.strategies.ai_confidence_threshold
        if confidence < threshold:
            return RiskCheckResult(
                allowed=False,
                reason=f"Confidence {confidence:.1f}% < threshold {threshold}%"
            )
        return RiskCheckResult(allowed=True, reason=f"Confidence {confidence:.1f}% >= {threshold}%")

    def check_risk_reward(self, risk_reward: float) -> RiskCheckResult:
        min_rr = self.config.strategies.min_risk_reward
        if risk_reward < min_rr:
            return RiskCheckResult(
                allowed=False,
                reason=f"Risk/Reward {risk_reward:.2f} < min {min_rr}"
            )
        return RiskCheckResult(allowed=True, reason=f"RR {risk_reward:.2f} >= {min_rr}")

    def calculate_position_size(self, entry_price: float, stop_loss: float, account_balance: float = None) -> RiskCheckResult:
        """Calculate position size with extensive methods"""
        balance = account_balance or self.config.account_balance
        risk_pct = self.config.risk.risk_per_trade_pct
        
        # Check symbol override
        # For simplicity, use global risk
        
        risk_amount = balance * (risk_pct / 100)
        
        # Risk-based sizing: position = risk_amount / |entry - SL|
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return RiskCheckResult(allowed=False, reason="Risk per share is 0 - invalid SL")
        
        if self.config.risk.position_size_method == "fixed":
            position_size = self.config.risk.fixed_position_size / entry_price
        elif self.config.risk.position_size_method == "percent_balance":
            position_value = balance * (self.config.risk.percent_balance_per_trade / 100)
            position_size = position_value / entry_price
        elif self.config.risk.position_size_method == "risk_based":
            position_size = risk_amount / risk_per_share
        elif self.config.risk.position_size_method == "kelly":
            # Simplified Kelly: (win_rate * avg_win - loss_rate * avg_loss) / avg_win
            # For now use risk_based with kelly fraction
            base_size = risk_amount / risk_per_share
            position_size = base_size * self.config.risk.kelly_fraction
        else:
            position_size = risk_amount / risk_per_share
        
        # Check max leverage
        position_value = position_size * entry_price
        max_position_value = balance * self.config.risk.max_leverage
        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            logger.warning(f"Position size capped by max leverage {self.config.risk.max_leverage}x: {position_size:.4f}")
        
        return RiskCheckResult(
            allowed=True,
            reason=f"Position size calculated: {position_size:.4f} @ ${entry_price:.2f} = ${position_value:.2f}, risk ${risk_amount:.2f} ({risk_pct}%)",
            risk_amount=risk_amount,
            position_size=position_size,
            details={
                "entry": entry_price,
                "stop_loss": stop_loss,
                "risk_per_share": risk_per_share,
                "method": self.config.risk.position_size_method,
                "position_value": position_value
            }
        )

    def full_check(self, symbol: str, confidence: float = 100, risk_reward: float = 2.0,
                   entry_price: float = 0, stop_loss: float = 0) -> Dict:
        """Full risk check with extensive controls"""
        checks = [
            ("emergency_stop", self.check_emergency_stop()),
            ("enabled", self.check_enabled()),
            ("trading_hours", self.check_trading_hours()),
            ("daily_loss", self.check_daily_loss()),
            ("max_positions", self.check_max_positions()),
            ("max_drawdown", self.check_max_drawdown()),
            ("consecutive_losses", self.check_consecutive_losses()),
            ("daily_trades", self.check_daily_trades()),
            ("cooldown", self.check_cooldown()),
            ("symbol_allowed", self.check_symbol_allowed(symbol)),
            ("confidence", self.check_signal_confidence(confidence)),
            ("risk_reward", self.check_risk_reward(risk_reward)),
        ]
        
        # Position size check if prices provided
        if entry_price and stop_loss:
            pos_check = self.calculate_position_size(entry_price, stop_loss)
            checks.append(("position_size", pos_check))
        
        all_passed = all(c[1].allowed for c in checks)
        
        return {
            "allowed": all_passed,
            "checks": {name: {"allowed": res.allowed, "reason": res.reason, "risk_amount": res.risk_amount, "position_size": res.position_size, "details": res.details} for name, res in checks},
            "failed": [name for name, res in checks if not res.allowed],
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "extensive": "All risk controls checked - user has full control"
        }

    def record_trade(self, symbol: str, side: str, pnl: float = 0, success: bool = True):
        """Record trade for risk tracking"""
        trade = {
            "symbol": symbol,
            "side": side,
            "pnl": pnl,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.daily_trades.append(trade)
        self.last_trade_time = datetime.utcnow()
        
        if not success or pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Keep only last 100 trades
        if len(self.daily_trades) > 100:
            self.daily_trades = self.daily_trades[-100:]
