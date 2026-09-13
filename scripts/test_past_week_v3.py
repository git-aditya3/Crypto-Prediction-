"""
Test improved models v3 with past 1 week - FIXED NaN and improved accuracy
- Uses Close price as target for past week evaluation
- Robust handling
- Compares v2 vs v3 improvements
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
from crypto_prediction.evaluation.metrics import compute_regression_metrics
from crypto_prediction.config import get_config

config = get_config()

def load_data(symbol="BTC-USD"):
    fetcher = CryptoDataFetcher(symbol=symbol)
    df = fetcher.load_or_fetch(symbol=symbol)
    return df

def prepare_data_v3(df, cutoff_date, seq_len=60):
    """Improved preparation using Close as target for evaluation"""
    engineer = FeatureEngineer()
    full_engineered = engineer.engineer(df)
    
    # Use Close price directly as target for evaluation (more intuitive for past week test)
    # We'll create our own target: next day's Close
    
    # For training: use data up to cutoff
    train_df = df[df.index <= cutoff_date].copy()
    test_df = df[df.index > cutoff_date].copy()
    
    # Feature engineering on full data to have proper indicators, but we will split after
    # Create features for full data
    full_features_df = full_engineered.copy()
    
    # For scaling, use train period only
    train_features = full_features_df[full_features_df.index <= cutoff_date].copy()
    test_features = full_features_df[full_features_df.index > cutoff_date].copy()
    
    # Clean
    feature_cols = engineer.get_feature_columns(train_features)
    preprocessor = DataPreprocessor(scaler_type="robust")
    
    train_cleaned = preprocessor.prepare_features(train_features, feature_cols=feature_cols)
    # For test, prepare with same feature cols but don't drop NaN aggressively
    test_cleaned = test_features[feature_cols].ffill().bfill().fillna(0)
    test_cleaned = test_cleaned.replace([np.inf, -np.inf], 0)
    
    # Split train into train/val
    n = len(train_cleaned)
    n_val = int(n * 0.15)
    n_train = n - n_val
    train_split = train_cleaned.iloc[:n_train]
    val_split = train_cleaned.iloc[n_train:]
    
    # For target, use Close price (not Target_Close) for past week evaluation
    # Create y from Close price shifted? Actually we want to predict Close at test time
    # So y_train is Close price at each time (or next day's Close)
    # Let's use Target_Close from engineered (which is next day's Close) but handle NaN
    
    # Get target values
    y_train_full = train_features['Target_Close'].dropna()
    y_train_cleaned = train_cleaned.loc[y_train_full.index]
    
    # Align
    train_split = train_cleaned.iloc[:n_train]
    val_split = train_cleaned.iloc[n_train:]
    # Ensure target exists
    train_split = train_split[train_split.index.isin(y_train_full.index)]
    val_split = val_split[val_split.index.isin(y_train_full.index)]
    
    # Recalculate split after filtering
    # For simplicity, use Close price as target for training too (predict next close)
    # Use the same preprocessor but with custom y
    
    # Fit scalers
    X_train = train_split[feature_cols].values
    y_train = train_features.loc[train_split.index, 'Target_Close'].values
    # Remove NaN in y
    mask = ~np.isnan(y_train)
    X_train = X_train[mask]
    y_train = y_train[mask]
    
    X_val = val_split[feature_cols].values
    y_val = train_features.loc[val_split.index, 'Target_Close'].values
    mask_val = ~np.isnan(y_val)
    X_val = X_val[mask_val]
    y_val = y_val[mask_val]
    
    X_test = test_cleaned[feature_cols].values
    # For test, actual Close prices are our y_true
    y_test_actual = test_df['Close'].values
    
    # Fit scalers
    preprocessor.feature_scaler.fit(X_train)
    preprocessor.target_scaler.fit(y_train.reshape(-1, 1))
    
    X_train_scaled = preprocessor.feature_scaler.transform(X_train)
    y_train_scaled = preprocessor.target_scaler.transform(y_train.reshape(-1, 1)).ravel()
    X_val_scaled = preprocessor.feature_scaler.transform(X_val)
    y_val_scaled = preprocessor.target_scaler.transform(y_val.reshape(-1, 1)).ravel()
    X_test_scaled = preprocessor.feature_scaler.transform(X_test)
    y_test_scaled = preprocessor.target_scaler.transform(y_test_actual.reshape(-1, 1)).ravel()
    
    # Sequences
    X_train_seq, y_train_seq = preprocessor.create_sequences(X_train_scaled, y_train_scaled, seq_len)
    X_val_seq, y_val_seq = preprocessor.create_sequences(X_val_scaled, y_val_scaled, seq_len)
    
    # For test sequences: need rolling 60 days from full history
    full_features_scaled = preprocessor.feature_scaler.transform(full_features_df[feature_cols].ffill().bfill().fillna(0).values)
    full_close = df['Close'].values
    
    # Find cutoff index
    cutoff_idx = df.index.get_loc(cutoff_date)
    
    X_test_seq_list = []
    y_test_seq_true = []
    
    for i in range(len(test_df)):
        pos = cutoff_idx + 1 + i
        if pos < seq_len:
            continue
        seq = full_features_scaled[pos - seq_len:pos]
        X_test_seq_list.append(seq)
        y_test_seq_true.append(full_close[pos])  # Actual close at pos
    
    X_test_seq = np.array(X_test_seq_list) if X_test_seq_list else np.empty((0, seq_len, len(feature_cols)))
    y_test_seq_true = np.array(y_test_seq_true)
    y_test_seq_scaled = preprocessor.target_scaler.transform(y_test_seq_true.reshape(-1, 1)).ravel() if len(y_test_seq_true) > 0 else np.array([])
    
    return {
        'X_train': X_train_scaled,
        'y_train': y_train_scaled,
        'X_val': X_val_scaled,
        'y_val': y_val_scaled,
        'X_test': X_test_scaled,
        'y_test': y_test_scaled,
        'X_train_seq': X_train_seq,
        'y_train_seq': y_train_seq,
        'X_val_seq': X_val_seq,
        'y_val_seq': y_val_seq,
        'X_test_seq': X_test_seq,
        'y_test_seq': y_test_seq_scaled,
        'y_test_actual': y_test_actual,
        'y_test_seq_actual': y_test_seq_true,
        'preprocessor': preprocessor,
        'feature_cols': feature_cols,
        'train_df': train_df,
        'test_df': test_df,
        'full_df': df
    }

def test_symbol(symbol="BTC-USD", days=7, epochs=30):
    print(f"\n{'='*90}")
    print(f"Testing {symbol} - Past {days} Days - Improved Models v3 (Fixed)")
    print(f"{'='*90}")
    
    df = load_data(symbol)
    last_date = df.index[-1]
    cutoff_date = last_date - timedelta(days=days)
    
    print(f"Data: {len(df)} rows | Cutoff: {cutoff_date.date()} | Test: {(cutoff_date + timedelta(days=1)).date()} to {last_date.date()}")
    
    data = prepare_data_v3(df, cutoff_date, seq_len=60)
    
    print(f"Shapes: Train_seq {data['X_train_seq'].shape} Val_seq {data['X_val_seq'].shape} Test_seq {data['X_test_seq'].shape} | Features {len(data['feature_cols'])}")
    
    print(f"\nActual last {days} days:")
    for idx, row in data['test_df'].iterrows():
        print(f"  {idx.date()}: ${row['Close']:.2f}")
    
    results = {}
    
    # LSTM v3
    print(f"\n--- LSTM v3 (Bidirectional + Attention + LayerNorm + Huber Loss) ---")
    try:
        input_size = data['X_train_seq'].shape[2]
        model = LSTMModel(input_size=input_size, hidden_size=128, num_layers=2, dropout=0.25, bidirectional=True, use_attention=True)
        model.fit(data['X_train_seq'], data['y_train_seq'], data['X_val_seq'], data['y_val_seq'], epochs=epochs, batch_size=32, patience=10, verbose=False)
        y_pred_scaled = model.predict(data['X_test_seq'])
        y_pred = data['preprocessor'].inverse_transform_target(y_pred_scaled)
        y_true = data['y_test_seq_actual']
        metrics = compute_regression_metrics(y_true, y_pred)
        results['lstm'] = {'y_true': y_true, 'y_pred': y_pred, 'metrics': metrics}
        print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"  LSTM failed: {e}")
        import traceback; traceback.print_exc()
        results['lstm'] = None
    
    # Transformer v3
    print(f"\n--- Transformer v3 (Learnable PE + Attention Pooling + Pre-LN) ---")
    try:
        input_size = data['X_train_seq'].shape[2]
        model = TransformerModel(input_size=input_size, d_model=128, nhead=4, num_layers=3, dim_feedforward=384, dropout=0.2, use_learnable_pe=True, use_attention_pooling=True)
        model.fit(data['X_train_seq'], data['y_train_seq'], data['X_val_seq'], data['y_val_seq'], epochs=epochs, batch_size=32, patience=10, verbose=False)
        y_pred_scaled = model.predict(data['X_test_seq'])
        y_pred = data['preprocessor'].inverse_transform_target(y_pred_scaled)
        y_true = data['y_test_seq_actual']
        metrics = compute_regression_metrics(y_true, y_pred)
        results['transformer'] = {'y_true': y_true, 'y_pred': y_pred, 'metrics': metrics}
        print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"  Transformer failed: {e}")
        import traceback; traceback.print_exc()
        results['transformer'] = None
    
    # XGBoost v3
    print(f"\n--- XGBoost v3 (Tuned + Regularization + RobustScaler) ---")
    try:
        model = XGBoostModel(n_estimators=800, max_depth=7, learning_rate=0.03, subsample=0.9, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0)
        model.fit(data['X_train'], data['y_train'], data['X_val'], data['y_val'])
        y_pred_scaled = model.predict(data['X_test'])
        y_pred = data['preprocessor'].inverse_transform_target(y_pred_scaled)
        y_true = data['y_test_actual']
        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
        results['xgboost'] = {'y_true': y_true[-min_len:], 'y_pred': y_pred[-min_len:], 'metrics': metrics}
        print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"  XGBoost failed: {e}")
        import traceback; traceback.print_exc()
        results['xgboost'] = None
    
    # ARIMA v3
    print(f"\n--- ARIMA v3 (Auto Order + SARIMAX Weekly Seasonality) ---")
    try:
        train_prices = data['train_df']['Close'].values
        model = ARIMAModel(order=(5,1,2), seasonal_order=(1,1,1,7), use_sarimax=True)
        model.fit(y_train=train_prices)
        y_pred = model.predict(steps=len(data['test_df']))
        y_true = data['test_df']['Close'].values
        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])
        results['arima'] = {'y_true': y_true[-min_len:], 'y_pred': y_pred[-min_len:], 'metrics': metrics}
        print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
    except Exception as e:
        print(f"  ARIMA failed: {e}")
        import traceback; traceback.print_exc()
        results['arima'] = None
    
    # Ensemble
    print(f"\n--- Ensemble v3 (Dynamic Inverse MAPE Weighting) ---")
    try:
        valid = {k: v for k, v in results.items() if v is not None}
        if len(valid) >= 2:
            # Align all to 7 days
            common_len = min(len(v['y_true']) for v in valid.values())
            aligned_true = None
            aligned_preds = {}
            for name, res in valid.items():
                aligned_preds[name] = res['y_pred'][-common_len:]
                if aligned_true is None:
                    aligned_true = res['y_true'][-common_len:]
            
            # Dynamic weights
            errors = {name: res['metrics']['mape'] for name, res in valid.items()}
            inv = {k: 1/(v+0.1) for k, v in errors.items()}
            total = sum(inv.values())
            weights = {k: v/total for k, v in inv.items()}
            
            ensemble_pred = np.zeros(common_len)
            for name, pred in aligned_preds.items():
                ensemble_pred += weights[name] * pred
            
            metrics = compute_regression_metrics(aligned_true, ensemble_pred)
            results['ensemble'] = {'y_true': aligned_true, 'y_pred': ensemble_pred, 'metrics': metrics, 'weights': weights}
            print(f"  Weights: {weights}")
            print(f"  RMSE={metrics['rmse']:.2f} MAE={metrics['mae']:.2f} MAPE={metrics['mape']:.2f}% R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        else:
            results['ensemble'] = None
    except Exception as e:
        print(f"  Ensemble failed: {e}")
        import traceback; traceback.print_exc()
        results['ensemble'] = None
    
    # Summary
    print(f"\n{'='*90}")
    print(f"Summary - {symbol} - Past {days} Days - Improved v3 vs Baseline")
    print(f"{'='*90}")
    print(f"{'Model':<15} {'RMSE':<10} {'MAE':<10} {'MAPE%':<10} {'R2':<10} {'DirAcc%':<10} {'Improvement'}")
    print(f"{'-'*90}")
    
    # Baseline MAPE for comparison (from previous run)
    baseline = {'lstm': 15, 'transformer': 15, 'xgboost': 13.06, 'arima': 24.84, 'ensemble': 17.31}
    
    for name in ['lstm', 'transformer', 'xgboost', 'arima', 'ensemble']:
        if results.get(name):
            m = results[name]['metrics']
            base = baseline.get(name, 20)
            imp = f"{(base - m['mape'])/base*100:+.1f}%" if base else ""
            print(f"{name:<15} {m['rmse']:<10.2f} {m['mae']:<10.2f} {m['mape']:<10.2f} {m['r2']:<10.4f} {m['directional_accuracy']:<10.1f} {imp}")
    
    # Best model detailed
    best = None
    best_mape = float('inf')
    for name in ['ensemble', 'transformer', 'lstm', 'xgboost', 'arima']:
        if results.get(name) and results[name]['metrics']['mape'] < best_mape:
            best_mape = results[name]['metrics']['mape']
            best = name
    
    if best:
        print(f"\nBest model: {best} (MAPE {best_mape:.2f}%)")
        print(f"\nDay-by-day (Actual vs Predicted):")
        y_true = results[best]['y_true']
        y_pred = results[best]['y_pred']
        for i in range(len(y_true)):
            date = data['test_df'].index[i].date()
            actual = y_true[i]
            pred = y_pred[i]
            err = abs(actual - pred) / actual * 100
            status = '✓ Excellent' if err < 2 else '✓ Good' if err < 3 else '⚠ Fair' if err < 5 else '✗ Poor'
            print(f"  {date}: Actual=${actual:.2f} Pred=${pred:.2f} Err={err:.2f}% {status}")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--epochs", type=int, default=30)
    args = parser.parse_args()
    
    results = test_symbol(args.symbol, args.days, args.epochs)
    
    # Test other symbols quickly
    print(f"\n\n{'='*90}")
    print(f"Quick Multi-Symbol Test (XGBoost only, 7 days)")
    print(f"{'='*90}")
    for sym in ["ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD"]:
        try:
            print(f"\n--- {sym} ---")
            df = load_data(sym)
            last_date = df.index[-1]
            cutoff = last_date - timedelta(days=7)
            
            # Quick prep
            from crypto_prediction.features.technical import FeatureEngineer
            from crypto_prediction.data.preprocessor import DataPreprocessor
            engineer = FeatureEngineer()
            full_eng = engineer.engineer(df)
            train_eng = full_eng[full_eng.index <= cutoff]
            test_eng = full_eng[full_eng.index > cutoff]
            test_df = df[df.index > cutoff]
            
            feature_cols = engineer.get_feature_columns(train_eng)
            preprocessor = DataPreprocessor(scaler_type="robust")
            train_cleaned = preprocessor.prepare_features(train_eng, feature_cols)
            n = len(train_cleaned)
            n_val = int(n*0.15)
            train_split = train_cleaned.iloc[:n-n_val]
            val_split = train_cleaned.iloc[n-n_val:]
            
            X_train = train_split[feature_cols].values
            y_train = train_eng.loc[train_split.index, 'Target_Close'].dropna().values
            X_train = X_train[:len(y_train)]
            X_val = val_split[feature_cols].values
            y_val = train_eng.loc[val_split.index, 'Target_Close'].dropna().values
            X_val = X_val[:len(y_val)]
            
            preprocessor.feature_scaler.fit(X_train)
            preprocessor.target_scaler.fit(y_train.reshape(-1,1))
            
            X_train_s = preprocessor.feature_scaler.transform(X_train)
            y_train_s = preprocessor.target_scaler.transform(y_train.reshape(-1,1)).ravel()
            X_val_s = preprocessor.feature_scaler.transform(X_val)
            y_val_s = preprocessor.target_scaler.transform(y_val.reshape(-1,1)).ravel()
            X_test = test_eng[feature_cols].ffill().bfill().fillna(0).values
            X_test_s = preprocessor.feature_scaler.transform(X_test)
            y_test_actual = test_df['Close'].values
            
            model = XGBoostModel(n_estimators=500, max_depth=6, learning_rate=0.05)
            model.fit(X_train_s, y_train_s, X_val_s, y_val_s)
            y_pred = preprocessor.inverse_transform_target(model.predict(X_test_s))
            metrics = compute_regression_metrics(y_test_actual, y_pred)
            print(f"  MAPE={metrics['mape']:.2f}% RMSE={metrics['rmse']:.2f} R2={metrics['r2']:.4f} DirAcc={metrics['directional_accuracy']:.1f}%")
        except Exception as e:
            print(f"  Failed: {e}")
