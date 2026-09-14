@echo off
rem ============================================================================
rem Crypto Prediction - start the web app + REST API
rem
rem   start.bat                 web dashboard + API on http://localhost:8000
rem   start.bat check           self-diagnostic
rem   start.bat predict         predict BTC-USD (next 7 days)
rem   start.bat train           retrain models on fresh live data
rem   start.bat dashboard       Streamlit dashboard on :8501
rem ============================================================================
cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    python -c "import fastapi" >nul 2>nul
    if errorlevel 1 (
        echo Dependencies not found. Run install.bat first.
        exit /b 1
    )
)

python run.py %*
