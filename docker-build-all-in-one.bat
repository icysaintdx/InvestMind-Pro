@echo off
chcp 65001 > nul
echo ============================================================
echo AlphaCouncil All-in-One Docker Build
echo ============================================================
echo.

echo This will build a single Docker image containing:
echo   - FastAPI Backend (Python)
echo   - Vue Frontend (Nginx)
echo   - All dependencies
echo.
echo Final image size: ~1-1.5GB
echo.
pause

echo.
echo Building all-in-one image...
echo This may take 5-15 minutes...
echo.

docker build -f Dockerfile.all-in-one -t alphacouncil:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo.
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS: All-in-one image built!
echo ============================================================
echo.

echo Saving to TAR file...
docker save alphacouncil:latest -o alphacouncil-all-in-one.tar

if errorlevel 1 (
    echo ERROR: Failed to save image!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build Complete!
echo ============================================================
echo.

for %%F in (alphacouncil-all-in-one.tar) do (
    echo File: %%F
    echo Size: %%~zF bytes (~%%~zF / 1024 / 1024 MB)
)

echo.
echo ============================================================
echo Quick Start
echo ============================================================
echo.
echo Local Test:
echo   docker run -p 80:80 --env-file .env alphacouncil:latest
echo.
echo NAS Deployment:
echo   1. Upload alphacouncil-all-in-one.tar to NAS
echo   2. docker load -i alphacouncil-all-in-one.tar
echo   3. docker run -d -p 80:80 \
echo        -v ./data:/app/data \
echo        --env-file .env \
echo        --name alphacouncil \
echo        alphacouncil:latest
echo.
echo Access: http://your-nas-ip
echo.
pause
