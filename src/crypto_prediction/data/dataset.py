"""
High-level dataset pipeline v5 MAX - fetcher + feature engineering + preprocessing + caching + sentiment
- Unified pipeline with sentiment enrichment, Kalman smoothing, feature selection
- Thread-safe caching, versioning, metrics
"""
import pandas as pd
from typing import Tuple, Dict, Optional
from pathlib import Path
import threading
import time

from .fetcher import CryptoDataFetcher
from ..features.technical import FeatureEngineer
from .preprocessor import DataPreprocessor
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class CryptoDataset:
    def __init__(self, symbol: str = "BTC-USD", scaler_type: str = None, use_feature_selection: bool = None,
                 k_features: int = None):
        self.symbol = symbol
        self.fetcher = CryptoDataFetcher(symbol=symbol)
        self.engineer = FeatureEngineer()
        self.preprocessor = DataPreprocessor(
            scaler_type=scaler_type or ("robust" if config.training.use_robust_scaler else "standard"),
            use_feature_selection=use_feature_selection if use_feature_selection is not None else config.training.use_feature_selection,
            k_features=k_features or config.training.feature_selection_k
        )
        self.raw_df: Optional[pd.DataFrame] = None
        self.feature_df: Optional[pd.DataFrame] = None
        self.processed: Optional[Dict] = None
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_lock = threading.Lock()
        self._metrics = {
            "loads": 0,
            "feature_engineering_time": 0,
            "preprocessing_time": 0
        }

    def load(self, period: str = None, interval: str = None, force_refresh: bool = False) -> pd.DataFrame:
        period = period or config.data.period
        interval = interval or config.data.interval
        self.fetcher.period = period
        self.fetcher.interval = interval
        
        cache_key = f"{self.symbol}_{period}_{interval}"
        if not force_refresh:
            with self._cache_lock:
                if cache_key in self._cache:
                    cached = self._cache[cache_key]
                    if isinstance(cached, pd.DataFrame) and len(cached) > 100:
                        self.raw_df = cached.copy()
                        return self.raw_df
        
        start = time.time()
        self.raw_df = self.fetcher.load_or_fetch(symbol=self.symbol, force_refresh=force_refresh)
        elapsed = time.time() - start
        
        with self._cache_lock:
            self._cache[cache_key] = self.raw_df.copy()
        
        self._metrics["loads"] += 1
        logger.info(f"Dataset v5 load {self.symbol}: {len(self.raw_df)} rows in {elapsed:.2f}s | cache {cache_key}")
        return self.raw_df

    def engineer_features(self, df: pd.DataFrame = None, use_sentiment: bool = None) -> pd.DataFrame:
        df = df if df is not None else self.raw_df
        if df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        start = time.time()
        self.feature_df = self.engineer.engineer(df)
        
        # Sentiment enrichment if enabled
        if use_sentiment is None:
            use_sentiment = config.features.use_sentiment
        
        if use_sentiment:
            try:
                from ..features.sentiment import SentimentFeatureEngineer
                senti_eng = SentimentFeatureEngineer()
                self.feature_df = senti_eng.enrich_price_df(self.feature_df, symbol=self.symbol)
                logger.info(f"Dataset v5 sentiment enriched for {self.symbol}")
            except Exception as e:
                logger.debug(f"Sentiment enrich failed v5 for {self.symbol}: {e}")
        
        elapsed = time.time() - start
        self._metrics["feature_engineering_time"] = elapsed
        logger.info(f"Dataset v5 feature engineering {self.symbol}: {self.feature_df.shape[1]} features, {len(self.feature_df)} rows in {elapsed:.2f}s")
        return self.feature_df

    def prepare(self, df: pd.DataFrame = None, test_size: float = None, val_size: float = None, sequence_length: int = None):
        df = df if df is not None else self.feature_df
        if df is None:
            raise ValueError("No feature df. Call engineer_features() first.")

        start = time.time()
        cleaned = self.preprocessor.prepare_features(df, feature_cols=self.engineer.get_feature_columns(df))
        train_df, val_df, test_df = self.preprocessor.split(cleaned, test_size=test_size, val_size=val_size)
        
        scaled = self.preprocessor.fit_transform(train_df, val_df, test_df)

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
        elapsed = time.time() - start
        self._metrics["preprocessing_time"] = elapsed
        logger.info(f"Dataset v5 ready {self.symbol}: seq train {X_train_seq.shape}, val {X_val_seq.shape}, test {X_test_seq.shape} | selected feats {len(scaled['feature_columns'])} in {elapsed:.2f}s")
        return scaled

    def get_full_pipeline(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False, use_sentiment: bool = None):
        self.load(period=period, interval=interval, force_refresh=force_refresh)
        self.engineer_features(use_sentiment=use_sentiment)
        return self.prepare()

    def save_preprocessor(self, path: str = None, version: str = "v6"):
        if path is None:
            safe_sym = self.symbol.replace('-','_').replace('/','_')
            path = str(config.project_root / "models" / f"{safe_sym}_preprocessor_{version}.joblib")
        self.preprocessor.save(path)
        return path

    def get_metrics(self) -> Dict:
        return {
            **self._metrics,
            "symbol": self.symbol,
            "raw_rows": len(self.raw_df) if self.raw_df is not None else 0,
            "feature_rows": len(self.feature_df) if self.feature_df is not None else 0,
            "feature_cols": len(self.feature_df.columns) if self.feature_df is not None else 0,
            "selected_features": len(self.preprocessor.feature_columns) if self.preprocessor.feature_columns else 0,
            "version": "v5_max"
        }

    def validate(self) -> Dict:
        """Validate dataset integrity"""
        issues = []
        if self.raw_df is None or self.raw_df.empty:
            issues.append("raw_df empty")
        else:
            if self.raw_df['Close'].isna().sum() > 0:
                issues.append(f"Close has {self.raw_df['Close'].isna().sum()} NaNs")
            if (self.raw_df['Close'] <= 0).any():
                issues.append("Close has non-positive values")
            if len(self.raw_df) < 100:
                issues.append(f"Too few rows {len(self.raw_df)}")
        
        if self.feature_df is not None:
            if self.feature_df.isna().sum().sum() > len(self.feature_df) * len(self.feature_df.columns) * 0.1:
                issues.append("Too many NaNs in feature_df")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "symbol": self.symbol,
            "version": "v5_max"
        }
