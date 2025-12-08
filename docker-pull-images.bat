@echo off
chcp 65001 > nul
echo ============================================================
echo Pre-pull Docker Base Images
echo ============================================================
echo.

echo This will download required base images first
echo.

echo Step 1: Pull Python base image
echo ------------------------------------------------------------
docker pull python:3.11-slim
if errorlevel 1 (
    echo ERROR: Failed to pull python:3.11-slim
    echo.
    echo Try:
    echo 1. Configure Docker mirror (see 配置Docker镜像源.md)
    echo 2. Check your internet connection
    echo 3. Use VPN if needed
    pause
    exit /b 1
)
echo Python: OK
echo.

echo Step 2: Pull Node.js base image
echo ------------------------------------------------------------
docker pull node:18-alpine
if errorlevel 1 (
    echo ERROR: Failed to pull node:18-alpine
    pause
    exit /b 1
)
echo Node.js: OK
echo.

echo Step 3: Pull Nginx base image
echo ------------------------------------------------------------
docker pull nginx:alpine
if errorlevel 1 (
    echo ERROR: Failed to pull nginx:alpine
    pause
    exit /b 1
)
echo Nginx: OK
echo.

echo ============================================================
echo SUCCESS: All base images downloaded!
echo ============================================================
echo.
echo Now you can run: docker-build-offline.bat
echo.
pause
