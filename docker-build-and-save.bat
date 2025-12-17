@echo off
chcp 65001 > nul
echo ============================================================
echo InvestMindPro Docker Build and Save
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
docker build -t InvestMindPro-backend:latest .
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
docker build -t InvestMindPro-frontend:latest .
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
docker save InvestMindPro-backend:latest -o InvestMindPro-backend.tar
if errorlevel 1 (
    echo ERROR: Failed to save backend image!
    pause
    exit /b 1
)
echo Backend saved: InvestMindPro-backend.tar

echo.
echo Saving frontend image...
docker save InvestMindPro-frontend:latest -o InvestMindPro-frontend.tar
if errorlevel 1 (
    echo ERROR: Failed to save frontend image!
    pause
    exit /b 1
)
echo Frontend saved: InvestMindPro-frontend.tar
echo.

echo Step 5: Compress TAR files (optional)
echo ------------------------------------------------------------
echo Compressing images...
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tgzip InvestMindPro-backend.tar.gz InvestMindPro-backend.tar
    "C:\Program Files\7-Zip\7z.exe" a -tgzip InvestMindPro-frontend.tar.gz InvestMindPro-frontend.tar
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
echo   - InvestMindPro-backend.tar  (Backend image)
echo   - InvestMindPro-frontend.tar (Frontend image)
echo.
echo Upload these files to your NAS, then load them:
echo   docker load -i InvestMindPro-backend.tar
echo   docker load -i InvestMindPro-frontend.tar
echo.
echo Then use docker-compose-nas.yml to start services
echo.
pause
