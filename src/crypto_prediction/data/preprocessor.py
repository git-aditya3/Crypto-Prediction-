"""
Data preprocessing v3 Improved Accuracy
- RobustScaler for crypto outliers
- Outlier clipping
- Better sequence creation
- TimeSeriesSplit support
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
    def __init__(self, scaler_type: str = None):
        # Use RobustScaler by default for crypto (handles outliers better)
        if scaler_type is None:
            scaler_type = "robust" if config.training.use_robust_scaler else "standard"
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
        scaler_cls = scaler_map.get(self.scaler_type, RobustScaler)
        self.feature_scaler = scaler_cls()
        self.target_scaler = scaler_cls()
        logger.info(f"Using {self.scaler_type} scaler for preprocessing")

    def prepare_features(self, df: pd.DataFrame, feature_cols: List[str] = None) -> pd.DataFrame:
        """Clean and select features with outlier handling"""
        df = df.copy()
        
        initial_len = len(df)
        df = df.dropna(subset=['Close', 'Target_Close'])
        
        if feature_cols:
            self.feature_columns = feature_cols
        else:
            exclude = ['Target_Close', 'Target_Returns', 'Target_Log_Returns', 'Target_Direction']
            exclude += [c for c in df.columns if c.startswith('Target_Close_')]
            exclude += [c for c in df.columns if c.startswith('Target_Returns_')]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            self.feature_columns = [c for c in numeric_cols if c not in exclude and c not in ['Open','High','Low','Close','Volume']]
        
        # Forward/backward fill then 0
        df[self.feature_columns] = df[self.feature_columns].ffill().bfill().fillna(0)
        
        # Replace inf and clip extreme outliers (crypto has fat tails)
        df.replace([np.inf, -np.inf], 0, inplace=True)
        
        # Clip outliers at 1st and 99th percentile for each feature (robust)
        for col in self.feature_columns:
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                lower = df[col].quantile(0.01)
                upper = df[col].quantile(0.99)
                df[col] = df[col].clip(lower, upper)
        
        logger.info(f"Preprocessing v3: {initial_len} -> {len(df)} rows after cleaning. Features: {len(self.feature_columns)} | Scaler: {self.scaler_type}")
        return df

    def split(self, df: pd.DataFrame, test_size: float = None, val_size: float = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Time-series aware split - chronological"""
        test_size = test_size or config.data.test_size
        val_size = val_size or config.data.val_size
        
        n = len(df)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        n_train = n - n_test - n_val

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train:n_train+n_val].copy()
        test_df = df.iloc[n_train+n_val:].copy()

        logger.info(f"Split v3: train={len(train_df)} ({len(train_df)/n*100:.1f}%) val={len(val_df)} ({len(val_df)/n*100:.1f}%) test={len(test_df)} ({len(test_df)/n*100:.1f}%)")
        return train_df, val_df, test_df

    def split_with_gap(self, df: pd.DataFrame, test_size: float = None, val_size: float = None, gap: int = 7):
        """Split with gap to prevent leakage for time series (important for crypto)"""
        test_size = test_size or config.data.test_size
        val_size = val_size or config.data.val_size
        
        n = len(df)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        n_train = n - n_test - n_val - gap*2

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train+gap:n_train+gap+n_val].copy()
        test_df = df.iloc[n_train+gap*2+n_val:].copy()

        logger.info(f"Split with gap={gap}: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
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
        """Create sequences for LSTM/Transformer with improved handling"""
        seq_length = seq_length or config.data.sequence_length
        Xs, ys = [], []
        for i in range(len(X) - seq_length):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        Xs = np.array(Xs)
        ys = np.array(ys)
        
        # Log sequence stats
        logger.info(f"Created sequences: X {Xs.shape}, y {ys.shape} | seq_len {seq_length}")
        return Xs, ys

    def create_sequences_with_overlap(self, X: np.ndarray, y: np.ndarray, seq_length: int = None, stride: int = 1):
        """Create sequences with custom stride for data augmentation"""
        seq_length = seq_length or config.data.sequence_length
        Xs, ys = [], []
        for i in range(0, len(X) - seq_length, stride):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        return np.array(Xs), np.array(ys)

    def get_time_series_splits(self, X, y, n_splits=5):
        """Get TimeSeriesSplit for cross-validation"""
        tscv = TimeSeriesSplit(n_splits=n_splits)
        return tscv.split(X)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'feature_scaler': self.feature_scaler,
            'target_scaler': self.target_scaler,
            'feature_columns': self.feature_columns,
            'scaler_type': self.scaler_type
        }, path)
        logger.info(f"Saved preprocessor v3 to {path}")

    def load(self, path: str):
        data = joblib.load(path)
        self.feature_scaler = data['feature_scaler']
        self.target_scaler = data['target_scaler']
        self.feature_columns = data['feature_columns']
        self.scaler_type = data['scaler_type']
        logger.info(f"Loaded preprocessor v3 from {path}")
        return self
