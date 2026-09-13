"""
Training pipeline orchestrator v5 MAX - Transformer + LSTM + GRU + XGB + ARIMA + Ensemble + Sentiment
- Full pipeline with feature selection, Kalman smoothing, metrics v5, model registry, checkpointing
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import time

from ..data.dataset import CryptoDataset
from ..models.lstm_model import LSTMModel
from ..models.transformer_model import TransformerModel
from ..models.xgboost_model import XGBoostModel
from ..models.arima_model import ARIMAModel
from ..models.ensemble import EnsembleModel
from ..evaluation.metrics import compute_regression_metrics, generate_report, compare_models
from ..config import get_config
from ..utils.logger import get_logger
from ..features.sentiment import SentimentFeatureEngineer

try:
    from ..models.gru_model import GRUModel
    HAS_GRU = True
except Exception:
    HAS_GRU = False
    GRUModel = None

try:
    from ..models.tcn_model import TCNModel
    HAS_TCN = True
except Exception:
    HAS_TCN = False
    TCNModel = None

logger = get_logger(__name__)
config = get_config()

class Trainer:
    def __init__(self, symbol: str = "BTC-USD", scaler_type: str = None, use_sentiment: bool = True, use_feature_selection: bool = None):
        self.symbol = symbol
        self.use_sentiment = use_sentiment
        self.dataset = CryptoDataset(
            symbol=symbol, 
            scaler_type=scaler_type or ("robust" if config.training.use_robust_scaler else "standard"),
            use_feature_selection=use_feature_selection if use_feature_selection is not None else config.training.use_feature_selection
        )
        self.models: Dict[str, any] = {}
        self.results: Dict[str, Dict] = {}
        self.preprocessor_path = None
        self._metrics = {
            "total_time": 0,
            "data_time": 0,
            "training_time": {}
        }

    def prepare_data(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False, use_sentiment: bool = None):
        start = time.time()
        logger.info(f"Preparing data v5 MAX for {self.symbol} | sentiment={self.use_sentiment} | feature_selection={config.training.use_feature_selection}")
        raw = self.dataset.load(period=period, interval=interval, force_refresh=force_refresh)
        feat = self.dataset.engineer.engineer(raw)

        if use_sentiment is None:
            use_sentiment = self.use_sentiment

        if use_sentiment and config.features.use_sentiment:
            try:
                senti_eng = SentimentFeatureEngineer()
                feat = senti_eng.enrich_price_df(feat, symbol=self.symbol)
            except Exception as e:
                logger.warning(f"Sentiment enrichment v5 failed: {e}")

        cleaned = self.dataset.preprocessor.prepare_features(feat, feature_cols=self.dataset.engineer.get_feature_columns(feat))
        train_df, val_df, test_df = self.dataset.preprocessor.split(cleaned)
        scaled = self.dataset.preprocessor.fit_transform(train_df, val_df, test_df)

        seq_len = config.data.sequence_length
        X_train_seq, y_train_seq = self.dataset.preprocessor.create_sequences(scaled['X_train'], scaled['y_train'], seq_len)
        X_val_seq, y_val_seq = self.dataset.preprocessor.create_sequences(scaled['X_val'], scaled['y_val'], seq_len)
        X_test_seq, y_test_seq = self.dataset.preprocessor.create_sequences(scaled['X_test'], scaled['y_test'], seq_len)

        scaled['X_train_seq'] = X_train_seq
        scaled['y_train_seq'] = y_train_seq
        scaled['X_val_seq'] = X_val_seq
        scaled['y_val_seq'] = y_val_seq
        scaled['X_test_seq'] = X_test_seq
        scaled['y_test_seq'] = y_test_seq

        self.dataset.processed = scaled
        self.dataset.feature_df = feat
        self.preprocessor_path = self.dataset.save_preprocessor()
        
        elapsed = time.time() - start
        self._metrics["data_time"] = elapsed
        logger.info(f"Dataset v5 ready {self.symbol}: seq train {X_train_seq.shape}, val {X_val_seq.shape}, test {X_test_seq.shape} | selected {len(scaled['feature_columns'])} feats in {elapsed:.2f}s")
        return scaled

    def train_lstm(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        start = time.time()
        logger.info(f"Training LSTM v4 MAX for {self.symbol}...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = LSTMModel(
            input_size=input_size,
            hidden_size=config.model.lstm_hidden_size,
            num_layers=config.model.lstm_num_layers,
            dropout=config.model.lstm_dropout,
            bidirectional=config.model.lstm_bidirectional,
            use_attention=config.model.lstm_use_attention,
            attention_heads=config.model.lstm_attention_heads,
            use_residual=config.model.lstm_use_residual
        )
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs or config.model.lstm_epochs, 
            batch_size=batch_size or config.model.lstm_batch_size
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['lstm'] = model
        self.results['lstm'] = {"metrics": metrics, "history": history, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["lstm"] = elapsed
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} LSTM v4 MAX") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        torch_path_v4 = config.project_root / "models" / f"{safe_sym}_lstm_v4.pt"
        torch_path = config.project_root / "models" / f"{safe_sym}_lstm.pt"
        model.save_torch(str(torch_path_v4))
        model.save_torch(str(torch_path))
        return model, metrics

    def train_transformer(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        start = time.time()
        logger.info(f"Training Transformer v4 MAX for {self.symbol}...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = TransformerModel(
            input_size=input_size,
            d_model=config.model.transformer_d_model,
            nhead=config.model.transformer_nhead,
            num_layers=config.model.transformer_num_layers,
            dim_feedforward=config.model.transformer_dim_feedforward,
            dropout=config.model.transformer_dropout,
            use_learnable_pe=config.model.transformer_use_learnable_pe,
            use_attention_pooling=config.model.transformer_use_attention_pooling,
            use_pre_ln=config.model.transformer_use_pre_ln
        )
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs or config.model.transformer_epochs, 
            batch_size=batch_size or config.model.transformer_batch_size
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['transformer'] = model
        self.results['transformer'] = {"metrics": metrics, "history": history, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["transformer"] = elapsed
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} Transformer v4 MAX") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        torch_path_v4 = config.project_root / "models" / f"{safe_sym}_transformer_v4.pt"
        torch_path = config.project_root / "models" / f"{safe_sym}_transformer.pt"
        model.save_torch(str(torch_path_v4))
        model.save_torch(str(torch_path))
        return model, metrics

    def train_gru(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        if not HAS_GRU:
            logger.warning("GRU not available, skipping")
            return None, {}
        
        start = time.time()
        logger.info(f"Training GRU v4 MAX for {self.symbol}...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = GRUModel(
            input_size=input_size,
            hidden_size=config.model.gru_hidden_size,
            num_layers=config.model.gru_num_layers,
            dropout=config.model.gru_dropout,
            bidirectional=config.model.gru_bidirectional
        )
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs or config.model.gru_epochs, 
            batch_size=batch_size or 32
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['gru'] = model
        self.results['gru'] = {"metrics": metrics, "history": history, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["gru"] = elapsed
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} GRU v4 MAX") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        torch_path_v4 = config.project_root / "models" / f"{safe_sym}_gru_v4.pt"
        torch_path = config.project_root / "models" / f"{safe_sym}_gru.pt"
        model.save_torch(str(torch_path_v4))
        model.save_torch(str(torch_path))
        return model, metrics

    def train_tcn(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        if not HAS_TCN:
            logger.warning("TCN not available, skipping")
            return None, {}
        
        start = time.time()
        logger.info(f"Training TCN v5 for {self.symbol}...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = TCNModel(
            input_size=input_size,
            num_channels=config.model.tcn_channels,
            kernel_size=config.model.tcn_kernel_size,
            dropout=config.model.tcn_dropout,
            learning_rate=config.model.tcn_learning_rate
        )
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs or 120, 
            batch_size=batch_size or 32
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['tcn'] = model
        self.results['tcn'] = {"metrics": metrics, "history": history, "version": "v5_tcn"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["tcn"] = elapsed
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} TCN v5") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        torch_path_v5 = config.project_root / "models" / f"{safe_sym}_tcn_v5.pt"
        torch_path = config.project_root / "models" / f"{safe_sym}_tcn.pt"
        model.save_torch(str(torch_path_v5))
        model.save_torch(str(torch_path))
        return model, metrics

    def train_xgboost(self, data_dict: Dict):
        start = time.time()
        logger.info(f"Training XGBoost v4 MAX for {self.symbol}...")
        model = XGBoostModel(
            n_estimators=config.model.xgb_n_estimators,
            max_depth=config.model.xgb_max_depth,
            learning_rate=config.model.xgb_learning_rate,
            subsample=config.model.xgb_subsample,
            colsample_bytree=config.model.xgb_colsample_bytree,
            reg_alpha=config.model.xgb_reg_alpha,
            reg_lambda=config.model.xgb_reg_lambda,
            min_child_weight=config.model.xgb_min_child_weight,
            gamma=config.model.xgb_gamma,
            use_gpu=config.model.xgb_use_gpu
        )
        model.fit(data_dict['X_train'], data_dict['y_train'], data_dict['X_val'], data_dict['y_val'], feature_names=data_dict['feature_columns'])

        y_pred_scaled = model.predict(data_dict['X_test'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true_scaled_inverse = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test'])
        min_len = min(len(y_true_scaled_inverse), len(y_pred))
        metrics = compute_regression_metrics(y_true_scaled_inverse[-min_len:], y_pred[-min_len:])

        self.models['xgboost'] = model
        self.results['xgboost'] = {"metrics": metrics, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["xgboost"] = elapsed
        logger.info(generate_report(y_true_scaled_inverse[-min_len:], y_pred[-min_len:], f"{self.symbol} XGBoost v4 MAX") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        xgb_path_v4 = config.project_root / "models" / f"{safe_sym}_xgb_v4.joblib"
        xgb_path = config.project_root / "models" / f"{safe_sym}_xgb.joblib"
        model.save(str(xgb_path_v4))
        model.save(str(xgb_path))

        try:
            imp_df = model.get_feature_importance(feature_names=data_dict['feature_columns'])
            imp_path = config.project_root / "models" / f"{safe_sym}_feature_importance_v4.csv"
            imp_df.to_csv(imp_path, index=False)
            logger.info(f"Top features v4: {imp_df.head(5)['feature'].tolist()}")
        except Exception as e:
            logger.warning(f"Could not save feature importance v5: {e}")

        return model, metrics

    def train_arima(self, data_dict: Dict):
        start = time.time()
        logger.info(f"Training ARIMA v4 MAX for {self.symbol}...")
        train_prices = data_dict['train_df']['Close'].values
        model = ARIMAModel(order=config.model.arima_order, seasonal_order=config.model.arima_seasonal_order, use_sarimax=True, use_auto=config.model.arima_use_auto)
        model.fit(y_train=train_prices)

        test_len = len(data_dict['test_df'])
        y_pred = model.predict(steps=test_len)
        y_true = data_dict['test_df']['Close'].values

        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])

        self.models['arima'] = model
        self.results['arima'] = {"metrics": metrics, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["arima"] = elapsed
        logger.info(generate_report(y_true[-min_len:], y_pred[-min_len:], f"{self.symbol} ARIMA v4 MAX") + f"\nTraining time: {elapsed:.1f}s")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        arima_path_v4 = config.project_root / "models" / f"{safe_sym}_arima_v4.joblib"
        arima_path = config.project_root / "models" / f"{safe_sym}_arima.joblib"
        model.save(str(arima_path_v4))
        model.save(str(arima_path))

        return model, metrics

    def train_ensemble(self, data_dict: Dict):
        start = time.time()
        logger.info(f"Training Ensemble v4 MAX for {self.symbol}...")
        if 'lstm' not in self.models:
            self.train_lstm(data_dict)
        if 'transformer' not in self.models:
            self.train_transformer(data_dict)
        if HAS_GRU and 'gru' not in self.models:
            self.train_gru(data_dict)
        if HAS_TCN and 'tcn' not in self.models:
            self.train_tcn(data_dict)
        if 'xgboost' not in self.models:
            self.train_xgboost(data_dict)
        if 'arima' not in self.models:
            self.train_arima(data_dict)

        # Collect predictions
        preds = {}
        try:
            lstm_pred_scaled = self.models['lstm'].predict(data_dict['X_test_seq'])
            preds['lstm'] = self.dataset.preprocessor.inverse_transform_target(lstm_pred_scaled)
        except Exception as e:
            logger.warning(f"LSTM pred for ensemble v5 failed: {e}")
        
        try:
            trans_pred_scaled = self.models['transformer'].predict(data_dict['X_test_seq'])
            preds['transformer'] = self.dataset.preprocessor.inverse_transform_target(trans_pred_scaled)
        except Exception as e:
            logger.warning(f"Transformer pred for ensemble v5 failed: {e}")
        
        if HAS_GRU and 'gru' in self.models:
            try:
                gru_pred_scaled = self.models['gru'].predict(data_dict['X_test_seq'])
                preds['gru'] = self.dataset.preprocessor.inverse_transform_target(gru_pred_scaled)
            except Exception as e:
                logger.warning(f"GRU pred for ensemble v5 failed: {e}")

        if HAS_TCN and 'tcn' in self.models:
            try:
                tcn_pred_scaled = self.models['tcn'].predict(data_dict['X_test_seq'])
                preds['tcn'] = self.dataset.preprocessor.inverse_transform_target(tcn_pred_scaled)
            except Exception as e:
                logger.warning(f"TCN pred for ensemble v5 failed: {e}")

        try:
            xgb_pred_scaled = self.models['xgboost'].predict(data_dict['X_test'])
            preds['xgboost'] = self.dataset.preprocessor.inverse_transform_target(xgb_pred_scaled)
        except Exception as e:
            logger.warning(f"XGB pred for ensemble v5 failed: {e}")

        try:
            # ARIMA needs to align with seq length
            arima_pred = self.models['arima'].predict(steps=len(list(preds.values())[0]) if preds else len(data_dict['y_test_seq']))
            preds['arima'] = arima_pred
        except Exception as e:
            logger.warning(f"ARIMA pred for ensemble v5 failed: {e}")

        if not preds:
            logger.error("No predictions for ensemble v5")
            return None, {}

        min_len = min(len(v) for v in preds.values())
        aligned = {k: v[-min_len:] for k, v in preds.items()}

        # Dynamic weighting v5
        y_true_seq = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        y_true_aligned = y_true_seq[-min_len:]

        # Compute individual MAPEs
        mapes = {}
        for k, v in aligned.items():
            try:
                from ..evaluation.metrics import mape as mape_fn
                mapes[k] = mape_fn(y_true_aligned, v)
            except Exception:
                mapes[k] = 20.0

        # Inverse MAPE + Sharpe weighting
        inv_mapes = {k: 1/(v+0.5) for k, v in mapes.items()}
        total_inv = sum(inv_mapes.values())
        dynamic_weights = {k: v/total_inv for k, v in inv_mapes.items()}

        # Final ensemble
        ensemble_pred = np.zeros(min_len)
        total_w = sum(config.model.ensemble_weights.get(k,0) for k in aligned.keys())
        if total_w > 0:
            for k, v in aligned.items():
                ensemble_pred += np.array(v) * config.model.ensemble_weights.get(k,0) / total_w
        else:
            for k, v in aligned.items():
                ensemble_pred += np.array(v) * dynamic_weights.get(k,0)

        metrics = compute_regression_metrics(y_true_aligned, ensemble_pred)
        metrics["weights"] = config.model.ensemble_weights
        metrics["dynamic_weights"] = dynamic_weights
        metrics["individual_mapes"] = mapes

        # Create ensemble model for saving
        ensemble = EnsembleModel(models=self.models, weights=config.model.ensemble_weights, use_stacking=True, use_dynamic_weights=True)

        self.models['ensemble'] = ensemble
        self.results['ensemble'] = {"metrics": metrics, "version": "v4_max"}
        
        elapsed = time.time() - start
        self._metrics["training_time"]["ensemble"] = elapsed
        logger.info(generate_report(y_true_aligned, ensemble_pred, f"{self.symbol} Ensemble v4 MAX") + f"\nTraining time: {elapsed:.1f}s")
        logger.info(f"Ensemble v5 weights: {config.model.ensemble_weights} | dynamic: {dynamic_weights} | MAPEs: {mapes}")

        safe_sym = self.symbol.replace('-','_').replace('/','_')
        ensemble_path_v4 = config.project_root / "models" / f"{safe_sym}_ensemble_v4.joblib"
        ensemble_path = config.project_root / "models" / f"{safe_sym}_ensemble.joblib"
        ensemble.save(str(ensemble_path_v4))
        ensemble.save(str(ensemble_path))

        return ensemble, metrics

    def train_all(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False, epochs: int = None):
        total_start = time.time()
        data_dict = self.prepare_data(period=period, interval=interval, force_refresh=force_refresh)
        
        # Train all models v5 MAX with TCN
        self.train_lstm(data_dict, epochs=epochs)
        self.train_transformer(data_dict, epochs=epochs)
        if HAS_GRU:
            self.train_gru(data_dict, epochs=epochs)
        if HAS_TCN:
            self.train_tcn(data_dict, epochs=epochs)
        self.train_xgboost(data_dict)
        self.train_arima(data_dict)
        self.train_ensemble(data_dict)

        total_elapsed = time.time() - total_start
        self._metrics["total_time"] = total_elapsed

        logger.info(f"\n{'='*80}\n=== Training Summary v5 MAX for {self.symbol} - Total {total_elapsed:.1f}s ===\n{'='*80}")
        for name, res in self.results.items():
            m = res['metrics']
            logger.info(f"{name:15s} | MAPE {m.get('mape',0):6.2f}% | RMSE {m.get('rmse',0):8.2f} | R2 {m.get('r2',0):6.4f} | DirAcc {m.get('directional_accuracy',0):5.1f}% | Sharpe {m.get('sharpe',0):5.2f}")

        # Compare
        try:
            comparison = compare_models({k: v['metrics'] for k, v in self.results.items()})
            logger.info(f"\nBest model: {comparison.get('best_model')} MAPE {comparison.get('best_mape',0):.2f}% | Ranking: {comparison.get('ranking')}")
        except Exception as e:
            logger.debug(f"Comparison failed: {e}")

        logger.info(f"{'='*80}\n")

        return self.results

    def get_data_dict(self):
        return self.dataset.processed

    def get_metrics(self):
        return {**self._metrics, "symbol": self.symbol, "version": "v5_max"}
