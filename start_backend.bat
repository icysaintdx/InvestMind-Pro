@echo off
echo ===================================
echo Starting InvestMindPro Backend Server
echo ===================================
echo.

cd /d D:\InvestMindPro

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo Starting FastAPI server...
python backend/server.py

pause
