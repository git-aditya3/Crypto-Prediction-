"""
Training pipeline orchestrator
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from ..data.dataset import CryptoDataset
from ..models.lstm_model import LSTMModel
from ..models.xgboost_model import XGBoostModel
from ..models.arima_model import ARIMAModel
from ..models.ensemble import EnsembleModel
from ..evaluation.metrics import compute_regression_metrics, generate_report
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class Trainer:
    def __init__(self, symbol: str = "BTC-USD", scaler_type: str = "standard"):
        self.symbol = symbol
        self.dataset = CryptoDataset(symbol=symbol, scaler_type=scaler_type)
        self.models: Dict[str, any] = {}
        self.results: Dict[str, Dict] = {}
        self.preprocessor_path = None

    def prepare_data(self, period: str = "2y", interval: str = "1d", force_refresh: bool = False):
        logger.info(f"Preparing data for {self.symbol}")
        data_dict = self.dataset.get_full_pipeline(period=period, interval=interval, force_refresh=force_refresh)
        self.preprocessor_path = self.dataset.save_preprocessor()
        return data_dict

    def train_lstm(self, data_dict: Dict, epochs: int = None, batch_size: int = None):
        logger.info("Training LSTM...")
        input_size = data_dict['X_train_seq'].shape[2]
        model = LSTMModel(input_size=input_size)
        history = model.fit(
            data_dict['X_train_seq'], data_dict['y_train_seq'],
            data_dict['X_val_seq'], data_dict['y_val_seq'],
            epochs=epochs, batch_size=batch_size
        )
        # Evaluate
        y_pred_scaled = model.predict(data_dict['X_test_seq'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test_seq'])
        metrics = compute_regression_metrics(y_true, y_pred)

        self.models['lstm'] = model
        self.results['lstm'] = {"metrics": metrics, "history": history}
        logger.info(generate_report(y_true, y_pred, f"{self.symbol} LSTM"))

        # Save torch model
        torch_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_lstm.pt"
        model.save_torch(str(torch_path))
        return model, metrics

    def train_xgboost(self, data_dict: Dict):
        logger.info("Training XGBoost...")
        model = XGBoostModel()
        model.fit(data_dict['X_train'], data_dict['y_train'], data_dict['X_val'], data_dict['y_val'])

        y_pred_scaled = model.predict(data_dict['X_test'])
        y_pred = self.dataset.preprocessor.inverse_transform_target(y_pred_scaled)
        y_true_raw = data_dict['y_test_raw'][-len(y_pred):] if len(data_dict['y_test_raw']) >= len(y_pred) else self.dataset.preprocessor.inverse_transform_target(data_dict['y_test'])

        # Align lengths for metric - use scaled inverse for both
        y_true_scaled_inverse = self.dataset.preprocessor.inverse_transform_target(data_dict['y_test'])
        min_len = min(len(y_true_scaled_inverse), len(y_pred))
        metrics = compute_regression_metrics(y_true_scaled_inverse[-min_len:], y_pred[-min_len:])

        self.models['xgboost'] = model
        self.results['xgboost'] = {"metrics": metrics}
        logger.info(generate_report(y_true_scaled_inverse[-min_len:], y_pred[-min_len:], f"{self.symbol} XGBoost"))

        # Save
        xgb_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_xgb.joblib"
        model.save(str(xgb_path))

        # Feature importance
        try:
            imp_df = model.get_feature_importance(feature_names=data_dict['feature_columns'])
            imp_path = config.project_root / "models" / f"{self.symbol.replace('-','_')}_feature_importance.csv"
            imp_df.to_csv(imp_path, index=False)
        except Exception as e:
            logger.warning(f"Could not save feature importance: {e}")

        return model, metrics

    def train_arima(self, data_dict: Dict):
        logger.info("Training ARIMA...")
        # ARIMA on raw close price train series
        train_prices = data_dict['train_df']['Close'].values
        model = ARIMAModel(order=config.model.arima_order)
        model.fit(y_train=train_prices)

        # Forecast test length
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
        # Ensure individual models exist
        if 'lstm' not in self.models:
            self.train_lstm(data_dict)
        if 'xgboost' not in self.models:
            self.train_xgboost(data_dict)
        if 'arima' not in self.models:
            self.train_arima(data_dict)

        ensemble = EnsembleModel(models={
            'lstm': self.models['lstm'],
            'xgboost': self.models['xgboost'],
            'arima': self.models['arima']
        })

        # Prepare dicts for prediction
        X_test_dict = {
            'lstm': data_dict['X_test_seq'],
            'xgboost': data_dict['X_test'],
            'arima': len(data_dict['X_test_seq'])  # steps
        }

        # For ensemble prediction we need to handle length alignment carefully
        # LSTM predictions are on seq test set, XGB on flat test set
        # We'll predict separately and align
        lstm_pred_scaled = self.models['lstm'].predict(data_dict['X_test_seq'])
        lstm_pred = self.dataset.preprocessor.inverse_transform_target(lstm_pred_scaled)

        xgb_pred_scaled = self.models['xgboost'].predict(data_dict['X_test'])
        xgb_pred = self.dataset.preprocessor.inverse_transform_target(xgb_pred_scaled)

        # ARIMA predicts on raw scale directly
        arima_pred = self.models['arima'].predict(steps=len(lstm_pred))

        # Align to shortest (lstm seq test is smaller than flat test)
        min_len = min(len(lstm_pred), len(xgb_pred), len(arima_pred))
        # For XGB, take last min_len because seq test is at end
        lstm_aligned = lstm_pred[-min_len:]
        xgb_aligned = xgb_pred[-min_len:]
        arima_aligned = arima_pred[-min_len:]

        weights = config.model.ensemble_weights
        ensemble_pred = weights['lstm']*lstm_aligned + weights['xgboost']*xgb_aligned + weights['arima']*arima_aligned

        # True values aligned
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
        self.train_xgboost(data_dict)
        self.train_arima(data_dict)
        self.train_ensemble(data_dict)

        # Summary
        logger.info("\n=== Training Summary ===")
        for name, res in self.results.items():
            logger.info(f"{name:15s} | RMSE: {res['metrics']['rmse']:.2f} | MAE: {res['metrics']['mae']:.2f} | R2: {res['metrics']['r2']:.4f} | DA: {res['metrics']['directional_accuracy']:.2f}%")

        return self.results

    def get_data_dict(self):
        return self.dataset.processed
