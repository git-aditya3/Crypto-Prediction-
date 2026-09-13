import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import numpy as np
from crypto_prediction.models.transformer_model import TransformerModel

def test_transformer():
    np.random.seed(42)
    X_train = np.random.randn(100, 20, 10)
    y_train = np.random.randn(100)
    X_val = np.random.randn(20, 20, 10)
    y_val = np.random.randn(20)

    model = TransformerModel(input_size=10, d_model=32, nhead=2, num_layers=1, dim_feedforward=64)
    hist = model.fit(X_train, y_train, X_val, y_val, epochs=3, batch_size=16)
    preds = model.predict(X_val)
    assert len(preds) == len(y_val)
    print(f"Transformer test passed, preds {preds[:3]}")

if __name__ == "__main__":
    test_transformer()
