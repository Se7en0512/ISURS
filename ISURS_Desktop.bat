@echo off
title PULSE Desktop App
cd /d "%~dp0"

echo ============================================
echo  PULSE Desktop App
echo  Hospital Asset ^& Supply
echo     Management System
echo ============================================
echo.

REM Install dependencies if needed
pip install -r requirements.txt >nul 2>&1

echo Starting desktop app...
python desktop.py
