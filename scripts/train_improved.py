"""
Train improved models v3 with full data and save
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.features.technical import FeatureEngineer
from crypto_prediction.data.preprocessor import DataPreprocessor
from crypto_prediction.models.lstm_model import LSTMModel
from crypto_prediction.models.transformer_model import TransformerModel
from crypto_prediction.models.xgboost_model import XGBoostModel
from crypto_prediction.models.arima_model import ARIMAModel
from crypto_prediction.models.ensemble import EnsembleModel
from crypto_prediction.evaluation.metrics import compute_regression_metrics
from crypto_prediction.config import get_config

config = get_config()

def train_symbol(symbol="BTC-USD", epochs=50):
    print(f"\n{'='*80}")
    print(f"Training Improved Models v3 for {symbol} - Epochs {epochs}")
    print(f"{'='*80}")
    
    fetcher = CryptoDataFetcher(symbol=symbol)
    df = fetcher.load_or_fetch(symbol=symbol)
    print(f"Data: {len(df)} rows")
    
    engineer = FeatureEngineer()
    engineered = engineer.engineer(df)
    print(f"Engineered: {engineered.shape}")
    
    preprocessor = DataPreprocessor(scaler_type="robust")
    feature_cols = engineer.get_feature_columns(engineered)
    cleaned = preprocessor.prepare_features(engineered, feature_cols=feature_cols)
    
    # Time series split
    n = len(cleaned)
    n_test = int(n * 0.15)
    n_val = int(n * 0.15)
    n_train = n - n_test - n_val
    
    train_df = cleaned.iloc[:n_train]
    val_df = cleaned.iloc[n_train:n_train+n_val]
    test_df = cleaned.iloc[n_train+n_val:]
    
    scaled = preprocessor.fit_transform(train_df, val_df, test_df)
    
    # Sequences
    seq_len = config.data.sequence_length
    X_train_seq, y_train_seq = preprocessor.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
    X_val_seq, y_val_seq = preprocessor.create_sequences(scaled['X_val'], scaled['y_val'], seq_len)
    X_test_seq, y_test_seq = preprocessor.create_sequences(scaled['X_test'], scaled['y_test'], seq_len)
    
    scaled['X_train_seq'] = X_train_seq
    scaled['y_train_seq'] = y_train_seq
    scaled['X_val_seq'] = X_val_seq
    scaled['y_val_seq'] = y_val_seq
    scaled['X_test_seq'] = X_test_seq
    scaled['y_test_seq'] = y_test_seq
    
    print(f"Train_seq: {X_train_seq.shape} Val_seq: {X_val_seq.shape} Test_seq: {X_test_seq.shape}")
    
    results = {}
    
    # LSTM
    print(f"\n--- LSTM v3 ---")
    try:
        model = LSTMModel(input_size=X_train_seq.shape[2], hidden_size=256, num_layers=3, dropout=0.3, bidirectional=True, use_attention=True)
        model.fit(X_train_seq, y_train_seq, X_val_seq, y_val_seq, epochs=epochs, batch_size=32, patience=15, verbose=True)
        y_pred = preprocessor.inverse_transform_target(model.predict(X_test_seq))
        y_true = preprocessor.inverse_transform_target(y_test_seq)
        metrics = compute_regression_metrics(y_true, y_pred)
        print(f"LSTM Metrics: {metrics}")
        results['lstm'] = metrics
        
        # Save
        path = config.project_root / "models" / f"{symbol.replace('-','_')}_lstm_v3.pt"
        model.save_torch(str(path))
        print(f"Saved LSTM to {path}")
    except Exception as e:
        print(f"LSTM failed: {e}")
        import traceback; traceback.print_exc()
    
    # Transformer
    print(f"\n--- Transformer v3 ---")
    try:
        model = TransformerModel(input_size=X_train_seq.shape[2], d_model=256, nhead=8, num_layers=4, dim_feedforward=512, dropout=0.2, use_learnable_pe=True, use_attention_pooling=True)
        model.fit(X_train_seq, y_train_seq, X_val_seq, y_val_seq, epochs=epochs, batch_size=32, patience=15, verbose=True)
        y_pred = preprocessor.inverse_transform_target(model.predict(X_test_seq))
        y_true = preprocessor.inverse_transform_target(y_test_seq)
        metrics = compute_regression_metrics(y_true, y_pred)
        print(f"Transformer Metrics: {metrics}")
        results['transformer'] = metrics
        
        path = config.project_root / "models" / f"{symbol.replace('-','_')}_transformer_v3.pt"
        model.save_torch(str(path))
        print(f"Saved Transformer to {path}")
    except Exception as e:
        print(f"Transformer failed: {e}")
        import traceback; traceback.print_exc()
    
    # XGBoost
    print(f"\n--- XGBoost v3 ---")
    try:
        model = XGBoostModel(n_estimators=1000, max_depth=8, learning_rate=0.03, subsample=0.9, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0)
        model.fit(scaled['X_train'], scaled['y_train'], scaled['X_val'], scaled['y_val'])
        y_pred = preprocessor.inverse_transform_target(model.predict(scaled['X_test']))
        y_true = preprocessor.inverse_transform_target(scaled['y_test'])
        metrics = compute_regression_metrics(y_true, y_pred)
        print(f"XGBoost Metrics: {metrics}")
        results['xgboost'] = metrics
        
        path = config.project_root / "models" / f"{symbol.replace('-','_')}_xgb_v3.joblib"
        model.save(str(path))
        
        # Feature importance
        imp = model.get_feature_importance(feature_cols)
        imp_path = config.project_root / "models" / f"{symbol.replace('-','_')}_feature_importance_v3.csv"
        imp.to_csv(imp_path, index=False)
        print(f"Saved feature importance to {imp_path}")
        print(f"Top 10 features:\n{imp.head(10)}")
    except Exception as e:
        print(f"XGBoost failed: {e}")
        import traceback; traceback.print_exc()
    
    # ARIMA
    print(f"\n--- ARIMA v3 ---")
    try:
        train_prices = scaled['train_df']['Close'].values
        model = ARIMAModel(order=(5,1,2), seasonal_order=(1,1,1,7), use_sarimax=True)
        model.fit(y_train=train_prices)
        y_pred = model.predict(steps=len(scaled['test_df']))
        y_true = scaled['test_df']['Close'].values
        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
        print(f"ARIMA Metrics: {metrics}")
        results['arima'] = metrics
        
        path = config.project_root / "models" / f"{symbol.replace('-','_')}_arima_v3.joblib"
        model.save(str(path))
    except Exception as e:
        print(f"ARIMA failed: {e}")
        import traceback; traceback.print_exc()
    
    # Save preprocessor
    prep_path = config.project_root / "models" / f"{symbol.replace('-','_')}_preprocessor_v3.joblib"
    preprocessor.save(str(prep_path))
    print(f"\nSaved preprocessor to {prep_path}")
    
    print(f"\n{'='*80}")
    print(f"Summary for {symbol}")
    print(f"{'='*80}")
    for name, metrics in results.items():
        print(f"{name}: RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD")
    parser.add_argument("--epochs", type=int, default=50)
    args = parser.parse_args()
    
    train_symbol(args.symbol, args.epochs)
