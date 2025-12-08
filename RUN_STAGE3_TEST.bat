@echo off
echo ========================================
echo Stage 3 Real Concurrent Test
echo ========================================
echo.
echo This test simulates the REAL Stage 3 requests
echo - 6 risk control agents
echo - Real previous outputs
echo - Real instructions
echo.
echo Make sure backend is running on port 8000!
echo.
pause

python test_stage3_real.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
pause
