@echo off
chcp 65001 >nul
echo ============================================
echo InvestMindPro - Full Stack Launcher
echo ============================================
echo.
echo Starting Backend and Frontend...
echo.

cd /d D:\InvestMindPro

REM Phase 1: Quick dependency check
echo [1/4] Checking dependencies...
python fix_chromadb_auto.py >nul 2>&1

REM Phase 2: Set Python path
echo [2/4] Setting environment...
set PYTHONPATH=%cd%;%PYTHONPATH%

REM Phase 3: Start Backend Server
echo [3/4] Starting Backend Server...
echo Backend will run on http://localhost:8000
start "InvestMindPro Backend" cmd /k "python backend/server.py"

REM Wait for backend to initialize
timeout /t 5 /nobreak >nul

REM Phase 4: Start Frontend
echo [4/4] Starting Frontend...
echo Frontend will run on http://localhost:8080
cd alpha-council-vue
start "InvestMindPro Frontend" cmd /k "npm run serve"

echo.
echo ============================================
echo InvestMindPro Started Successfully!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:8080
echo.
echo Press any key to stop all services...
pause >nul

REM Stop all services
taskkill /FI "WINDOWTITLE eq InvestMindPro Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq InvestMindPro Frontend*" /T /F >nul 2>&1

echo.
echo All services stopped.
pause
