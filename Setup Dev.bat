@echo off
rem ============================================================================
rem  English Coach - one-shot dev setup (Windows)
rem
rem  README promises the app can be run straight from source with
rem  python english_coach.py, but pip install -r requirements.txt is not
rem  enough on its own: the model weights are not pip packages and the spaCy
rem  English model is not on PyPI. This script does both halves.
rem
rem  Usage:
rem      "Setup Dev.bat"             install whatever is missing
rem      "Setup Dev.bat" --force     re-download even what is already there
rem      "Setup Dev.bat" whisper     only the named assets
rem
rem  What to install and where from comes from the _ASSETS table in
rem  english_coach.py; this script keeps no copy of those addresses.
rem ============================================================================
setlocal
cd /d "%~dp0"

if "%PYTHON%"=="" set "PYTHON=python"
echo ==^> Python:
"%PYTHON%" -V || goto :nopy

echo ==^> [1/2] Installing pip dependencies
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r requirements.txt || goto :fail

echo ==^> [2/2] Downloading components and models
"%PYTHON%" setup_assets.py %*

echo.
pause
exit /b 0

:nopy
echo   [X] Python not found. Activate your conda env first, or set PYTHON.
pause
exit /b 1

:fail
echo   [X] pip install failed; see the messages above.
pause
exit /b 1
