@echo off
echo ========================================
echo Restarting AlphaCouncil Server
echo ========================================
echo.

cd /d D:\AlphaCouncil

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo Starting server...
python backend/server.py

pause
