import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd, numpy as np
from crypto_prediction.backtesting.engine import BacktestEngine
from crypto_prediction.backtesting.strategies import MovingAverageStrategy, RSIStrategy

def test_backtest():
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=200)
    df = pd.DataFrame({
        'Open': np.cumsum(np.random.randn(200))*10+100,
        'High': np.cumsum(np.random.randn(200))*10+105,
        'Low': np.cumsum(np.random.randn(200))*10+95,
        'Close': np.cumsum(np.random.randn(200))*10+100,
        'Volume': np.random.rand(200)*10000
    }, index=dates)
    df['High'] = df[['Open','Close']].max(axis=1)+5
    df['Low'] = df[['Open','Close']].min(axis=1)-5

    from crypto_prediction.features.technical import FeatureEngineer
    eng = FeatureEngineer()
    df = eng.engineer(df)

    engine = BacktestEngine(initial_capital=10000)
    strat = MovingAverageStrategy(20,50)
    result = engine.run(df, strat)
    print(f"Backtest metrics: {result.metrics}")
    assert 'total_return_pct' in result.metrics
    print("Backtest test passed")

if __name__ == "__main__":
    test_backtest()
