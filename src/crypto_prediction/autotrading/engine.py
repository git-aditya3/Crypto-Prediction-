"""
Auto Trading Engine - Real trades with CoinDCX INR integration
Fixed: CoinDCX price source when broker=coindcx, INR handling, validation
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
        self._lock = threading.Lock()
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
                with self._lock:
                    self.trades = trades_data.get("trades", [])
                    self.pending_approvals = trades_data.get("pending_approvals", [])
        except Exception as e:
            logger.warning(f"Failed to load auto trading config: {e}")

    def save(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config.updated_at = datetime.utcnow().isoformat()
            self.config_path.write_text(json.dumps(self.config.to_dict(), indent=2))
            with self._lock:
                trades_copy = list(self.trades[-200:])
                pending_copy = list(self.pending_approvals)
            self.trades_path.write_text(json.dumps({
                "trades": trades_copy,
                "pending_approvals": pending_copy,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2))
        except Exception as e:
            logger.error(f"Failed to save auto trading config: {e}")

    def update_config(self, new_config: Dict) -> AutoTradingConfig:
        self.config = AutoTradingConfig.from_dict(new_config)
        self.risk_guard.update_config(self.config)
        self.save()
        logger.info(f"Updated auto trading config: enabled={self.config.enabled} mode={self.config.mode} broker={self.config.execution.broker_id}")
        return self.config

    def get_status(self) -> Dict:
        try:
            broker_id = self.config.execution.broker_id
            broker = self.broker_manager.get_broker(broker_id)
            connected = broker.connected if broker and hasattr(broker, 'connected') else False
            paper_mode = broker.paper_mode if broker and hasattr(broker, 'paper_mode') else True
        except Exception:
            connected=False
            paper_mode=True
            broker_id=self.config.execution.broker_id

        try:
            open_pos = len(self.portfolio_manager.get_portfolio().positions)
        except Exception:
            open_pos=0

        try:
            with self._lock:
                total_trades = len(self.trades)
                pending = len(self.pending_approvals)
                trades_copy = list(self.trades)
        except Exception:
            total_trades=0
            pending=0
            trades_copy=[]

        try:
            today = datetime.utcnow().date()
            daily_trades = len([t for t in trades_copy if datetime.fromisoformat(t.get("timestamp","")).date() == today])
        except Exception:
            daily_trades=0

        return {
            "enabled": self.config.enabled,
            "mode": self.config.mode,
            "is_running": self.is_running,
            "emergency_stop": self.config.emergency_stop,
            "broker_id": broker_id,
            "broker_connected": connected,
            "broker_paper_mode": paper_mode,
            "real_trading": broker_id == "coindcx" and connected and not paper_mode and self.config.mode == "full_auto",
            "account_balance": self.config.account_balance,
            "risk_per_trade": self.config.risk.risk_per_trade_pct,
            "max_positions": self.config.risk.max_positions,
            "open_positions": open_pos,
            "total_trades": total_trades,
            "pending_approvals": pending,
            "daily_trades": daily_trades,
            "config": self.config.to_dict(),
            "paper_mode": self.config.mode == "paper" or paper_mode,
            "price_source": "CoinDCX INR primary" if broker_id == "coindcx" else "Binance USD with CoinDCX fallback",
            "extensive_controls": "User has full control over risk, strategies, symbols, execution"
        }

    def _get_live_price(self, symbol: str) -> Optional[float]:
        """Get live price - CoinDCX primary when broker=coindcx"""
        try:
            broker_id = self.config.execution.broker_id.lower() if self.config.execution.broker_id else "paper"
        except Exception:
            broker_id = "paper"

        if broker_id == "coindcx":
            try:
                from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
                coindcx = CoinDCXRealtimeFetcher(symbol=symbol)
                price = coindcx.get_current_price()
                if price and price > 0:
                    logger.info(f"CoinDCX price for {symbol}: ₹{price:.2f}")
                    return price
            except Exception as e:
                logger.debug(f"CoinDCX price failed {symbol}: {e}")

            try:
                broker = self.broker_manager.get_broker("coindcx")
                if broker and hasattr(broker, 'get_price'):
                    p = broker.get_price(symbol)
                    if p and p > 0:
                        return p
            except Exception as e:
                logger.debug(f"CoinDCX broker get_price failed {symbol}: {e}")

        try:
            from ..data.realtime import BinanceRealtimeFetcher
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price()
            if price and price > 0:
                if broker_id == "coindcx" and "USD" in symbol.upper() and "INR" not in symbol.upper():
                    # Convert USD to INR for coindcx broker consistency
                    inr_price = price * 83.5
                    return inr_price
                return price
        except Exception as e:
            logger.debug(f"Binance fetcher price failed {symbol}: {e}")

        return None

    def check_trade_allowed(self, symbol: str, signal: Dict) -> Dict:
        confidence = signal.get("confidence", 0)
        risk_reward_val = signal.get("risk_reward", 2.0)
        if isinstance(risk_reward_val, dict):
            risk_reward = risk_reward_val.get("tp2") or risk_reward_val.get("tp1") or (max(risk_reward_val.values()) if risk_reward_val else 2.0)
        else:
            risk_reward = risk_reward_val
        entry = signal.get("entry_price", 0)
        sl = signal.get("stop_loss", 0)

        try:
            entry_f = float(entry or 0)
            sl_f = float(sl or 0)
            if entry_f <= 0 or sl_f <= 0:
                live = self._get_live_price(symbol)
                if live and live > 0:
                    if entry_f <= 0:
                        entry = live
                    # If SL still 0, set 2% below entry for LONG, 2% above for SHORT
                    if sl_f <= 0:
                        if signal.get("signal","").upper() in ["BUY","LONG","STRONG_BUY"]:
                            sl = entry * 0.98
                        else:
                            sl = entry * 1.02
        except (ValueError, TypeError):
            pass

        try:
            entry = float(entry or 0)
            sl = float(sl or 0)
            rr = float(risk_reward or 2.0)
        except (ValueError, TypeError):
            entry=0
            sl=0
            rr=2.0

        return self.risk_guard.full_check(
            symbol=symbol,
            confidence=float(confidence or 0),
            risk_reward=rr,
            entry_price=entry,
            stop_loss=sl
        )

    def execute_trade(self, symbol: str, call: Dict = None, manual: bool = False) -> Dict:
        try:
            if not call:
                trading_call = self.call_generator.generate_call(
                    symbol=symbol,
                    account_balance=self.config.account_balance
                )
                call = trading_call.to_dict()

            signal_type = call.get("signal", "")
            allowed_signals = self.config.strategies.allowed_signals
            if signal_type not in allowed_signals:
                return {
                    "success": False,
                    "reason": f"Signal {signal_type} not in allowed {allowed_signals}",
                    "symbol": symbol,
                    "call": call
                }

            rr_val = call.get("risk_reward", 2.0)
            if isinstance(rr_val, dict):
                rr_val = rr_val.get("tp2") or rr_val.get("tp1") or (max(rr_val.values()) if rr_val else 2.0)

            # Override entry price with live CoinDCX price if broker is coindcx
            broker_id = self.config.execution.broker_id
            live_price = self._get_live_price(symbol)
            if live_price and live_price > 0:
                # If broker is coindcx and call entry is USD but live is INR, keep live INR
                # Otherwise if call entry differs too much (>5%) from live, use live
                try:
                    call_entry = float(call.get("entry_price",0) or 0)
                    if call_entry > 0:
                        # Check if both are same currency magnitude
                        # USD price ~ 50k, INR price ~ 4M for BTC - different magnitude
                        # So if live > call_entry*10, likely INR vs USD
                        if broker_id == "coindcx":
                            # For coindcx, always use INR live price
                            call["entry_price"] = live_price
                            # Also convert SL/TP to INR if they are USD
                            if "USD" in symbol.upper():
                                # Original SL/TP are USD, convert to INR
                                try:
                                    if call.get("stop_loss"):
                                        sl = float(call["stop_loss"])
                                        if sl < live_price/10:  # Likely USD
                                            call["stop_loss"] = sl * 83.5
                                    tps = call.get("take_profits",{})
                                    if isinstance(tps, dict):
                                        new_tps={}
                                        for k,v in tps.items():
                                            try:
                                                tv = float(v)
                                                if tv < live_price/10:
                                                    new_tps[k] = tv * 83.5
                                                else:
                                                    new_tps[k] = tv
                                            except (ValueError, TypeError):
                                                continue
                                        call["take_profits"] = new_tps
                                except Exception:
                                    pass
                        else:
                            # Binance broker - use USD live if close, else keep call
                            if abs(call_entry - live_price) / call_entry > 0.05:
                                call["entry_price"] = live_price
                    else:
                        call["entry_price"] = live_price
                except Exception:
                    pass
            else:
                logger.warning(f"No live price for {symbol} - using call entry {call.get('entry_price')}")

            risk_check = self.check_trade_allowed(
                symbol=symbol,
                signal={
                    "confidence": call.get("confidence", 0),
                    "risk_reward": float(rr_val or 2.0),
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
            if quantity <= 0:
                return {"success": False, "reason": f"Invalid quantity {quantity}", "symbol": symbol}

            mode = self.config.mode
            broker_id = self.config.execution.broker_id
            broker = self.broker_manager.get_broker(broker_id)

            if not broker:
                return {"success": False, "reason": f"Broker {broker_id} not found"}

            if mode == "semi_auto" and not manual:
                approval = {
                    "id": f"approval_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "call": call,
                    "quantity": quantity,
                    "risk_check": risk_check,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "PENDING",
                    "mode": mode,
                    "broker": broker_id,
                    "price_source": "CoinDCX INR" if broker_id == "coindcx" else "Binance USD"
                }
                with self._lock:
                    self.pending_approvals.append(approval)
                self.save()
                logger.info(f"📋 Trade requires approval (semi-auto): {symbol} {call['signal']} {quantity:.4f} @ {call['entry_price']:.2f} broker={broker_id}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "approval_id": approval["id"],
                    "reason": "Semi-auto mode - requires user approval",
                    "call": call,
                    "quantity": quantity,
                    "risk_check": risk_check
                }

            is_real = mode == "full_auto" and self.config.execution.enable_real_trading and not getattr(broker, 'paper_mode', True)

            if is_real:
                logger.warning(f"🚨 REAL AUTO TRADE EXECUTING: {symbol} {call['signal']} {quantity:.4f} @ {call['entry_price']:.2f} broker={broker_id} - REAL MONEY")
                if self.config.execution.require_confirmation and not manual:
                    return {
                        "success": False,
                        "requires_confirmation": True,
                        "reason": "Real trading requires explicit confirmation - set require_confirmation=False or use manual=true",
                        "call": call,
                        "is_real": True
                    }
            else:
                logger.info(f"📝 PAPER Auto Trade: {symbol} {call['signal']} {quantity:.4f} @ {call['entry_price']:.2f} - {mode} mode broker={broker_id}")

            side = "BUY" if "BUY" in call["signal"].upper() else "SELL"
            order_type = self.config.execution.order_type

            # For CoinDCX, quantity is in crypto amount, not INR - ensure valid
            # If symbol is BTC and quantity is tiny (<0.0001) may be rejected - but risk guard should handle
            order = broker.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=call["entry_price"],
                stop_price=None,
                stop_loss=call.get("stop_loss"),
                take_profits=call.get("take_profits"),
                leverage=call.get("position", {}).get("leverage", "1x"),
                trailing_pct=self.config.risk.trailing_stop_pct if self.config.risk.use_trailing_stop else None,
                strategy=call.get("strategy", "AI Ensemble")
            )

            try:
                self.portfolio_manager.open_position(
                    symbol=symbol,
                    side="LONG" if side == "BUY" else "SHORT",
                    entry_price=order.filled_price or call["entry_price"],
                    quantity=quantity,
                    stop_loss=call.get("stop_loss"),
                    take_profits=call.get("take_profits"),
                    leverage=getattr(order, 'leverage', '1x'),
                    risk_amount=pos_size_check.risk_amount
                )
            except Exception as e:
                logger.warning(f"Failed to open portfolio position: {e}")

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
                "price_source": "CoinDCX INR" if broker_id == "coindcx" else "Binance USD",
                "live_price_used": live_price,
                "timestamp": datetime.utcnow().isoformat(),
                "pnl": 0,
                "status": "OPEN"
            }

            with self._lock:
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
                "broker": broker_id,
                "price_source": "CoinDCX INR" if broker_id == "coindcx" else "Binance USD",
                "message": f"{'REAL' if is_real else 'PAPER'} trade executed: {symbol} {side} {quantity:.4f} @ {order.filled_price or call['entry_price']:.2f} broker={broker_id}",
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
        with self._lock:
            for i, approval in enumerate(self.pending_approvals):
                if approval["id"] == approval_id:
                    # Copy and remove
                    approval_copy = dict(approval)
                    self.pending_approvals.pop(i)
                    break
            else:
                return {"success": False, "reason": f"Approval {approval_id} not found"}
        self.save()
        result = self.execute_trade(
            symbol=approval_copy["symbol"],
            call=approval_copy["call"],
            manual=True
        )
        return result

    def reject_trade(self, approval_id: str) -> Dict:
        with self._lock:
            for i, approval in enumerate(self.pending_approvals):
                if approval["id"] == approval_id:
                    self.pending_approvals.pop(i)
                    self.save()
                    return {"success": True, "message": f"Rejected trade {approval_id}"}
        return {"success": False, "reason": f"Approval {approval_id} not found"}

    def start(self) -> bool:
        if self.is_running:
            return False
        if self.config.emergency_stop:
            logger.warning("Cannot start - emergency stop enabled")
            return False
        self.is_running = True
        self.thread = threading.Thread(target=self._trading_loop, daemon=True, name="AutoTradingLoop")
        self.thread.start()
        logger.info(f"🚀 Auto trading started - mode={self.config.mode} broker={self.config.execution.broker_id} enabled={self.config.enabled}")
        return True

    def stop(self) -> bool:
        if not self.is_running:
            return False
        self.is_running = False
        if self.thread:
            try:
                self.thread.join(timeout=5)
            except Exception:
                pass
        logger.info("🛑 Auto trading stopped")
        return True

    def _trading_loop(self):
        logger.info("Auto trading loop started - CoinDCX INR integration active")
        while self.is_running:
            try:
                if not self.config.enabled or self.config.emergency_stop:
                    time.sleep(60)
                    continue

                symbols = self.config.symbols.whitelist
                if not symbols:
                    symbols = config.data.supported_symbols[:4]

                symbols = [s for s in symbols if s not in self.config.symbols.blacklist]

                logger.info(f"Auto trading scan - checking {len(symbols)} symbols: {symbols} broker={self.config.execution.broker_id} price_source={'CoinDCX INR' if self.config.execution.broker_id=='coindcx' else 'Binance'}")

                for symbol in symbols:
                    if not self.is_running:
                        break
                    try:
                        call = self.call_generator.generate_call(
                            symbol=symbol,
                            account_balance=self.config.account_balance
                        )
                        call_dict = call.to_dict()

                        if call_dict["signal"] in ["HOLD", "NEUTRAL"]:
                            continue

                        if call_dict["confidence"] < self.config.strategies.ai_confidence_threshold:
                            logger.info(f"Skipping {symbol}: confidence {call_dict['confidence']:.1f}% < {self.config.strategies.ai_confidence_threshold}%")
                            continue

                        result = self.execute_trade(symbol=symbol, call=call_dict, manual=False)

                        if result["success"]:
                            logger.info(f"✅ Auto trade executed: {symbol} {result['message']}")
                        elif result.get("requires_approval"):
                            logger.info(f"📋 Trade pending approval: {symbol}")
                        else:
                            logger.info(f"⏭️ Skipped {symbol}: {result.get('reason')}")

                        time.sleep(5)

                    except Exception as e:
                        logger.error(f"Auto trading failed for {symbol}: {e}")

                sleep_minutes = 5 if self.config.strategies.primary_timeframe == "1d" else 1
                logger.info(f"Auto trading scan complete - sleeping {sleep_minutes}min")
                for _ in range(sleep_minutes * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Auto trading loop error: {e}")
                time.sleep(60)

_engine = None
_lock = threading.Lock()

def get_autotrading_engine() -> AutoTradingEngine:
    global _engine
    with _lock:
        if _engine is None:
            _engine = AutoTradingEngine()
    return _engine
