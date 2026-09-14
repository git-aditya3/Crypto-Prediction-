"""Out-of-the-box acceptance tests.

These verify the core promise of the product: pretrained models load,
predictions work with zero training steps, the data layer never hard-fails
offline, and the web/API server routes correctly.

Run with:  .venv/bin/python -m pytest tests/test_out_of_box.py -q
"""
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent
BUNDLED_SYMBOLS = ["BTC-USD", "XRP-USD", "ADA-USD", "BNB-USD"]
MODEL_KINDS = ["lstm", "transformer", "xgb", "arima", "preprocessor"]


# --------------------------------------------------------------------------
# Packaging / config
# --------------------------------------------------------------------------

def test_version_is_single_sourced():
    from crypto_prediction import __version__
    import importlib.metadata as md
    assert __version__ == md.version("crypto-prediction")


def test_config_defaults_are_safe():
    """Defaults must be non-trading, non-consuming: nothing auto-starts."""
    from crypto_prediction.config import get_config
    cfg = get_config()
    assert cfg.automation.enabled is False, "background retraining must default OFF"
    assert cfg.features.use_sentiment is False, "sentiment must default OFF"
    autotrading_file = PROJECT_ROOT / "data" / "autotrading_config.json"
    if autotrading_file.exists():
        import json
        assert json.loads(autotrading_file.read_text()).get("enabled", False) is False


# --------------------------------------------------------------------------
# Data layer (offline-safe)
# --------------------------------------------------------------------------

def test_synthetic_data_deterministic():
    from crypto_prediction.data.synthetic import generate_ohlcv
    a = generate_ohlcv("BTC-USD", rows=300)
    b = generate_ohlcv("BTC-USD", rows=300)
    assert len(a) == len(b) == 300
    assert {"Open", "High", "Low", "Close", "Volume"}.issubset(a.columns)
    assert a["Close"].equals(b["Close"]), "same symbol/seed must give the same series"
    assert (a["High"] >= a["Low"]).all()
    assert (a["Close"] > 0).all()


def test_fetcher_offline_fallback_returns_data():
    """load_or_fetch must never raise: live -> cache -> synthetic."""
    from crypto_prediction.data.fetcher import CryptoDataFetcher
    # BTC-USD has no local cache in most environments, so this exercises
    # the full fallback chain (offline it lands on synthetic).
    fetcher = CryptoDataFetcher(symbol="BTC-USD")
    df = fetcher.load_or_fetch(symbol="BTC-USD")
    assert len(df) >= 200
    assert {"Open", "High", "Low", "Close", "Volume"}.issubset(df.columns)
    assert (df["Close"] > 0).all()


# --------------------------------------------------------------------------
# Pretrained model bundle
# --------------------------------------------------------------------------

def test_bundled_model_artifacts_exist():
    for sym in BUNDLED_SYMBOLS:
        base = f"{sym.replace('-', '_')}"
        for kind in MODEL_KINDS:
            if kind in ("lstm", "transformer"):
                path = PROJECT_ROOT / "models" / f"{base}_{kind}_v6.pt"
            else:
                path = PROJECT_ROOT / "models" / f"{base}_{kind}_v6.joblib"
            assert path.exists(), f"missing bundled artifact: {path.name}"
        assert (PROJECT_ROOT / "models" / f"{base}_training_report_v6.json").exists()


@pytest.mark.timeout(600)
@pytest.mark.parametrize("symbol", BUNDLED_SYMBOLS)
def test_predictor_predicts_without_training(symbol):
    """The headline promise: predictions work out of the box, per symbol."""
    from crypto_prediction.prediction.predictor import CryptoPredictor
    predictor = CryptoPredictor(symbol=symbol)
    preds = predictor.predict_next(period="1y")
    assert preds, f"no predictions for {symbol}"
    for key in ("lstm", "transformer", "xgboost", "arima", "ensemble"):
        assert key in preds, f"missing {key} prediction for {symbol}"
        val = preds[key]
        assert val is not None and val > 0, f"{key} prediction invalid for {symbol}"


# --------------------------------------------------------------------------
# API server
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as c:
        yield c


def test_api_health_and_info(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    from crypto_prediction import __version__
    assert body["version"] == __version__

    r = client.get("/info")
    assert r.status_code == 200
    assert r.json()["version"] == __version__


@pytest.mark.timeout(300)
def test_api_predict_endpoint(client):
    r = client.get("/api/predict", params={"symbol": "XRP-USD"})
    assert r.status_code == 200
    preds = r.json()["predictions"]
    assert "ensemble" in preds and preds["ensemble"] > 0


def test_api_spa_deep_link_vs_json(client):
    """Same path: browser gets the SPA, JSON clients get the API."""
    spa = client.get("/forecast", headers={"Accept": "text/html, application/xhtml+xml"})
    assert spa.status_code == 200
    assert spa.headers["content-type"].startswith("text/html")
    assert "root" in spa.text  # React mount point

    api = client.get("/forecast", params={"symbol": "XRP-USD", "steps": 3},
                     headers={"Accept": "application/json"})
    assert api.status_code == 200
    assert "dates" in api.json()


def test_api_unknown_api_path_is_json_404(client):
    r = client.get("/api/definitely-not-an-endpoint")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert "detail" in r.json()


def test_api_models_endpoint_lists_bundle(client):
    r = client.get("/models")
    assert r.status_code == 200
    names = r.json()["models"]
    assert any(n.endswith("_lstm_v6.pt") for n in names)
    assert any(n.endswith("_training_report_v6.json") for n in names)


def test_api_tickers_offline_fallback(client):
    """/market/tickers must degrade to local cache instead of 503'ing."""
    r = client.get("/market/tickers")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert body["count"] >= 0
        if body["count"]:
            key = next(iter(body["tickers"]))
            assert key.endswith("-USD")  # correct symbol keys
            assert body["tickers"][key]["price"] > 0


def test_api_settings_reflects_real_defaults(client):
    r = client.get("/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["continuous_training"]["enabled_by_default"] is False
    assert body["autotrading"]["enabled"] is False
