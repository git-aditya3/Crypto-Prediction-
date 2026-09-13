import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import numpy as np
from crypto_prediction.models.xgboost_model import XGBoostModel
from crypto_prediction.models.arima_model import ARIMAModel

def test_xgboost():
    X_train = np.random.rand(100, 10)
    y_train = np.random.rand(100)
    X_val = np.random.rand(20, 10)
    y_val = np.random.rand(20)
    
    model = XGBoostModel(n_estimators=10, max_depth=3)
    model.fit(X_train, y_train, X_val, y_val)
    preds = model.predict(X_val)
    assert len(preds) == len(y_val)
    print("XGBoost test passed")

def test_arima():
    y_train = np.random.rand(100)*100 + 100
    model = ARIMAModel(order=(1,1,0))
    model.fit(y_train=y_train)
    preds = model.predict(steps=5)
    assert len(preds) == 5
    print("ARIMA test passed")

if __name__ == "__main__":
    test_xgboost()
    test_arima()
