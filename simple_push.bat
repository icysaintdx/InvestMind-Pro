@echo off
echo.
echo === Simple GitHub Push Solution ===
echo.
echo Removing existing remote...
git remote remove origin 2>nul
echo.
echo Go to: https://github.com/settings/tokens/new
echo Create token with 'repo' scope
echo.
set /p token="Paste new token (ghp_...): "
echo.
echo Setting up remote with token...
git remote add origin https://icysaintdx:%token%@github.com/icysaintdx/InvestMind-Pro.git
echo.
echo Pushing code...
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo SUCCESS! Your code is now on GitHub!
    echo URL: https://github.com/icysaintdx/InvestMind-Pro
) else (
    echo Push failed. Please check your token and try again.
)
echo.
pause
