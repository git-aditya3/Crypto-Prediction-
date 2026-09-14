#!/usr/bin/env bash
# ============================================================================
# Crypto Prediction - one-shot installer (git bash / macOS / Linux)
#
#   ./install.sh
#
# Creates a virtual environment and installs everything the app needs.
# Pretrained models already ship in models/ - no training step required.
# ============================================================================
set -e
cd "$(dirname "$0")"

echo "==> [1/3] Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.10+ from https://www.python.org"
    exit 1
fi
echo "    $(python3 --version 2>&1)"

echo "==> [2/3] Creating virtual environment (.venv)..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null

echo "==> [3/3] Installing dependencies (torch is large - can take a few minutes)..."
pip install -r requirements.txt

echo
echo "============================================================"
echo "  Install complete!"
echo
echo "  Start the app:       ./start.sh          (web + API on :8000)"
echo "  Self-diagnostic:     python run.py check"
echo "  Predict from CLI:    python run.py predict --symbol BTC-USD"
echo "  Web dashboard:       http://localhost:8000"
echo "  API docs:            http://localhost:8000/docs"
echo "============================================================"
