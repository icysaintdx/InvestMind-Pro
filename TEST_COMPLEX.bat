@echo off
chcp 65001 >nul
echo ========================================
echo Complex Concurrency Test
echo Using Real Risk Agent Prompts
echo ========================================
echo.

echo This test uses REAL risk agent prompts
echo Each request will take 30-60 seconds
echo Testing concurrent: 1, 2, 3, 4, 5, 6
echo.
echo Total test time: 10-15 minutes
echo.
echo Press Ctrl+C to cancel
timeout /t 3 >nul

python test_concurrency_complex.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
pause
