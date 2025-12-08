@echo off
chcp 65001 >nul
echo ========================================
echo AlphaCouncil Backend Concurrency Test
echo ========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install aiohttp -q

echo.
echo ========================================
echo Starting Concurrency Test
echo ========================================
echo.
echo This will test concurrent requests from 1 to 10
echo Each test will take about 30-60 seconds
echo Total test time: approximately 5-10 minutes
echo.
echo Press Ctrl+C to cancel
timeout /t 3 >nul

python test_concurrency.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Check the generated JSON file for detailed results
echo.
pause
