@echo off
chcp 65001 >nul
echo ============================================================
echo Quick Test - Data Integration
echo ============================================================

echo.
echo [1/3] Testing Social Media Data Module...
python test_social_media_fixed.py

echo.
echo [2/3] Testing API Endpoints (requires server running)...
echo Starting server in background...
start /B python backend/server.py
timeout /t 5 /nobreak >nul

echo.
echo Testing endpoints...
curl http://localhost:8000/api/akshare/social-media/weibo/stock-hot
echo.
curl http://localhost:8000/api/akshare/fund-flow/600519
echo.
curl http://localhost:8000/api/akshare/financial/600519/summary

echo.
echo [3/3] Stopping server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server.py*" 2>nul

echo.
echo ============================================================
echo Test Complete!
echo ============================================================
pause
