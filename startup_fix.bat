@echo off
echo ===================================
echo InvestMindPro Startup Fix Script
echo ===================================
echo.

cd /d D:\InvestMindPro

echo Step 1: Installing dependencies...
echo Installing colorlog and related packages...
pip install colorlog colorama termcolor python-dotenv >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install colorlog. Please run manually:
    echo pip install colorlog colorama termcolor
    pause
    exit /b 1
)
echo OK - Dependencies installed

echo.
echo Step 2: Fixing import issues...
python fix_all_imports_v2.py
if %errorlevel% neq 0 (
    echo Failed to fix imports. Please check the error above.
    pause
    exit /b 1
)

echo.
echo Step 3: Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo Step 4: Starting FastAPI server...
echo ===================================
python backend/server.py

pause
