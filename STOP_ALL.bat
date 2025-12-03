@echo off
chcp 65001 >nul
echo ============================================
echo Stopping AlphaCouncil Services
echo ============================================
echo.

REM Stop backend
echo Stopping Backend Server...
taskkill /FI "WINDOWTITLE eq AlphaCouncil Backend*" /T /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

REM Stop frontend
echo Stopping Frontend Server...
taskkill /FI "WINDOWTITLE eq AlphaCouncil Frontend*" /T /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo.
echo All services stopped.
echo.
pause
