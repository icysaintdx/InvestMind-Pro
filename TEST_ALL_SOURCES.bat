@echo off
echo ========================================
echo  Testing All Data Sources
echo ========================================
echo.

echo Step 1: Testing Data Sources Priority
echo ----------------------------------------
python test_data_sources_priority.py
echo.
pause

echo Step 2: Testing Stock Data Adapter
echo ----------------------------------------
python test_stock_adapter.py
echo.
pause

echo Step 3: Testing Stock API Endpoint
echo ----------------------------------------
echo Make sure backend is running!
python test_stock_api.py
echo.

echo ========================================
echo  All Tests Completed
echo ========================================
pause
