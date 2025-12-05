@echo off
chcp 65001 >nul
echo ============================================================
echo AlphaCouncil - Start Server and Test APIs
echo ============================================================

echo.
echo [Step 1] Killing existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID: %%a
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo.
echo [Step 2] Starting backend server...
start "AlphaCouncil Backend" python backend/server.py
echo Waiting for server to start (10 seconds)...
timeout /t 10 /nobreak

echo.
echo [Step 3] Testing API endpoints...
echo.
echo Testing Social Media API...
curl http://localhost:8000/api/akshare/social-media/weibo/stock-hot
echo.
echo.
echo Testing Fund Flow API...
curl http://localhost:8000/api/akshare/fund-flow/600519
echo.
echo.
echo Testing Financial API...
curl http://localhost:8000/api/akshare/financial/600519/summary
echo.

echo.
echo ============================================================
echo Test Complete!
echo ============================================================
echo.
echo Server is still running in the background.
echo To stop it, run: KILL_PORT_8000.bat
echo.
pause
