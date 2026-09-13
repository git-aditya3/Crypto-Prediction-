"""
Test model predictions with past 1 week data - Improved Accuracy Evaluation
- Trains on data up to 7 days ago
- Predicts last 7 days
- Compares with actuals
- Computes detailed metrics
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

def load_data(symbol="BTC-USD"):
    fetcher = CryptoDataFetcher(symbol=symbol)
    df = fetcher.load_or_fetch(symbol=symbol)
    print(f"Loaded {symbol}: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
    return df

def prepare_data_for_backtest(df, cutoff_date, sequence_length=60):
    """
    Prepare data: train on data before cutoff_date, test on last 7 days after cutoff
    """
    # Cutoff: train up to cutoff, test is 7 days after
    train_df_raw = df[df.index <= cutoff_date].copy()
    test_df_raw = df[df.index > cutoff_date].copy()
    
    print(f"Train: {len(train_df_raw)} rows up to {cutoff_date}")
    print(f"Test (actual last week): {len(test_df_raw)} rows from {test_df_raw.index[0] if len(test_df_raw) > 0 else 'N/A'}")
    
    if len(test_df_raw) < 7:
        print(f"Warning: Only {len(test_df_raw)} days in test, need 7")
    
    # Feature engineering on full data to avoid leakage? Actually engineer on train only then apply to test
    # For simplicity, engineer on train and then on test separately with same logic
    engineer = FeatureEngineer()
    train_engineered = engineer.engineer(train_df_raw)
    
    # For test, we need to engineer but ensure we have enough history
    # Use full df for feature engineering to have proper rolling windows, then split
    full_engineered = engineer.engineer(df)
    # Now split engineered
    train_eng = full_engineered[full_engineered.index <= cutoff_date].copy()
    test_eng = full_engineered[full_engineered.index > cutoff_date].copy()
    
    # Preprocessing
    preprocessor = DataPreprocessor(scaler_type="robust")
    feature_cols = engineer.get_feature_columns(train_eng)
    train_cleaned = preprocessor.prepare_features(train_eng, feature_cols=feature_cols)
    test_cleaned = preprocessor.prepare_features(test_eng, feature_cols=feature_cols)
    
    # Split train into train/val (time series)
    n = len(train_cleaned)
    n_val = int(n * 0.15)
    n_train = n - n_val
    
    train_split = train_cleaned.iloc[:n_train]
    val_split = train_cleaned.iloc[n_train:]
    
    # Fit scaler on train_split only
    scaled = preprocessor.fit_transform(train_split, val_split, test_cleaned)
    
    # Sequences
    seq_len = sequence_length
    X_train_seq, y_train_seq = preprocessor.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
    X_val_seq, y_val_seq = preprocessor.create_sequences(scaled['X_val'], scaled['y_val'], seq_len)
    X_test_seq, y_test_seq = preprocessor.create_sequences(scaled['X_test'], scaled['y_test'], seq_len)
    
    scaled['X_train_seq'] = X_train_seq
    scaled['y_train_seq'] = y_train_seq
    scaled['X_val_seq'] = X_val_seq
    scaled['y_val_seq'] = y_val_seq
    scaled['X_test_seq'] = X_test_seq
    scaled['y_test_seq'] = y_test_seq
    scaled['preprocessor'] = preprocessor
    scaled['feature_columns'] = feature_cols
    scaled['test_raw'] = test_eng
    scaled['train_raw'] = train_eng
    
    return scaled, preprocessor, feature_cols

def train_and_evaluate(symbol="BTC-USD", cutoff_days_ago=7, sequence_length=60):
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - Past 1 Week Evaluation (Improved Models v3)")
    print(f"{'='*80}")
    
    df = load_data(symbol)
    
    # Cutoff date = 7 days before last date
    last_date = df.index[-1]
    cutoff_date = last_date - timedelta(days=cutoff_days_ago)
    print(f"Last date in data: {last_date}")
    print(f"Cutoff date (train up to): {cutoff_date}")
    print(f"Testing period: {cutoff_date + timedelta(days=1)} to {last_date} (7 days)")
    
    scaled, preprocessor, feature_cols = prepare_data_for_backtest(df, cutoff_date, sequence_length)
    
    print(f"\nData shapes:")
    print(f"  X_train_seq: {scaled['X_train_seq'].shape}")
    print(f"  X_val_seq: {scaled['X_val_seq'].shape}")
    print(f"  X_test_seq: {scaled['X_test_seq'].shape}")
    print(f"  X_train: {scaled['X_train'].shape}")
    print(f"  Features: {len(feature_cols)}")
    
    results = {}
    
    # 1. LSTM v3
    print(f"\n--- Training LSTM v3 (Improved) ---")
    try:
        input_size = scaled['X_train_seq'].shape[2]
        lstm_model = LSTMModel(input_size=input_size, hidden_size=256, num_layers=3, 
                               dropout=0.3, bidirectional=True, use_attention=True)
        lstm_history = lstm_model.fit(
            scaled['X_train_seq'], scaled['y_train_seq'],
            scaled['X_val_seq'], scaled['y_val_seq'],
            epochs=100, batch_size=32, patience=15, verbose=False
        )
        y_pred_lstm_scaled = lstm_model.predict(scaled['X_test_seq'])
        y_pred_lstm = preprocessor.inverse_transform_target(y_pred_lstm_scaled)
        y_true_lstm = preprocessor.inverse_transform_target(scaled['y_test_seq'])
        
        metrics_lstm = compute_regression_metrics(y_true_lstm, y_pred_lstm)
        results['lstm'] = {
            'model': lstm_model,
            'y_true': y_true_lstm,
            'y_pred': y_pred_lstm,
            'metrics': metrics_lstm,
            'history': lstm_history
        }
        print(f"LSTM v3 Metrics: RMSE={metrics_lstm['rmse']:.2f} MAE={metrics_lstm['mae']:.2f} MAPE={metrics_lstm['mape']:.2f}% R2={metrics_lstm['r2']:.4f} DirAcc={metrics_lstm['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"LSTM failed: {e}")
        import traceback
        traceback.print_exc()
        results['lstm'] = None
    
    # 2. Transformer v3
    print(f"\n--- Training Transformer v3 (Improved) ---")
    try:
        input_size = scaled['X_train_seq'].shape[2]
        transformer_model = TransformerModel(input_size=input_size, d_model=256, nhead=8, 
                                            num_layers=4, dim_feedforward=512, dropout=0.2,
                                            use_learnable_pe=True, use_attention_pooling=True)
        trans_history = transformer_model.fit(
            scaled['X_train_seq'], scaled['y_train_seq'],
            scaled['X_val_seq'], scaled['y_val_seq'],
            epochs=100, batch_size=32, patience=15, verbose=False
        )
        y_pred_trans_scaled = transformer_model.predict(scaled['X_test_seq'])
        y_pred_trans = preprocessor.inverse_transform_target(y_pred_trans_scaled)
        y_true_trans = preprocessor.inverse_transform_target(scaled['y_test_seq'])
        
        metrics_trans = compute_regression_metrics(y_true_trans, y_pred_trans)
        results['transformer'] = {
            'model': transformer_model,
            'y_true': y_true_trans,
            'y_pred': y_pred_trans,
            'metrics': metrics_trans,
            'history': trans_history
        }
        print(f"Transformer v3 Metrics: RMSE={metrics_trans['rmse']:.2f} MAE={metrics_trans['mae']:.2f} MAPE={metrics_trans['mape']:.2f}% R2={metrics_trans['r2']:.4f} DirAcc={metrics_trans['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"Transformer failed: {e}")
        import traceback
        traceback.print_exc()
        results['transformer'] = None
    
    # 3. XGBoost v3
    print(f"\n--- Training XGBoost v3 (Improved) ---")
    try:
        xgb_model = XGBoostModel(n_estimators=1000, max_depth=8, learning_rate=0.03,
                                 subsample=0.9, colsample_bytree=0.8,
                                 reg_alpha=0.1, reg_lambda=1.0)
        xgb_history = xgb_model.fit(scaled['X_train'], scaled['y_train'], scaled['X_val'], scaled['y_val'])
        y_pred_xgb_scaled = xgb_model.predict(scaled['X_test'])
        y_pred_xgb = preprocessor.inverse_transform_target(y_pred_xgb_scaled)
        y_true_xgb = preprocessor.inverse_transform_target(scaled['y_test'])
        
        # Align lengths
        min_len = min(len(y_true_xgb), len(y_pred_xgb))
        metrics_xgb = compute_regression_metrics(y_true_xgb[-min_len:], y_pred_xgb[-min_len:])
        results['xgboost'] = {
            'model': xgb_model,
            'y_true': y_true_xgb[-min_len:],
            'y_pred': y_pred_xgb[-min_len:],
            'metrics': metrics_xgb,
            'history': xgb_history
        }
        print(f"XGBoost v3 Metrics: RMSE={metrics_xgb['rmse']:.2f} MAE={metrics_xgb['mae']:.2f} MAPE={metrics_xgb['mape']:.2f}% R2={metrics_xgb['r2']:.4f} DirAcc={metrics_xgb['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"XGBoost failed: {e}")
        import traceback
        traceback.print_exc()
        results['xgboost'] = None
    
    # 4. ARIMA v3
    print(f"\n--- Training ARIMA v3 (Improved) ---")
    try:
        train_prices = scaled['train_df']['Close'].values
        arima_model = ARIMAModel(order=(5,1,2), seasonal_order=(1,1,1,7), use_sarimax=True)
        arima_model.fit(y_train=train_prices)
        
        test_len = len(scaled['test_df'])
        y_pred_arima = arima_model.predict(steps=test_len)
        y_true_arima = scaled['test_df']['Close'].values
        
        min_len = min(len(y_true_arima), len(y_pred_arima))
        metrics_arima = compute_regression_metrics(y_true_arima[-min_len:], y_pred_arima[-min_len:])
        results['arima'] = {
            'model': arima_model,
            'y_true': y_true_arima[-min_len:],
            'y_pred': y_pred_arima[-min_len:],
            'metrics': metrics_arima
        }
        print(f"ARIMA v3 Metrics: RMSE={metrics_arima['rmse']:.2f} MAE={metrics_arima['mae']:.2f} MAPE={metrics_arima['mape']:.2f}% R2={metrics_arima['r2']:.4f} DirAcc={metrics_arima['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"ARIMA failed: {e}")
        import traceback
        traceback.print_exc()
        results['arima'] = None
    
    # 5. Ensemble v3
    print(f"\n--- Training Ensemble v3 (Improved) ---")
    try:
        # Use models that succeeded
        valid_models = {k: v['model'] for k, v in results.items() if v is not None and k != 'ensemble'}
        if len(valid_models) >= 2:
            # Prepare data dict for ensemble
            X_train_dict = {
                'lstm': scaled['X_train_seq'],
                'transformer': scaled['X_train_seq'],
                'xgboost': scaled['X_train'],
                'arima': scaled['train_df']['Close'].values
            }
            y_train_dict = {
                'lstm': scaled['y_train_seq'],
                'transformer': scaled['y_train_seq'],
                'xgboost': scaled['y_train'],
                'arima': scaled['train_df']['Close'].values
            }
            X_val_dict = {
                'lstm': scaled['X_val_seq'],
                'transformer': scaled['X_val_seq'],
                'xgboost': scaled['X_val'],
                'arima': scaled['val_df']['Close'].values if 'val_df' in scaled else None
            }
            y_val_dict = {
                'lstm': scaled['y_val_seq'],
                'transformer': scaled['y_val_seq'],
                'xgboost': scaled['y_val'],
                'arima': scaled['val_df']['Close'].values if 'val_df' in scaled else None
            }
            
            # Only include valid models
            X_train_dict = {k: v for k, v in X_train_dict.items() if k in valid_models}
            y_train_dict = {k: v for k, v in y_train_dict.items() if k in valid_models}
            X_val_dict = {k: v for k, v in X_val_dict.items() if k in valid_models and v is not None}
            y_val_dict = {k: v for k, v in y_val_dict.items() if k in valid_models and v is not None}
            
            ensemble_model = EnsembleModel(models=valid_models, use_stacking=True, use_dynamic_weights=True)
            ensemble_model.fit(X_train_dict, y_train_dict, X_val_dict, y_val_dict)
            
            # Predict
            X_test_dict = {
                'lstm': scaled['X_test_seq'],
                'transformer': scaled['X_test_seq'],
                'xgboost': scaled['X_test'],
                'arima': len(scaled['test_df'])
            }
            X_test_dict = {k: v for k, v in X_test_dict.items() if k in valid_models}
            
            y_pred_ensemble = ensemble_model.predict(X_test_dict)
            # Use lstm true as reference (they should all be aligned)
            y_true_ensemble = results.get('lstm', {}).get('y_true') or results.get('transformer', {}).get('y_true')
            if y_true_ensemble is None:
                y_true_ensemble = preprocessor.inverse_transform_target(scaled['y_test_seq'])
            
            min_len = min(len(y_true_ensemble), len(y_pred_ensemble))
            metrics_ensemble = compute_regression_metrics(y_true_ensemble[-min_len:], y_pred_ensemble[-min_len:])
            results['ensemble'] = {
                'model': ensemble_model,
                'y_true': y_true_ensemble[-min_len:],
                'y_pred': y_pred_ensemble[-min_len:],
                'metrics': metrics_ensemble
            }
            print(f"Ensemble v3 Metrics: RMSE={metrics_ensemble['rmse']:.2f} MAE={metrics_ensemble['mae']:.2f} MAPE={metrics_ensemble['mape']:.2f}% R2={metrics_ensemble['r2']:.4f} DirAcc={metrics_ensemble['directional_accuracy']:.1f}%")
            print(f"  Dynamic weights: {ensemble_model.dynamic_weights}")
            if ensemble_model.meta_learner:
                print(f"  Stacking coefs: {ensemble_model.meta_learner.coef_}")
        else:
            print("Not enough valid models for ensemble")
            results['ensemble'] = None
    except Exception as e:
        print(f"Ensemble failed: {e}")
        import traceback
        traceback.print_exc()
        results['ensemble'] = None
    
    # Detailed past week comparison
    print(f"\n{'='*80}")
    print(f"Past 1 Week Detailed Comparison - {symbol}")
    print(f"{'='*80}")
    
    # Get actual last 7 days from original df
    actual_last_week = df.tail(7)
    print(f"\nActual prices last 7 days:")
    for idx, row in actual_last_week.iterrows():
        print(f"  {idx.date()}: Close=${row['Close']:.2f} Open=${row['Open']:.2f} High=${row['High']:.2f} Low=${row['Low']:.2f}")
    
    # Compare predictions if available
    if results.get('ensemble') and results['ensemble'] is not None:
        print(f"\nEnsemble predictions vs Actual (last {len(results['ensemble']['y_true'])} days):")
        y_true = results['ensemble']['y_true']
        y_pred = results['ensemble']['y_pred']
        for i in range(min(7, len(y_true))):
            actual = y_true[-(7-i)] if len(y_true) >= 7 else y_true[i]
            pred = y_pred[-(7-i)] if len(y_pred) >= 7 else y_pred[i]
            error_pct = abs(actual - pred) / actual * 100
            print(f"  Day {i+1}: Actual=${actual:.2f} Pred=${pred:.2f} Error={error_pct:.2f}%")
    
    # Summary table
    print(f"\n{'='*80}")
    print(f"Summary - Model Comparison (Lower is better for RMSE/MAE/MAPE, Higher for R2/DirAcc)")
    print(f"{'='*80}")
    print(f"{'Model':<15} {'RMSE':<10} {'MAE':<10} {'MAPE%':<10} {'R2':<10} {'DirAcc%':<10}")
    print(f"{'-'*80}")
    for name in ['lstm', 'transformer', 'xgboost', 'arima', 'ensemble']:
        if results.get(name) and results[name] is not None:
            m = results[name]['metrics']
            print(f"{name:<15} {m['rmse']:<10.2f} {m['mae']:<10.2f} {m['mape']:<10.2f} {m['r2']:<10.4f} {m['directional_accuracy']:<10.1f}")
    
    return results, actual_last_week

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD", help="Symbol to test")
    parser.add_argument("--days", type=int, default=7, help="Days to test (past week)")
    args = parser.parse_args()
    
    results, actual = train_and_evaluate(symbol=args.symbol, cutoff_days_ago=args.days)
    
    # Also test other symbols quickly with XGBoost only for speed
    print(f"\n\nQuick test on other symbols (XGBoost only for speed):")
    for sym in ["ETH-USD", "BNB-USD", "SOL-USD"]:
        try:
            print(f"\n--- Quick test {sym} ---")
            df = load_data(sym)
            last_date = df.index[-1]
            cutoff_date = last_date - timedelta(days=7)
            scaled, preprocessor, _ = prepare_data_for_backtest(df, cutoff_date)
            
            xgb_model = XGBoostModel(n_estimators=500, max_depth=6, learning_rate=0.05)
            xgb_model.fit(scaled['X_train'], scaled['y_train'], scaled['X_val'], scaled['y_val'])
            y_pred = preprocessor.inverse_transform_target(xgb_model.predict(scaled['X_test']))
            y_true = preprocessor.inverse_transform_target(scaled['y_test'])
            min_len = min(len(y_true), len(y_pred))
            metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
            print(f"{sym} XGBoost: RMSE={metrics['rmse']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        except Exception as e:
            print(f"{sym} failed: {e}")
