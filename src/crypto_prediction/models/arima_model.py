"""
ARIMA model v3 Improved Accuracy
- Auto order selection
- Seasonal ARIMA support
- Better handling of non-stationary data
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class ARIMAModel(BaseModel):
    def __init__(self, order: tuple = None, seasonal_order: tuple = None, use_sarimax: bool = True):
        super().__init__(name="arima")
        self.order = order or config.model.arima_order
        self.seasonal_order = seasonal_order or config.model.arima_seasonal_order
        self.use_sarimax = use_sarimax
        self.model_fit = None
        self.history = None

    def _find_best_order(self, y, max_p=3, max_d=2, max_q=3):
        """Simple grid search for best ARIMA order based on AIC"""
        best_aic = float('inf')
        best_order = self.order
        
        # Try few combinations around default
        candidates = [
            self.order,
            (1, 1, 0),
            (1, 1, 1),
            (2, 1, 1),
            (2, 1, 2),
            (3, 1, 1),
            (5, 1, 0),
            (5, 1, 2),
        ]
        
        for order in candidates:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = ARIMA(y, order=order)
                    fit = model.fit()
                    if fit.aic < best_aic:
                        best_aic = fit.aic
                        best_order = order
            except Exception:
                continue
        
        logger.info(f"Auto-selected ARIMA order {best_order} with AIC {best_aic:.2f} (from {len(candidates)} candidates)")
        return best_order

    def fit(self, X_train=None, y_train: np.ndarray = None, X_val=None, y_val=None, **kwargs):
        if y_train is None:
            raise ValueError("y_train required for ARIMA")
        
        if isinstance(y_train, pd.Series):
            y = y_train.values
        else:
            y = y_train

        self.history = y.copy()
        logger.info(f"Training ARIMA v3 order={self.order} seasonal={self.seasonal_order} on {len(y)} points | use_sarimax={self.use_sarimax}")

        # Auto-select order if enabled
        try:
            best_order = self._find_best_order(y)
            self.order = best_order
        except Exception as e:
            logger.warning(f"Auto order selection failed: {e}, using default {self.order}")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if self.use_sarimax:
                    # SARIMAX with weekly seasonality (7 days)
                    model = SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order, 
                                   enforce_stationarity=False, enforce_invertibility=False)
                    self.model_fit = model.fit(disp=False)
                else:
                    model = ARIMA(y, order=self.order)
                    self.model_fit = model.fit()
                logger.info(f"ARIMA v3 AIC: {self.model_fit.aic:.2f} BIC: {self.model_fit.bic:.2f}")
            except Exception as e:
                logger.error(f"ARIMA v3 fit failed: {e}, trying simpler order (1,1,0)")
                try:
                    model = ARIMA(y, order=(1,1,0))
                    self.model_fit = model.fit()
                except Exception as e2:
                    logger.error(f"Even simple ARIMA failed: {e2}, using naive forecast")
                    # Fallback: store last value for naive forecast
                    self.model_fit = None

        self.is_fitted = True
        return {"aic": getattr(self.model_fit, 'aic', 0) if self.model_fit else 0, 
                "bic": getattr(self.model_fit, 'bic', 0) if self.model_fit else 0,
                "order": self.order}

    def predict(self, X=None, steps: int = None) -> np.ndarray:
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
            # Naive forecast: last value
            logger.warning("Using naive forecast (last value) as ARIMA fallback")
            return np.full(steps, self.history[-1])

        try:
            forecast = self.model_fit.forecast(steps=steps)
            return np.array(forecast)
        except Exception as e:
            logger.warning(f"Forecast failed: {e}, using naive")
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
