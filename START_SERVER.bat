@echo off
echo ============================================
echo AlphaCouncil Server - FINAL START
echo ============================================
echo.
echo Checking and fixing dependencies...
echo.

cd /d D:\AlphaCouncil

echo 1. Fixing NumPy/ChromaDB compatibility...
python fix_chromadb_auto.py

echo.
echo 2. Setting Python path...
set PYTHONPATH=%cd%;%PYTHONPATH%

echo.
echo 3. Testing imports...
python -c "from backend.agents.utils.agent_utils import Toolkit; print('Import test OK')" 2>&1

echo.
echo ============================================
echo Starting AlphaCouncil Server
echo ============================================
echo.
echo Note: If you see ChromaDB warnings, memory 
echo features will be disabled but the server
echo will work normally.
echo ============================================
echo.

python backend/server.py

pause
