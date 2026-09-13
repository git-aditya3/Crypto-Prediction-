"""
Auto Trading Engine - Real trades with CoinDCX INR integration
Fixed: thread safety, validation, price source, daily trades calc, INR handling
"""
from typing import Dict, List, Optional
from datetime import datetime, date
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
        self._save_lock = threading.Lock()
        self.load()

    def load(self):
        try:
            if self.config_path.exists():
                try:
                    raw = self.config_path.read_text()
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        self.config = AutoTradingConfig.from_dict(data)
                        self.risk_guard.update_config(self.config)
                        logger.info(f"Loaded auto trading config: enabled={self.config.enabled} mode={self.config.mode} broker={self.config.execution.broker_id}")
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Invalid autotrading config JSON: {e}, using defaults")
            if self.trades_path.exists():
                try:
                    raw = self.trades_path.read_text()
                    trades_data = json.loads(raw)
                    if isinstance(trades_data, dict):
                        with self._lock:
                            trades_list = trades_data.get("trades", [])
                            pending_list = trades_data.get("pending_approvals", [])
                            if isinstance(trades_list, list):
                                self.trades = trades_list[-500:]
                            if isinstance(pending_list, list):
                                self.pending_approvals = pending_list[:100]
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Invalid trades JSON: {e}")
        except Exception as e:
            logger.warning(f"Failed to load auto trading config: {e}")

    def save(self):
        try:
            with self._save_lock:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config.updated_at = datetime.utcnow().isoformat()
                # Atomic write via tmp
                tmp_path = self.config_path.with_suffix('.tmp')
                tmp_path.write_text(json.dumps(self.config.to_dict(), indent=2))
                tmp_path.replace(self.config_path)

                with self._lock:
                    trades_copy = list(self.trades[-200:])
                    pending_copy = list(self.pending_approvals)

                trades_tmp = self.trades_path.with_suffix('.tmp')
                trades_tmp.write_text(json.dumps({
                    "trades": trades_copy,
                    "pending_approvals": pending_copy,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2))
                trades_tmp.replace(self.trades_path)
        except Exception as e:
            logger.error(f"Failed to save auto trading config: {e}")

    def update_config(self, new_config: Dict) -> AutoTradingConfig:
        try:
            if not isinstance(new_config, dict):
                raise ValueError("Config must be dict")
            self.config = AutoTradingConfig.from_dict(new_config)
            self.risk_guard.update_config(self.config)
            self.save()
            logger.info(f"Updated auto trading config: enabled={self.config.enabled} mode={self.config.mode} broker={self.config.execution.broker_id}")
            return self.config
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            raise

    def get_status(self) -> Dict:
        try:
            broker_id = getattr(self.config.execution, 'broker_id', 'paper') or 'paper'
            broker = self.broker_manager.get_broker(broker_id)
            connected = bool(getattr(broker, 'connected', False)) if broker else False
            paper_mode = bool(getattr(broker, 'paper_mode', True)) if broker else True
        except Exception:
            connected=False
            paper_mode=True
            try:
                broker_id=self.config.execution.broker_id
            except Exception:
                broker_id="paper"

        try:
            portfolio = self.portfolio_manager.get_portfolio()
            positions = getattr(portfolio, 'positions', {})
            open_pos = len(positions) if isinstance(positions, dict) else 0
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

        daily_trades = 0
        try:
            today = date.today()
            # Use UTC date for consistency but also handle local
            today_utc = datetime.utcnow().date()
            for t in trades_copy:
                try:
                    if not isinstance(t, dict):
                        continue
                    ts_str = t.get("timestamp","")
                    if not ts_str or not isinstance(ts_str, str):
                        continue
                    # Handle ISO with Z
                    ts_clean = ts_str.replace("Z","").split(".")[0]
                    try:
                        dt = datetime.fromisoformat(ts_clean)
                    except ValueError:
                        continue
                    # Compare both local and UTC date to be safe
                    if dt.date() == today or dt.date() == today_utc:
                        daily_trades+=1
                except Exception:
                    continue
        except Exception:
            daily_trades=0

        try:
            is_real = broker_id == "coindcx" and connected and not paper_mode and self.config.mode == "full_auto"
        except Exception:
            is_real = False

        return {
            "enabled": bool(getattr(self.config, 'enabled', False)),
            "mode": getattr(self.config, 'mode', 'paper'),
            "is_running": bool(self.is_running),
            "emergency_stop": bool(getattr(self.config, 'emergency_stop', False)),
            "broker_id": broker_id,
            "broker_connected": connected,
            "broker_paper_mode": paper_mode,
            "real_trading": is_real,
            "account_balance": float(getattr(self.config, 'account_balance', 10000) or 10000),
            "risk_per_trade": float(getattr(self.config.risk, 'risk_per_trade_pct', 2.0) or 2.0),
            "max_positions": int(getattr(self.config.risk, 'max_positions', 5) or 5),
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
        """Get live price - CoinDCX primary when broker=coindcx, Binance fallback"""
        if not symbol or not isinstance(symbol, str):
            return None
        symbol = symbol.strip()
        if len(symbol) < 3:
            return None

        try:
            broker_id = (getattr(self.config.execution, 'broker_id', 'paper') or 'paper').lower()
        except Exception:
            broker_id = "paper"

        # Try CoinDCX first if broker is coindcx or symbol is INR
        is_inr_symbol = "INR" in symbol.upper()
        should_try_coindcx = broker_id == "coindcx" or is_inr_symbol

        if should_try_coindcx:
            try:
                from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
                coindcx = CoinDCXRealtimeFetcher(symbol=symbol)
                price = coindcx.get_current_price()
                if price and isinstance(price, (int, float)) and price > 0 and price < 200_000_000:
                    logger.debug(f"CoinDCX price for {symbol}: ₹{price:.2f}")
                    return float(price)
            except Exception as e:
                logger.debug(f"CoinDCX price failed {symbol}: {e}")

            try:
                broker = self.broker_manager.get_broker("coindcx")
                if broker and hasattr(broker, 'get_price'):
                    p = broker.get_price(symbol)
                    if p and isinstance(p, (int, float)) and p > 0 and p < 200_000_000:
                        return float(p)
            except Exception as e:
                logger.debug(f"CoinDCX broker get_price failed {symbol}: {e}")

        # Try Binance fetcher
        try:
            from ..data.realtime import BinanceRealtimeFetcher
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            price = fetcher.get_current_price()
            if price and isinstance(price, (int, float)) and price > 0 and price < 10_000_000:
                # If broker is coindcx and symbol is USD, convert to INR for consistency
                if broker_id == "coindcx" and "USD" in symbol.upper() and "INR" not in symbol.upper():
                    inr_price = float(price) * 83.5
                    if inr_price > 0 and inr_price < 200_000_000:
                        return inr_price
                return float(price)
        except Exception as e:
            logger.debug(f"Binance fetcher price failed {symbol}: {e}")

        # Last resort: price_helper
        try:
            from ..data.price_helper import get_live_price
            p = get_live_price(symbol)
            if p and p > 0:
                return float(p)
        except Exception:
            pass

        return None

    def check_trade_allowed(self, symbol: str, signal: Dict) -> Dict:
        if not isinstance(signal, dict):
            return {"allowed": False, "failed": ["Invalid signal"], "checks": {}}

        confidence = signal.get("confidence", 0)
        try:
            confidence = float(confidence or 0)
        except (ValueError, TypeError):
            confidence = 0.0

        risk_reward_val = signal.get("risk_reward", 2.0)
        if isinstance(risk_reward_val, dict):
            try:
                rr = risk_reward_val.get("tp2") or risk_reward_val.get("tp1")
                if rr is None:
                    vals = [float(v) for v in risk_reward_val.values() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.','',1).isdigit())]
                    rr = max(vals) if vals else 2.0
                risk_reward = float(rr)
            except (ValueError, TypeError):
                risk_reward = 2.0
        else:
            try:
                risk_reward = float(risk_reward_val or 2.0)
            except (ValueError, TypeError):
                risk_reward = 2.0

        entry = signal.get("entry_price", 0)
        sl = signal.get("stop_loss", 0)
        try:
            entry_f = float(entry or 0)
            sl_f = float(sl or 0)
        except (ValueError, TypeError):
            entry_f = 0.0
            sl_f = 0.0

        if entry_f <= 0 or sl_f <= 0:
            try:
                live = self._get_live_price(symbol)
                if live and live > 0:
                    if entry_f <= 0:
                        entry_f = live
                        entry = live
                    if sl_f <= 0:
                        sig = signal.get("signal","").upper()
                        if sig in ["BUY","LONG","STRONG_BUY"]:
                            sl = entry_f * 0.98
                            sl_f = sl
                        else:
                            sl = entry_f * 1.02
                            sl_f = sl
            except Exception:
                pass

        try:
            entry = float(entry or 0)
            sl = float(sl or 0)
            rr = float(risk_reward or 2.0)
        except (ValueError, TypeError):
            entry=0.0
            sl=0.0
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
            if not isinstance(symbol, str) or len(symbol) < 3:
                return {"success": False, "reason": f"Invalid symbol {symbol}"}

            if not call or not isinstance(call, dict):
                try:
                    trading_call = self.call_generator.generate_call(
                        symbol=symbol,
                        account_balance=float(self.config.account_balance or 10000)
                    )
                    call = trading_call.to_dict()
                except Exception as e:
                    return {"success": False, "reason": f"Failed to generate call: {e}", "symbol": symbol}

            if not isinstance(call, dict):
                return {"success": False, "reason": "Invalid call generated", "symbol": symbol}

            signal_type = call.get("signal", "")
            if not isinstance(signal_type, str):
                signal_type = str(signal_type)

            allowed_signals = getattr(self.config.strategies, 'allowed_signals', ["STRONG_BUY","BUY","STRONG_SELL","SELL"])
            if signal_type not in allowed_signals:
                return {
                    "success": False,
                    "reason": f"Signal {signal_type} not in allowed {allowed_signals}",
                    "symbol": symbol,
                    "call": call
                }

            rr_val = call.get("risk_reward", 2.0)
            if isinstance(rr_val, dict):
                try:
                    rr_val = rr_val.get("tp2") or rr_val.get("tp1")
                    if rr_val is None:
                        vals = [float(v) for v in call.get("risk_reward",{}).values() if isinstance(v, (int,float))]
                        rr_val = max(vals) if vals else 2.0
                except (ValueError, TypeError):
                    rr_val = 2.0
            try:
                rr_val = float(rr_val or 2.0)
            except (ValueError, TypeError):
                rr_val = 2.0

            broker_id = getattr(self.config.execution, 'broker_id', 'paper') or 'paper'
            live_price = self._get_live_price(symbol)

            if live_price and live_price > 0:
                try:
                    call_entry_raw = call.get("entry_price",0) or 0
                    try:
                        call_entry = float(call_entry_raw)
                    except (ValueError, TypeError):
                        call_entry = 0.0

                    if call_entry <= 0:
                        call["entry_price"] = live_price
                    else:
                        # Heuristic: if broker coindcx and live is INR (much larger), always use live INR
                        if broker_id == "coindcx":
                            # If live > call_entry*10, likely INR vs USD difference
                            if live_price > call_entry * 10:
                                call["entry_price"] = live_price
                                # Convert SL/TP if they look like USD
                                try:
                                    sl_raw = call.get("stop_loss")
                                    if sl_raw:
                                        sl_f = float(sl_raw)
                                        if sl_f < live_price/10:
                                            call["stop_loss"] = sl_f * 83.5
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
                                        if new_tps:
                                            call["take_profits"] = new_tps
                                except Exception:
                                    pass
                            else:
                                # If close (>5% diff), use live for accuracy
                                if abs(call_entry - live_price) / max(call_entry,1) > 0.05:
                                    call["entry_price"] = live_price
                        else:
                            if abs(call_entry - live_price) / max(call_entry,1) > 0.05:
                                call["entry_price"] = live_price
                except Exception:
                    pass
            else:
                logger.warning(f"No live price for {symbol} - using call entry {call.get('entry_price')}")

            # Validate entry_price and stop_loss before risk check
            try:
                entry_check = float(call.get("entry_price",0) or 0)
                if entry_check <=0 or entry_check > 200_000_000:
                    return {"success": False, "reason": f"Invalid entry price {entry_check}", "symbol": symbol}
            except (ValueError, TypeError):
                return {"success": False, "reason": "Invalid entry price type", "symbol": symbol}

            risk_check = self.check_trade_allowed(
                symbol=symbol,
                signal={
                    "confidence": call.get("confidence", 0),
                    "risk_reward": float(rr_val or 2.0),
                    "entry_price": call.get("entry_price", 0),
                    "stop_loss": call.get("stop_loss", 0)
                }
            )

            if not isinstance(risk_check, dict) or not risk_check.get("allowed", False):
                if not manual:
                    return {
                        "success": False,
                        "reason": f"Risk check failed: {risk_check.get('failed', []) if isinstance(risk_check, dict) else 'unknown'}",
                        "risk_check": risk_check,
                        "symbol": symbol,
                        "call": call
                    }

            pos_size_check = self.risk_guard.calculate_position_size(
                entry_price=float(call["entry_price"]),
                stop_loss=float(call.get("stop_loss",0) or 0),
                account_balance=float(self.config.account_balance or 10000)
            )

            if not pos_size_check or not getattr(pos_size_check, 'allowed', False):
                reason = getattr(pos_size_check, 'reason', 'Position size failed') if pos_size_check else 'Position size failed'
                return {
                    "success": False,
                    "reason": f"Position size failed: {reason}",
                    "symbol": symbol
                }

            quantity = getattr(pos_size_check, 'position_size', 0) or 0
            try:
                quantity = float(quantity)
            except (ValueError, TypeError):
                quantity = 0.0
            if quantity <= 0 or quantity > 1e9:
                return {"success": False, "reason": f"Invalid quantity {quantity}", "symbol": symbol}

            mode = getattr(self.config, 'mode', 'paper')
            broker_id = getattr(self.config.execution, 'broker_id', 'paper') or 'paper'
            broker = self.broker_manager.get_broker(broker_id)

            if not broker:
                return {"success": False, "reason": f"Broker {broker_id} not found", "symbol": symbol}

            if mode == "semi_auto" and not manual:
                approval = {
                    "id": f"approval_{int(time.time())}_{symbol}_{int(time.time()*1000)%1000}",
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
                logger.info(f"📋 Trade requires approval (semi-auto): {symbol} {call.get('signal')} {quantity:.6f} @ {call.get('entry_price')} broker={broker_id}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "approval_id": approval["id"],
                    "reason": "Semi-auto mode - requires user approval",
                    "call": call,
                    "quantity": quantity,
                    "risk_check": risk_check
                }

            is_real = mode == "full_auto" and getattr(self.config.execution, 'enable_real_trading', False) and not getattr(broker, 'paper_mode', True)

            if is_real:
                logger.warning(f"🚨 REAL AUTO TRADE EXECUTING: {symbol} {call.get('signal')} {quantity:.6f} @ {call.get('entry_price')} broker={broker_id} - REAL MONEY")
                if getattr(self.config.execution, 'require_confirmation', False) and not manual:
                    return {
                        "success": False,
                        "requires_confirmation": True,
                        "reason": "Real trading requires explicit confirmation - set require_confirmation=False or use manual=true",
                        "call": call,
                        "is_real": True
                    }
            else:
                logger.info(f"📝 PAPER Auto Trade: {symbol} {call.get('signal')} {quantity:.6f} @ {call.get('entry_price')} - {mode} mode broker={broker_id}")

            side = "BUY" if "BUY" in str(call.get("signal","")).upper() else "SELL"
            order_type = getattr(self.config.execution, 'order_type', 'MARKET') or 'MARKET'

            try:
                order = broker.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=float(call["entry_price"]),
                    stop_price=None,
                    stop_loss=call.get("stop_loss"),
                    take_profits=call.get("take_profits"),
                    leverage=call.get("position", {}).get("leverage", "1x") if isinstance(call.get("position"), dict) else "1x",
                    trailing_pct=float(getattr(self.config.risk, 'trailing_stop_pct', 1.0) or 1.0) if getattr(self.config.risk, 'use_trailing_stop', False) else None,
                    strategy=call.get("strategy", "AI Ensemble") if isinstance(call.get("strategy"), str) else "AI Ensemble"
                )
            except Exception as e:
                logger.error(f"Broker place_order failed {symbol}: {e}")
                return {"success": False, "reason": f"Broker order failed: {e}", "symbol": symbol}

            if not order:
                return {"success": False, "reason": "Broker returned no order", "symbol": symbol}

            try:
                self.portfolio_manager.open_position(
                    symbol=symbol,
                    side="LONG" if side == "BUY" else "SHORT",
                    entry_price=float(getattr(order, 'filled_price', None) or call["entry_price"]),
                    quantity=quantity,
                    stop_loss=call.get("stop_loss"),
                    take_profits=call.get("take_profits"),
                    leverage=getattr(order, 'leverage', '1x'),
                    risk_amount=float(getattr(pos_size_check, 'risk_amount', 0) or 0)
                )
            except Exception as e:
                logger.warning(f"Failed to open portfolio position: {e}")

            try:
                order_dict = order.to_dict() if hasattr(order, 'to_dict') else {"id": getattr(order, 'id', 'unknown')}
            except Exception:
                order_dict = {"id": getattr(order, 'id', 'unknown')}

            trade_record = {
                "id": getattr(order, 'id', f"trade_{int(time.time())}"),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": float(getattr(order, 'filled_price', None) or call.get("entry_price",0) or 0),
                "stop_loss": call.get("stop_loss"),
                "take_profits": call.get("take_profits"),
                "signal": call.get("signal"),
                "confidence": call.get("confidence"),
                "risk_reward": call.get("risk_reward"),
                "order": order_dict,
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
            try:
                self.risk_guard.record_trade(symbol, side, pnl=0, success=True)
            except Exception:
                pass
            self.save()

            return {
                "success": True,
                "order": order_dict,
                "trade": trade_record,
                "real_trading": is_real,
                "mode": mode,
                "quantity": quantity,
                "broker": broker_id,
                "price_source": "CoinDCX INR" if broker_id == "coindcx" else "Binance USD",
                "message": f"{'REAL' if is_real else 'PAPER'} trade executed: {symbol} {side} {quantity:.6f} @ {order_dict.get('filled_price') or call.get('entry_price')} broker={broker_id}",
                "warning": "Real trading can lose money - monitor positions" if is_real else "Paper trading - safe simulation"
            }

        except Exception as e:
            logger.error(f"Trade execution failed for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "reason": str(e)[:500],
                "symbol": symbol,
                "error": traceback.format_exc()[-2000:]
            }

    def approve_trade(self, approval_id: str) -> Dict:
        if not approval_id or not isinstance(approval_id, str):
            return {"success": False, "reason": "Invalid approval_id"}
        approval_copy = None
        with self._lock:
            for i, approval in enumerate(self.pending_approvals):
                try:
                    if isinstance(approval, dict) and approval.get("id") == approval_id:
                        approval_copy = dict(approval)
                        self.pending_approvals.pop(i)
                        break
                except Exception:
                    continue
            else:
                return {"success": False, "reason": f"Approval {approval_id} not found"}
        self.save()
        try:
            result = self.execute_trade(
                symbol=approval_copy.get("symbol",""),
                call=approval_copy.get("call"),
                manual=True
            )
            return result
        except Exception as e:
            return {"success": False, "reason": f"Approve failed: {e}"}

    def reject_trade(self, approval_id: str) -> Dict:
        if not approval_id or not isinstance(approval_id, str):
            return {"success": False, "reason": "Invalid approval_id"}
        with self._lock:
            for i, approval in enumerate(self.pending_approvals):
                try:
                    if isinstance(approval, dict) and approval.get("id") == approval_id:
                        self.pending_approvals.pop(i)
                        self.save()
                        return {"success": True, "message": f"Rejected trade {approval_id}"}
                except Exception:
                    continue
        return {"success": False, "reason": f"Approval {approval_id} not found"}

    def start(self) -> bool:
        if self.is_running:
            return False
        if getattr(self.config, 'emergency_stop', False):
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
                if not getattr(self.config, 'enabled', False) or getattr(self.config, 'emergency_stop', False):
                    time.sleep(60)
                    continue

                symbols = getattr(self.config.symbols, 'whitelist', []) or []
                if not symbols or not isinstance(symbols, list):
                    try:
                        symbols = config.data.supported_symbols[:4]
                    except Exception:
                        symbols = ["BTC-USD","ETH-USD","BNB-USD","SOL-USD"]

                blacklist = getattr(self.config.symbols, 'blacklist', []) or []
                if isinstance(blacklist, list):
                    symbols = [s for s in symbols if s not in blacklist]

                # Validate symbols
                validated=[]
                for s in symbols:
                    if isinstance(s, str) and len(s.strip()) >=3:
                        validated.append(s.strip())
                symbols = validated[:10]
                if not symbols:
                    symbols = ["BTC-USD","ETH-USD"]

                logger.info(f"Auto trading scan - checking {len(symbols)} symbols: {symbols} broker={self.config.execution.broker_id}")

                for symbol in symbols:
                    if not self.is_running:
                        break
                    try:
                        call = self.call_generator.generate_call(
                            symbol=symbol,
                            account_balance=float(self.config.account_balance or 10000)
                        )
                        if not call:
                            continue
                        call_dict = call.to_dict() if hasattr(call, 'to_dict') else {}
                        if not isinstance(call_dict, dict):
                            continue

                        sig = call_dict.get("signal","")
                        if sig in ["HOLD", "NEUTRAL", ""]:
                            continue

                        conf = call_dict.get("confidence",0)
                        try:
                            conf_f = float(conf or 0)
                        except (ValueError, TypeError):
                            conf_f = 0.0

                        threshold = float(getattr(self.config.strategies, 'ai_confidence_threshold', 70) or 70)
                        if conf_f < threshold:
                            logger.info(f"Skipping {symbol}: confidence {conf_f:.1f}% < {threshold}%")
                            continue

                        result = self.execute_trade(symbol=symbol, call=call_dict, manual=False)

                        if result.get("success"):
                            logger.info(f"✅ Auto trade executed: {symbol} {result.get('message','')}")
                        elif result.get("requires_approval"):
                            logger.info(f"📋 Trade pending approval: {symbol}")
                        else:
                            logger.info(f"⏭️ Skipped {symbol}: {result.get('reason','')}")

                        time.sleep(5)

                    except Exception as e:
                        logger.error(f"Auto trading failed for {symbol}: {e}")

                try:
                    primary_tf = getattr(self.config.strategies, 'primary_timeframe', '1d') or '1d'
                except Exception:
                    primary_tf = '1d'
                sleep_minutes = 5 if primary_tf == "1d" else 1
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
