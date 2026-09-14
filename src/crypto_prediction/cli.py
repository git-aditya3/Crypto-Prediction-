"""
Crypto Prediction - unified command line interface.

One entry point for the whole platform:

    crypto-prediction            (serve the web app + API, the default)
    crypto-prediction serve      start FastAPI + web dashboard
    crypto-prediction dashboard  start the Streamlit dashboard
    crypto-prediction predict    run a prediction for a symbol
    crypto-prediction train      (re)train models on fresh data
    crypto-prediction backtest   run a backtest
    crypto-prediction check      self-diagnostic (deps, data, models, prediction)
    crypto-prediction install    install python dependencies

Everything works out of the box: pretrained models ship in ``models/`` and
the data layer falls back (live API -> local cache -> labelled synthetic
series) so no command requires the network.
"""
import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Make the repo importable even when the package is not pip-installed
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from crypto_prediction.config import get_config, validate_config  # noqa: E402
from crypto_prediction.utils.logger import get_logger  # noqa: E402

logger = get_logger("crypto_prediction.cli")
config = get_config()

BUNDLED_SYMBOLS = ["BTC-USD", "XRP-USD", "ADA-USD", "BNB-USD"]

OK = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def _check_deps() -> list:
    checks = []
    required = {
        "numpy": "numpy", "pandas": "pandas", "scikit-learn": "sklearn",
        "torch": "torch", "xgboost": "xgboost", "statsmodels": "statsmodels",
        "yfinance": "yfinance", "requests": "requests", "fastapi": "fastapi",
        "uvicorn": "uvicorn", "joblib": "joblib", "python-dotenv": "dotenv",
        "plotly": "plotly",
    }
    for pip_name, mod in required.items():
        try:
            __import__(mod)
            checks.append((f"dependency: {pip_name}", True, ""))
        except Exception as e:
            checks.append((f"dependency: {pip_name}", False, f"{e} - run: python run.py install"))
    optional = {
        "streamlit": "streamlit (dashboard)",
        "websockets": "websockets (realtime feed)",
        "lightgbm": "lightgbm (ensemble meta-learner, optional)",
        "transformers": "transformers (FinBERT sentiment, optional)",
        "praw": "praw (Reddit sentiment, optional)",
    }
    for mod, label in optional.items():
        try:
            __import__(mod)
            checks.append((f"optional: {label}", True, "installed"))
        except Exception:
            checks.append((f"optional: {label}", None, "not installed (features degrade gracefully)"))
    return checks


def _check_bundled_models() -> list:
    checks = []
    models_dir = config.project_root / "models"
    for symbol in BUNDLED_SYMBOLS:
        safe = symbol.replace("-", "_")
        pre = models_dir / f"{safe}_preprocessor_v6.joblib"
        have = [n for n in ("lstm", "transformer", "xgb", "arima", "ensemble")
                if (models_dir / f"{safe}_{n}_v6.{'pt' if n in ('lstm', 'transformer') else 'joblib'}").exists()]
        if pre.exists() and len(have) >= 2:
            checks.append((f"bundled models: {symbol}", True, ", ".join(have)))
        elif pre.exists() or have:
            checks.append((f"bundled models: {symbol}", None, "partial - " + ", ".join(have)))
        else:
            checks.append((f"bundled models: {symbol}", False, "missing - run: python run.py train --symbol " + symbol))
    return checks


def _check_data(offline: bool = False) -> list:
    checks = []
    from crypto_prediction.data.fetcher import CryptoDataFetcher
    for symbol in BUNDLED_SYMBOLS:
        fetcher = CryptoDataFetcher(symbol=symbol)
        if offline:
            # seed from local cache / synthetic without touching the network
            safe = symbol.replace("-", "_")
            cache_path = config.project_root / "data" / "raw" / f"{safe}_1d.csv"
            if cache_path.exists():
                import pandas as pd
                fetcher._cache[safe] = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            else:
                from crypto_prediction.data.synthetic import generate_ohlcv
                fetcher._cache[safe] = generate_ohlcv(symbol=symbol, rows=1100)
        try:
            df = fetcher.load_or_fetch(symbol=symbol, force_refresh=False)
            age_note = ""
            src = "live/cache"
            checks.append((f"data: {symbol}", True, f"{len(df)} rows, {df.index[0].date()} -> {df.index[-1].date()}{age_note}"))
        except Exception as e:
            checks.append((f"data: {symbol}", False, str(e)[:120]))
    return checks


