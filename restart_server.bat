@echo off
echo ========================================
echo Restarting InvestMindPro Server
echo ========================================
echo.

cd /d D:\InvestMindPro

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo Starting server...
python backend/server.py

pause
