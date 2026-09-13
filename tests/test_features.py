import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from crypto_prediction.features.technical import FeatureEngineer, TechnicalIndicators

def test_indicators():
    series = pd.Series([1,2,3,4,5,6,7,8,9,10]*10)
    sma = TechnicalIndicators.sma(series, 5)
    assert len(sma) == len(series)
    rsi = TechnicalIndicators.rsi(series, 14)
    assert len(rsi) == len(series)

def test_engineer():
    df = pd.DataFrame({
        'Open': np.random.rand(100)*100+100,
        'High': np.random.rand(100)*10+110,
        'Low': np.random.rand(100)*10+90,
        'Close': np.random.rand(100)*100+100,
        'Volume': np.random.rand(100)*10000+1000
    }, index=pd.date_range('2023-01-01', periods=100))
    
    eng = FeatureEngineer()
    feat = eng.engineer(df)
    assert 'RSI' in feat.columns
    assert 'MACD' in feat.columns
    assert 'Target_Close' in feat.columns
    print(f"Engineered {len(feat.columns)} features")

if __name__ == "__main__":
    test_indicators()
    test_engineer()
    print("Feature tests passed")
