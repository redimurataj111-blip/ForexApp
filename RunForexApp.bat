@echo off
title EUR/USD ForexApp Launcher
color 0A

echo ============================================
echo     EUR/USD ForexApp - Starting...
echo ============================================
echo.

cd /d "C:\Users\redim\OneDrive\Documents"

echo [1/2] Checking dependencies...
python -m pip install streamlit yfinance plotly feedparser pytz requests --quiet

echo.
echo [2/2] Launching ForexApp in browser...
echo.
echo  Press CTRL+C in this window to stop the app.
echo ============================================

python -m streamlit run ForexApp.py --server.headless false --browser.gatherUsageStats false

echo.
echo App stopped. Press any key to close.
pause >nul
