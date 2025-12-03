@echo off
echo ============================================================
echo AlphaCouncil v2.0.0-beta Quick Start
echo ============================================================
echo.

echo [1] Starting Backend Server...
start cmd /k "cd /d %~dp0 && python backend\server.py"
timeout /t 3 /nobreak > nul

echo [2] Starting Vue Frontend...
start cmd /k "cd /d %~dp0\alpha-council-vue && npm run serve"
timeout /t 3 /nobreak > nul

echo.
echo ============================================================
echo Services Started:
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Frontend: http://localhost:8080
echo ============================================================
echo.
echo Press any key to test API endpoints...
pause > nul

echo.
echo [3] Testing API Endpoints...
cd /d %~dp0
python scripts\test_all_apis.py

echo.
echo ============================================================
echo AlphaCouncil is Ready!
echo ============================================================
pause
