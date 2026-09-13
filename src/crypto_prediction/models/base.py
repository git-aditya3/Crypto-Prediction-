"""
Base model interface
"""
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import joblib
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)

class BaseModel(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.model = None

    @abstractmethod
    def fit(self, X_train, y_train, X_val=None, y_val=None, **kwargs):
        pass

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        pass

    def evaluate(self, X, y_true) -> Dict[str, float]:
        from ..evaluation.metrics import compute_regression_metrics
        y_pred = self.predict(X)
        return compute_regression_metrics(y_true, y_pred)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Saved model {self.name} to {path}")

    @classmethod
    def load(cls, path: str):
        model = joblib.load(path)
        logger.info(f"Loaded model {model.name} from {path}")
        return model

    def forecast_future(self, last_sequence: np.ndarray, steps: int = 7) -> np.ndarray:
        """Autoregressive future forecast - override if needed"""
        raise NotImplementedError(f"{self.name} does not implement forecast_future")
