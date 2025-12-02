@echo off
echo ============================================================
echo InvestMind Pro Vue Setup
echo ============================================================
echo.

echo Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install from https://nodejs.org
    pause
    exit /b 1
)

echo.
echo Checking npm...
npm --version
if errorlevel 1 (
    echo ERROR: npm not found!
    pause
    exit /b 1
)

echo.
echo Installing Vue CLI globally...
npm install -g @vue/cli

echo.
echo Creating Vue project...
cd /d %~dp0
if not exist "alpha-council-vue" (
    echo Creating new Vue project...
    vue create alpha-council-vue --default
) else (
    echo Vue project already exists!
)

echo.
echo Installing dependencies...
cd alpha-council-vue
if not exist "node_modules" (
    npm install
)

echo Additional dependencies...
npm install axios pinia @vueuse/core echarts vue-echarts
npm install -D @types/node sass sass-loader

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To start development:
echo   cd alpha-council-vue
echo   npm run serve
echo.
pause
