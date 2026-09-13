"""
High-level dataset pipeline combining fetcher + feature engineering + preprocessing
"""
import pandas as pd
from typing import Tuple, Dict, Optional
from .fetcher import CryptoDataFetcher
from ..features.technical import FeatureEngineer
from .preprocessor import DataPreprocessor
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CryptoDataset:
    def __init__(self, symbol: str = "BTC-USD", scaler_type: str = "standard"):
        self.symbol = symbol
        self.fetcher = CryptoDataFetcher(symbol=symbol)
        self.engineer = FeatureEngineer()
        self.preprocessor = DataPreprocessor(scaler_type=scaler_type)
        self.raw_df: Optional[pd.DataFrame] = None
        self.feature_df: Optional[pd.DataFrame] = None
        self.processed: Optional[Dict] = None

    def load(self, period: str = None, interval: str = None, force_refresh: bool = False) -> pd.DataFrame:
        period = period or config.data.period
        interval = interval or config.data.interval
        self.fetcher.period = period
        self.fetcher.interval = interval
        self.raw_df = self.fetcher.load_or_fetch(symbol=self.symbol, force_refresh=force_refresh)
        return self.raw_df

    def engineer_features(self, df: pd.DataFrame = None) -> pd.DataFrame:
        df = df if df is not None else self.raw_df
        if df is None:
            raise ValueError("No data loaded. Call load() first.")
        self.feature_df = self.engineer.engineer(df)
        return self.feature_df

    def prepare(self, df: pd.DataFrame = None, test_size: float = None, val_size: float = None, sequence_length: int = None):
        df = df if df is not None else self.feature_df
        if df is None:
            raise ValueError("No feature df. Call engineer_features() first.")

        # Clean and select features
        cleaned = self.preprocessor.prepare_features(df, feature_cols=self.engineer.get_feature_columns(df))
        train_df, val_df, test_df = self.preprocessor.split(cleaned, test_size=test_size, val_size=val_size)
        
        # Scale
        scaled = self.preprocessor.fit_transform(train_df, val_df, test_df)

        # Sequences for LSTM
        seq_len = sequence_length or config.data.sequence_length
        X_train_seq, y_train_seq = self.preprocessor.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
        X_val_seq, y_val_seq = self.preprocessor.create_sequences(scaled['X_val'], scaled['y_val'], seq_len)
        X_test_seq, y_test_seq = self.preprocessor.create_sequences(scaled['X_test'], scaled['y_test'], seq_len)

        scaled['X_train_seq'] = X_train_seq
        scaled['y_train_seq'] = y_train_seq
        scaled['X_val_seq'] = X_val_seq
        scaled['y_val_seq'] = y_val_seq
        scaled['X_test_seq'] = X_test_seq
        scaled['y_test_seq'] = y_test_seq

        self.processed = scaled
        logger.info(f"Dataset ready: seq train {X_train_seq.shape}, val {X_val_seq.shape}, test {X_test_seq.shape}")
        return scaled

    def get_full_pipeline(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False):
        self.load(period=period, interval=interval, force_refresh=force_refresh)
        self.engineer_features()
        return self.prepare()

    def save_preprocessor(self, path: str = None):
        if path is None:
            path = str(config.project_root / "models" / f"{self.symbol.replace('-','_')}_preprocessor.joblib")
        self.preprocessor.save(path)
        return path
