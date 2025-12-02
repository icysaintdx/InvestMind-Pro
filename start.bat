@echo off
echo ========================================
echo Starting InvestMind Pro Services
echo ========================================

REM Kill processes using port 8000
echo Killing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 >nul

REM Start backend server
echo Starting backend server...
start cmd /k "cd /d %~dp0 && python backend\server.py"
timeout /t 3 >nul

REM Start Vue frontend
echo Starting Vue frontend...
start cmd /k "cd /d %~dp0\alpha-council-vue && npm run serve"

echo ========================================
echo Services started!
echo ========================================
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
pause
