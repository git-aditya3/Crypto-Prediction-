#!/usr/bin/env bash
# ============================================================================
# Crypto Prediction - start the web app + REST API
#
#   ./start.sh                 # web dashboard + API on http://localhost:8000
#   ./start.sh check           # self-diagnostic
#   ./start.sh predict         # predict BTC-USD (next 7 days)
#   ./start.sh train           # retrain models on fresh live data
#   ./start.sh dashboard       # Streamlit dashboard on :8501
#
# Uses the .venv created by ./install.sh (falls back to system python).
# ============================================================================
set -e
cd "$(dirname "$0")"

if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
elif ! python -c "import fastapi" >/dev/null 2>&1; then
    echo "Dependencies not found. Run ./install.sh first."
    exit 1
fi

exec python run.py "$@"
