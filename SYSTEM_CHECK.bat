@echo off
echo ========================================
echo  System Health Check
echo ========================================
echo.

echo Checking ports...
echo ----------------------------------------
netstat -ano | findstr :8000 > nul
if %errorlevel% == 0 (
    echo Port 8000: IN USE
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do echo   PID: %%a
) else (
    echo Port 8000: FREE
)

netstat -ano | findstr :8080 > nul
if %errorlevel% == 0 (
    echo Port 8080: IN USE
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do echo   PID: %%a
) else (
    echo Port 8080: FREE
)
echo.

echo Testing backend API...
echo ----------------------------------------
python test_api_status.py
echo.

echo Testing stock adapter...
echo ----------------------------------------
python test_optimized_adapter.py 2>nul | findstr /C:"AKShare" /C:"sina" /C:"tushare" /C:"成功"
echo.

echo ========================================
echo  Check Complete
echo ========================================
echo.
echo If ports are in use, run: FULL_RESTART.bat
echo.
pause
