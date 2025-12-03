@echo off
echo ===================================
echo Starting AlphaCouncil Backend Server
echo ===================================
echo.

cd /d D:\AlphaCouncil

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo Starting FastAPI server...
python backend/server.py

pause
