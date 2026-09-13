"""
Auto Trading Engine - Executes real trades with extensive user control
Supports paper, semi-auto (approval), full-auto (real) modes
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import threading
import time

from .config import AutoTradingConfig
from .risk_guard import RiskGuard
from ..brokers.manager import get_broker_manager
from ..trading.calls import TradingCallGenerator
from ..portfolio.manager import get_portfolio_manager
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class AutoTradingEngine:
    """
    Extensive auto trading engine for real trades
    - Paper mode: safe simulation with real prices
    - Semi-auto: generates signals, requires user approval
    - Full-auto: executes real trades automatically (with risk guards)
    """

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else config.project_root / "data" / "autotrading_config.json"
        self.trades_path = config.project_root / "data" / "autotrading_trades.json"
        self.config = AutoTradingConfig()
        self.risk_guard = RiskGuard(self.config)
        self.broker_manager = get_broker_manager()
        self.call_generator = TradingCallGenerator()
        self.portfolio_manager = get_portfolio_manager()
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.trades: List[Dict] = []
        self.pending_approvals: List[Dict] = []
        self.load()

    def load(self):
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text())
                self.config = AutoTradingConfig.from_dict(data)
                self.risk_guard.update_config(self.config)
                logger.info(f"Loaded auto trading config: enabled={self.config.enabled} mode={self.config.mode} broker={self.config.execution.broker_id}")
            
            if self.trades_path.exists():
                trades_data = json.loads(self.trades_path.read_text())
                self.trades = trades_data.get("trades", [])
                self.pending_approvals = trades_data.get("pending_approvals", [])
        except Exception as e:
            logger.warning(f"Failed to load auto trading config: {e}")

    def save(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config.updated_at = datetime.utcnow().isoformat()
            self.config_path.write_text(json.dumps(self.config.to_dict(), indent=2))
            
            self.trades_path.write_text(json.dumps({
                "trades": self.trades[-200:],  # Keep last 200
                "pending_approvals": self.pending_approvals,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2))
        except Exception as e:
            logger.error(f"Failed to save auto trading config: {e}")

    def update_config(self, new_config: Dict) -> AutoTradingConfig:
        """Update config with extensive user controls"""
        self.config = AutoTradingConfig.from_dict(new_config)
        self.risk_guard.update_config(self.config)
        self.save()
        logger.info(f"Updated auto trading config: enabled={self.config.enabled} mode={self.config.mode}")
        return self.config

    def get_status(self) -> Dict:
        """Get extensive status"""
        return {
            "enabled": self.config.enabled,
            "mode": self.config.mode,
            "is_running": self.is_running,
            "emergency_stop": self.config.emergency_stop,
            "broker_id": self.config.execution.broker_id,
            "broker_connected": self.broker_manager.get_broker(self.config.execution.broker_id).connected if self.broker_manager.get_broker(self.config.execution.broker_id) else False,
            "account_balance": self.config.account_balance,
            "risk_per_trade": self.config.risk.risk_per_trade_pct,
            "max_positions": self.config.risk.max_positions,
            "open_positions": len(self.portfolio_manager.get_portfolio().positions),
            "total_trades": len(self.trades),
            "pending_approvals": len(self.pending_approvals),
            "daily_trades": len([t for t in self.trades if datetime.fromisoformat(t["timestamp"]).date() == datetime.utcnow().date()]),
            "config": self.config.to_dict(),
            "real_trading": self.config.mode == "full_auto" and self.config.execution.enable_real_trading,
            "paper_mode": self.config.mode == "paper",
            "extensive_controls": "User has full control over risk, strategies, symbols, execution"
        }

    def check_trade_allowed(self, symbol: str, signal: Dict) -> Dict:
        """Check if trade allowed with extensive risk guards"""
        confidence = signal.get("confidence", 0)
        risk_reward_val = signal.get("risk_reward", 2.0)
        # risk_reward can be dict like {"tp1":1.0,"tp2":2.0} - take max or avg
        if isinstance(risk_reward_val, dict):
            # Use tp2 or max value
            risk_reward = risk_reward_val.get("tp2") or risk_reward_val.get("tp1") or max(risk_reward_val.values()) if risk_reward_val else 2.0
        else:
            risk_reward = risk_reward_val
        entry = signal.get("entry_price", 0)
        sl = signal.get("stop_loss", 0)
        
        return self.risk_guard.full_check(
            symbol=symbol,
            confidence=confidence,
            risk_reward=float(risk_reward),
            entry_price=entry,
            stop_loss=sl
        )

    def execute_trade(self, symbol: str, call: Dict = None, manual: bool = False) -> Dict:
        """Execute real trade with extensive controls"""
        try:
            # Get trading call if not provided
            if not call:
                trading_call = self.call_generator.generate_call(
                    symbol=symbol,
                    account_balance=self.config.account_balance
                )
                call = trading_call.to_dict()
            
            # Check if signal is tradable
            signal_type = call.get("signal", "")
            allowed_signals = self.config.strategies.allowed_signals
            if signal_type not in allowed_signals:
                return {
                    "success": False,
                    "reason": f"Signal {signal_type} not in allowed {allowed_signals}",
                    "symbol": symbol,
                    "call": call
                }
            
            # Risk check - handle risk_reward dict
            rr_val = call.get("risk_reward", 2.0)
            if isinstance(rr_val, dict):
                rr_val = rr_val.get("tp2") or rr_val.get("tp1") or (max(rr_val.values()) if rr_val else 2.0)
            risk_check = self.check_trade_allowed(
                symbol=symbol,
                signal={
                    "confidence": call.get("confidence", 0),
                    "risk_reward": float(rr_val),
                    "entry_price": call.get("entry_price", 0),
                    "stop_loss": call.get("stop_loss", 0)
                }
            )
            
            if not risk_check["allowed"] and not manual:
                return {
                    "success": False,
                    "reason": f"Risk check failed: {risk_check['failed']}",
                    "risk_check": risk_check,
                    "symbol": symbol,
                    "call": call
                }
            
            # Calculate position size
            pos_size_check = self.risk_guard.calculate_position_size(
                entry_price=call["entry_price"],
                stop_loss=call["stop_loss"],
                account_balance=self.config.account_balance
            )
            
            if not pos_size_check.allowed:
                return {
                    "success": False,
                    "reason": f"Position size failed: {pos_size_check.reason}",
                    "symbol": symbol
                }
            
            quantity = pos_size_check.position_size
            
            # Determine execution mode
            mode = self.config.mode
            broker_id = self.config.execution.broker_id
            broker = self.broker_manager.get_broker(broker_id)
            
            if not broker:
                return {"success": False, "reason": f"Broker {broker_id} not found"}
            
            # Semi-auto mode: require approval
            if mode == "semi_auto" and not manual:
                approval = {
                    "id": f"approval_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "call": call,
                    "quantity": quantity,
                    "risk_check": risk_check,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "PENDING",
                    "mode": mode
                }
                self.pending_approvals.append(approval)
                self.save()
                logger.info(f"📋 Trade requires approval (semi-auto): {symbol} {call['signal']} {quantity:.4f} @ ${call['entry_price']:.2f}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "approval_id": approval["id"],
                    "reason": "Semi-auto mode - requires user approval",
                    "call": call,
                    "quantity": quantity,
                    "risk_check": risk_check
                }
            
            # Full-auto or paper or manual override
            # Safety: check if real trading enabled
            is_real = mode == "full_auto" and self.config.execution.enable_real_trading and not broker.paper_mode
            
            if is_real:
                logger.warning(f"🚨 REAL AUTO TRADE EXECUTING: {symbol} {call['signal']} {quantity:.4f} @ ${call['entry_price']:.2f} - REAL MONEY")
                if self.config.execution.require_confirmation and not manual:
                    # Extra confirmation for real trades
                    return {
                        "success": False,
                        "requires_confirmation": True,
                        "reason": "Real trading requires explicit confirmation - set require_confirmation=False or use manual=true",
                        "call": call,
                        "is_real": True
                    }
            else:
                logger.info(f"📝 PAPER Auto Trade: {symbol} {call['signal']} {quantity:.4f} @ ${call['entry_price']:.2f} - {mode} mode")
            
            # Place order via broker - always pass entry_price as fallback for paper mode when live price unavailable
            side = "BUY" if "BUY" in call["signal"] else "SELL"
            order_type = self.config.execution.order_type
            
            order = broker.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=call["entry_price"],  # Always pass entry_price as fallback - live price used if available, else this
                stop_price=None,
                stop_loss=call.get("stop_loss"),
                take_profits=call.get("take_profits"),
                leverage=call.get("position", {}).get("leverage", "1x"),
                trailing_pct=self.config.risk.trailing_stop_pct if self.config.risk.use_trailing_stop else None,
                strategy=call.get("strategy", "AI Ensemble")
            )
            
            # Open position in portfolio manager
            try:
                self.portfolio_manager.open_position(
                    symbol=symbol,
                    side="LONG" if side == "BUY" else "SHORT",
                    entry_price=order.filled_price or call["entry_price"],
                    quantity=quantity,
                    stop_loss=call.get("stop_loss"),
                    take_profits=call.get("take_profits"),
                    leverage=order.leverage,
                    risk_amount=pos_size_check.risk_amount
                )
            except Exception as e:
                logger.warning(f"Failed to open portfolio position: {e}")
            
            # Record trade
            trade_record = {
                "id": order.id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": order.filled_price or call["entry_price"],
                "stop_loss": call.get("stop_loss"),
                "take_profits": call.get("take_profits"),
                "signal": call["signal"],
                "confidence": call.get("confidence"),
                "risk_reward": call.get("risk_reward"),
                "order": order.to_dict(),
                "call": call,
                "risk_check": risk_check,
                "mode": mode,
                "real_trading": is_real,
                "broker": broker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "pnl": 0,
                "status": "OPEN"
            }
            
            self.trades.append(trade_record)
            self.risk_guard.record_trade(symbol, side, pnl=0, success=True)
            self.save()
            
            return {
                "success": True,
                "order": order.to_dict(),
                "trade": trade_record,
                "real_trading": is_real,
                "mode": mode,
                "quantity": quantity,
                "message": f"{'REAL' if is_real else 'PAPER'} trade executed: {symbol} {side} {quantity:.4f} @ ${order.filled_price or call['entry_price']:.2f}",
                "warning": "Real trading can lose money - monitor positions" if is_real else "Paper trading - safe simulation"
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "reason": str(e),
                "symbol": symbol,
                "error": traceback.format_exc()
            }

    def approve_trade(self, approval_id: str) -> Dict:
        """Approve pending trade in semi-auto mode"""
        for i, approval in enumerate(self.pending_approvals):
            if approval["id"] == approval_id:
                # Execute with manual override
                result = self.execute_trade(
                    symbol=approval["symbol"],
                    call=approval["call"],
                    manual=True
                )
                # Remove from pending
                self.pending_approvals.pop(i)
                self.save()
                return result
        
        return {"success": False, "reason": f"Approval {approval_id} not found"}

    def reject_trade(self, approval_id: str) -> Dict:
        """Reject pending trade"""
        for i, approval in enumerate(self.pending_approvals):
            if approval["id"] == approval_id:
                self.pending_approvals.pop(i)
                self.save()
                return {"success": True, "message": f"Rejected trade {approval_id}"}
        
        return {"success": False, "reason": f"Approval {approval_id} not found"}

    def start(self) -> bool:
        """Start auto trading loop"""
        if self.is_running:
            return False
        
        if self.config.emergency_stop:
            logger.warning("Cannot start - emergency stop enabled")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.thread.start()
        logger.info(f"🚀 Auto trading started - mode={self.config.mode} broker={self.config.execution.broker_id} enabled={self.config.enabled}")
        return True

    def stop(self) -> bool:
        """Stop auto trading"""
        if not self.is_running:
            return False
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 Auto trading stopped")
        return True

    def _trading_loop(self):
        """Main auto trading loop - checks signals and executes with risk guards"""
        logger.info("Auto trading loop started - extensive controls active")
        
        while self.is_running:
            try:
                if not self.config.enabled or self.config.emergency_stop:
                    time.sleep(60)
                    continue
                
                # Get trading calls for whitelisted symbols
                symbols = self.config.symbols.whitelist
                if not symbols:
                    symbols = config.data.supported_symbols[:4]
                
                # Filter blacklist
                symbols = [s for s in symbols if s not in self.config.symbols.blacklist]
                
                logger.info(f"Auto trading scan - checking {len(symbols)} symbols: {symbols}")
                
                for symbol in symbols:
                    if not self.is_running:
                        break
                    
                    try:
                        # Generate call
                        call = self.call_generator.generate_call(
                            symbol=symbol,
                            account_balance=self.config.account_balance
                        )
                        call_dict = call.to_dict()
                        
                        # Check if signal is strong enough
                        if call_dict["signal"] in ["HOLD", "NEUTRAL"]:
                            continue
                        
                        # Check confidence
                        if call_dict["confidence"] < self.config.strategies.ai_confidence_threshold:
                            logger.info(f"Skipping {symbol}: confidence {call_dict['confidence']:.1f}% < {self.config.strategies.ai_confidence_threshold}%")
                            continue
                        
                        # Execute trade (will go through risk checks and mode handling)
                        result = self.execute_trade(symbol=symbol, call=call_dict, manual=False)
                        
                        if result["success"]:
                            logger.info(f"✅ Auto trade executed: {symbol} {result['message']}")
                        elif result.get("requires_approval"):
                            logger.info(f"📋 Trade pending approval: {symbol}")
                        else:
                            logger.info(f"⏭️ Skipped {symbol}: {result.get('reason')}")
                        
                        # Cooldown between symbols
                        time.sleep(5)
                        
                    except Exception as e:
                        logger.error(f"Auto trading failed for {symbol}: {e}")
                
                # Sleep before next scan - 5 minutes for 1d, 1 min for lower timeframes
                sleep_minutes = 5 if self.config.strategies.primary_timeframe == "1d" else 1
                logger.info(f"Auto trading scan complete - sleeping {sleep_minutes}min")
                for _ in range(sleep_minutes * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Auto trading loop error: {e}")
                time.sleep(60)

# Global instance
_engine = None

def get_autotrading_engine() -> AutoTradingEngine:
    global _engine
    if _engine is None:
        _engine = AutoTradingEngine()
    return _engine
