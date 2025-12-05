@echo off
echo Killing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Killing PID: %%a
    taskkill /PID %%a /F 2>nul
)
echo Port 8000 is now free!
pause
