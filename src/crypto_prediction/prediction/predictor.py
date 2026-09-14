"""
Prediction / inference pipeline v5 MAX
Supports v2, v3, v4, v5 models with fallback + GRU + TCN + dynamic weighting
- Loads best available version: v5 -> v4 -> v3 -> v2
- Ensemble v5: dynamic weights + Sharpe + stacking + uncertainty + TCN
- Real trading calls with Kelly, risk, confidence intervals
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..data.dataset import CryptoDataset
from ..models.lstm_model import LSTMModel
from ..models.transformer_model import TransformerModel
from ..models.xgboost_model import XGBoostModel
from ..models.arima_model import ARIMAModel
from ..config import get_config
from ..utils.logger import get_logger

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

class CryptoPredictor:
    def __init__(self, symbol: str = "BTC-USD"):
        self.symbol = symbol
        self.dataset = CryptoDataset(symbol=symbol)
        self.preprocessor = None
        self.models = {}
        self.model_versions = {}
        self._load_artifacts()

    def _ensemble_weights(self, model_names: List[str]) -> Dict[str, float]:
        """Ensemble weights for the given loaded models.

        Prefers inverse-MAPE weights from the most recent training report
        (i.e. models that actually forecast well get more weight); falls
        back to the static configured weights.
        """
        try:
            safe = self.symbol.replace('-', '_').replace('/', '_')
            report_path = config.project_root / "models" / f"{safe}_training_report_v6.json"
            if report_path.exists():
                import json as _json
                with open(report_path) as f:
                    data = _json.load(f)
                metrics = data.get("metrics", {}) or {}
                weights = {}
                for name in model_names:
                    mape = (metrics.get(name) or {}).get("mape")
                    if mape is None or not np.isfinite(mape):
                        continue
                    weights[name] = 1.0 / (float(mape) + 0.5)
                if weights:
                    total = sum(weights.values())
                    return {k: w / total for k, w in weights.items()}
        except Exception:
            pass
        # Fallback: static config weights (missing entries -> small default)
        static = config.model.ensemble_weights
        return {k: static.get(k, 0.05) for k in model_names}

    def _load_artifacts(self):
        models_dir = config.project_root / "models"
        symbol_key = self.symbol.replace('-','_').replace('/','_')

        # Preprocessor - try v5, v4, v3, v2
        for version in ["v6", "v5", "v4", "v3", ""]:
            suffix = f"_{version}" if version else ""
            pre_path = models_dir / f"{symbol_key}_preprocessor{suffix}.joblib"
            if pre_path.exists():
                try:
                    from ..data.preprocessor import DataPreprocessor
                    self.preprocessor = DataPreprocessor()
                    self.preprocessor.load(str(pre_path))
                    self.model_versions['preprocessor'] = version or "v2"
                    logger.info(f"Loaded preprocessor {version or 'v2'} for {self.symbol}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load preprocessor {version}: {e}")

        # LSTM - v5, v4, v3, v2
        for version in ["v6", "v5", "v4", "v3", ""]:
            suffix = f"_{version}" if version else ""
            lstm_path = models_dir / f"{symbol_key}_lstm{suffix}.pt"
            if lstm_path.exists() and self.preprocessor:
                try:
                    self.models['lstm'] = LSTMModel.load_torch(str(lstm_path))
                    self.model_versions['lstm'] = version or "v2"
                    logger.info(f"Loaded LSTM model {version or 'v2'}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load LSTM {version}: {e}")

        # Transformer
        for version in ["v6", "v5", "v4", "v3", ""]:
            suffix = f"_{version}" if version else ""
            trans_path = models_dir / f"{symbol_key}_transformer{suffix}.pt"
            if trans_path.exists() and self.preprocessor:
                try:
                    self.models['transformer'] = TransformerModel.load_torch(str(trans_path))
                    self.model_versions['transformer'] = version or "v2"
                    logger.info(f"Loaded Transformer model {version or 'v2'}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load Transformer {version}: {e}")

        # GRU - v5, v4
        if HAS_GRU:
            for version in ["v6", "v5", "v4", ""]:
                suffix = f"_{version}" if version else ""
                gru_path = models_dir / f"{symbol_key}_gru{suffix}.pt"
                if gru_path.exists() and self.preprocessor:
                    try:
                        self.models['gru'] = GRUModel.load_torch(str(gru_path))
                        self.model_versions['gru'] = version or "v4"
                        logger.info(f"Loaded GRU model {version or 'v4'}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load GRU {version}: {e}")

        # TCN - v5
        if HAS_TCN:
            for version in ["v5", ""]:
                suffix = f"_{version}" if version else ""
                tcn_path = models_dir / f"{symbol_key}_tcn{suffix}.pt"
                if tcn_path.exists() and self.preprocessor:
                    try:
                        self.models['tcn'] = TCNModel.load_torch(str(tcn_path))
                        self.model_versions['tcn'] = version or "v5"
                        logger.info(f"Loaded TCN model {version or 'v5'}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load TCN {version}: {e}")

        # XGBoost
        for version in ["v6", "v5", "v4", "v3", ""]:
            suffix = f"_{version}" if version else ""
            xgb_path = models_dir / f"{symbol_key}_xgb{suffix}.joblib"
            if xgb_path.exists():
                try:
                    self.models['xgboost'] = XGBoostModel.load(str(xgb_path))
                    self.model_versions['xgboost'] = version or "v2"
                    logger.info(f"Loaded XGBoost model {version or 'v2'}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load XGB {version}: {e}")

        # ARIMA
        for version in ["v6", "v5", "v4", "v3", ""]:
            suffix = f"_{version}" if version else ""
            arima_path = models_dir / f"{symbol_key}_arima{suffix}.joblib"
            if arima_path.exists():
                try:
                    self.models['arima'] = ARIMAModel.load(str(arima_path))
                    self.model_versions['arima'] = version or "v2"
                    logger.info(f"Loaded ARIMA model {version or 'v2'}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load ARIMA {version}: {e}")

    def prepare_latest_data(self, period: str = "1y", interval: str = "1d") -> Dict:
        if self.preprocessor is None:
            logger.info("No preprocessor found, building fresh pipeline v5")
            try:
                from ..features.sentiment import SentimentFeatureEngineer
                raw = self.dataset.load(period=period, interval=interval)
                feat = self.dataset.engineer.engineer(raw)
                senti_eng = SentimentFeatureEngineer()
                feat = senti_eng.enrich_price_df(feat, symbol=self.symbol)
                cleaned = self.dataset.preprocessor.prepare_features(feat, feature_cols=self.dataset.engineer.get_feature_columns(feat))
                X = self.dataset.preprocessor.feature_scaler.transform(cleaned[self.dataset.preprocessor.feature_columns].values) if hasattr(self.dataset.preprocessor, 'feature_scaler') and self.dataset.preprocessor.feature_columns else None
                if X is None:
                    data_dict = self.dataset.get_full_pipeline(period=period, interval=interval)
                    self.preprocessor = self.dataset.preprocessor
                    return data_dict
                seq_len = config.data.sequence_length
                X_seq, _ = self.dataset.preprocessor.create_sequences(X, np.zeros(len(X)), seq_length=seq_len)
                return {
                    'X': X,
                    'X_seq': X_seq,
                    'cleaned_df': cleaned,
                    'raw_df': raw,
                    'feature_df': feat,
                    'feature_columns': self.dataset.preprocessor.feature_columns
                }
            except Exception as e:
                logger.warning(f"Enriched pipeline failed, fallback: {e}")
                data_dict = self.dataset.get_full_pipeline(period=period, interval=interval)
                self.preprocessor = self.dataset.preprocessor
                return data_dict
        else:
            raw = self.dataset.load(period=period, interval=interval)
            feat = self.dataset.engineer.engineer(raw)
            # Only enrich with sentiment when the loaded model was actually
            # trained on sentiment features - otherwise the fetch just adds
            # latency (and fails offline) without being used.
            saved_cols = set(self.preprocessor.feature_columns)
            needs_sentiment = any('Sentiment' in c or c.startswith('sentiment') for c in saved_cols)
            if config.features.use_sentiment and needs_sentiment:
                try:
                    from ..features.sentiment import SentimentFeatureEngineer
                    senti_eng = SentimentFeatureEngineer()
                    feat = senti_eng.enrich_price_df(feat, symbol=self.symbol)
                except Exception as e:
                    logger.warning(f"Sentiment enrich failed in predict: {e}")

            cleaned = self.preprocessor.prepare_features(feat, feature_cols=self.preprocessor.feature_columns)
            X = self.preprocessor.feature_scaler.transform(cleaned[self.preprocessor.feature_columns].values)
            seq_len = config.data.sequence_length
            X_seq, _ = self.preprocessor.create_sequences(X, np.zeros(len(X)), seq_length=seq_len)
            data_dict = {
                'X': X,
                'X_seq': X_seq,
                'cleaned_df': cleaned,
                'raw_df': raw,
                'feature_df': feat
            }
        return data_dict

    def predict_next(self, period: str = "1y", interval: str = "1d") -> Dict:
        data = self.prepare_latest_data(period=period, interval=interval)
        
        results = {}
        latest_flat = data['X'][-1] if 'X' in data else data.get('X_test', [None])[-1] if 'X_test' in data else None
        latest_seq = data['X_seq'][-1] if 'X_seq' in data else None

        if latest_flat is None or latest_seq is None:
            latest_flat = data['X_test'][-1] if 'X_test' in data else data['X_train'][-1]
            latest_seq = data['X_test_seq'][-1] if 'X_test_seq' in data else data['X_train_seq'][-1]

        if 'lstm' in self.models:
            try:
                pred_scaled = self.models['lstm'].predict(latest_seq.reshape(1, *latest_seq.shape))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['lstm'] = float(pred)
            except Exception as e:
                logger.warning(f"LSTM predict failed: {e}")

        if 'transformer' in self.models:
            try:
                pred_scaled = self.models['transformer'].predict(latest_seq.reshape(1, *latest_seq.shape))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['transformer'] = float(pred)
            except Exception as e:
                logger.warning(f"Transformer predict failed: {e}")

        if 'gru' in self.models:
            try:
                pred_scaled = self.models['gru'].predict(latest_seq.reshape(1, *latest_seq.shape))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['gru'] = float(pred)
            except Exception as e:
                logger.warning(f"GRU predict failed: {e}")

        if 'tcn' in self.models:
            try:
                pred_scaled = self.models['tcn'].predict(latest_seq.reshape(1, *latest_seq.shape))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['tcn'] = float(pred)
            except Exception as e:
                logger.warning(f"TCN predict failed: {e}")

        if 'xgboost' in self.models:
            try:
                pred_scaled = self.models['xgboost'].predict(latest_flat.reshape(1, -1))
                pred = self.preprocessor.inverse_transform_target(pred_scaled)[0]
                results['xgboost'] = float(pred)
            except Exception as e:
                logger.warning(f"XGB predict failed: {e}")

        if 'arima' in self.models:
            try:
                pred = self.models['arima'].predict(steps=1)[0]
                results['arima'] = float(pred)
            except Exception as e:
                logger.warning(f"ARIMA predict failed: {e}")

        if results:
            weights = self._ensemble_weights([k for k in results.keys() if k != 'ensemble'])
            
            total_w = sum(weights.get(k,0) for k in results.keys())
            if total_w > 0:
                ensemble = sum(results[k] * weights.get(k,0) / total_w for k in results.keys())
                results['ensemble'] = float(ensemble)
            
            # Uncertainty: std across models
            if len(results) >= 2:
                preds = [v for k,v in results.items() if k != 'ensemble']
                results['uncertainty'] = float(np.std(preds))
                results['confidence'] = float(1 - min(np.std(preds) / (np.mean(preds)+1e-8), 0.5))
            else:
                results['uncertainty'] = 0.0
                results['confidence'] = 0.7

        return results

    def forecast(self, steps: int = 7, period: str = "1y", interval: str = "1d") -> Dict[str, List[float]]:
        data = self.prepare_latest_data(period=period, interval=interval)
        
        latest_flat = data['X'][-1] if 'X' in data else None
        latest_seq = data['X_seq'][-1] if 'X_seq' in data else None
        if latest_flat is None or latest_seq is None:
            proc = data
            latest_flat = proc['X_test'][-1] if 'X_test' in proc else proc['X_train'][-1]
            latest_seq = proc['X_test_seq'][-1] if 'X_test_seq' in proc else proc['X_train_seq'][-1]

        forecasts = {}

        if 'lstm' in self.models:
            try:
                preds_scaled = self.models['lstm'].forecast_future(latest_seq, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['lstm'] = preds.tolist()
            except Exception as e:
                logger.warning(f"LSTM forecast failed: {e}")

        if 'transformer' in self.models:
            try:
                preds_scaled = self.models['transformer'].forecast_future(latest_seq, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['transformer'] = preds.tolist()
            except Exception as e:
                logger.warning(f"Transformer forecast failed: {e}")

        if 'gru' in self.models:
            try:
                preds_scaled = self.models['gru'].forecast_future(latest_seq, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['gru'] = preds.tolist()
            except Exception as e:
                logger.warning(f"GRU forecast failed: {e}")

        if 'tcn' in self.models:
            try:
                preds_scaled = self.models['tcn'].forecast_future(latest_seq, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['tcn'] = preds.tolist()
            except Exception as e:
                logger.warning(f"TCN forecast failed: {e}")

        if 'xgboost' in self.models:
            try:
                preds_scaled = self.models['xgboost'].forecast_future(latest_flat, steps=steps)
                preds = self.preprocessor.inverse_transform_target(preds_scaled)
                forecasts['xgboost'] = preds.tolist()
            except Exception as e:
                logger.warning(f"XGB forecast failed: {e}")

        if 'arima' in self.models:
            try:
                preds = self.models['arima'].forecast_future(steps=steps)
                forecasts['arima'] = preds.tolist()
            except Exception as e:
                logger.warning(f"ARIMA forecast failed: {e}")

        if forecasts:
            min_len = min(len(v) for v in forecasts.values())
            aligned = {k: v[:min_len] for k, v in forecasts.items()}
            weights = self._ensemble_weights(list(aligned.keys()))
            total_w = sum(weights.get(k,0) for k in aligned.keys())
            if total_w > 0:
                ensemble = np.zeros(min_len)
                for k, v in aligned.items():
                    ensemble += np.array(v) * weights.get(k,0) / total_w
                forecasts['ensemble'] = ensemble.tolist()
                
                # Uncertainty bands per step
                all_preds = np.array(list(aligned.values()))  # (num_models, steps)
                forecasts['uncertainty'] = np.std(all_preds, axis=0).tolist()
                forecasts['upper_band'] = (ensemble + 1.96 * np.std(all_preds, axis=0)).tolist()
                forecasts['lower_band'] = (ensemble - 1.96 * np.std(all_preds, axis=0)).tolist()
                forecasts['confidence'] = (1 - np.std(all_preds, axis=0) / (np.abs(ensemble) + 1e-8)).clip(0.3, 0.95).tolist()

        last_date = data['cleaned_df'].index[-1] if 'cleaned_df' in data else pd.Timestamp.now()
        future_dates = [last_date + timedelta(days=i+1) for i in range(steps)]
        forecasts['dates'] = [d.strftime('%Y-%m-%d') for d in future_dates]

        current_price = float(data['cleaned_df']['Close'].iloc[-1]) if 'cleaned_df' in data else None
        forecasts['current_price'] = current_price
        forecasts['symbol'] = self.symbol
        forecasts['model_versions'] = self.model_versions
        forecasts['version'] = "v5_max"
        forecasts['model_count'] = len(self.models)

        try:
            if 'Sentiment_Compound' in data['cleaned_df'].columns:
                forecasts['sentiment'] = float(data['cleaned_df']['Sentiment_Compound'].iloc[-1])
                forecasts['sentiment_ma7'] = float(data['cleaned_df']['Sentiment_MA7'].iloc[-1]) if 'Sentiment_MA7' in data['cleaned_df'].columns else 0
        except Exception:
            pass

        # Market regime
        try:
            if 'Bull_Market' in data['cleaned_df'].columns:
                forecasts['regime'] = {
                    'bull': int(data['cleaned_df']['Bull_Market'].iloc[-1]),
                    'bear': int(data['cleaned_df']['Bear_Market'].iloc[-1]),
                    'sideways': int(data['cleaned_df']['Sideways_Market'].iloc[-1]) if 'Sideways_Market' in data['cleaned_df'].columns else 0
                }
            if 'Volatility' in data['cleaned_df'].columns:
                forecasts['volatility'] = float(data['cleaned_df']['Volatility'].iloc[-1])
                forecasts['volatility_regime'] = int(data['cleaned_df']['Volatility_Regime'].iloc[-1]) if 'Volatility_Regime' in data['cleaned_df'].columns else 0
        except Exception:
            pass

        return forecasts

    def get_trading_signal(self, forecast: Dict) -> Dict:
        current = forecast.get('current_price')
        ensemble = forecast.get('ensemble') or forecast.get('transformer') or forecast.get('lstm') or forecast.get('tcn') or forecast.get('gru') or forecast.get('xgboost')
        
        if not current or not ensemble:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "Insufficient data", "model_versions": forecast.get('model_versions', {}), "version": "v5_max"}

        next_price = ensemble[0] if isinstance(ensemble, list) else ensemble
        change_pct = (next_price - current) / current * 100

        sentiment_boost = 0
        if 'sentiment' in forecast:
            sentiment_boost = forecast['sentiment'] * 0.5
            change_pct += sentiment_boost

        # v5 thresholds - more sensitive with volatility adjustment
        volatility = forecast.get('volatility', 0.02)
        # Adjust thresholds by volatility: higher vol -> higher threshold
        vol_mult = max(1.0, min(2.0, 1 + volatility * 10))
        
        strong_buy_thr = 3.0 * vol_mult
        buy_thr = 0.8 * vol_mult
        strong_sell_thr = -3.0 * vol_mult
        sell_thr = -0.8 * vol_mult

        if change_pct > strong_buy_thr:
            signal = "STRONG_BUY"
        elif change_pct > buy_thr:
            signal = "BUY"
        elif change_pct < strong_sell_thr:
            signal = "STRONG_SELL"
        elif change_pct < sell_thr:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Confidence based on change + model agreement + uncertainty
        base_conf = min(abs(change_pct) * 20, 85)
        # Boost confidence if multiple models agree
        if isinstance(forecast, dict):
            model_preds = [v[0] if isinstance(v, list) else v for k, v in forecast.items() if k in ['lstm','transformer','gru','tcn','xgboost','arima'] and v is not None]
            if len(model_preds) >= 2:
                agreement = 1 - (np.std(model_preds) / (np.mean(model_preds) + 1e-8))
                agreement_boost = max(0, agreement * 15)
                base_conf += agreement_boost

        # Uncertainty penalty
        uncertainty = forecast.get('uncertainty', [0])[0] if isinstance(forecast.get('uncertainty'), list) else forecast.get('uncertainty', 0)
        if uncertainty:
            uncertainty_penalty = min(20, uncertainty / current * 100 * 5)
            base_conf -= uncertainty_penalty

        confidence = min(max(base_conf + (abs(forecast.get('sentiment',0))*10), 10), 95)

        # Risk management v5: Kelly, ATR, position sizing
        atr_pct = 0.02
        try:
            if 'ATR_Pct' in forecast:
                atr_pct = forecast['ATR_Pct']
        except Exception:
            pass

        # Calculate SL/TP with ATR
        sl_pct = max(1.5, atr_pct * 100 * 1.5)  # 1.5x ATR
        tp_pct = sl_pct * 2  # 1:2 RR
        
        if signal in ["BUY", "STRONG_BUY"]:
            stop_loss = current * (1 - sl_pct/100)
            take_profit = current * (1 + tp_pct/100)
            take_profit2 = current * (1 + tp_pct*1.5/100)
            take_profit3 = current * (1 + tp_pct*2/100)
        elif signal in ["SELL", "STRONG_SELL"]:
            stop_loss = current * (1 + sl_pct/100)
            take_profit = current * (1 - tp_pct/100)
            take_profit2 = current * (1 - tp_pct*1.5/100)
            take_profit3 = current * (1 - tp_pct*2/100)
        else:
            stop_loss = current * (1 - sl_pct/100)
            take_profit = current * (1 + tp_pct/100)
            take_profit2 = take_profit
            take_profit3 = take_profit

        # Kelly position sizing
        kelly_fraction = forecast.get('kelly', 0.02)
        risk_per_trade = min(0.05, max(0.005, kelly_fraction)) if kelly_fraction else 0.02

        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "current_price": current,
            "predicted_price": next_price,
            "change_pct": round(change_pct, 2),
            "sentiment": forecast.get('sentiment', 0),
            "model_versions": forecast.get('model_versions', {}),
            "version": "v5_max",
            "volatility": volatility,
            "uncertainty": uncertainty,
            "thresholds": {"strong_buy": strong_buy_thr, "buy": buy_thr, "sell": sell_thr, "strong_sell": strong_sell_thr},
            "risk_management": {
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
                "take_profit2": round(take_profit2, 2),
                "take_profit3": round(take_profit3, 2),
                "risk_per_trade": risk_per_trade,
                "risk_reward": 2.0,
                "atr_pct": atr_pct,
                "sl_pct": sl_pct,
                "tp_pct": tp_pct
            },
            "reason": f"Predicted {change_pct:.2f}% change v5 | Vol {volatility*100:.2f}% | Models {forecast.get('model_versions', {})} | Conf {confidence:.1f}% | SL {sl_pct:.1f}% TP {tp_pct:.1f}%",
            "model_agreement": len([k for k in ['lstm','transformer','gru','tcn','xgboost','arima'] if k in forecast]) if isinstance(forecast, dict) else 0
        }
