#!/usr/bin/env python3
"""
Crypto Prediction - single entry point.

    python run.py                # start the web app + REST API (default)
    python run.py check          # self-diagnostic (deps, data, models, prediction)
    python run.py predict        # predict BTC-USD for the next 7 days
    python run.py train          # (re)train models on fresh live data
    python run.py dashboard      # Streamlit dashboard
    python run.py backtest       # backtest the ensemble strategy
    python run.py install        # install python dependencies

Pretrained models ship in models/ - prediction works out of the box,
no training step required.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from crypto_prediction.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
