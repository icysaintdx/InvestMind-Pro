@echo off
chcp 65001 > nul
echo ============================================================
echo AlphaCouncil Docker Build (Offline/Slow Network)
echo ============================================================
echo.

echo This script will:
echo 1. Build backend image (Python base)
echo 2. Build frontend image (Node + Nginx base)
echo 3. Save both images as TAR files
echo.
echo Note: First build may take 10-30 minutes depending on network
echo.
pause

echo.
echo ============================================================
echo Step 1: Build Backend Image
echo ============================================================
echo.
cd backend
echo Building alphacouncil-backend:latest...
echo This may take a while on first run...
echo.

docker build --progress=plain -t alphacouncil-backend:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Backend build failed!
    echo.
    echo Possible solutions:
    echo 1. Check your internet connection
    echo 2. Try using a VPN or proxy
    echo 3. Use Docker mirror registry
    echo.
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo Backend build: SUCCESS
echo.

echo ============================================================
echo Step 2: Build Frontend Image
echo ============================================================
echo.
cd alpha-council-vue
echo Building alphacouncil-frontend:latest...
echo This includes Node.js build process...
echo.

docker build --progress=plain -t alphacouncil-frontend:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Frontend build failed!
    echo.
    echo Possible solutions:
    echo 1. Check your internet connection
    echo 2. Try: npm config set registry https://registry.npmmirror.com
    echo 3. Build locally first: npm run build
    echo.
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo Frontend build: SUCCESS
echo.

echo ============================================================
echo Step 3: Save Images to TAR Files
echo ============================================================
echo.

echo Saving backend image...
docker save alphacouncil-backend:latest -o alphacouncil-backend.tar
if errorlevel 1 (
    echo ERROR: Failed to save backend image!
    pause
    exit /b 1
)

echo Saving frontend image...
docker save alphacouncil-frontend:latest -o alphacouncil-frontend.tar
if errorlevel 1 (
    echo ERROR: Failed to save frontend image!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS: Images built and saved!
echo ============================================================
echo.

echo Files created:
for %%F in (alphacouncil-*.tar) do (
    echo   %%F - %%~zF bytes
)

echo.
echo Next steps:
echo 1. Upload TAR files to your NAS
echo 2. On NAS, run: docker load -i alphacouncil-backend.tar
echo 3. On NAS, run: docker load -i alphacouncil-frontend.tar
echo 4. Use docker-compose-nas.yml to start services
echo.
echo See docs/NAS部署指南.md for detailed instructions
echo.
pause
