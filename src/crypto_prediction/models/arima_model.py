"""
ARIMA model v4 Max Performance
- Auto order selection via AIC grid search
- SARIMAX with weekly seasonality + exogenous features support
- Robust fallback + confidence intervals
- Kalman filter integration
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import warnings
from typing import Tuple, Optional
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class ARIMAModel(BaseModel):
    def __init__(self, order: tuple = None, seasonal_order: tuple = None, use_sarimax: bool = True, use_auto: bool = None):
        super().__init__(name="arima")
        self.order = order or config.model.arima_order
        self.seasonal_order = seasonal_order or config.model.arima_seasonal_order
        self.use_sarimax = use_sarimax
        self.use_auto = use_auto if use_auto is not None else config.model.arima_use_auto
        self.model_fit = None
        self.history = None
        self.residuals = None
        self.conf_int = None

    def _check_stationarity(self, y) -> int:
        """Determine d via ADF test"""
        try:
            result = adfuller(y)
            if result[1] > 0.05:
                return 1
            return 0
        except Exception:
            return 1

    def _find_best_order(self, y, max_p=5, max_d=2, max_q=5) -> Tuple[Tuple[int,int,int], Tuple[int,int,int,int]]:
        """Extended grid search for best ARIMA order based on AIC + BIC weighted"""
        best_score = float('inf')
        best_order = self.order
        best_seasonal = self.seasonal_order
        
        # Auto determine d
        d = self._check_stationarity(y)
        
        candidates = [
            (5,1,3), (5,1,2), (3,1,3), (4,1,3), (3,1,2),
            (2,1,2), (2,1,1), (1,1,1), (1,1,0), (2,1,0),
            (3,d,2), (5,d,2), (4,d,2), (3,d,3), (2,d,2),
            (5,d,0), (0,d,5), (2,d,3), (3,d,1), (4,d,1)
        ]
        
        seasonal_candidates = [
            self.seasonal_order,
            (1,1,1,7), (2,1,1,7), (1,1,2,7), (2,1,2,7),
            (1,0,1,7), (0,1,1,7), (1,1,0,7), (2,0,1,7)
        ]
        
        for order in candidates[:12]:
            for s_order in seasonal_candidates[:4]:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        if self.use_sarimax:
                            model = SARIMAX(y, order=order, seasonal_order=s_order, enforce_stationarity=False, enforce_invertibility=False)
                            fit = model.fit(disp=False, maxiter=100)
                        else:
                            model = ARIMA(y, order=order)
                            fit = model.fit()
                        # Weighted AIC/BIC
                        score = 0.6 * fit.aic + 0.4 * fit.bic
                        if score < best_score:
                            best_score = score
                            best_order = order
                            best_seasonal = s_order
                except Exception:
                    continue
        
        logger.info(f"Auto-selected ARIMA v4 order {best_order} seasonal {best_seasonal} score {best_score:.2f}")
        return best_order, best_seasonal

    def fit(self, X_train=None, y_train: np.ndarray = None, X_val=None, y_val=None, exog=None, **kwargs):
        if y_train is None:
            raise ValueError("y_train required for ARIMA")
        
        if isinstance(y_train, pd.Series):
            y = y_train.values
        else:
            y = np.asarray(y_train).ravel()

        self.history = y.copy()
        logger.info(f"Training ARIMA v4 MAX order={self.order} seasonal={self.seasonal_order} on {len(y)} points | auto={self.use_auto} sarimax={self.use_sarimax}")

        if self.use_auto:
            try:
                best_order, best_seasonal = self._find_best_order(y)
                self.order = best_order
                self.seasonal_order = best_seasonal
            except Exception as e:
                logger.warning(f"Auto order selection failed: {e}, using default {self.order}")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if self.use_sarimax:
                    model = SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order, 
                                   exog=exog,
                                   enforce_stationarity=False, enforce_invertibility=False,
                                   initialization='approximate_diffuse')
                    self.model_fit = model.fit(disp=False, maxiter=200, low_memory=True)
                else:
                    model = ARIMA(y, order=self.order, exog=exog)
                    self.model_fit = model.fit()
                
                self.residuals = self.model_fit.resid
                try:
                    self.conf_int = self.model_fit.conf_int()
                except Exception:
                    pass
                
                logger.info(f"ARIMA v4 AIC: {self.model_fit.aic:.2f} BIC: {self.model_fit.bic:.2f} | params {len(self.model_fit.params)} | resid std {np.std(self.residuals):.4f}")
            except Exception as e:
                logger.error(f"ARIMA v4 fit failed: {e}, trying simpler (2,1,2)")
                try:
                    model = ARIMA(y, order=(2,1,2))
                    self.model_fit = model.fit()
                    self.residuals = self.model_fit.resid
                except Exception as e2:
                    logger.error(f"Even simple ARIMA failed: {e2}, trying (1,1,0)")
                    try:
                        model = ARIMA(y, order=(1,1,0))
                        self.model_fit = model.fit()
                        self.residuals = self.model_fit.resid
                    except Exception as e3:
                        logger.error(f"All ARIMA failed: {e3}, using naive forecast")
                        self.model_fit = None
                        self.residuals = np.diff(y)

        self.is_fitted = True
        return {
            "aic": getattr(self.model_fit, 'aic', 0) if self.model_fit else 0, 
            "bic": getattr(self.model_fit, 'bic', 0) if self.model_fit else 0,
            "order": self.order,
            "seasonal_order": self.seasonal_order,
            "resid_std": float(np.std(self.residuals)) if self.residuals is not None else 0,
            "version": "v4_max"
        }

    def predict(self, X=None, steps: int = None, return_conf_int: bool = False) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        if steps is None:
            if X is not None:
                if isinstance(X, (int, np.integer)):
                    steps = int(X)
                elif isinstance(X, np.ndarray):
                    steps = len(X) if X.ndim == 1 else X.shape[0]
                else:
                    steps = len(X)
            else:
                steps = 1

        if self.model_fit is None:
            logger.warning("Using naive forecast (last value) as ARIMA fallback v4")
            # Trend-adjusted naive
            if len(self.history) >= 2:
                trend = self.history[-1] - self.history[-2]
                return np.array([self.history[-1] + trend * (i+1) * 0.5 for i in range(steps)])
            return np.full(steps, self.history[-1])

        try:
            if return_conf_int:
                forecast = self.model_fit.get_forecast(steps=steps)
                return forecast.predicted_mean, forecast.conf_int()
            else:
                forecast = self.model_fit.forecast(steps=steps)
                return np.array(forecast)
        except Exception as e:
            logger.warning(f"Forecast failed: {e}, using trend-adjusted naive")
            if len(self.history) >= 2:
                trend = np.mean(np.diff(self.history[-10:]))
                return np.array([self.history[-1] + trend * (i+1) for i in range(steps)])
            return np.full(steps, self.history[-1])

    def predict_in_sample(self) -> np.ndarray:
        if not self.is_fitted or self.model_fit is None:
            return self.history
        try:
            return self.model_fit.fittedvalues
        except Exception:
            return self.history

    def forecast_future(self, last_sequence=None, steps: int = 7) -> np.ndarray:
        return self.predict(steps=steps)

    def get_residuals(self):
        return self.residuals
