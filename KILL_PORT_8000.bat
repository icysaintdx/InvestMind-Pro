@echo off
chcp 65001 >nul
echo ============================================================
echo Kill Port 8000 Process
echo ============================================================
echo.
echo Checking port 8000...
netstat -ano | findstr :8000
echo.
echo Killing all processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID: %%a
    taskkill /F /PID %%a 2>nul
)
echo.
echo Killing all Python processes (just in case)...
taskkill /F /IM python.exe 2>nul
echo.
echo ============================================================
echo Done! Port 8000 should be free now.
echo ============================================================
echo.
echo You can now run: python backend/server.py
echo.
pause
