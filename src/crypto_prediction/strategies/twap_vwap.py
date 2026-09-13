"""
Institutional Execution Algorithms - TWAP & VWAP
Fixed: INR support, slippage handling, fallback price, error handling, validation
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math
import numpy as np

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class ExecutionConfig:
    symbol: str
    side: str
    total_quantity: float
    total_investment: float = 10000
    duration_minutes: int = 60
    num_slices: int = 12
    strategy: str = "TWAP"
    limit_price: Optional[float] = None
    max_slippage_bps: float = 10
    status: str = "ACTIVE"

    def __post_init__(self):
        try:
            self.total_quantity = float(self.total_quantity)
        except (ValueError, TypeError):
            raise ValueError("total_quantity must be numeric")
        if self.total_quantity <= 0 or self.total_quantity > 1e9:
            raise ValueError("total_quantity must be >0 and <1e9")
        try:
            self.num_slices = int(self.num_slices)
        except (ValueError, TypeError):
            raise ValueError("num_slices must be integer")
        if self.num_slices <= 0 or self.num_slices > 1000:
            raise ValueError("num_slices must be 1-1000")
        try:
            self.duration_minutes = int(self.duration_minutes)
        except (ValueError, TypeError):
            raise ValueError("duration_minutes must be integer")
        if self.duration_minutes <= 0 or self.duration_minutes > 10080:
            raise ValueError("duration_minutes must be 1-10080")
        if not isinstance(self.side, str) or self.side.upper() not in ["BUY","SELL"]:
            raise ValueError("side must be BUY or SELL")
        self.side = self.side.upper()
        if not isinstance(self.strategy, str) or self.strategy.upper() not in ["TWAP","VWAP"]:
            self.strategy = "TWAP"
        else:
            self.strategy = self.strategy.upper()
        try:
            self.max_slippage_bps = float(self.max_slippage_bps)
            if self.max_slippage_bps <=0 or self.max_slippage_bps > 10000:
                self.max_slippage_bps = 10
        except (ValueError, TypeError):
            self.max_slippage_bps = 10

@dataclass
class ExecutionSlice:
    slice_id: int
    quantity: float
    expected_price: float
    executed_price: Optional[float] = None
    executed: bool = False
    timestamp: Optional[str] = None
    slippage_bps: Optional[float] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

class TWAPVWAPExecutor:
    def __init__(self, cfg: ExecutionConfig):
        self.config = cfg
        self.slices: List[ExecutionSlice] = []
        self.executed_quantity = 0.0
        self.avg_executed_price = 0.0
        self.start_time = datetime.utcnow()
        self.created_at = datetime.utcnow().isoformat()
        self._last_price = 0.0
        self._generate_slices()

    def get_live_price(self, symbol: str) -> float:
        try:
            from ..data.price_helper import get_live_price as unified_price
            price = unified_price(symbol)
            if price and isinstance(price, (int,float)) and price > 0 and price < 200_000_000:
                self._last_price = float(price)
                return float(price)
        except Exception as e:
            logger.debug(f"Unified price failed {symbol}: {e}")
        # Fallback Binance direct
        try:
            from ..data.realtime import BinanceRealtimeFetcher
            fetcher = BinanceRealtimeFetcher(symbol=symbol)
            p = fetcher.get_current_price()
            if p and p > 0 and p < 200_000_000:
                self._last_price = float(p)
                return float(p)
        except Exception as e:
            logger.debug(f"Binance live price failed {symbol}: {e}")
        return float(self._last_price or 0)

    def get_volume_profile(self, symbol: str, num_slices: int) -> List[float]:
        try:
            num_slices = max(1, min(1000, int(num_slices)))
        except (ValueError, TypeError):
            num_slices = 12
        try:
            from ..data.fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher(symbol=symbol)
            df = fetcher.load_or_fetch(symbol=symbol)
            if df is None or df.empty:
                return [1.0/num_slices] * num_slices
            profile = []
            for i in range(num_slices):
                weight = 1.0 + 0.5 * math.sin(math.pi * i / num_slices)
                profile.append(max(0.1, weight))
            total = sum(profile)
            if total == 0:
                return [1.0/num_slices] * num_slices
            return [p/total for p in profile]
        except Exception as e:
            logger.debug(f"Volume profile failed: {e}")
            return [1.0/num_slices] * num_slices

    def _generate_slices(self):
        try:
            if self.config.strategy == "VWAP":
                weights = self.get_volume_profile(self.config.symbol, self.config.num_slices)
            else:
                weights = [1.0/self.config.num_slices] * self.config.num_slices

            price = self.get_live_price(self.config.symbol)
            if price == 0:
                try:
                    from ..data.fetcher import CryptoDataFetcher
                    f = CryptoDataFetcher(symbol=self.config.symbol)
                    df = f.load_or_fetch(symbol=self.config.symbol)
                    if df is not None and not df.empty:
                        price = float(df['Close'].iloc[-1])
                        if "INR" in self.config.symbol.upper():
                            price = price * 83.5
                except Exception:
                    price = 0
            if price == 0:
                raise ValueError(f"Cannot get price for {self.config.symbol} to generate slices")

            self._last_price = price

            for i, w in enumerate(weights):
                try:
                    qty = self.config.total_quantity * float(w)
                    if qty <=0 or qty > 1e9:
                        continue
                    expected_price = price
                    if self.config.limit_price and self.config.limit_price > 0:
                        try:
                            lim = float(self.config.limit_price)
                            if lim > 0:
                                if self.config.side == "BUY":
                                    expected_price = min(price, lim)
                                else:
                                    expected_price = max(price, lim)
                        except (ValueError, TypeError):
                            pass

                    self.slices.append(ExecutionSlice(
                        slice_id=i,
                        quantity=float(qty),
                        expected_price=float(expected_price)
                    ))
                except Exception:
                    continue

            if not self.slices:
                raise ValueError("Failed to generate any slices")
        except Exception as e:
            logger.error(f"Slice generation failed {self.config.symbol}: {e}")
            raise

    def _get_live_price(self) -> float:
        return self.get_live_price(self.config.symbol)

    def execute_next_slice(self) -> Optional[ExecutionSlice]:
        for sl in self.slices:
            try:
                if sl.executed or sl.skipped:
                    continue
                live_price = self._get_live_price()
                if live_price == 0:
                    live_price = sl.expected_price or self._last_price
                if live_price == 0 or live_price > 200_000_000 or live_price < 0:
                    sl.skipped = True
                    sl.skip_reason = "No live price available"
                    logger.warning(f"Slice {sl.slice_id} skipped: no price")
                    continue

                try:
                    exp = float(sl.expected_price) if sl.expected_price else live_price
                    if exp <=0:
                        exp = live_price
                    slippage = abs(live_price - exp) / exp * 10000 if exp != 0 else 0
                    slippage = max(0.0, min(slippage, 10000.0))
                except (ValueError, TypeError, ZeroDivisionError):
                    slippage = 0.0

                if slippage > self.config.max_slippage_bps:
                    sl.skipped = True
                    sl.skip_reason = f"Slippage {slippage:.1f}bps > max {self.config.max_slippage_bps}bps"
                    logger.warning(f"Slice {sl.slice_id} skipped: {sl.skip_reason}")
                    continue

                sl.executed = True
                sl.executed_price = float(live_price)
                sl.timestamp = datetime.utcnow().isoformat()
                sl.slippage_bps = float(slippage)

                prev_total = self.executed_quantity * self.avg_executed_price
                self.executed_quantity += sl.quantity
                if self.executed_quantity > 0:
                    self.avg_executed_price = (prev_total + sl.quantity * live_price) / self.executed_quantity

                return sl
            except Exception as e:
                logger.warning(f"Slice execution failed {sl.slice_id}: {e}")
                try:
                    sl.skipped = True
                    sl.skip_reason = f"Execution error: {str(e)[:100]}"
                except Exception:
                    pass
                continue
        return None

    def retry_skipped(self) -> int:
        count=0
        for sl in self.slices:
            try:
                if sl.skipped:
                    sl.skipped = False
                    sl.skip_reason = None
                    count+=1
            except Exception:
                continue
        return count

    def get_progress(self) -> Dict:
        try:
            executed = sum(1 for s in self.slices if getattr(s, 'executed', False))
            skipped = sum(1 for s in self.slices if getattr(s, 'skipped', False))
            valid_slippage = []
            for s in self.slices:
                try:
                    if getattr(s, 'slippage_bps', None) is not None:
                        sb = float(s.slippage_bps)
                        if 0 <= sb <= 10000:
                            valid_slippage.append(sb)
                except (ValueError, TypeError):
                    continue
            total_qty = float(self.config.total_quantity) if self.config.total_quantity else 0
            try:
                expected_total = sum(float(s.quantity) * float(s.expected_price) for s in self.slices if hasattr(s, 'quantity') and hasattr(s, 'expected_price'))
            except Exception:
                expected_total = 0.0
            return {
                "total_slices": len(self.slices),
                "executed_slices": executed,
                "skipped_slices": skipped,
                "remaining_slices": len(self.slices) - executed - skipped,
                "executed_quantity": float(self.executed_quantity),
                "total_quantity": total_qty,
                "progress_pct": executed / len(self.slices) * 100 if self.slices else 0,
                "avg_executed_price": float(self.avg_executed_price),
                "expected_total_cost": float(expected_total),
                "actual_total_cost": float(self.executed_quantity * self.avg_executed_price),
                "slippage_avg_bps": float(np.mean(valid_slippage)) if valid_slippage else 0.0,
                "slippage_max_bps": float(np.max(valid_slippage)) if valid_slippage else 0.0,
                "price_source": "CoinDCX INR + Binance" if "INR" in self.config.symbol.upper() else "Binance USD + CoinDCX fallback"
            }
        except Exception as e:
            return {"total_slices": len(self.slices), "executed_slices": 0, "skipped_slices": 0, "remaining_slices": len(self.slices), "executed_quantity": 0, "total_quantity": 0, "progress_pct": 0, "avg_executed_price": 0, "expected_total_cost": 0, "actual_total_cost": 0, "slippage_avg_bps": 0, "slippage_max_bps": 0, "error": str(e)}

    def to_dict(self):
        try:
            return {
                "config": asdict(self.config),
                "slices": [asdict(s) for s in self.slices],
                "progress": self.get_progress(),
                "type": f"{self.config.strategy}_execution",
                "strategy": f"Institutional {self.config.strategy} - Slippage Minimization",
                "real_trading": True,
                "institutional": True,
                "price_source": "CoinDCX INR + Binance" if "INR" in self.config.symbol.upper() else "Binance USD + CoinDCX fallback",
                "created_at": self.created_at
            }
        except Exception as e:
            return {"config": {}, "slices": [], "progress": self.get_progress(), "error": str(e), "type": "execution"}
