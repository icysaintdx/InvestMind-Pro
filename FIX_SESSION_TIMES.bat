@echo off
chcp 65001 >nul
echo ========================================
echo Fix Session Times - Repair Database
echo ========================================
echo.

cd /d %~dp0

echo Running fix script...
python fix_session_times.py

echo.
echo ========================================
echo Done! Press any key to exit...
pause >nul
