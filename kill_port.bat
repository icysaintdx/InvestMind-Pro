@echo off
echo Killing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)
echo Done!
