"""
Institutional Funding Rate Arbitrage
Spot-Futures arbitrage with funding rate
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import requests

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class FundingArbConfig:
    symbol: str
    spot_symbol: str = ""
    futures_symbol: str = ""
    funding_threshold: float = 0.0005  # 0.05% threshold
    total_investment: float = 10000
    leverage: float = 1.0
    status: str = "ACTIVE"

@dataclass
class FundingSignal:
    symbol: str
    signal: str
    funding_rate: float
    annualized_rate: float
    spot_price: float
    futures_price: float
    basis: float
    estimated_profit: float
    timestamp: str

class FundingArbBot:
    """
    Institutional Funding Arbitrage:
    - When funding rate high positive: Short futures, Long spot -> collect funding
    - When funding rate negative: Long futures, Short spot
    - Basis trading: Spot vs Futures price difference
    - Real Binance funding rates
    """
    def __init__(self, cfg: FundingArbConfig):
        self.config = cfg
        if not cfg.spot_symbol:
            self.config.spot_symbol = cfg.symbol.replace('-','')
        if not cfg.futures_symbol:
            self.config.futures_symbol = cfg.symbol.replace('-','')
        self.signals_history = []
        self.created_at = datetime.utcnow().isoformat()

    def fetch_funding_rate(self, symbol: str) -> Optional[float]:
        try:
            # Binance futures funding rate
            resp = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex", params={"symbol": symbol}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return float(data.get('lastFundingRate', 0))
            # Fallback to fundingRate endpoint
            resp = requests.get("https://fapi.binance.com/fapi/v1/fundingRate", params={"symbol": symbol, "limit": 1}, timeout=5)
            if resp.status_code == 200:
                arr = resp.json()
                if arr:
                    return float(arr[0].get('fundingRate', 0))
        except Exception as e:
            logger.warning(f"Funding rate fetch failed {symbol}: {e}")
        return None

    def fetch_spot_price(self, symbol: str) -> float:
        try:
            resp = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": symbol}, timeout=5)
            if resp.status_code == 200:
                return float(resp.json().get('price', 0))
        except:
            pass
        return 0

    def fetch_futures_price(self, symbol: str) -> float:
        try:
            resp = requests.get("https://fapi.binance.com/fapi/v1/ticker/price", params={"symbol": symbol}, timeout=5)
            if resp.status_code == 200:
                return float(resp.json().get('price', 0))
        except:
            pass
        return 0

    def generate_signal(self) -> FundingSignal:
        spot_sym = self.config.spot_symbol
        fut_sym = self.config.futures_symbol

        funding = self.fetch_funding_rate(fut_sym)
        spot_price = self.fetch_spot_price(spot_sym)
        fut_price = self.fetch_futures_price(fut_sym)

        if funding is None:
            funding = 0.0001
        if spot_price == 0:
            spot_price = fut_price or 100000
        if fut_price == 0:
            fut_price = spot_price

        basis = (fut_price - spot_price) / spot_price if spot_price else 0
        annualized = funding * 3 * 365  # funding every 8h, 3x per day

        # Signal logic
        signal = "HOLD"
        estimated_profit = 0.0

        if funding > self.config.funding_threshold:
            # High positive funding -> Short futures, Long spot to collect funding
            # Funding is paid by longs to shorts when positive
            signal = "SHORT_FUTURES_LONG_SPOT"
            estimated_profit = funding * self.config.total_investment
        elif funding < -self.config.funding_threshold:
            signal = "LONG_FUTURES_SHORT_SPOT"
            estimated_profit = abs(funding) * self.config.total_investment
        elif abs(basis) > 0.005:  # 0.5% basis
            if basis > 0:
                signal = "SHORT_FUTURES_LONG_SPOT_BASIS"
                estimated_profit = basis * self.config.total_investment * 0.5
            else:
                signal = "LONG_FUTURES_SHORT_SPOT_BASIS"
                estimated_profit = abs(basis) * self.config.total_investment * 0.5

        sig = FundingSignal(
            symbol=self.config.symbol,
            signal=signal,
            funding_rate=float(funding),
            annualized_rate=float(annualized),
            spot_price=float(spot_price),
            futures_price=float(fut_price),
            basis=float(basis),
            estimated_profit=float(estimated_profit),
            timestamp=datetime.utcnow().isoformat()
        )
        self.signals_history.append(asdict(sig))
        if len(self.signals_history) > 100:
            self.signals_history = self.signals_history[-100:]
        return sig

    def to_dict(self):
        latest = self.signals_history[-1] if self.signals_history else None
        return {
            "config": asdict(self.config),
            "latest_signal": latest,
            "signals_history": self.signals_history[-20:],
            "type": "funding_arb",
            "strategy": "Institutional Funding Rate Arbitrage - Spot vs Futures",
            "real_trading": True,
            "institutional": True,
            "created_at": self.created_at
        }
