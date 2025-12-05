@echo off
chcp 65001 >nul
echo ============================================================
echo Test Financial Data Fix
echo ============================================================

echo.
echo [1/2] Testing financial data module...
python -c "import sys; sys.path.insert(0, 'backend'); from dataflows.akshare.financial_data import get_financial_data; f = get_financial_data(); data = f.get_latest_financial_summary('600519'); print('Success!' if data else 'Failed')"

echo.
echo [2/2] Testing API endpoint...
echo Please make sure server is running on port 8000
echo.
curl http://localhost:8000/api/akshare/financial/600519/summary

echo.
echo ============================================================
echo Test Complete!
echo ============================================================
pause
