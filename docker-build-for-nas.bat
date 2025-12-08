@echo off
chcp 65001 > nul
echo ============================================================
echo AlphaCouncil Docker Build for NAS (Standalone)
echo ============================================================
echo.

echo This script builds standalone images that can run independently
echo (not requiring docker-compose network)
echo.
pause

echo.
echo ============================================================
echo Step 1: Build Backend Image
echo ============================================================
echo.
cd backend
echo Building alphacouncil-backend:latest...
docker build --progress=plain -t alphacouncil-backend:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Backend build failed!
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo Backend build: SUCCESS
echo.

echo ============================================================
echo Step 2: Build Frontend Image (Standalone Version)
echo ============================================================
echo.
cd alpha-council-vue
echo Building alphacouncil-frontend:latest (standalone)...
docker build --progress=plain -f Dockerfile.standalone -t alphacouncil-frontend:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Frontend build failed!
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
echo ============================================================
echo NAS Deployment Instructions
echo ============================================================
echo.
echo 1. Upload these files to your NAS:
echo    - alphacouncil-backend.tar
echo    - alphacouncil-frontend.tar
echo    - .env (with your API keys)
echo    - backend/agent_configs.json
echo.
echo 2. On NAS, load images:
echo    docker load -i alphacouncil-backend.tar
echo    docker load -i alphacouncil-frontend.tar
echo.
echo 3. Run backend:
echo    docker run -d --name alphacouncil-backend \
echo      -p 8000:8000 \
echo      -v ./data:/app/data \
echo      -v ./backend/agent_configs.json:/app/backend/agent_configs.json \
echo      --env-file .env \
echo      alphacouncil-backend:latest
echo.
echo 4. Run frontend:
echo    docker run -d --name alphacouncil-frontend \
echo      -p 80:80 \
echo      alphacouncil-frontend:latest
echo.
echo 5. Access: http://your-nas-ip
echo.
echo See NAS_QUICK_START.md for detailed instructions
echo.
pause
