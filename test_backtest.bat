@echo off
echo ==================================================
echo Testing Backtest System
echo ==================================================

cd /d D:\InvestMindPro
python test_backtest_system.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==================================================
    echo All tests passed successfully!
    echo ==================================================
) else (
    echo.
    echo ==================================================
    echo Some tests failed. Please check the output above.
    echo ==================================================
)

pause
