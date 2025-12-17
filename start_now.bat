@echo off
echo ========================================
echo InvestMindPro Server Startup
echo ========================================
echo.

cd /d D:\InvestMindPro

echo Setting environment...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo Starting server...
echo.
echo NOTE: Some optional modules may show warnings.
echo This is normal if you haven't installed them.
echo The core functionality will still work.
echo ========================================
echo.

python backend/server.py

pause
