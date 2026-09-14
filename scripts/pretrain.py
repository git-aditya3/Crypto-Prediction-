"""
Train the BUNDLED PRETRAINED models that ship with the repository.

These artifacts are committed under ``models/`` so that prediction works
out of the box - users do NOT need to train anything first.

Data sources (in priority order, per symbol):
  1. local cache in data/raw (real market data, e.g. XRP/ADA/BNB CSVs),
  2. live fetch (Binance -> Yahoo -> CoinGecko),
  3. deterministic synthetic series (offline safety net, clearly labelled).

Usage:
    python scripts/pretrain.py                        # all bundled symbols
    python scripts/pretrain.py --symbols BTC-USD      # one symbol
    python scripts/pretrain.py --keep-all-versions    # keep v5/v4/no-suffix copies too
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.config import get_config
from crypto_prediction.utils.logger import get_logger
import crypto_prediction.training.trainer as trainer_mod

logger = get_logger(__name__)
config = get_config()

BUNDLED_SYMBOLS = ["BTC-USD", "XRP-USD", "ADA-USD", "BNB-USD"]
MODELS_PER_SYMBOL = ["lstm", "transformer", "xgb", "arima", "ensemble"]


def apply_bundle_overrides():
    """Smaller hyperparameters => fast CPU training, small artifacts.

    The point of bundled models is a working, well-behaved baseline, not a
    research-grade fit. Users can retrain full-size models with
    ``python run.py train --symbol BTC-USD`` whenever they want.
    """
    m = config.model
    # LSTM - compact but non-trivial
    m.lstm_hidden_size = 96
    m.lstm_num_layers = 2
    m.lstm_epochs = 60
    m.lstm_patience = 10
    m.lstm_dropout = 0.25
    m.lstm_attention_heads = 4
    m.lstm_batch_size = 32
    # Transformer - compact
    m.transformer_d_model = 96
    m.transformer_nhead = 4
    m.transformer_num_layers = 2
    m.transformer_dim_feedforward = 192
    m.transformer_epochs = 45
    m.transformer_patience = 8
    m.transformer_dropout = 0.20
    m.transformer_batch_size = 32
    # XGBoost - fewer trees keeps the artifact small
    m.xgb_n_estimators = 400
    m.xgb_max_depth = 6
    m.xgb_learning_rate = 0.03
    m.xgb_early_stopping_rounds = 50
    m.xgb_use_shap = False
    # ARIMA - keep auto search but it is fast enough
    # Training pipeline
    t = config.training
    t.feature_selection_k = 60
    t.use_robust_scaler = True
    t.use_kalman_smoothing = True
    t.random_state = 42


def seed_offline_data(trainer, symbol: str):
    """Preseed the fetcher cache with synthetic data when there is no local
    real-data cache, so pretraining never depends on the network."""
    safe = symbol.replace("-", "_").replace("/", "_")
    cache_path = config.project_root / "data" / "raw" / f"{safe}_1d.csv"
    if not cache_path.exists():
        from crypto_prediction.data.synthetic import generate_ohlcv
        df = generate_ohlcv(symbol=symbol, rows=1100)
        trainer.dataset.fetcher._cache[safe] = df
        logger.info(f"Seeded synthetic offline data for {symbol} (no local cache found)")
    else:
        logger.info(f"Using local real-data cache for {symbol}: {cache_path}")


def clean_versions(symbol: str, keep_versions: set):
    """Delete model artifact copies not in keep_versions (trainer writes v6/v5/v4/'')."""
    safe = symbol.replace("-", "_").replace("/", "_")
    models_dir = config.project_root / "models"
    removed = []
    for p in models_dir.glob(f"{safe}_*"):
        if p.suffix not in (".pt", ".joblib"):
            continue
        matched_ver = None
        for ver in ("v6", "v5", "v4"):
            if p.name.endswith(f"_{ver}{p.suffix}"):
                matched_ver = ver
                break
        if matched_ver is None:
            # No version suffix: remove it when a kept versioned copy exists
            has_kept = any((models_dir / f"{p.stem}_{v}{p.suffix}").exists() for v in keep_versions)
            if has_kept:
                p.unlink()
                removed.append(p.name)
        elif matched_ver not in keep_versions:
            p.unlink()
            removed.append(p.name)
    if removed:
        logger.info(f"Cleaned {len(removed)} extra artifact copies for {symbol}: {removed}")


def main():
    parser = argparse.ArgumentParser(description="Train bundled pretrained models")
    parser.add_argument("--symbols", nargs="+", default=BUNDLED_SYMBOLS)
    parser.add_argument("--period", type=str, default="2y")
    parser.add_argument("--keep-all-versions", action="store_true")
    args = parser.parse_args()

    logger.info("Applying bundled-model hyperparameter overrides (fast CPU training)")
    apply_bundle_overrides()
    # GRU/TCN are not part of the bundled set (keeps artifacts lean)
    trainer_mod.HAS_GRU = False
    trainer_mod.HAS_TCN = False

    summary = {}
    for symbol in args.symbols:
        logger.info(f"\n{'='*70}\nPRETRAINING {symbol}\n{'='*70}")
        trainer = trainer_mod.Trainer(symbol=symbol, use_sentiment=False)
        seed_offline_data(trainer, symbol)
        results = trainer.train_all(period=args.period, interval="1d", force_refresh=False)
        keep = {"v6", "v5", "v4"} if args.keep_all_versions else {"v6"}
        clean_versions(symbol, keep)
        # The ensemble artifact embeds every sub-model (tens of MB) and is not
        # needed at prediction time - the predictor combines the individual
        # models itself. Keep the repo lean.
        ens = config.project_root / "models" / f"{symbol.replace('-', '_')}_ensemble_v6.joblib"
        if ens.exists():
            ens.unlink()
            logger.info("Removed bundled ensemble artifact (redundant at prediction time)")
        summary[symbol] = {
            name: {k: v for k, v in (res.get("metrics", {}) or {}).items() if k in ("mape", "rmse", "r2", "directional_accuracy", "sharpe")}
            for name, res in (results or {}).items()
        }
        logger.info(f"Bundled models ready for {symbol}: {list((results or {}).keys())}")

    report_path = config.project_root / "models" / "bundled_models_report.json"
    report = {"symbols": summary, "note": "Pretrained baseline models bundled for out-of-the-box prediction. Retrain on live data with: python run.py train --symbol BTC-USD"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"\nBundled pretraining complete. Report: {report_path}")
    for sym, res in summary.items():
        logger.info(f"  {sym}: " + ", ".join(f"{k} MAPE {v.get('mape', 0):.2f}%" for k, v in res.items() if v))


if __name__ == "__main__":
    main()