def _check_prediction(offline: bool = False) -> list:
    checks = []
    from crypto_prediction.prediction.predictor import CryptoPredictor
    for symbol in BUNDLED_SYMBOLS:
        try:
            predictor = CryptoPredictor(symbol=symbol)
            if not predictor.models:
                checks.append((f"prediction: {symbol}", False, "no models loaded"))
                continue
            preds = predictor.predict_next(period="2y")
            if preds and "ensemble" in preds:
                checks.append((
                    f"prediction: {symbol}", True,
                    f"next-day ensemble ${preds['ensemble']:,.2f} from {len(preds) - 2} models"
                ))
            else:
                checks.append((f"prediction: {symbol}", False, "prediction returned empty"))
        except Exception as e:
            checks.append((f"prediction: {symbol}", False, str(e)[:120]))
    return checks


def _check_api() -> list:
    try:
        api_dir = str(PROJECT_ROOT / "api")
        if api_dir not in sys.path:
            sys.path.insert(0, api_dir)
        import main  # noqa: F401  (api/main.py)
        return [("api: import api.main", True, "FastAPI app imports cleanly")]
    except Exception as e:
        return [("api: import api.main", False, str(e)[:160])]


def cmd_check(args):
    print("\nCrypto Prediction - self diagnostic")
    print("=" * 60)
    all_checks = []
    all_checks += _check_deps()
    all_checks += _check_bundled_models()
    all_checks += _check_data(offline=args.offline)
    all_checks += _check_prediction(offline=args.offline)
    all_checks += _check_api()

    failures = 0
    for name, status, detail in all_checks:
        if status is True:
            mark = OK
        elif status is False:
            mark = FAIL
            failures += 1
        else:
            mark = WARN
        print(f"  [{mark}] {name}" + (f"  -  {detail}" if detail else ""))

    print("=" * 60)
    if failures:
        print(f"  {failures} check(s) FAILED. Re-run with `python run.py install` to repair dependencies.")
        return 1
    print("  All required checks passed - you are ready to go: `python run.py`")
    return 0


# --------------------------------------------------------------------------
# serve
# --------------------------------------------------------------------------
def cmd_serve(args):
    import uvicorn
    port = args.port or int(os.getenv("CRYPTOPRED_API_PORT", config.api.port))
    host = args.host or config.api.host
    print(f"\n  Starting Crypto Prediction on http://{host}:{port}")
    print(f"  Web dashboard : http://localhost:{port}/")
    print(f"  REST API docs : http://localhost:{port}/docs")
    print(f"  Predict now   : curl 'http://localhost:{port}/predict?symbol=BTC-USD'")
    print("  (pretrained models bundled - prediction works without any training)\n")
    try:
        # Import the app in-process so `serve` works from any CWD and when
        # installed via pip (uvicorn's "api.main:app" import string would not).
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from api.main import app
        uvicorn.run(app, host=host, port=port, log_level="warning")
    except Exception as e:
        print(f"  Failed to start API: {e}")
        print("  Hint: run `python run.py check` to diagnose.")
        sys.exit(1)


def cmd_dashboard(args):
    import subprocess
    port = args.port or int(os.getenv("STREAMLIT_PORT", "8501"))
    print(f"\n  Starting Streamlit dashboard on http://localhost:{port}\n")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(PROJECT_ROOT / "app" / "streamlit_app.py"),
        "--server.port", str(port), "--server.address", "0.0.0.0",
        "--server.headless", "true",
    ]
    subprocess.run(cmd)


# --------------------------------------------------------------------------
# predict / train / backtest
# --------------------------------------------------------------------------
def cmd_predict(args):
    import json as _json
    from crypto_prediction.prediction.predictor import CryptoPredictor
    predictor = CryptoPredictor(symbol=args.symbol)
    if not predictor.models:
        print(f"No models found for {args.symbol}.")
        print(f"  - Bundled models cover: {', '.join(BUNDLED_SYMBOLS)}")
        print(f"  - Or train: python run.py train --symbol {args.symbol}")
        sys.exit(1)
    try:
        next_preds = predictor.predict_next(period=args.period)
        forecast = predictor.forecast(steps=args.steps, period=args.period)
        signal = predictor.get_trading_signal(forecast)
    except Exception as e:
        print(f"Prediction failed: {e}")
        sys.exit(1)

    if args.json:
        print(_json.dumps({"next": next_preds, "forecast": forecast, "signal": signal}, indent=2, default=float))
        return

    print(f"\n=== {args.symbol} Prediction ===")
    print(f"Current Price: ${forecast.get('current_price', 0):,.2f}")
    print("\nNext Price Predictions:")
    for model, price in next_preds.items():
        if model in ("uncertainty", "confidence"):
            continue
        print(f"  {model:12s}: ${price:,.2f}")
    print(f"\n{args.steps}-Day Forecast (Ensemble):")
    for d, p in zip(forecast.get('dates', []), forecast.get('ensemble', [])):
        print(f"  {d}: ${p:,.2f}")
    if "upper_band" in forecast and "lower_band" in forecast:
        print("\n95% Confidence Band (ensemble):")
        for d, up, lo in zip(forecast.get('dates', []), forecast['upper_band'], forecast['lower_band']):
            print(f"  {d}: ${lo:,.2f} - ${up:,.2f}")
    print(f"\nTrading Signal: {signal['signal']} ({signal['confidence']:.0f}% confidence)")
    print(f"  {signal['reason']}")


