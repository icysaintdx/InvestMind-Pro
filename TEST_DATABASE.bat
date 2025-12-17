@echo off
chcp 65001 > nul
echo ============================================================
echo InvestMindPro Database Integration Test
echo ============================================================
echo.

echo Step 1: Initialize Database
echo ------------------------------------------------------------
cd /d "%~dp0backend"
python init_database.py
if errorlevel 1 (
    echo ERROR: Database initialization failed
    pause
    exit /b 1
)
echo.

echo Step 2: Test Database Integration
echo ------------------------------------------------------------
cd /d "%~dp0"
python test_database_integration.py
if errorlevel 1 (
    echo ERROR: Integration test failed
    pause
    exit /b 1
)
echo.

echo ============================================================
echo SUCCESS: All tests passed!
echo ============================================================
echo.
echo Next steps:
echo 1. Start backend: python backend\server.py
echo 2. Start frontend: cd alpha-council-vue ^&^& npm run dev
echo 3. Test analysis with database persistence
echo.
pause
