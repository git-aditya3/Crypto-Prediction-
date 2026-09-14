@echo off
rem ============================================================================
rem Crypto Prediction - one-shot installer (Windows cmd / PowerShell / git bash)
rem
rem   install.bat
rem
rem Creates a virtual environment (.venv) and installs everything needed.
rem Pretrained models already ship in models/ - no training step required.
rem ============================================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: python not found. Install Python 3.10+ from https://www.python.org
    echo        and make sure "Add python.exe to PATH" is checked.
    exit /b 1
)

if not exist .venv (
    echo ==^> Creating virtual environment (.venv)...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo ==^> Upgrading pip...
python -m pip install --upgrade pip >nul

echo ==^> Installing dependencies (torch is large - can take a few minutes)...
pip install -r requirements.txt

echo.
echo ============================================================
echo  Install complete!
echo.
echo  Start the app:       start.bat           (web + API on :8000)
echo  Self-diagnostic:     python run.py check
echo  Predict from CLI:    python run.py predict --symbol BTC-USD
echo  Web dashboard:       http://localhost:8000
echo  API docs:            http://localhost:8000/docs
echo ============================================================
