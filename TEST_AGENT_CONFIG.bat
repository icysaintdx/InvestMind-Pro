@echo off
chcp 65001 > nul
echo ========================================
echo Agent Config System Test
echo ========================================
echo.

echo [1/3] Checking backend server...
curl -s http://localhost:8000/docs > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Backend server not running!
    echo Please start backend first: python backend/server.py
    pause
    exit /b 1
)
echo OK: Backend server is running

echo.
echo [2/3] Testing agent config API...
python test_agent_config_api.py
if %errorlevel% neq 0 (
    echo ERROR: API test failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Opening frontend...
start http://localhost:8080
echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Click "Agent" button in top navigation
echo 2. Try different configuration profiles
echo 3. Check the impact preview
echo.
pause
