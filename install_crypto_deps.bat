@echo off
chcp 65001 >nul
echo ================================================================================
echo Installing Crypto Dependencies
echo ================================================================================
echo.

echo [1/2] Installing pycryptodome...
pip install pycryptodome

echo.
echo [2/2] Installing curl_cffi...
pip install curl_cffi

echo.
echo ================================================================================
echo Installation Complete!
echo ================================================================================
echo.
echo You can now run:
echo   python test_cninfo_api.py       - Test Cninfo API
echo   python test_wenshu_crypto.py    - Test WenShu encryption
echo.
pause
