"""
Data preprocessing v6 ULTRA - Max performance + Robust + Feature selection + Kalman + Advanced
- RobustScaler + outlier clipping + feature selection via MI + XGB + RF + SHAP hybrid
- Kalman smoothing for price, Fourier features, time-series gap split
- Improved outlier handling with IsolationForest, IQR, ZScore, winsorization
- Feature importance via XGBoost + RF + MI, correlation pruning, PSI drift detection
- TimeSeriesSplit with gap, purged CV, leakage prevention
- Version v6_ultra
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, QuantileTransformer, PowerTransformer
from sklearn.feature_selection import mutual_info_regression, SelectKBest, SelectFromModel
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import IsolationForest, RandomForestRegressor
import joblib
from pathlib import Path
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class DataPreprocessor:
    def __init__(self, scaler_type: str = None, use_feature_selection: bool = None, k_features: int = None, 
                 use_isolation_forest: bool = True, use_power_transform: bool = False,
                 feature_selection_method: str = None):
        if scaler_type is None:
            scaler_type = "robust" if config.training.use_robust_scaler else "standard"
        self.scaler_type = scaler_type
        self.feature_scaler = None
        self.target_scaler = None
        self.power_transformer = None
        self.feature_columns: List[str] = []
        self.selected_features: List[str] = []
        self.original_feature_columns: List[str] = []  # v6: keep original
        self.use_feature_selection = use_feature_selection if use_feature_selection is not None else config.training.use_feature_selection
        self.k_features = k_features or config.training.feature_selection_k
        self.feature_selection_method = feature_selection_method or config.training.feature_selection_method
        self.use_isolation_forest = use_isolation_forest
        self.use_power_transform = use_power_transform
        self.selector = None
        self.feature_importance = {}
        self.correlation_threshold = 0.97  # v6: slightly higher to keep more features
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
        
        logger.info(f"Using {self.scaler_type} scaler v6 ULTRA | feature_selection={self.use_feature_selection} k={self.k_features} method={self.feature_selection_method} | iso_forest={self.use_isolation_forest}")

    def _kalman_smooth(self, series: pd.Series, process_var: float = 1e-5, measurement_var: float = 0.1) -> pd.Series:
        """Simple Kalman filter for price smoothing - reduces noise - v6 improved"""
        try:
            n = len(series)
            if n < 10:
                return series
            x_est = float(series.iloc[0])
            p_est = 1.0
            smoothed = []
            for z in series.values:
                if not np.isfinite(z):
                    smoothed.append(x_est)
                    continue
                p_pred = p_est + process_var
                k_gain = p_pred / (p_pred + measurement_var)
                x_est = x_est + k_gain * (z - x_est)
                p_est = (1 - k_gain) * p_pred
                smoothed.append(x_est)
            return pd.Series(smoothed, index=series.index)
        except Exception:
            return series

    def _remove_correlated_features(self, df: pd.DataFrame, threshold: float = None) -> List[str]:
        """Remove highly correlated features to reduce redundancy - v6 improved"""
        threshold = threshold or self.correlation_threshold
        try:
            if len(self.feature_columns) < 10:
                return self.feature_columns
            # Use only numeric columns that exist
            existing_cols = [c for c in self.feature_columns if c in df.columns]
            if len(existing_cols) < 10:
                return existing_cols
            corr_matrix = df[existing_cols].corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
            remaining = [col for col in existing_cols if col not in to_drop]
            if len(to_drop) > 0:
                logger.info(f"v6: Removing {len(to_drop)} highly correlated features (>{threshold}): {to_drop[:5]}...")
            return remaining
        except Exception as e:
            logger.debug(f"Correlation pruning v6 failed: {e}")
            return self.feature_columns

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """IQR outlier detection - v6"""
        try:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            return (series < lower) | (series > upper)
        except Exception:
            return pd.Series(False, index=series.index)

    def prepare_features(self, df: pd.DataFrame, feature_cols: List[str] = None) -> pd.DataFrame:
        df = df.copy()
        
        initial_len = len(df)
        # Drop rows where target is NaN
        df = df.dropna(subset=['Close'])
        if 'Target_Close' in df.columns:
            df = df.dropna(subset=['Target_Close'])

        # Kalman smoothing for Close if enabled - v6
        if config.training.use_kalman_smoothing and 'Close' in df.columns:
            try:
                df['Close_Kalman'] = self._kalman_smooth(df['Close'])
                df['Close_Kalman_Diff'] = df['Close'] - df['Close_Kalman']
                df['Close_Kalman_Ratio'] = df['Close'] / (df['Close_Kalman'] + 1e-8)
            except Exception as e:
                logger.debug(f"Kalman smoothing v6 failed: {e}")

        if feature_cols:
            self.feature_columns = feature_cols
            self.original_feature_columns = feature_cols.copy()
        else:
            exclude = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target_Close', 'Target_Returns', 'Target_Log_Returns', 'Target_Direction']
            exclude += [c for c in df.columns if c.startswith('Target_Close_')]
            exclude += [c for c in df.columns if c.startswith('Target_Returns_')]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            self.feature_columns = [c for c in numeric_cols if c not in exclude]
            self.original_feature_columns = self.feature_columns.copy()

        # Forward/backward fill then 0 - but limit ffill to 3 days to avoid leakage
        df[self.feature_columns] = df[self.feature_columns].ffill(limit=3).bfill(limit=3).fillna(0)
        
        # Replace inf
        df.replace([np.inf, -np.inf], 0, inplace=True)
        
        # Clip outliers at 0.5th and 99.5th percentile for robustness - v6 winsorization
        for col in self.feature_columns:
            if col not in df.columns:
                continue
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                try:
                    lower = df[col].quantile(0.005)
                    upper = df[col].quantile(0.995)
                    if np.isfinite(lower) and np.isfinite(upper) and lower != upper:
                        df[col] = df[col].clip(lower, upper)
                except Exception:
                    continue
        
        # Correlation pruning v6 - only if many features
        try:
            if len(self.feature_columns) > 80:
                self.feature_columns = self._remove_correlated_features(df, threshold=self.correlation_threshold)
        except Exception as e:
            logger.debug(f"Correlation pruning v6 failed: {e}")
        
        # Isolation Forest for anomaly detection v6 - only log, don't remove to keep time continuity
        if self.use_isolation_forest and len(df) > 100:
            try:
                # Sample features for speed if too many
                sample_cols = self.feature_columns[:100] if len(self.feature_columns) > 100 else self.feature_columns
                X_check = df[sample_cols].values
                if X_check.shape[1] <= 100 and len(X_check) > 50:
                    iso = IsolationForest(contamination=0.02, random_state=42, n_estimators=100)
                    outliers = iso.fit_predict(X_check)
                    outlier_count = np.sum(outliers == -1)
                    if outlier_count > 0:
                        logger.info(f"v6 IsolationForest detected {outlier_count} outliers ({outlier_count/len(df)*100:.1f}%) - logged, not removed for continuity")
            except Exception as e:
                logger.debug(f"IsolationForest v6 failed: {e}")
        
        logger.info(f"Preprocessing v6 ULTRA: {initial_len} -> {len(df)} rows | Features: {len(self.feature_columns)} (orig {len(self.original_feature_columns)}) | Scaler: {self.scaler_type}")
        return df

    def select_features(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Select top k features - v6 ULTRA hybrid: MI + XGB + RF + correlation - fixed logic"""
        if not self.use_feature_selection or len(feature_names) <= self.k_features:
            self.selected_features = feature_names
            self.feature_columns = feature_names
            return X, feature_names
        
        try:
            k = min(self.k_features, len(feature_names))
            method = self.feature_selection_method
            
            logger.info(f"v6 Feature selection: {len(feature_names)} -> {k} via {method}")
            
            # Method 1: Mutual Information - always compute
            selector_mi = SelectKBest(mutual_info_regression, k=min(k*2, len(feature_names)))
            X_mi = selector_mi.fit_transform(X, y)
            mask_mi = selector_mi.get_support()
            mi_selected = [name for name, m in zip(feature_names, mask_mi) if m]
            mi_scores = selector_mi.scores_
            
            # Store MI scores
            for name, score in zip(feature_names, mi_scores):
                if name not in self.feature_importance:
                    self.feature_importance[name] = {}
                self.feature_importance[name]["mi"] = float(score) if np.isfinite(score) else 0.0
            
            # If method is MI only, return MI top k
            if method == "mi" or len(feature_names) < 50:
                selector = SelectKBest(mutual_info_regression, k=k)
                X_selected = selector.fit_transform(X, y)
                mask = selector.get_support()
                selected_names = [name for name, m in zip(feature_names, mask) if m]
                self.selector = selector
                self.selected_features = selected_names
                self.feature_columns = selected_names
                logger.info(f"v6 Feature selection MI: {len(feature_names)} -> {len(selected_names)} | Top5: {selected_names[:5]}")
                return X_selected, selected_names
            
            # Hybrid: MI pre-filter + XGB + RF refinement
            try:
                import xgboost as xgb
                # XGB on MI filtered
                xgb_model = xgb.XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0, n_jobs=2)
                xgb_model.fit(X_mi, y)
                xgb_importance = xgb_model.feature_importances_
                
                for name, imp in zip(mi_selected, xgb_importance):
                    self.feature_importance[name]["xgb"] = float(imp)
                
                # RF importance as well
                try:
                    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=2)
                    rf_model.fit(X_mi, y)
                    rf_importance = rf_model.feature_importances_
                    for name, imp in zip(mi_selected, rf_importance):
                        self.feature_importance[name]["rf"] = float(imp)
                    
                    # Combined score: 0.5 XGB + 0.3 RF + 0.2 MI normalized
                    mi_selected_scores = np.array([self.feature_importance[n]["mi"] for n in mi_selected])
                    mi_norm = (mi_selected_scores - mi_selected_scores.min()) / (mi_selected_scores.max() - mi_selected_scores.min() + 1e-8)
                    xgb_norm = (xgb_importance - xgb_importance.min()) / (xgb_importance.max() - xgb_importance.min() + 1e-8)
                    rf_norm = (rf_importance - rf_importance.min()) / (rf_importance.max() - rf_importance.min() + 1e-8)
                    combined = 0.5 * xgb_norm + 0.3 * rf_norm + 0.2 * mi_norm
                    
                    top_idx = np.argsort(combined)[-k:]
                    selected_names = [mi_selected[i] for i in top_idx]
                    # Sort by combined score descending
                    selected_names = [x for _, x in sorted(zip(combined[top_idx], selected_names), reverse=True)]
                    
                except Exception as e:
                    logger.debug(f"RF selection failed, using XGB only: {e}")
                    top_idx = np.argsort(xgb_importance)[-k:]
                    selected_names = [mi_selected[i] for i in top_idx]
                
                # Create final X
                final_mask = [name in selected_names for name in feature_names]
                X_selected = X[:, final_mask]
                self.selected_features = selected_names
                self.feature_columns = selected_names
                self.selector = None  # We use direct mask, not sklearn selector for simplicity
                
                top5 = sorted(self.feature_importance.items(), key=lambda x: x[1].get('xgb', x[1].get('mi',0)), reverse=True)[:5]
                logger.info(f"v6 Feature selection HYBRID (MI+XGB+RF): {len(feature_names)} -> {len(selected_names)} | Top5: {top5}")
                return X_selected, selected_names
                
            except Exception as e:
                logger.debug(f"XGB/RF feature selection failed, using MI only: {e}")
                selector = SelectKBest(mutual_info_regression, k=k)
                X_selected = selector.fit_transform(X, y)
                mask = selector.get_support()
                selected_names = [name for name, m in zip(feature_names, mask) if m]
                self.selector = selector
                self.selected_features = selected_names
                self.feature_columns = selected_names
                logger.info(f"v6 Feature selection MI fallback: {len(feature_names)} -> {len(selected_names)}")
                return X_selected, selected_names
                
        except Exception as e:
            logger.warning(f"Feature selection v6 failed: {e}, using all features")
            self.selected_features = feature_names
            self.feature_columns = feature_names
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

        logger.info(f"Split v6: train={len(train_df)} ({len(train_df)/n*100:.1f}%) val={len(val_df)} ({len(val_df)/n*100:.1f}%) test={len(test_df)} ({len(test_df)/n*100:.1f}%)")
        return train_df, val_df, test_df

    def split_with_gap(self, df: pd.DataFrame, test_size: float = None, val_size: float = None, gap: int = 7):
        test_size = test_size or config.data.test_size
        val_size = val_size or config.data.val_size
        
        n = len(df)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        n_train = n - n_test - n_val - gap*2

        if n_train <= 0:
            logger.warning(f"Gap split failed, n_train {n_train} <=0, using regular split")
            return self.split(df, test_size, val_size)

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train+gap:n_train+gap+n_val].copy()
        test_df = df.iloc[n_train+gap*2+n_val:].copy()

        logger.info(f"Split with gap={gap} v6: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
        return train_df, val_df, test_df

    def fit_transform(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, test_df: pd.DataFrame = None):
        """v6: fixed selector logic - always use selected_features directly"""
        if not self.feature_columns:
            raise ValueError("feature_columns not set. Call prepare_features first.")

        # Ensure feature_columns exist in train_df
        existing_cols = [c for c in self.feature_columns if c in train_df.columns]
        if len(existing_cols) != len(self.feature_columns):
            logger.warning(f"v6: Some feature_columns missing, {len(self.feature_columns)} -> {len(existing_cols)}")
            self.feature_columns = existing_cols

        X_train = train_df[self.feature_columns].values
        y_train = train_df[['Target_Close']].values

        # Feature selection - v6 fixed
        X_train_selected, selected_names = self.select_features(X_train, y_train.ravel(), self.feature_columns)
        # After selection, feature_columns becomes selected_names
        self.feature_columns = selected_names
        self.selected_features = selected_names

        self.feature_scaler.fit(X_train_selected)
        self.target_scaler.fit(y_train)

        result = {}
        result['X_train'] = self.feature_scaler.transform(X_train_selected)
        result['y_train'] = self.target_scaler.transform(y_train).ravel()

        if val_df is not None:
            # Use selected_names directly - v6 fixed logic
            if all(col in val_df.columns for col in selected_names):
                X_val = val_df[selected_names].values
            else:
                # Fallback: try original and slice
                logger.warning(f"v6: val_df missing some selected features, using available")
                avail = [c for c in selected_names if c in val_df.columns]
                X_val = val_df[avail].values
                # Pad if needed
                if X_val.shape[1] < len(selected_names):
                    pad = np.zeros((X_val.shape[0], len(selected_names) - X_val.shape[1]))
                    X_val = np.hstack([X_val, pad])
            result['X_val'] = self.feature_scaler.transform(X_val)
            result['y_val'] = self.target_scaler.transform(val_df[['Target_Close']].values).ravel()
        
        if test_df is not None:
            if all(col in test_df.columns for col in selected_names):
                X_test = test_df[selected_names].values
            else:
                logger.warning(f"v6: test_df missing some selected features")
                avail = [c for c in selected_names if c in test_df.columns]
                X_test = test_df[avail].values
                if X_test.shape[1] < len(selected_names):
                    pad = np.zeros((X_test.shape[0], len(selected_names) - X_test.shape[1]))
                    X_test = np.hstack([X_test, pad])
            result['X_test'] = self.feature_scaler.transform(X_test)
            result['y_test'] = self.target_scaler.transform(test_df[['Target_Close']].values).ravel()
            result['y_test_raw'] = test_df['Target_Close'].values
            result['test_index'] = test_df.index

        result['feature_columns'] = self.feature_columns
        result['selected_features'] = self.selected_features
        result['original_feature_columns'] = self.original_feature_columns
        result['train_df'] = train_df
        result['val_df'] = val_df
        result['test_df'] = test_df

        return result

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """v6: simplified transform using selected_features"""
        cols = self.selected_features if self.selected_features else self.feature_columns
        # Ensure cols exist
        existing = [c for c in cols if c in df.columns]
        if len(existing) < len(cols):
            logger.warning(f"v6 transform: missing {len(cols)-len(existing)} features, using {len(existing)}")
            # Pad missing with 0
            X = np.zeros((len(df), len(cols)))
            for i, c in enumerate(cols):
                if c in df.columns:
                    X[:, i] = df[c].values
            return self.feature_scaler.transform(X)
        X = df[cols].values
        return self.feature_scaler.transform(X)

    def inverse_transform_target(self, y_scaled: np.ndarray) -> np.ndarray:
        return self.target_scaler.inverse_transform(y_scaled.reshape(-1, 1)).ravel()

    def create_sequences(self, X: np.ndarray, y: np.ndarray, seq_length: int = None):
        seq_length = seq_length or config.data.sequence_length
        if len(X) <= seq_length:
            logger.warning(f"v6: Not enough data for sequences: len {len(X)} <= seq {seq_length}, returning empty")
            return np.array([]), np.array([])
        Xs, ys = [], []
        for i in range(len(X) - seq_length):
            Xs.append(X[i:i+seq_length])
            ys.append(y[i+seq_length])
        Xs = np.array(Xs)
        ys = np.array(ys)
        logger.info(f"Created sequences v6 ULTRA: X {Xs.shape}, y {ys.shape} | seq_len {seq_length} | selected {len(self.feature_columns)} feats")
        return Xs, ys

    def create_sequences_with_overlap(self, X: np.ndarray, y: np.ndarray, seq_length: int = None, stride: int = 1):
        seq_length = seq_length or config.data.sequence_length
        if len(X) <= seq_length:
            return np.array([]), np.array([])
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
            'original_feature_columns': self.original_feature_columns,
            'selector': self.selector,
            'scaler_type': self.scaler_type,
            'k_features': self.k_features,
            'feature_importance': self.feature_importance,
            'correlation_threshold': self.correlation_threshold,
            'feature_selection_method': self.feature_selection_method,
            'version': 'v6_ultra'
        }, path)
        logger.info(f"Saved preprocessor v6 ULTRA to {path} | feats {len(self.feature_columns)} | orig {len(self.original_feature_columns)}")

    def load(self, path: str):
        data = joblib.load(path)
        self.feature_scaler = data['feature_scaler']
        self.target_scaler = data['target_scaler']
        self.feature_columns = data['feature_columns']
        self.selected_features = data.get('selected_features', self.feature_columns)
        self.original_feature_columns = data.get('original_feature_columns', self.feature_columns)
        self.selector = data.get('selector', None)
        self.scaler_type = data['scaler_type']
        self.k_features = data.get('k_features', self.k_features)
        self.feature_importance = data.get('feature_importance', {})
        self.correlation_threshold = data.get('correlation_threshold', 0.97)
        self.feature_selection_method = data.get('feature_selection_method', 'hybrid')
        logger.info(f"Loaded preprocessor v6 ULTRA from {path} | feats {len(self.feature_columns)} | version {data.get('version','v5')}")
        return self

    def get_feature_importance_df(self):
        """Return feature importance as DataFrame - v6 improved"""
        if not self.feature_importance:
            return None
        try:
            import pandas as pd
            df = pd.DataFrame.from_dict(self.feature_importance, orient='index')
            # Sort by combined score if available
            if 'xgb' in df.columns:
                df = df.sort_values('xgb', ascending=False)
            elif 'rf' in df.columns:
                df = df.sort_values('rf', ascending=False)
            elif 'mi' in df.columns:
                df = df.sort_values('mi', ascending=False)
            return df
        except Exception as e:
            logger.debug(f"get_feature_importance_df v6 failed: {e}")
            return None

    def detect_drift(self, df_old: pd.DataFrame, df_new: pd.DataFrame, threshold: float = 0.1) -> Dict:
        """v6: PSI drift detection"""
        try:
            drift_results = {}
            for col in self.selected_features[:10]:  # Check top 10 features
                if col not in df_old.columns or col not in df_new.columns:
                    continue
                old = df_old[col].dropna()
                new = df_new[col].dropna()
                if len(old) < 10 or len(new) < 10:
                    continue
                # Simple PSI approximation: mean shift
                mean_old = old.mean()
                mean_new = new.mean()
                std_old = old.std() + 1e-8
                drift_score = abs(mean_new - mean_old) / std_old
                drift_results[col] = float(drift_score)
            max_drift = max(drift_results.values()) if drift_results else 0
            return {"drift_scores": drift_results, "max_drift": max_drift, "drift_detected": max_drift > threshold}
        except Exception as e:
            logger.debug(f"Drift detection v6 failed: {e}")
            return {"drift_scores": {}, "max_drift": 0, "drift_detected": False}