def cmd_train(args):
    from crypto_prediction.training.trainer import Trainer
    if args.epochs:
        config.model.lstm_epochs = args.epochs
        config.model.transformer_epochs = args.epochs
        config.model.gru_epochs = args.epochs
        config.model.tcn_epochs = args.epochs
    trainer = Trainer(symbol=args.symbol, use_sentiment=not args.no_sentiment)
    results = trainer.train_all(period=args.period, interval=args.interval, force_refresh=args.force_refresh, epochs=args.epochs)
    print("\nTraining complete:")
    for name, res in (results or {}).items():
        m = res.get("metrics", {}) or {}
        print(f"  {name:12s} MAPE {m.get('mape', 0):6.2f}%  DirAcc {m.get('directional_accuracy', 0):5.1f}%")
    print(f"\nModels saved to {config.project_root / 'models'}")
    print(f"Predict again:  python run.py predict --symbol {args.symbol}")


def cmd_backtest(args):
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.backtest import main as backtest_main
    sys.argv = ["backtest.py", "--symbol", args.symbol, "--strategy", args.strategy, "--period", args.period]
    backtest_main()


def cmd_install(args):
    import subprocess
    req = PROJECT_ROOT / "requirements.txt"
    print(f"Installing dependencies from {req.name} into {sys.executable} ...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)])
    if r.returncode != 0:
        print("Install failed - check the output above (internet access required).")
        sys.exit(r.returncode)
    print("\nDependencies installed. Next:  python run.py check   then   python run.py")


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crypto-prediction", description="Crypto Prediction platform - one command for everything")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("serve", help="start the web app + REST API (default)")
    sp.add_argument("--host", type=str, default=None)
    sp.add_argument("--port", type=int, default=None)
    sp.set_defaults(func=cmd_serve)

    sp = sub.add_parser("dashboard", help="start the Streamlit dashboard")
    sp.add_argument("--port", type=int, default=None)
    sp.set_defaults(func=cmd_dashboard)

    sp = sub.add_parser("predict", help="predict prices for a symbol")
    sp.add_argument("--symbol", type=str, default="BTC-USD")
    sp.add_argument("--steps", type=int, default=7)
    sp.add_argument("--period", type=str, default="2y")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_predict)

    sp = sub.add_parser("train", help="(re)train models on fresh data")
    sp.add_argument("--symbol", type=str, default="BTC-USD")
    sp.add_argument("--period", type=str, default="2y")
    sp.add_argument("--interval", type=str, default="1d")
    sp.add_argument("--epochs", type=int, default=None)
    sp.add_argument("--force-refresh", action="store_true")
    sp.add_argument("--no-sentiment", action="store_true")
    sp.set_defaults(func=cmd_train)

    sp = sub.add_parser("backtest", help="run a backtest")
    sp.add_argument("--symbol", type=str, default="BTC-USD")
    sp.add_argument("--strategy", type=str, default="ensemble")
    sp.add_argument("--period", type=str, default="2y")
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("check", help="self-diagnostic: deps, data, models, prediction")
    sp.add_argument("--offline", action="store_true", help="skip live network attempts (use cache/synthetic)")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("install", help="install python dependencies")
    sp.set_defaults(func=cmd_install)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        # default: serve
        args.host = None
        args.port = None
        args.func = cmd_serve
    try:
        validate_config()
    except AssertionError as e:
        print(f"Config error: {e}")
        sys.exit(1)
    rc = args.func(args)
    sys.exit(rc if isinstance(rc, int) else 0)


# Console-script entry points (pyproject [project.scripts]).
# All user arguments are passed through, so e.g.
# `crypto-predict --symbol XRP-USD --steps 14` behaves exactly like the
# `python run.py predict --symbol XRP-USD --steps 14` equivalent.
def entry_serve():
    args = sys.argv[1:]
    if not args:
        main(["serve"])
    elif args[0] in ("-h", "--help"):
        main(["--help"])            # top-level help
    elif args[0] == "serve":
        main(args)
    elif args[0].startswith("-"):
        main(["serve"] + args)      # `crypto-prediction --port 9000`
    else:
        main(args)


def entry_train():
    main(["train"] + sys.argv[1:])


def entry_predict():
    main(["predict"] + sys.argv[1:])


def entry_backtest():
    main(["backtest"] + sys.argv[1:])


def entry_check():
    main(["check"] + sys.argv[1:])


if __name__ == "__main__":
    main()
