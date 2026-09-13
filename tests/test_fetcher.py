import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
from crypto_prediction.data.fetcher import CryptoDataFetcher

def test_fetcher_init():
    f = CryptoDataFetcher(symbol="BTC-USD")
    assert f.symbol == "BTC-USD"

def test_fetch_mock():
    # Create mock dataframe
    df = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [95, 96, 97],
        'Close': [102, 103, 104],
        'Volume': [1000, 1100, 1200]
    }, index=pd.date_range('2023-01-01', periods=3))
    assert len(df) == 3
    assert 'Close' in df.columns

if __name__ == "__main__":
    test_fetcher_init()
    test_fetch_mock()
    print("Fetcher tests passed")
