@echo off
chcp 65001 >nul
echo ================================================================================
echo InvestMind-Pro Strategy Backtest Test
echo ================================================================================
echo.

echo Running strategy backtest tests...
echo.

python test_simple_backtest.py

echo.
echo ================================================================================
echo Test completed!
echo ================================================================================
echo.
pause
