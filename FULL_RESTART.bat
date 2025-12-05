@echo off
echo ========================================
echo  Full System Restart
echo ========================================
echo.

echo Step 1: Kill port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Killing PID: %%a
    taskkill /PID %%a /F 2>nul
)
echo Port 8000 is now free!
echo.

echo Step 2: Kill port 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
    echo Killing PID: %%a
    taskkill /PID %%a /F 2>nul
)
echo Port 8080 is now free!
echo.

echo Step 3: Starting backend server...
start cmd /k "cd /d d:\AlphaCouncil && python backend\server.py"
timeout /t 3 /nobreak > nul

echo Step 4: Starting frontend...
start cmd /k "cd /d d:\AlphaCouncil\alpha-council-vue && npm run serve"

echo.
echo ========================================
echo  Services are starting...
echo ========================================
echo  Backend: http://localhost:8000
echo  Frontend: http://localhost:8080
echo  API Docs: http://localhost:8000/docs
echo ========================================
echo.
pause
