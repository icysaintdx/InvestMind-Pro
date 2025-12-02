@echo off
echo === Git Push to GitHub ===
echo.

echo Checking git status...
git status --short
echo.

echo Current branch:
git branch --show-current
echo.

echo Remote repositories:
git remote -v
echo.

echo Pushing to GitHub...
git push -u origin main --verbose
echo.

echo === Push Complete ===
pause
