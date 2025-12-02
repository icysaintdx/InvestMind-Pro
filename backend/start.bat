@echo off
echo ============================================
echo   IcySaint AI - Starting Backend Server
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/Update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Start the server
echo.
echo Starting Python backend server...
echo ============================================
python server.py

pause
