@echo off
echo ========================================
echo AlphaCouncil Server - Final Start
echo ========================================
echo.

cd /d D:\AlphaCouncil

echo Setting environment...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo All import issues have been fixed.
echo Starting server now...
echo ========================================
echo.

python backend/server.py

pause
