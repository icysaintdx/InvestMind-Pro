@echo off
chcp 65001 > nul
echo ============================================================
echo AlphaCouncil Docker Deployment
echo ============================================================
echo.

echo Step 1: Check Docker
echo ------------------------------------------------------------
docker --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found! Please install Docker first.
    echo Download: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo Docker: OK
echo.

echo Step 2: Check Docker Compose
echo ------------------------------------------------------------
docker-compose --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found!
    pause
    exit /b 1
)
echo Docker Compose: OK
echo.

echo Step 3: Check .env file
echo ------------------------------------------------------------
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your API keys!
    echo Then run this script again.
    pause
    exit /b 1
)
echo .env: OK
echo.

echo Step 4: Build and Start Services
echo ------------------------------------------------------------
echo This may take a few minutes on first run...
echo.
docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start services!
    echo Check logs: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS: AlphaCouncil is running!
echo ============================================================
echo.
echo Frontend: http://localhost
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Useful commands:
echo   docker-compose logs -f          View logs
echo   docker-compose ps               View status
echo   docker-compose stop             Stop services
echo   docker-compose down             Stop and remove
echo.
pause
