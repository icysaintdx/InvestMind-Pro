@echo off
echo ========================================
echo Comprehensive Stress Test
echo ========================================
echo.
echo This will test ALL combinations of:
echo - Concurrency: 2, 4, 6, 8, 10
echo - Prompt Size: 1000, 2000, 4000, 6000, 8000, 10000
echo.
echo Total: 30 tests
echo Estimated time: 30-60 minutes
echo.
echo Make sure backend is running on port 8000!
echo.
pause

python test_comprehensive_stress.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo Check stress_test_results.json for details
pause
