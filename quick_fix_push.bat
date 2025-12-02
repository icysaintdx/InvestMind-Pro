@echo off
echo.
echo === Quick Fix for GitHub Push ===
echo.
echo This will help you push your code to GitHub.
echo.
echo Option 1: Enter your GitHub username and password
echo Option 2: Create a new token at https://github.com/settings/tokens/new
echo.
echo Creating new token is recommended. Required scopes: repo
echo.
set /p method="Use [T]oken or [U]sername/Password? (T/U): "
echo.

if /i "%method%"=="T" (
    echo Please create a token at: https://github.com/settings/tokens/new
    echo Required scope: repo (Full control of private repositories)
    echo.
    set /p newtoken="Paste your new token (starts with ghp_): "
    echo.
    echo Updating remote...
    git remote set-url origin https://icysaintdx:%newtoken%@github.com/icysaintdx/InvestMind-Pro.git
    echo.
    echo Pushing to GitHub...
    git push -u origin main
) else (
    echo.
    echo Using username/password authentication...
    echo Note: GitHub may require token instead of password.
    echo.
    git push -u origin main
)

echo.
echo === Operation Complete ===
pause
