"""
Data preprocessing, scaling, and train/val/test splitting
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
import joblib
from pathlib import Path
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class DataPreprocessor:
    def __init__(self, scaler_type: str = "standard"):
        self.scaler_type = scaler_type
        self.feature_scaler = None
        self.target_scaler = None
        self.feature_columns: List[str] = []
        self._init_scalers()

    def _init_scalers(self):
        scaler_map = {
            "standard": StandardScaler,
            "minmax": MinMaxScaler,
            "robust": RobustScaler
        }
        scaler_cls = scaler_map.get(self.scaler_type, StandardScaler)
        self.feature_scaler = scaler_cls()
        self.target_scaler = scaler_cls()

    def prepare_features(self, df: pd.DataFrame, feature_cols: List[str] = None) -> pd.DataFrame:
        """Clean and select features"""
        df = df.copy()
        
        # Drop rows with too many NaNs (from rolling windows)
        # Keep only rows where at least 70% of features are present before final drop
        initial_len = len(df)
        df = df.dropna(subset=['Close', 'Target_Close'])
        
        if feature_cols:
            self.feature_columns = feature_cols
        else:
            # Auto-detect numeric feature columns
            exclude = ['Target_Close', 'Target_Returns', 'Target_Direction']
            exclude += [c for c in df.columns if c.startswith('Target_Close_')]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            self.feature_columns = [c for c in numeric_cols if c not in exclude and c not in ['Open','High','Low','Close','Volume']]
        
        # For remaining NaNs in features, forward fill then backward fill, then 0
        df[self.feature_columns] = df[self.feature_columns].ffill().bfill().fillna(0)
        
        # Replace inf
        df.replace([np.inf, -np.inf], 0, inplace=True)
        
        logger.info(f"Preprocessing: {initial_len} -> {len(df)} rows after cleaning. Features: {len(self.feature_columns)}")
        return df

    def split(self, df: pd.DataFrame, test_size: float = None, val_size: float = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Time-series aware split"""
        test_size = test_size or config.data.test_size
        val_size = val_size or config.data.val_size
        
        n = len(df)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        n_train = n - n_test - n_val

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train:n_train+n_val].copy()
        test_df = df.iloc[n_train+n_val:].copy()

        logger.info(f"Split: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
        return train_df, val_df, test_df

    def fit_transform(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, test_df: pd.DataFrame = None):
        """Fit scalers on train and transform all"""
        if not self.feature_columns:
            raise ValueError("feature_columns not set. Call prepare_features first.")

        X_train = train_df[self.feature_columns].values
        y_train = train_df[['Target_Close']].values

        self.feature_scaler.fit(X_train)
        self.target_scaler.fit(y_train)

        result = {}
        result['X_train'] = self.feature_scaler.transform(X_train)
        result['y_train'] = self.target_scaler.transform(y_train).ravel()

        if val_df is not None:
            result['X_val'] = self.feature_scaler.transform(val_df[self.feature_columns].values)
            result['y_val'] = self.target_scaler.transform(val_df[['Target_Close']].values).ravel()
        if test_df is not None:
            result['X_test'] = self.feature_scaler.transform(test_df[self.feature_columns].values)
            result['y_test'] = self.target_scaler.transform(test_df[['Target_Close']].values).ravel()
            result['y_test_raw'] = test_df['Target_Close'].values
            result['test_index'] = test_df.index

        # Keep raw for inverse transform
        result['feature_columns'] = self.feature_columns
        result['train_df'] = train_df
        result['val_df'] = val_df
        result['test_df'] = test_df

        return result

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.feature_scaler.transform(df[self.feature_columns].values)

    def inverse_transform_target(self, y_scaled: np.ndarray) -> np.ndarray:
        return self.target_scaler.inverse_transform(y_scaled.reshape(-1, 1)).ravel()

    def create_sequences(self, X: np.ndarray, y: np.ndarray, seq_length: int = None):
        """Create sequences for LSTM: (samples, seq_len, features)"""
        seq_length = seq_length or config.data.sequence_length
        Xs, ys = [], []
        for i in range(len(X) - seq_length):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        return np.array(Xs), np.array(ys)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'feature_scaler': self.feature_scaler,
            'target_scaler': self.target_scaler,
            'feature_columns': self.feature_columns,
            'scaler_type': self.scaler_type
        }, path)
        logger.info(f"Saved preprocessor to {path}")

    def load(self, path: str):
        data = joblib.load(path)
        self.feature_scaler = data['feature_scaler']
        self.target_scaler = data['target_scaler']
        self.feature_columns = data['feature_columns']
        self.scaler_type = data['scaler_type']
        logger.info(f"Loaded preprocessor from {path}")
        return self
