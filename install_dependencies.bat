@echo off
echo ===================================
echo Installing AlphaCouncil Dependencies
echo ===================================
echo.

echo Installing essential packages...
pip install colorlog==6.7.0
pip install colorama==0.4.6
pip install termcolor==2.3.0

echo.
echo Installing FastAPI and web framework...
pip install fastapi uvicorn httpx python-dotenv

echo.
echo Installing data processing...
pip install pandas numpy

echo.
echo Installing market data APIs...
pip install akshare tushare beautifulsoup4 lxml

echo.
echo Installing other requirements...
pip install pydantic aiofiles

echo.
echo ===================================
echo Installation Complete!
echo ===================================
echo.
echo You can now run: start_backend.bat
pause
