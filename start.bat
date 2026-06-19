@echo off
title PULSE - Hospital Asset & Supply Management System
cd /d "%~dp0"

echo ============================================
echo  PULSE - Hospital Asset ^& Supply
echo     Management System
echo ============================================
echo.

REM Install dependencies if needed
pip install -r requirements.txt >nul 2>&1

REM Show IP address
echo Your computer's IP addresses:
for /f "tokens=2 delims=: " %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    echo    http://%%a:5000
)
echo.

echo Starting server... Press Ctrl+C to stop.
echo.
python app.py
