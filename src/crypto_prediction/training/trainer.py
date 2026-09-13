"""
Training pipeline orchestrator - v2 with Transformer & Sentiment
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from ..data.dataset import CryptoDataset
from ..models.lstm_model import LSTMModel
from ..models.transformer_model import TransformerModel
from ..models.xgboost_model import XGBoostModel
from ..models.arima_model import ARIMAModel
from ..models.ensemble import EnsembleModel
from ..evaluation.metrics import compute_regression_metrics, generate_report
from ..config import get_config
from ..utils.logger import get_logger
from ..features.sentiment import SentimentFeatureEngineer

logger = get_logger(__name__)
config = get_config()

class Trainer:
    def __init__(self, symbol: str = "BTC-USD", scaler_type: str = "standard", use_sentiment: bool = True):
        self.symbol = symbol
        self.use_sentiment = use_sentiment
        self.dataset = CryptoDataset(symbol=symbol, scaler_type=scaler_type)
        self.models: Dict[str, any] = {}
        self.results: Dict[str, Dict] = {}
        self.preprocessor_path = None

    def prepare_data(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False):
        logger.info(f"Preparing data for {self.symbol} | sentiment={self.use_sentiment}")
        # Fetch base data
        raw = self.dataset.load(period=period, interval=interval, force_refresh=force_refresh)
        feat = self.dataset.engineer.engineer(raw)

        # Enrich with sentiment if enabled
        if self.use_sentiment and config.features.use_sentiment:
            try:
                senti_eng = SentimentFeatureEngineer()
                feat = senti_eng.enrich_price_df(feat, symbol=self.symbol)
            except Exception as e:
                logger.warning(f"Sentiment enrichment failed: {e}")

        # Prepare
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
        logger.info(f"Dataset ready: seq train {X_train_seq.shape}, val {X_val_seq.shape}, test {X_test_seq.shape}")
        return scaled

    def train_lstm(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        logger.info("Training LSTM...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = LSTMModel(input_size=input_size)
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs, batch_size=batch_size
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['lstm'] = model
        self.results['lstm'] = {"metrics": metrics, "history": history}
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} LSTM"))

        torch_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_lstm.pt"
        model.save_torch(str(torch_path))
        return model, metrics

    def train_transformer(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        logger.info("Training Transformer...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = TransformerModel(input_size=input_size)
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs, batch_size=batch_size
        )
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['transformer'] = model
        self.results['transformer'] = {"metrics": metrics, "history": history}
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} Transformer"))

        torch_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_transformer.pt"
        model.save_torch(str(torch_path))
        return model, metrics

    def train_xgboost(self, data_dict: Dict):
        logger.info("Training XGBoost...")
        model = XGBoostModel()
        model.fit(data_dict['X_train'], data_dict['y_train'], data_dict['X_val'], data_dict['y_val'])

        y_pred_scaled = model.predict(data_dict['X_test'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true_scaled_inverse = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test'])
        min_len = min(len(y_true_scaled_inverse), len(y_pred))
        metrics = compute_regression_metrics(y_true_scaled_inverse[-min_len:], y_pred[-min_len:])

        self.models['xgboost'] = model
        self.results['xgboost'] = {"metrics": metrics}
        logger.info(generate_report(y_true_scaled_inverse[-min_len:], y_pred[-min_len:], f"{self.symbol} XGBoost"))

        xgb_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_xgb.joblib"
        model.save(str(xgb_path))

        try:
            imp_df = model.get_feature_importance(feature_names=data_dict['feature_columns'])
            imp_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_feature_importance.csv"
            imp_df.to_csv(imp_path, index=False)
        except Exception as e:
            logger.warning(f"Could not save feature importance: {e}")

        return model, metrics

    def train_arima(self, data_dict: Dict):
        logger.info("Training ARIMA...")
        train_prices = data_dict['train_df']['Close'].values
        model = ARIMAModel(order=config.model.arima_order)
        model.fit(y_train=train_prices)

        test_len = len(data_dict['test_df'])
        y_pred = model.predict(steps=test_len)
        y_true = data_dict['test_df']['Close'].values

        min_len = min(len(y_true), len(y_pred))
        metrics = compute_regression_metrics(y_true[-min_len:], y_pred[-min_len:])

        self.models['arima'] = model
        self.results['arima'] = {"metrics": metrics}
        logger.info(generate_report(y_true[-min_len:], y_pred[-min_len:], f"{self.symbol} ARIMA"))

        arima_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_arima.joblib"
        model.save(str(arima_path))

        return model, metrics

    def train_ensemble(self, data_dict: Dict):
        logger.info("Training Ensemble...")
        if 'lstm' not in self.models:
            self.train_lstm(data_dict)
        if 'transformer' not in self.models:
            self.train_transformer(data_dict)
        if 'xgboost' not in self.models:
            self.train_xgboost(data_dict)
        if 'arima' not in self.models:
            self.train_arima(data_dict)

        ensemble = EnsembleModel(models={
            'lstm': self.models['lstm'],
            'transformer': self.models['transformer'],
            'xgboost': self.models['xgboost'],
            'arima': self.models['arima']
        })

        lstm_pred_scaled = self.models['lstm'].predict(data_dict['X_test_seq'])
        lstm_pred = self.dataset.preprocessor.inverse_transform_target(lstm_pred_scaled)

        trans_pred_scaled = self.models['transformer'].predict(data_dict['X_test_seq'])
        trans_pred = self.dataset.preprocessor.inverse_transform_target(trans_pred_scaled)

        xgb_pred_scaled = self.models['xgboost'].predict(data_dict['X_test'])
        xgb_pred = self.dataset.preprocessor.inverse_transform_target(xgb_pred_scaled)

        arima_pred = self.models['arima'].predict(steps=len(lstm_pred))

        min_len = min(len(lstm_pred), len(trans_pred), len(xgb_pred), len(arima_pred))
        lstm_aligned = lstm_pred[-min_len:]
        trans_aligned = trans_pred[-min_len:]
        xgb_aligned = xgb_pred[-min_len:]
        arima_aligned = arima_pred[-min_len:]

        weights = config.model.ensemble_weights
        ensemble_pred = weights['lstm']*lstm_aligned + weights.get('transformer',0.35)*trans_aligned + weights['xgboost']*xgb_aligned + weights['arima']*arima_aligned

        y_true_seq = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        y_true_aligned = y_true_seq[-min_len:]

        metrics = compute_regression_metrics(y_true_aligned, ensemble_pred)
        self.models['ensemble'] = ensemble
        self.results['ensemble'] = {"metrics": metrics}
        logger.info(generate_report(y_true_aligned, ensemble_pred, f"{self.symbol} Ensemble"))

        ensemble_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_ensemble.joblib"
        ensemble.save(str(ensemble_path))

        return ensemble, metrics

    def train_all(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False):
        data_dict = self.prepare_data(period=period, interval=interval, force_refresh=force_refresh)
        self.train_lstm(data_dict)
        self.train_transformer(data_dict)
        self.train_xgboost(data_dict)
        self.train_arima(data_dict)
        self.train_ensemble(data_dict)

        logger.info("\n=== Training Summary ===")
        for name, res in self.results.items():
            logger.info(f"{name:15s} | RMSE: {res['metrics']['rmse']:.2f} | MAE: {res['metrics']['mae']:.2f} | R2: {res['metrics']['r2']:.4f} | DA: {res['metrics']['directional_accuracy']:.2f}%")

        return self.results

    def get_data_dict(self):
        return self.dataset.processed
