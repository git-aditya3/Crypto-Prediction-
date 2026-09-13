"""
ARIMA model wrapper
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings
from .base import BaseModel
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class ARIMAModel(BaseModel):
    def __init__(self, order: tuple = None):
        super().__init__(name="arima")
        self.order = order or config.model.arima_order
        self.model_fit = None
        self.history = None

    def fit(self, X_train=None, y_train: np.ndarray = None, X_val=None, y_val=None, **kwargs):
        """
        ARIMA only needs y_train (price series). X ignored.
        y_train can be scaled or raw; we store history for forecasting
        """
        if y_train is None:
            raise ValueError("y_train required for ARIMA")
        
        # If X_train is provided as price series DataFrame, use Close
        if isinstance(y_train, pd.Series):
            y = y_train.values
        else:
            y = y_train

        self.history = y.copy()
        logger.info(f"Training ARIMA order={self.order} on {len(y)} points")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = ARIMA(y, order=self.order)
                self.model_fit = model.fit()
                logger.info(f"ARIMA AIC: {self.model_fit.aic:.2f}")
            except Exception as e:
                logger.error(f"ARIMA fit failed: {e}, trying simpler order (1,1,0)")
                model = ARIMA(y, order=(1,1,0))
                self.model_fit = model.fit()

        self.is_fitted = True
        return {"aic": self.model_fit.aic, "bic": self.model_fit.bic}

    def predict(self, X=None, steps: int = None) -> np.ndarray:
        """
        If X is None, predict in-sample or future
        For evaluation, if X is test y shape, we forecast len(X) steps
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        if steps is None:
            if X is not None:
                # X may be y_test or len
                if isinstance(X, (int, np.integer)):
                    steps = int(X)
                elif isinstance(X, np.ndarray):
                    steps = len(X) if X.ndim == 1 else X.shape[0]
                else:
                    steps = len(X)
            else:
                steps = 1

        # Forecast
        forecast = self.model_fit.forecast(steps=steps)
        return np.array(forecast)

    def predict_in_sample(self) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        return self.model_fit.fittedvalues

    def forecast_future(self, last_sequence=None, steps: int = 7) -> np.ndarray:
        return self.predict(steps=steps)
