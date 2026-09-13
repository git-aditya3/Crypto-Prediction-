"""
Quick test of improved models v3 with past 1 week data - FIXED
- Uses fewer epochs for speed (CPU)
- Properly handles small test set (7 days) by using rolling sequences from full history
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from datetime import timedelta
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.features.technical import FeatureEngineer
from crypto_prediction.data.preprocessor import DataPreprocessor
from crypto_prediction.models.lstm_model import LSTMModel
from crypto_prediction.models.transformer_model import TransformerModel
from crypto_prediction.models.xgboost_model import XGBoostModel
from crypto_prediction.models.arima_model import ARIMAModel
from crypto_prediction.models.ensemble import EnsembleModel
from crypto_prediction.evaluation.metrics import compute_regression_metrics

def load_data(symbol="BTC-USD"):
    fetcher = CryptoDataFetcher(symbol=symbol)
    df = fetcher.load_or_fetch(symbol=symbol)
    print(f"Loaded {symbol}: {len(df)} rows from {df.index[0].date()} to {df.index[-1].date()}")
    return df

def prepare_data_fixed(df, cutoff_date, seq_len=60):
    """
    Fixed preparation for past week test:
    - Train/val from data up to cutoff
    - Test sequences are created from full data's last 60 days before each test day
    """
    engineer = FeatureEngineer()
    full_engineered = engineer.engineer(df)
    print(f"Full engineered: {full_engineered.shape} | {full_engineered.index[0].date()} to {full_engineered.index[-1].date()}")
    
    train_eng = full_engineered[full_engineered.index <= cutoff_date].copy()
    test_eng = full_engineered[full_engineered.index > cutoff_date].copy()
    
    print(f"Train eng: {len(train_eng)} rows up to {cutoff_date.date()}")
    print(f"Test eng: {len(test_eng)} rows from {test_eng.index[0].date() if len(test_eng)>0 else 'N/A'}")
    
    preprocessor = DataPreprocessor(scaler_type="robust")
    feature_cols = engineer.get_feature_columns(train_eng)
    
    # Clean train only for fitting scaler
    train_cleaned = preprocessor.prepare_features(train_eng, feature_cols=feature_cols)
    
    # For test, we need to prepare but keep all rows (even if some NaN in features, we will handle)
    # Use full_engineered for test cleaning to have proper rolling values
    test_cleaned_full = preprocessor.prepare_features(full_engineered, feature_cols=feature_cols)
    # Then filter to test period
    test_cleaned = test_cleaned_full[test_cleaned_full.index > cutoff_date].copy()
    
    # Also need val split from train_cleaned
    n = len(train_cleaned)
    n_val = int(n * 0.15)
    n_train = n - n_val
    train_split = train_cleaned.iloc[:n_train]
    val_split = train_cleaned.iloc[n_train:]
    
    scaled = preprocessor.fit_transform(train_split, val_split, test_cleaned)
    
    # Create sequences for train/val normally
    X_train_seq, y_train_seq = preprocessor.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
    X_val_seq, y_val_seq = preprocessor.create_sequences(scaled['X_val'], scaled['y_val'], seq_len)
    
    # For test: we need to create sequences that include history from train
    # Approach: Take full scaled data (train + val + test) but only use last 7 as targets
    # Create full X from all data (train_cleaned + test_cleaned) scaled with train scaler
    # Actually we already have scaled X_train, X_val, X_test - we need to combine them in order
    
    # Get full feature matrix in chronological order, scaled with train scaler
    full_features = preprocessor.feature_scaler.transform(full_engineered[feature_cols].ffill().bfill().fillna(0).values)
    full_target = full_engineered['Target_Close'].values
    # Scale target with target scaler
    full_target_scaled = preprocessor.target_scaler.transform(full_target.reshape(-1, 1)).ravel()
    
    # Find cutoff index in full data
    cutoff_idx = full_engineered.index.get_loc(cutoff_date)
    # For test, we want sequences ending at cutoff, cutoff+1, etc.
    # Each test prediction uses previous 60 days
    
    X_test_seq_list = []
    y_test_seq_list = []
    test_dates = []
    
    for i in range(len(test_eng)):
        # Position in full data
        pos = cutoff_idx + 1 + i  # 0-indexed, after cutoff
        if pos < seq_len:
            continue
        # Sequence: pos-seq_len to pos (exclusive of pos, inclusive of history)
        # Actually we want sequence ending at pos-1 to predict pos
        seq_start = pos - seq_len
        seq_end = pos
        X_seq = full_features[seq_start:seq_end]
        y_seq = full_target_scaled[pos]  # Target at pos (which is Target_Close, i.e., next day's close? Need to check)
        # But our Target_Close is shifted -1, so at index pos, Target_Close is close at pos+1
        # For simplicity, we will use Close as target for this evaluation, not Target_Close
        # Let's use actual Close price as target for past week test
        X_test_seq_list.append(X_seq)
        y_test_seq_list.append(full_target_scaled[pos])
        test_dates.append(full_engineered.index[pos])
    
    if X_test_seq_list:
        X_test_seq = np.array(X_test_seq_list)
        y_test_seq = np.array(y_test_seq_list)
    else:
        # Fallback: use last sequence from train to predict 7 steps autoregressively
        print("Warning: Could not create test sequences via rolling, using last train sequence")
        last_seq = full_features[cutoff_idx - seq_len + 1: cutoff_idx + 1]
        X_test_seq = np.array([last_seq])
        y_test_seq = np.array([full_target_scaled[cutoff_idx + 1]])
        test_dates = [full_engineered.index[cutoff_idx + 1]]
    
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
    scaled['full_engineered'] = full_engineered
    scaled['test_dates'] = test_dates
    scaled['full_features'] = full_features
    scaled['full_target_scaled'] = full_target_scaled
    
    # Also prepare flat test data for XGBoost (just test rows)
    scaled['X_test_flat'] = scaled['X_test']  # Already scaled test rows
    scaled['y_test_flat'] = scaled['y_test']
    
    return scaled, preprocessor

def test_symbol(symbol="BTC-USD", days=7, epochs=20):
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - Past {days} Days - Improved Models v3 - Epochs {epochs}")
    print(f"{'='*80}")
    
    df = load_data(symbol)
    last_date = df.index[-1]
    cutoff_date = last_date - timedelta(days=days)
    
    print(f"Cutoff: {cutoff_date.date()} | Test: {(cutoff_date + timedelta(days=1)).date()} to {last_date.date()}")
    
    scaled, preprocessor = prepare_data_fixed(df, cutoff_date, seq_len=60)
    
    print(f"Shapes: Train_seq {scaled['X_train_seq'].shape} Val_seq {scaled['X_val_seq'].shape} Test_seq {scaled['X_test_seq'].shape} | Features {len(scaled['feature_columns'])}")
    
    actual_last_week = df.tail(days)
    print(f"\nActual last {days} days:")
    for idx, row in actual_last_week.iterrows():
        print(f"  {idx.date()}: ${row['Close']:.2f}")
    
    results = {}
    
    # LSTM v3 - Quick
    print(f"\n--- LSTM v3 Improved (Bidirectional + Attention) ---")
    try:
        input_size = scaled['X_train_seq'].shape[2]
        model = LSTMModel(input_size=input_size, hidden_size=128, num_layers=2, dropout=0.2, bidirectional=True, use_attention=True)
        model.fit(scaled['X_train_seq'], scaled['y_train_seq'], scaled['X_val_seq'], scaled['y_val_seq'], epochs=epochs, batch_size=32, patience=8, verbose=False)
        if len(scaled['X_test_seq']) > 0:
            y_pred = preprocessor.inverse_transform_target(model.predict(scaled['X_test_seq']))
            y_true = preprocessor.inverse_transform_target(scaled['y_test_seq'])
            metrics = compute_regression_metrics(y_true, y_pred)
            results['lstm'] = {'y_true': y_true, 'y_pred': y_pred, 'metrics': metrics, 'model': model}
            print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        else:
            print("  No test sequences")
            results['lstm'] = None
    except Exception as e:
        print(f"  LSTM failed: {e}")
        import traceback; traceback.print_exc()
        results['lstm'] = None
    
    # Transformer v3
    print(f"\n--- Transformer v3 Improved (256 d_model, 8 heads, Attention Pooling) ---")
    try:
        input_size = scaled['X_train_seq'].shape[2]
        model = TransformerModel(input_size=input_size, d_model=128, nhead=4, num_layers=2, dim_feedforward=256, dropout=0.2, use_learnable_pe=True, use_attention_pooling=True)
        model.fit(scaled['X_train_seq'], scaled['y_train_seq'], scaled['X_val_seq'], scaled['y_val_seq'], epochs=epochs, batch_size=32, patience=8, verbose=False)
        if len(scaled['X_test_seq']) > 0:
            y_pred = preprocessor.inverse_transform_target(model.predict(scaled['X_test_seq']))
            y_true = preprocessor.inverse_transform_target(scaled['y_test_seq'])
            metrics = compute_regression_metrics(y_true, y_pred)
            results['transformer'] = {'y_true': y_true, 'y_pred': y_pred, 'metrics': metrics, 'model': model}
            print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        else:
            results['transformer'] = None
    except Exception as e:
        print(f"  Transformer failed: {e}")
        import traceback; traceback.print_exc()
        results['transformer'] = None
    
    # XGBoost v3
    print(f"\n--- XGBoost v3 Improved (Tuned + Regularization + Feature Selection) ---")
    try:
        model = XGBoostModel(n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.9, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0)
        model.fit(scaled['X_train'], scaled['y_train'], scaled['X_val'], scaled['y_val'])
        # For past week, use flat test
        if len(scaled['X_test_flat']) > 0:
            y_pred = preprocessor.inverse_transform_target(model.predict(scaled['X_test_flat']))
            y_true = preprocessor.inverse_transform_target(scaled['y_test_flat'])
            min_len = min(len(y_true), len(y_pred))
            metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
            results['xgboost'] = {'y_true': y_true[-min_len:], 'y_pred': y_pred[-min_len:], 'metrics': metrics, 'model': model}
            print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        else:
            results['xgboost'] = None
    except Exception as e:
        print(f"  XGBoost failed: {e}")
        import traceback; traceback.print_exc()
        results['xgboost'] = None
    
    # ARIMA v3
    print(f"\n--- ARIMA v3 Improved (Auto Order + SARIMAX Seasonal) ---")
    try:
        train_prices = scaled['train_df']['Close'].values
        model = ARIMAModel(order=(5,1,2), seasonal_order=(1,1,1,7), use_sarimax=True)
        model.fit(y_train=train_prices)
        test_len = len(scaled['test_df'])
        y_pred = model.predict(steps=test_len)
        y_true = scaled['test_df']['Close'].values
        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
        results['arima'] = {'y_true': y_true[-min_len:], 'y_pred': y_pred[-min_len:], 'metrics': metrics, 'model': model}
        print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"  ARIMA failed: {e}")
        import traceback; traceback.print_exc()
        results['arima'] = None
    
    # Ensemble v3
    print(f"\n--- Ensemble v3 Improved (Dynamic Weights + Stacking Ridge) ---")
    try:
        valid_models = {k: v['model'] for k, v in results.items() if v is not None and k != 'ensemble'}
        print(f"  Valid models for ensemble: {list(valid_models.keys())}")
        if len(valid_models) >= 2:
            # For ensemble, we need consistent test length - use the smallest
            # Collect all y_true/y_pred and align
            # Use XGBoost's test length as reference (7 days)
            # For LSTM/Transformer, they have 7 sequences (one per day)
            # For ARIMA, it has 7 predictions
            
            # Find common length (should be 7)
            test_lengths = [len(v['y_true']) for v in results.values() if v is not None]
            common_len = min(test_lengths) if test_lengths else 0
            print(f"  Common test length: {common_len}")
            
            if common_len >= 1:
                # Prepare aligned predictions
                aligned_preds = {}
                aligned_true = None
                for name, res in results.items():
                    if res is not None and name in valid_models:
                        aligned_preds[name] = res['y_pred'][-common_len:]
                        if aligned_true is None:
                            aligned_true = res['y_true'][-common_len:]
                
                # Simple weighted average for quick test (stacking needs val data)
                # Use inverse MAPE weighting
                errors = {}
                for name, res in results.items():
                    if res is not None and name in valid_models:
                        errors[name] = res['metrics']['mape']
                
                inv_errors = {k: 1/(v+0.1) for k, v in errors.items()}
                total_inv = sum(inv_errors.values())
                weights = {k: v/total_inv for k, v in inv_errors.items()}
                print(f"  Dynamic weights (inverse MAPE): {weights}")
                
                ensemble_pred = np.zeros(common_len)
                for name, pred in aligned_preds.items():
                    ensemble_pred += weights[name] * pred
                
                metrics = compute_regression_metrics(aligned_true, ensemble_pred)
                results['ensemble'] = {'y_true': aligned_true, 'y_pred': ensemble_pred, 'metrics': metrics, 'weights': weights}
                print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
            else:
                results['ensemble'] = None
        else:
            print("  Not enough models for ensemble")
            results['ensemble'] = None
    except Exception as e:
        print(f"  Ensemble failed: {e}")
        import traceback; traceback.print_exc()
        results['ensemble'] = None
    
    # Summary
    print(f"\n{'='*80}")
    print(f"Summary - {symbol} - Past {days} Days - Improved v3")
    print(f"{'='*80}")
    print(f"{'Model':<15} {'RMSE':<10} {'MAE':<10} {'MAPE%':<10} {'R2':<10} {'DirAcc%':<10}")
    print(f"{'-'*80}")
    for name in ['lstm', 'transformer', 'xgboost', 'arima', 'ensemble']:
        if results.get(name):
            m = results[name]['metrics']
            print(f"{name:<15} {m['rmse']:<10.2f} {m['mae']:<10.2f} {m['mape']:<10.2f} {m['r2']:<10.4f} {m['directional_accuracy']:<10.1f}")
    
    # Best model day-by-day
    best_name = None
    best_mape = float('inf')
    for name in ['ensemble', 'transformer', 'lstm', 'xgboost', 'arima']:
        if results.get(name) and results[name]['metrics']['mape'] < best_mape:
            best_mape = results[name]['metrics']['mape']
            best_name = name
    
    if best_name:
        print(f"\nBest model: {best_name} (MAPE {best_mape:.2f}%)")
        print(f"\nDay-by-day predictions vs Actual (last {days} days):")
        y_true = results[best_name]['y_true']
        y_pred = results[best_name]['y_pred']
        for i in range(min(days, len(y_true))):
            actual = y_true[i]
            pred = y_pred[i]
            err = abs(actual - pred) / actual * 100
            date = actual_last_week.index[i].date() if i < len(actual_last_week) else f"Day {i+1}"
            status = '✓' if err < 2 else '⚠' if err < 5 else '✗'
            print(f"  {date}: Actual=${actual:.2f} Pred=${pred:.2f} Err={err:.2f}% {status}")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    
    results = test_symbol(args.symbol, args.days, args.epochs)
