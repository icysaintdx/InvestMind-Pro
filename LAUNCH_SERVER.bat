@echo off
echo ============================================
echo InvestMindPro Server - Complete Launch
echo ============================================
echo.

cd /d D:\InvestMindPro

echo Phase 1: Checking and fixing dependencies...
echo ----------------------------------------
python fix_chromadb_auto.py
echo.

echo Phase 2: Testing configuration utils...
echo ----------------------------------------
python test_config_utils_fix.py
echo.

echo Phase 2.5: Testing API imports...
echo ----------------------------------------
python test_api_import_fix.py
echo.

echo Phase 2.6: Final import test...
echo ----------------------------------------
python test_final_import.py
echo.

echo Phase 3: Setting Python path...
echo ----------------------------------------
set PYTHONPATH=%cd%;%PYTHONPATH%
echo PYTHONPATH set.
echo.

echo Phase 4: Final status check...
echo ----------------------------------------
python -c "print('Testing critical imports...')" 2>&1
python -c "from backend.dataflows.config_utils import get_float; print('  Config utils: OK')" 2>&1
python -c "from backend.agents.utils.agent_utils import Toolkit; print('  Agent utils: OK')" 2>&1
python -c "from backend.api.news_api import router; print('  API routes: OK')" 2>&1
echo.

echo ============================================
echo Starting InvestMindPro Server
echo ============================================
echo.
echo Server will start on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo ============================================
echo.

python backend/server.py

pause
