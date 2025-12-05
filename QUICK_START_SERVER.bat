@echo off
echo ========================================
echo  Quick Start Server
echo ========================================
echo.

echo Testing imports...
python test_server_imports.py
echo.

echo Creating static directory if not exists...
if not exist backend\static mkdir backend\static
echo.

echo Starting backend server...
python backend\server.py

pause
