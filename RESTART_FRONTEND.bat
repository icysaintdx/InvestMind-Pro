@echo off
chcp 65001 >nul
echo ================================================================================
echo Restarting Frontend
echo ================================================================================
echo.

echo [1/3] Stopping old frontend processes...
taskkill /F /IM node.exe /T 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/3] Clearing cache...
cd alpha-council-vue
if exist node_modules\.cache rmdir /s /q node_modules\.cache

echo.
echo [3/3] Starting frontend...
start cmd /k "npm run serve"

echo.
echo ================================================================================
echo Frontend Restarted!
echo ================================================================================
echo.
echo Please wait 10-20 seconds for the frontend to start
echo Then visit: http://localhost:8080
echo.
pause
