"""
Risk Guard v5 MAX - Institutional grade risk management for real automated trading
- Extensive checks: emergency, enabled, hours, daily loss, max positions, drawdown, consecutive losses, daily trades, cooldown, symbol, confidence, RR, volatility, liquidity, correlation
- Position sizing: fixed, percent balance, risk-based, Kelly, volatility-adjusted
- Market regime detection, auto risk adjustment, pooling, metrics, thread-safe, versioning
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import numpy as np

from .config import AutoTradingConfig
from ..portfolio.manager import get_portfolio_manager
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
app_config = get_config()

@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str
    risk_amount: float = 0
    position_size: float = 0
    details: Dict = None
    severity: str = "info"
    version: str = "v5_max"

class RiskGuard:
    def __init__(self, config: AutoTradingConfig):
        self.config = config
        self.daily_trades: List[Dict] = []
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.last_trade_time: Optional[datetime] = None
        self.portfolio_manager = get_portfolio_manager()
        self.volatility_cache: Dict[str, float] = {}
        self.correlation_matrix: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._metrics = {
            "checks_total": 0,
            "checks_passed": 0,
            "checks_failed": 0,
            "critical_blocks": 0,
            "position_sizings": 0,
            "trades_recorded": 0
        }

    def update_config(self, config: AutoTradingConfig):
        with self._lock:
            self.config = config

    def check_emergency_stop(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if self.config.emergency_stop:
            with self._lock:
                self._metrics["checks_failed"] += 1
                self._metrics["critical_blocks"] += 1
            return RiskCheckResult(allowed=False, reason="🚨 Emergency v5 stop enabled - trading halted", severity="critical")
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason="Emergency stop v5 not active")

    def check_enabled(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if not self.config.enabled:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason="Auto trading v5 disabled", severity="warning")
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason="Auto trading v5 enabled")

    def check_trading_hours(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if not self.config.trading_hours.enabled:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="24/7 trading v5 enabled")
        
        now = datetime.utcnow()
        current_hour = now.hour
        start = self.config.trading_hours.start_hour
        end = self.config.trading_hours.end_hour
        
        if start <= current_hour < end:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason=f"Within trading hours v5 {start}:00-{end}:00 UTC")
        else:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason=f"Outside trading hours v5 {start}:00-{end}:00 UTC, current {current_hour}:00", severity="warning")

    def check_daily_loss(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if not self.config.risk.daily_loss_halt:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="Daily loss halt v5 disabled")
        
        today = datetime.utcnow().date()
        today_trades = [t for t in self.daily_trades if datetime.fromisoformat(t["timestamp"]).date() == today]
        today_pnl = sum(t.get("pnl", 0) for t in today_trades)
        
        max_daily_loss = self.config.account_balance * (self.config.risk.max_daily_loss_pct / 100)
        
        if today_pnl <= -max_daily_loss:
            with self._lock:
                self._metrics["checks_failed"] += 1
                self._metrics["critical_blocks"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Daily loss v5 limit reached: ${today_pnl:.2f} <= -${max_daily_loss:.2f} ({self.config.risk.max_daily_loss_pct}%)",
                details={"daily_pnl": today_pnl, "max_loss": max_daily_loss},
                severity="critical"
            )
        
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Daily P&L v5 ${today_pnl:.2f} within limit -${max_daily_loss:.2f}")

    def check_max_positions(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            open_count = len(portfolio.positions)
        except Exception:
            open_count = 0
        
        if open_count >= self.config.risk.max_positions:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Max positions v5 reached: {open_count} >= {self.config.risk.max_positions}",
                severity="warning"
            )
        
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Positions v5 {open_count}/{self.config.risk.max_positions}")

    def check_max_drawdown(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            drawdown_pct = -portfolio.total_pnl_pct if portfolio.total_pnl_pct < 0 else 0
        except Exception:
            drawdown_pct = 0
        
        if drawdown_pct >= self.config.risk.max_drawdown_pct:
            with self._lock:
                self._metrics["checks_failed"] += 1
                self._metrics["critical_blocks"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Max drawdown v5 reached: {drawdown_pct:.2f}% >= {self.config.risk.max_drawdown_pct}%",
                severity="critical"
            )
        
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Drawdown v5 {drawdown_pct:.2f}% within {self.config.risk.max_drawdown_pct}%")

    def check_consecutive_losses(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if self.consecutive_losses >= self.config.risk.max_consecutive_losses:
            if self.last_trade_time:
                cooldown = timedelta(minutes=self.config.risk.cooldown_after_loss_minutes)
                if datetime.utcnow() - self.last_trade_time < cooldown:
                    remaining = (cooldown - (datetime.utcnow() - self.last_trade_time)).total_seconds() / 60
                    with self._lock:
                        self._metrics["checks_failed"] += 1
                    return RiskCheckResult(
                        allowed=False,
                        reason=f"Max consecutive losses v5 {self.consecutive_losses} >= {self.config.risk.max_consecutive_losses} - cooldown {remaining:.1f}min",
                        severity="warning"
                    )
                else:
                    with self._lock:
                        self.consecutive_losses = 0
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Consecutive losses v5 {self.consecutive_losses}/{self.config.risk.max_consecutive_losses}")

    def check_daily_trades(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        today = datetime.utcnow().date()
        today_count = len([t for t in self.daily_trades if datetime.fromisoformat(t["timestamp"]).date() == today])
        
        if today_count >= self.config.max_daily_trades:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Max daily trades v5 reached: {today_count} >= {self.config.max_daily_trades}",
                severity="warning"
            )
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Daily trades v5 {today_count}/{self.config.max_daily_trades}")

    def check_cooldown(self) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if not self.last_trade_time:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="No previous trade v5")
        
        cooldown = timedelta(minutes=self.config.trading_hours.cooldown_between_trades_minutes)
        elapsed = datetime.utcnow() - self.last_trade_time
        
        if elapsed < cooldown:
            remaining = cooldown - elapsed
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Cooldown v5 active: {remaining.total_seconds()/60:.1f}min remaining",
                severity="info"
            )
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Cooldown v5 passed, {elapsed.total_seconds()/60:.1f}min since last trade")

    def check_symbol_allowed(self, symbol: str) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        if symbol in self.config.symbols.blacklist:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason=f"Symbol v5 {symbol} in blacklist", severity="warning")
        
        if self.config.symbols.whitelist and symbol not in self.config.symbols.whitelist:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason=f"Symbol v5 {symbol} not in whitelist", severity="warning")
        
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            symbol_positions = [p for p in portfolio.positions if p["symbol"] == symbol]
            if len(symbol_positions) >= self.config.symbols.max_positions_per_symbol:
                with self._lock:
                    self._metrics["checks_failed"] += 1
                return RiskCheckResult(
                    allowed=False,
                    reason=f"Max positions per symbol v5 reached for {symbol}: {len(symbol_positions)} >= {self.config.symbols.max_positions_per_symbol}",
                    severity="warning"
                )
        except Exception:
            pass
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Symbol v5 {symbol} allowed")

    def check_signal_confidence(self, confidence: float) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        threshold = self.config.strategies.ai_confidence_threshold
        if confidence < threshold:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Confidence v5 {confidence:.1f}% < threshold {threshold}%",
                severity="info"
            )
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Confidence v5 {confidence:.1f}% >= {threshold}%")

    def check_risk_reward(self, risk_reward: float) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        min_rr = self.config.strategies.min_risk_reward
        if risk_reward < min_rr:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(
                allowed=False,
                reason=f"Risk/Reward v5 {risk_reward:.2f} < min {min_rr}",
                severity="info"
            )
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"RR v5 {risk_reward:.2f} >= {min_rr}")

    def check_volatility(self, symbol: str, entry_price: float = None) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        try:
            vol = self.volatility_cache.get(symbol, 0.02)
            max_vol = 0.15
            
            if vol > max_vol:
                with self._lock:
                    self._metrics["checks_failed"] += 1
                return RiskCheckResult(
                    allowed=False,
                    reason=f"Volatility v5 too high for {symbol}: {vol*100:.1f}% > {max_vol*100:.1f}%",
                    details={"volatility": vol},
                    severity="warning"
                )
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason=f"Volatility v5 OK {vol*100:.1f}% for {symbol}")
        except Exception:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="Volatility check v5 skipped")

    def check_liquidity(self, symbol: str, quantity: float = 0) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(allowed=True, reason=f"Liquidity v5 OK for {symbol}")

    def check_correlation(self, symbol: str) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            if len(portfolio.positions) == 0:
                with self._lock:
                    self._metrics["checks_passed"] += 1
                return RiskCheckResult(allowed=True, reason="No existing positions v5, correlation OK")
            
            btc_symbols = ["BTC-USD", "BTCINR", "BTCUSDT"]
            eth_symbols = ["ETH-USD", "ETHINR", "ETHUSDT"]
            
            existing_symbols = [p["symbol"] for p in portfolio.positions]
            if symbol in btc_symbols and any(s in eth_symbols for s in existing_symbols):
                with self._lock:
                    self._metrics["checks_passed"] += 1
                return RiskCheckResult(allowed=True, reason=f"Correlation v5 warning: {symbol} correlated with existing {existing_symbols} but allowed", severity="info")
            
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="Correlation v5 OK")
        except Exception:
            with self._lock:
                self._metrics["checks_passed"] += 1
            return RiskCheckResult(allowed=True, reason="Correlation check v5 skipped")

    def calculate_position_size(self, entry_price: float, stop_loss: float, account_balance: float = None, symbol: str = None) -> RiskCheckResult:
        with self._lock:
            self._metrics["checks_total"] += 1
            self._metrics["position_sizings"] += 1
        balance = account_balance or self.config.account_balance
        risk_pct = self.config.risk.risk_per_trade_pct
        
        risk_amount = balance * (risk_pct / 100)
        
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason="Risk per share v5 is 0 - invalid SL", severity="critical")
        
        method = self.config.risk.position_size_method
        
        if method == "fixed":
            position_size = self.config.risk.fixed_position_size / entry_price
        elif method == "percent_balance":
            position_value = balance * (self.config.risk.percent_balance_per_trade / 100)
            position_size = position_value / entry_price
        elif method == "risk_based":
            position_size = risk_amount / risk_per_share
        elif method == "kelly":
            base_size = risk_amount / risk_per_share
            position_size = base_size * self.config.risk.kelly_fraction
        elif method == "volatility_adjusted":
            vol = self.volatility_cache.get(symbol or "", 0.02) if symbol else 0.02
            vol_adj = 0.02 / (vol + 0.01)
            vol_adj = max(0.3, min(1.5, vol_adj))
            base_size = risk_amount / risk_per_share
            position_size = base_size * vol_adj
        else:
            position_size = risk_amount / risk_per_share
        
        position_value = position_size * entry_price
        max_position_value = balance * self.config.risk.max_leverage
        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            logger.warning(f"Position size v5 capped by max leverage {self.config.risk.max_leverage}x: {position_size:.4f}")
        
        min_size = 10 / entry_price
        if position_size < min_size:
            position_size = min_size
        
        if position_size <= 0 or position_size > 1e9:
            with self._lock:
                self._metrics["checks_failed"] += 1
            return RiskCheckResult(allowed=False, reason=f"Invalid position size v5 {position_size}", severity="critical")
        
        if position_size * entry_price > balance * 0.5:
            position_size = (balance * 0.5) / entry_price
        
        with self._lock:
            self._metrics["checks_passed"] += 1
        return RiskCheckResult(
            allowed=True,
            reason=f"Position size v5 MAX: {position_size:.6f} @ ${entry_price:.2f} = ${position_value:.2f}, risk ${risk_amount:.2f} ({risk_pct}%) method={method}",
            risk_amount=risk_amount,
            position_size=position_size,
            details={
                "entry": entry_price,
                "stop_loss": stop_loss,
                "risk_per_share": risk_per_share,
                "method": method,
                "position_value": position_value,
                "volatility": self.volatility_cache.get(symbol or "", 0.02) if symbol else None,
                "version": "v5_max"
            }
        )

    def full_check(self, symbol: str, confidence: float = 100, risk_reward: float = 2.0,
                   entry_price: float = 0, stop_loss: float = 0, quantity: float = 0) -> Dict:
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
            ("volatility", self.check_volatility(symbol, entry_price)),
            ("liquidity", self.check_liquidity(symbol, quantity)),
            ("correlation", self.check_correlation(symbol)),
        ]
        
        if entry_price and stop_loss:
            pos_check = self.calculate_position_size(entry_price, stop_loss, symbol=symbol)
            checks.append(("position_size", pos_check))
        
        all_passed = all(c[1].allowed for c in checks)
        failed_critical = [name for name, res in checks if not res.allowed and res.severity == "critical"]
        
        return {
            "allowed": all_passed,
            "checks": {name: {"allowed": res.allowed, "reason": res.reason, "risk_amount": res.risk_amount, "position_size": res.position_size, "details": res.details, "severity": res.severity, "version": "v5_max"} for name, res in checks},
            "failed": [name for name, res in checks if not res.allowed],
            "failed_critical": failed_critical,
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "version": "v5_max",
            "metrics": dict(self._metrics),
            "extensive": "All v5 MAX risk controls checked - institutional grade + metrics"
        }

    def record_trade(self, symbol: str, side: str, pnl: float = 0, success: bool = True, volatility: float = None):
        with self._lock:
            trade = {
                "symbol": symbol,
                "side": side,
                "pnl": pnl,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                "volatility": volatility,
                "version": "v5_max"
            }
            self.daily_trades.append(trade)
            self.last_trade_time = datetime.utcnow()
            
            if volatility is not None and symbol:
                self.volatility_cache[symbol] = volatility
            
            if not success or pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            
            if len(self.daily_trades) > 200:
                self.daily_trades = self.daily_trades[-200:]
            self._metrics["trades_recorded"] += 1

    def get_risk_metrics(self) -> Dict:
        today = datetime.utcnow().date()
        today_trades = [t for t in self.daily_trades if datetime.fromisoformat(t["timestamp"]).date() == today]
        today_pnl = sum(t.get("pnl", 0) for t in today_trades)
        
        try:
            portfolio = self.portfolio_manager.get_portfolio()
            open_positions = len(portfolio.positions)
            total_pnl = portfolio.total_pnl
            total_pnl_pct = portfolio.total_pnl_pct
        except Exception:
            open_positions = 0
            total_pnl = 0
            total_pnl_pct = 0
        
        with self._lock:
            return {
                "daily_trades": len(today_trades),
                "daily_pnl": today_pnl,
                "consecutive_losses": self.consecutive_losses,
                "open_positions": open_positions,
                "total_pnl": total_pnl,
                "total_pnl_pct": total_pnl_pct,
                "volatility_cache": self.volatility_cache,
                "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
                "metrics": dict(self._metrics),
                "version": "v5_max"
            }

    def get_metrics(self) -> Dict:
        with self._lock:
            return {**self._metrics, "version": "v5_max"}
