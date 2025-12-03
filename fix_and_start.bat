@echo off
echo ============================================
echo AlphaCouncil Complete Fix and Start Script
echo ============================================
echo.

cd /d D:\AlphaCouncil

echo [1/4] Installing missing dependencies...
echo Installing colorlog and related packages...
pip install colorlog colorama termcolor python-dotenv -q
if %errorlevel% neq 0 (
    echo Warning: Some packages may not have installed correctly
)
echo OK

echo.
echo [2/4] Fixing general import issues...
python fix_all_imports_v2.py
if %errorlevel% neq 0 (
    echo Warning: Some imports may not have been fixed
)

echo.
echo [3/4] Fixing LangChain import issues...
python fix_langchain_imports.py
if %errorlevel% neq 0 (
    echo Warning: Some LangChain imports may not have been fixed
)

echo.
echo [4/4] Setting Python path and starting server...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo ============================================
echo Starting FastAPI Server...
echo ============================================
python backend/server.py

pause
