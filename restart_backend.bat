@echo off
echo Stopping existing Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo Starting backend server...
cd /d "d:\InvestMind Pro\backend"
start /B python server.py

echo Backend server starting...
timeout /t 3 /nobreak >nul

echo Testing API endpoint...
curl http://localhost:8000/api/models

echo.
echo Backend server should be running now.
echo Press any key to exit...
pause >nul
