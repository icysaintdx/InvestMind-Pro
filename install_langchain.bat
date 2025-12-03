@echo off
echo ===================================
echo Installing LangChain Dependencies
echo ===================================
echo.

echo Installing LangChain core packages...
pip install langchain langchain-core langchain-openai langchain-community

echo.
echo Installing additional dependencies...
pip install python-dateutil

echo.
echo ===================================
echo LangChain Installation Complete!
echo ===================================
echo.
echo You can now run: start_backend.bat
pause
