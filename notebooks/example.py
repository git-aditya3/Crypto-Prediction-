"""
Example usage of Crypto Prediction core - can be run as notebook or script
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.data.dataset import CryptoDataset
from crypto_prediction.training.trainer import Trainer
from crypto_prediction.prediction.predictor import CryptoPredictor

# 1. Quick dataset pipeline with synthetic fallback
print("=== Example 1: Dataset Pipeline ===")
try:
    dataset = CryptoDataset(symbol="BTC-USD")
    # This will try yfinance, fallback to cache/coingecko
    data_dict = dataset.get_full_pipeline(period="1y", interval="1d")
    print(f"Data ready: X_train {data_dict['X_train'].shape}, X_train_seq {data_dict['X_train_seq'].shape}")
except Exception as e:
    print(f"Live fetch failed (no internet?), using synthetic demo: {e}")
    import pandas as pd, numpy as np
    from crypto_prediction.features.technical import FeatureEngineer
    from crypto_prediction.data.preprocessor import DataPreprocessor
    
    np.random.seed(42)
    dates = pd.date_range('2022-01-01', periods=500)
    df = pd.DataFrame({
        'Open': np.cumsum(np.random.randn(500))*20+30000,
        'High': np.cumsum(np.random.randn(500))*20+30500,
        'Low': np.cumsum(np.random.randn(500))*20+29500,
        'Close': np.cumsum(np.random.randn(500))*20+30000,
        'Volume': np.random.rand(500)*1e6+1e5
    }, index=dates)
    df['High'] = df[['Open','Close']].max(axis=1)+np.random.rand(500)*200
    df['Low'] = df[['Open','Close']].min(axis=1)-np.random.rand(500)*200
    
    eng = FeatureEngineer()
    feat = eng.engineer(df)
    prep = DataPreprocessor()
    cleaned = prep.prepare_features(feat, feature_cols=eng.get_feature_columns(feat))
    train, val, test = prep.split(cleaned)
    scaled = prep.fit_transform(train, val, test)
    seq_len = 60
    Xtr_seq, ytr_seq = prep.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
    print(f"Synthetic: X_train {scaled['X_train'].shape}, seq {Xtr_seq.shape}")

# 2. Training example (commented for quick run)
# trainer = Trainer(symbol="BTC-USD")
# results = trainer.train_all(period="1y")
# print(results)

# 3. Prediction example (requires trained models)
print("\n=== Example 2: Prediction (requires trained models) ===")
try:
    predictor = CryptoPredictor(symbol="BTC-USD")
    forecast = predictor.forecast(steps=7, period="1y")
    print(f"Forecast keys: {forecast.keys()}")
    print(f"Current: {forecast.get('current_price')}")
    if 'ensemble' in forecast:
        print(f"7-day ensemble: {forecast['ensemble']}")
    signal = predictor.get_trading_signal(forecast)
    print(f"Signal: {signal}")
except Exception as e:
    print(f"Prediction failed (models not trained): {e}")
    print("Run: python scripts/train.py --symbol BTC-USD --period 1y")

print("\nExample complete!")
