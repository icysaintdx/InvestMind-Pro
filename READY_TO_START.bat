@echo off
echo ============================================
echo AlphaCouncil Server - READY TO START
echo ============================================
echo.
echo All import issues have been fixed:
echo - log_args parameters removed from decorators
echo - log_analysis_step aliased properly
echo - LangChain compatibility layer created
echo - config.py fixed
echo.

cd /d D:\AlphaCouncil

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo ============================================
echo Starting AlphaCouncil Server
echo ============================================
echo.

python backend/server.py

pause
