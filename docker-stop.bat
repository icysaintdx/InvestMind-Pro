@echo off
chcp 65001 > nul
echo ============================================================
echo Stop InvestMindPro Docker Services
echo ============================================================
echo.

docker-compose stop

echo.
echo Services stopped.
echo.
echo To start again: docker-start.bat
echo To remove containers: docker-compose down
echo.
pause
