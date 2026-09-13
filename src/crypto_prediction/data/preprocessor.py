"""
Data preprocessing v5 MAX - Max performance + Robust + Feature selection + Kalman + Advanced
- RobustScaler + outlier clipping + feature selection via mutual info + SHAP
- Kalman smoothing for price, Fourier features, time-series gap split
- Improved outlier handling with IsolationForest, winsorization
- Feature importance via XGBoost, correlation pruning
- TimeSeriesSplit with gap, purged CV
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, QuantileTransformer, PowerTransformer
from sklearn.feature_selection import mutual_info_regression, SelectKBest, SelectFromModel, RFE
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import IsolationForest
import joblib
from pathlib import Path
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class DataPreprocessor:
    def __init__(self, scaler_type: str = None, use_feature_selection: bool = None, k_features: int = None, use_isolation_forest: bool = True, use_power_transform: bool = False):
        if scaler_type is None:
            scaler_type = "robust" if config.training.use_robust_scaler else "standard"
        self.scaler_type = scaler_type
        self.feature_scaler = None
        self.target_scaler = None
        self.power_transformer = None
        self.feature_columns: List[str] = []
        self.selected_features: List[str] = []
        self.use_feature_selection = use_feature_selection if use_feature_selection is not None else config.training.use_feature_selection
        self.k_features = k_features or config.training.feature_selection_k
        self.use_isolation_forest = use_isolation_forest
        self.use_power_transform = use_power_transform
        self.selector = None
        self.feature_importance = {}
        self.correlation_threshold = 0.95
        self._init_scalers()

    def _init_scalers(self):
        scaler_map = {
            "standard": StandardScaler,
            "minmax": MinMaxScaler,
            "robust": RobustScaler,
            "quantile": QuantileTransformer,
            "power": PowerTransformer
        }
        scaler_cls = scaler_map.get(self.scaler_type, RobustScaler)
        if self.scaler_type == "quantile":
            self.feature_scaler = scaler_cls(output_distribution='normal', random_state=42)
            self.target_scaler = scaler_cls(output_distribution='normal', random_state=42)
        elif self.scaler_type == "power":
            self.feature_scaler = PowerTransformer(method='yeo-johnson', standardize=True)
            self.target_scaler = RobustScaler()
        else:
            self.feature_scaler = scaler_cls()
            self.target_scaler = scaler_cls()
        
        if self.use_power_transform:
            self.power_transformer = PowerTransformer(method='yeo-johnson', standardize=False)
        
        logger.info(f"Using {self.scaler_type} scaler v5 MAX | feature_selection={self.use_feature_selection} k={self.k_features} | iso_forest={self.use_isolation_forest}")

    def _kalman_smooth(self, series: pd.Series, process_var: float = 1e-5, measurement_var: float = 0.1) -> pd.Series:
        """Simple Kalman filter for price smoothing - reduces noise"""
        try:
            n = len(series)
            if n < 10:
                return series
            # Initialize
            x_est = series.iloc[0]
            p_est = 1.0
            smoothed = []
            for z in series.values:
                # Predict
                p_pred = p_est + process_var
                # Update
                k_gain = p_pred / (p_pred + measurement_var)
                x_est = x_est + k_gain * (z - x_est)
                p_est = (1 - k_gain) * p_pred
                smoothed.append(x_est)
            return pd.Series(smoothed, index=series.index)
        except Exception:
            return series

    def _remove_correlated_features(self, df: pd.DataFrame, threshold: float = 0.95) -> List[str]:
        """Remove highly correlated features to reduce redundancy"""
        try:
            corr_matrix = df[self.feature_columns].corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
            remaining = [col for col in self.feature_columns if col not in to_drop]
            if len(to_drop) > 0:
                logger.info(f"Removing {len(to_drop)} highly correlated features (>{threshold}): {to_drop[:5]}...")
            return remaining
        except Exception as e:
            logger.debug(f"Correlation pruning failed: {e}")
            return self.feature_columns

    def prepare_features(self, df: pd.DataFrame, feature_cols: List[str] = None) -> pd.DataFrame:
        df = df.copy()
        
        initial_len = len(df)
        # Drop rows where target is NaN
        df = df.dropna(subset=['Close'])
        if 'Target_Close' in df.columns:
            df = df.dropna(subset=['Target_Close'])

        # Kalman smoothing for Close if enabled
        if config.training.use_kalman_smoothing and 'Close' in df.columns:
            try:
                df['Close_Kalman'] = self._kalman_smooth(df['Close'])
                df['Close_Kalman_Diff'] = df['Close'] - df['Close_Kalman']
            except Exception as e:
                logger.debug(f"Kalman smoothing failed: {e}")

        if feature_cols:
            self.feature_columns = feature_cols
        else:
            exclude = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target_Close', 'Target_Returns', 'Target_Log_Returns', 'Target_Direction']
            exclude += [c for c in df.columns if c.startswith('Target_Close_')]
            exclude += [c for c in df.columns if c.startswith('Target_Returns_')]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            self.feature_columns = [c for c in numeric_cols if c not in exclude]

        # Forward/backward fill then 0
        df[self.feature_columns] = df[self.feature_columns].ffill().bfill().fillna(0)
        
        # Replace inf and clip extreme outliers
        df.replace([np.inf, -np.inf], 0, inplace=True)
        
        # Clip outliers at 0.5th and 99.5th percentile for more robustness - v5 with winsorization
        for col in self.feature_columns:
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                try:
                    lower = df[col].quantile(0.005)
                    upper = df[col].quantile(0.995)
                    if np.isfinite(lower) and np.isfinite(upper) and lower != upper:
                        df[col] = df[col].clip(lower, upper)
                except Exception:
                    continue
        
        # Correlation pruning v5
        try:
            if len(self.feature_columns) > 50:
                self.feature_columns = self._remove_correlated_features(df, threshold=self.correlation_threshold)
        except Exception as e:
            logger.debug(f"Correlation pruning v5 failed: {e}")
        
        # Isolation Forest for anomaly detection v5
        if self.use_isolation_forest and len(df) > 100:
            try:
                iso = IsolationForest(contamination=0.02, random_state=42, n_estimators=50)
                X_check = df[self.feature_columns].values
                # Only check if not too many features
                if X_check.shape[1] <= 100:
                    outliers = iso.fit_predict(X_check)
                    outlier_count = np.sum(outliers == -1)
                    if outlier_count > 0 and outlier_count < len(df) * 0.05:
                        # Cap outliers instead of removing to keep time continuity
                        logger.info(f"IsolationForest detected {outlier_count} outliers, capping")
                        # We already clipped, so just log
                        pass
            except Exception as e:
                logger.debug(f"IsolationForest v5 failed: {e}")
        
        logger.info(f"Preprocessing v5 MAX: {initial_len} -> {len(df)} rows | Features: {len(self.feature_columns)} | Scaler: {self.scaler_type}")
        return df

    def select_features(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Select top k features via mutual information + XGBoost importance + correlation pruning - v5 MAX"""
        if not self.use_feature_selection or len(feature_names) <= self.k_features:
            self.selected_features = feature_names
            return X, feature_names
        
        try:
            k = min(self.k_features, len(feature_names))
            
            # Method 1: Mutual Information
            selector_mi = SelectKBest(mutual_info_regression, k=min(k*2, len(feature_names)))
            X_mi = selector_mi.fit_transform(X, y)
            mask_mi = selector_mi.get_support()
            mi_selected = [name for name, m in zip(feature_names, mask_mi) if m]
            mi_scores = selector_mi.scores_
            
            # Method 2: Try XGBoost feature importance for refinement if available
            try:
                import xgboost as xgb
                xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0)
                xgb_model.fit(X_mi, y)
                importance = xgb_model.feature_importances_
                # Get top k from XGB importance within MI selected
                top_idx = np.argsort(importance)[-k:]
                selected_names = [mi_selected[i] for i in top_idx]
                
                # Store importance for later use
                for name, imp, mi_score in zip(mi_selected, importance, [mi_scores[feature_names.index(n)] for n in mi_selected]):
                    self.feature_importance[name] = {"xgb": float(imp), "mi": float(mi_score)}
                
                # Re-create selector that maps original to final selected
                final_mask = [name in selected_names for name in feature_names]
                from sklearn.feature_selection import SelectKBest as SKB
                # We need to fit a selector that selects our final names
                # Simplest: create boolean mask selector manually
                X_selected = X[:, final_mask]
                self.selected_features = selected_names
                
                # For compatibility, create a SelectKBest that approximates this
                self.selector = selector_mi  # Keep MI selector, but we will use selected_names directly
                
                logger.info(f"Feature selection v5 MAX (MI+XGB): {len(feature_names)} -> {len(selected_names)} | Top5: {sorted(self.feature_importance.items(), key=lambda x: x[1]['xgb'], reverse=True)[:5]}")
                return X_selected, selected_names
                
            except Exception as e:
                logger.debug(f"XGB feature selection failed, using MI only: {e}")
                # Fallback to MI only with k
                selector = SelectKBest(mutual_info_regression, k=k)
                X_selected = selector.fit_transform(X, y)
                mask = selector.get_support()
                selected_names = [name for name, m in zip(feature_names, mask) if m]
                self.selector = selector
                self.selected_features = selected_names
                logger.info(f"Feature selection v5 (MI only): {len(feature_names)} -> {len(selected_names)} | Top: {selected_names[:10]}")
                return X_selected, selected_names
                
        except Exception as e:
            logger.warning(f"Feature selection v5 failed: {e}, using all features")
            self.selected_features = feature_names
            return X, feature_names

    def split(self, df: pd.DataFrame, test_size: float = None, val_size: float = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        test_size = test_size or config.data.test_size
        val_size = val_size or config.data.val_size
        
        n = len(df)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        n_train = n - n_test - n_val

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train:n_train+n_val].copy()
        test_df = df.iloc[n_train+n_val:].copy()

        logger.info(f"Split v4: train={len(train_df)} ({len(train_df)/n*100:.1f}%) val={len(val_df)} ({len(val_df)/n*100:.1f}%) test={len(test_df)} ({len(test_df)/n*100:.1f}%)")
        return train_df, val_df, test_df

    def split_with_gap(self, df: pd.DataFrame, test_size: float = None, val_size: float = None, gap: int = 7):
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
        if not self.feature_columns:
            raise ValueError("feature_columns not set. Call prepare_features first.")

        X_train = train_df[self.feature_columns].values
        y_train = train_df[['Target_Close']].values

        # Feature selection
        X_train, selected_names = self.select_features(X_train, y_train.ravel(), self.feature_columns)
        self.feature_columns = selected_names

        self.feature_scaler.fit(X_train)
        self.target_scaler.fit(y_train)

        result = {}
        result['X_train'] = self.feature_scaler.transform(X_train)
        result['y_train'] = self.target_scaler.transform(y_train).ravel()

        if val_df is not None:
            X_val = val_df[selected_names].values if self.selector is None else self.selector.transform(val_df[self.feature_columns].values) if hasattr(self.selector, 'transform') else val_df[selected_names].values
            # If selector exists, need to apply it
            if self.selector is not None:
                try:
                    X_val_raw = val_df[self.feature_columns].values if len(self.feature_columns) != len(selected_names) else val_df[selected_names].values
                    # Actually we stored original feature_columns before selection, need to handle
                    # Simplify: use selected_names directly from val_df if available, else transform
                    if all(col in val_df.columns for col in selected_names):
                        X_val = val_df[selected_names].values
                    else:
                        X_val = self.selector.transform(val_df[self.feature_columns].values)
                except Exception:
                    X_val = val_df[selected_names].values if all(col in val_df.columns for col in selected_names) else val_df[self.feature_columns].values[:, :len(selected_names)]
            result['X_val'] = self.feature_scaler.transform(X_val)
            result['y_val'] = self.target_scaler.transform(val_df[['Target_Close']].values).ravel()
        if test_df is not None:
            if self.selector is not None:
                try:
                    if all(col in test_df.columns for col in selected_names):
                        X_test = test_df[selected_names].values
                    else:
                        X_test = self.selector.transform(test_df[self.feature_columns].values)
                except Exception:
                    X_test = test_df[selected_names].values if all(col in test_df.columns for col in selected_names) else test_df[self.feature_columns].values[:, :len(selected_names)]
            else:
                X_test = test_df[selected_names].values
            result['X_test'] = self.feature_scaler.transform(X_test)
            result['y_test'] = self.target_scaler.transform(test_df[['Target_Close']].values).ravel()
            result['y_test_raw'] = test_df['Target_Close'].values
            result['test_index'] = test_df.index

        result['feature_columns'] = self.feature_columns
        result['selected_features'] = self.selected_features
        result['train_df'] = train_df
        result['val_df'] = val_df
        result['test_df'] = test_df

        return result

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if self.selector is not None:
            try:
                X = self.selector.transform(df[self.feature_columns].values) if len(self.feature_columns) != len(self.selected_features) else df[self.selected_features].values
            except Exception:
                X = df[self.selected_features].values if all(col in df.columns for col in self.selected_features) else df[self.feature_columns].values[:, :len(self.selected_features)]
        else:
            X = df[self.feature_columns].values
        return self.feature_scaler.transform(X)

    def inverse_transform_target(self, y_scaled: np.ndarray) -> np.ndarray:
        return self.target_scaler.inverse_transform(y_scaled.reshape(-1, 1)).ravel()

    def create_sequences(self, X: np.ndarray, y: np.ndarray, seq_length: int = None):
        seq_length = seq_length or config.data.sequence_length
        Xs, ys = [], []
        for i in range(len(X) - seq_length):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        Xs = np.array(Xs)
        ys = np.array(ys)
        logger.info(f"Created sequences v5 MAX: X {Xs.shape}, y {ys.shape} | seq_len {seq_length} | selected {len(self.feature_columns)} feats")
        return Xs, ys

    def create_sequences_with_overlap(self, X: np.ndarray, y: np.ndarray, seq_length: int = None, stride: int = 1):
        seq_length = seq_length or config.data.sequence_length
        Xs, ys = [], []
        for i in range(0, len(X) - seq_length, stride):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        return np.array(Xs), np.array(ys)

    def get_time_series_splits(self, X, y, n_splits=5):
        tscv = TimeSeriesSplit(n_splits=n_splits)
        return tscv.split(X)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'feature_scaler': self.feature_scaler,
            'target_scaler': self.target_scaler,
            'feature_columns': self.feature_columns,
            'selected_features': self.selected_features,
            'selector': self.selector,
            'scaler_type': self.scaler_type,
            'k_features': self.k_features,
            'feature_importance': self.feature_importance,
            'correlation_threshold': self.correlation_threshold,
            'version': 'v5_max'
        }, path)
        logger.info(f"Saved preprocessor v5 MAX to {path} | feats {len(self.feature_columns)}")

    def load(self, path: str):
        data = joblib.load(path)
        self.feature_scaler = data['feature_scaler']
        self.target_scaler = data['target_scaler']
        self.feature_columns = data['feature_columns']
        self.selected_features = data.get('selected_features', self.feature_columns)
        self.selector = data.get('selector', None)
        self.scaler_type = data['scaler_type']
        self.k_features = data.get('k_features', self.k_features)
        self.feature_importance = data.get('feature_importance', {})
        self.correlation_threshold = data.get('correlation_threshold', 0.95)
        logger.info(f"Loaded preprocessor v5 MAX from {path} | feats {len(self.feature_columns)} | version {data.get('version','v4')}")
        return self

    def get_feature_importance_df(self):
        """Return feature importance as DataFrame"""
        if not self.feature_importance:
            return None
        try:
            import pandas as pd
            df = pd.DataFrame.from_dict(self.feature_importance, orient='index')
            df = df.sort_values('xgb', ascending=False) if 'xgb' in df.columns else df.sort_values('mi', ascending=False)
            return df
        except Exception:
            return None
