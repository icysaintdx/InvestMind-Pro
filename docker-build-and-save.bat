@echo off
chcp 65001 > nul
echo ============================================================
echo AlphaCouncil Docker Build and Save
echo ============================================================
echo.

echo Step 1: Check Docker
echo ------------------------------------------------------------
docker --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found!
    pause
    exit /b 1
)
echo Docker: OK
echo.

echo Step 2: Build Backend Image
echo ------------------------------------------------------------
echo Building backend image...
cd backend
docker build -t alphacouncil-backend:latest .
if errorlevel 1 (
    echo ERROR: Backend build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo Backend: OK
echo.

echo Step 3: Build Frontend Image
echo ------------------------------------------------------------
echo Building frontend image...
cd alpha-council-vue
docker build -t alphacouncil-frontend:latest .
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend: OK
echo.

echo Step 4: Save Images to TAR files
echo ------------------------------------------------------------
echo Saving backend image...
docker save alphacouncil-backend:latest -o alphacouncil-backend.tar
if errorlevel 1 (
    echo ERROR: Failed to save backend image!
    pause
    exit /b 1
)
echo Backend saved: alphacouncil-backend.tar

echo.
echo Saving frontend image...
docker save alphacouncil-frontend:latest -o alphacouncil-frontend.tar
if errorlevel 1 (
    echo ERROR: Failed to save frontend image!
    pause
    exit /b 1
)
echo Frontend saved: alphacouncil-frontend.tar
echo.

echo Step 5: Compress TAR files (optional)
echo ------------------------------------------------------------
echo Compressing images...
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tgzip alphacouncil-backend.tar.gz alphacouncil-backend.tar
    "C:\Program Files\7-Zip\7z.exe" a -tgzip alphacouncil-frontend.tar.gz alphacouncil-frontend.tar
    echo Compressed files created!
) else (
    echo 7-Zip not found, skipping compression
    echo You can manually compress the .tar files
)
echo.

echo ============================================================
echo SUCCESS: Docker images built and saved!
============================================================
echo.
echo Files created:
echo   - alphacouncil-backend.tar  (Backend image)
echo   - alphacouncil-frontend.tar (Frontend image)
echo.
echo Upload these files to your NAS, then load them:
echo   docker load -i alphacouncil-backend.tar
echo   docker load -i alphacouncil-frontend.tar
echo.
echo Then use docker-compose-nas.yml to start services
echo.
pause
