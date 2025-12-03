@echo off
echo ========================================
echo Testing AlphaCouncil Server
echo ========================================
echo.

cd /d D:\AlphaCouncil

echo Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo Testing critical imports...
python -c "import sys; sys.path.insert(0, r'D:\AlphaCouncil'); from backend.agents.utils.agent_utils import Toolkit; print('Import successful')" 2>&1

echo.
echo If you see 'Import successful' above, the server should work.
echo.
echo Starting server...
python backend/server.py

pause
