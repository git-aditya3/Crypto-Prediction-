"""
Auto Trading Config - Extensive user controls for real automated trading
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class RiskConfig:
    """Extensive risk controls"""
    risk_per_trade_pct: float = 2.0  # % of account per trade
    max_daily_loss_pct: float = 6.0  # Max 6% per day (3 trades)
    max_positions: int = 5  # Max concurrent positions
    max_drawdown_pct: float = 10.0  # Max portfolio drawdown
    max_leverage: int = 5  # Max leverage
    position_size_method: str = "risk_based"  # fixed, risk_based, kelly, percent_balance
    fixed_position_size: float = 100  # For fixed method
    percent_balance_per_trade: float = 10.0  # % of balance per trade
    use_kelly: bool = False
    kelly_fraction: float = 0.5  # Half Kelly for safety
    stop_loss_atr_multiplier: float = 1.5
    take_profit_rr: float = 2.0  # Risk/reward ratio
    use_trailing_stop: bool = False
    trailing_stop_pct: float = 1.0
    move_sl_to_breakeven_at_tp1: bool = True
    daily_loss_halt: bool = True  # Halt trading if daily loss exceeded
    max_consecutive_losses: int = 3
    cooldown_after_loss_minutes: int = 60

@dataclass
class StrategyConfig:
    """Strategy controls"""
    use_ai_ensemble: bool = True
    use_dca_bot: bool = False
    use_grid_bot: bool = False
    use_breakout: bool = True
    use_rsi_signals: bool = True
    use_volume_spikes: bool = True
    ai_confidence_threshold: float = 70.0  # Min confidence % to trade
    min_risk_reward: float = 1.5  # Min RR ratio
    allowed_signals: List[str] = field(default_factory=lambda: ["STRONG_BUY", "BUY", "STRONG_SELL", "SELL"])
    timeframes: List[str] = field(default_factory=lambda: ["1d", "4h", "1h"])
    primary_timeframe: str = "1d"

@dataclass
class SymbolConfig:
    """Symbol controls"""
    whitelist: List[str] = field(default_factory=lambda: ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD"])
    blacklist: List[str] = field(default_factory=list)
    max_positions_per_symbol: int = 1
    symbol_risk_override: Dict[str, float] = field(default_factory=dict)  # Custom risk per symbol

@dataclass
class ExecutionConfig:
    """Execution controls"""
    mode: str = "paper"  # paper, semi_auto (requires approval), full_auto (real)
    order_type: str = "MARKET"  # MARKET, LIMIT
    limit_offset_pct: float = 0.1  # % offset for limit orders
    slippage_tolerance_pct: float = 0.5
    use_oco: bool = True  # One-Cancels-Other for SL/TP
    auto_sl_tp: bool = True
    multiple_tp: bool = True
    tp1_pct: float = 50.0  # % to close at TP1
    tp2_pct: float = 30.0
    tp3_pct: float = 20.0
    broker_id: str = "paper"  # Which broker to use
    testnet: bool = True  # Use testnet for real brokers
    enable_real_trading: bool = False  # Explicit flag for real trading
    require_confirmation: bool = True  # Require user confirmation for real trades

@dataclass
class TradingHoursConfig:
    """Trading hours and cooldowns"""
    enabled: bool = False  # If false, trade 24/7
    start_hour: int = 9
    end_hour: int = 17
    timezone: str = "UTC"
    cooldown_between_trades_minutes: int = 15
    avoid_high_volatility: bool = False
    max_volatility_pct: float = 10.0

@dataclass
class AutoTradingConfig:
    """Master config with extensive user controls"""
    enabled: bool = False
    mode: str = "paper"  # paper, semi_auto, full_auto
    account_balance: float = 10000
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategies: StrategyConfig = field(default_factory=StrategyConfig)
    symbols: SymbolConfig = field(default_factory=SymbolConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    trading_hours: TradingHoursConfig = field(default_factory=TradingHoursConfig)
    emergency_stop: bool = False
    max_daily_trades: int = 10
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "account_balance": self.account_balance,
            "risk": asdict(self.risk),
            "strategies": asdict(self.strategies),
            "symbols": asdict(self.symbols),
            "execution": asdict(self.execution),
            "trading_hours": asdict(self.trading_hours),
            "emergency_stop": self.emergency_stop,
            "max_daily_trades": self.max_daily_trades,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "real_trading_warning": "Real trading can lose money - use risk management, start with paper",
            "extensive_controls": "All parameters user controllable - risk, strategies, symbols, execution, hours"
        }

    @classmethod
    def from_dict(cls, data: Dict):
        risk = RiskConfig(**data.get("risk", {}))
        strategies = StrategyConfig(**data.get("strategies", {}))
        symbols = SymbolConfig(**data.get("symbols", {}))
        execution = ExecutionConfig(**data.get("execution", {}))
        trading_hours = TradingHoursConfig(**data.get("trading_hours", {}))
        
        return cls(
            enabled=data.get("enabled", False),
            mode=data.get("mode", "paper"),
            account_balance=data.get("account_balance", 10000),
            risk=risk,
            strategies=strategies,
            symbols=symbols,
            execution=execution,
            trading_hours=trading_hours,
            emergency_stop=data.get("emergency_stop", False),
            max_daily_trades=data.get("max_daily_trades", 10),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            updated_at=datetime.utcnow().isoformat()
        )
