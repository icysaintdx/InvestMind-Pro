@echo off
chcp 65001 >nul
echo.
echo ===================================================
echo     GitHub Push Fix Script
echo ===================================================
echo.

echo Step 1: Checking current remote configuration...
echo ---------------------------------------------------
git remote -v
echo.

echo Step 2: Removing old remote...
echo ---------------------------------------------------
git remote remove origin
echo Remote 'origin' removed (if it existed).
echo.

echo Step 3: Adding new remote with HTTPS...
echo ---------------------------------------------------
git remote add origin https://github.com/icysaintdx/InvestMind-Pro.git
echo Remote added.
echo.

echo Step 4: Verifying remote...
echo ---------------------------------------------------
git remote -v
echo.

echo Step 5: Choose authentication method:
echo ---------------------------------------------------
echo.
echo   [1] Use Personal Access Token (Recommended)
echo   [2] Use GitHub Credentials (May not work)
echo   [3] Switch to SSH instead
echo.
set /p auth_choice="Enter choice (1-3): "
echo.

if "%auth_choice%"=="1" goto use_token
if "%auth_choice%"=="2" goto use_credentials
if "%auth_choice%"=="3" goto use_ssh
goto invalid

:use_token
echo.
echo To create a new token:
echo 1. Open: https://github.com/settings/tokens/new
echo 2. Name: InvestMind-Pro
echo 3. Expiration: 90 days
echo 4. Scopes: Check 'repo' (Full control)
echo 5. Click 'Generate token'
echo 6. Copy the token (starts with ghp_)
echo.
set /p github_token="Paste your GitHub token here: "
echo.
echo Setting up remote with token...
git remote set-url origin https://%github_token%@github.com/icysaintdx/InvestMind-Pro.git
echo.
echo Testing connection...
git ls-remote --heads origin >nul 2>&1
if %errorlevel% equ 0 (
    echo Connection successful!
    echo.
    echo Pushing to GitHub...
    git push -u origin main
    echo.
    echo SUCCESS: Code pushed to GitHub!
) else (
    echo ERROR: Failed to connect. Please check your token.
)
goto end

:use_credentials
echo.
echo Attempting to push with credentials...
echo You will be prompted for username and password.
echo NOTE: Password should be a Personal Access Token, not your account password.
echo.
git push -u origin main
goto end

:use_ssh
echo.
echo Setting up SSH...
echo.
echo Checking for SSH keys...
if not exist "%USERPROFILE%\.ssh\id_ed25519" (
    echo No SSH key found. Generating new key...
    ssh-keygen -t ed25519 -C "investmind-pro" -f "%USERPROFILE%\.ssh\id_ed25519" -N ""
    echo.
)
echo.
echo Your SSH public key:
echo =====================================
type "%USERPROFILE%\.ssh\id_ed25519.pub"
echo =====================================
echo.
echo IMPORTANT: Copy the key above and add it to GitHub:
echo 1. Go to: https://github.com/settings/ssh/new
echo 2. Title: InvestMind-Pro
echo 3. Key: Paste the key above
echo 4. Click 'Add SSH key'
echo.
pause
echo.
echo Changing remote to SSH...
git remote set-url origin git@github.com:icysaintdx/InvestMind-Pro.git
echo.
echo Testing SSH connection...
ssh -T git@github.com 2>&1
echo.
echo Pushing to GitHub...
git push -u origin main
goto end

:invalid
echo Invalid choice.
goto end

:end
echo.
echo ===================================================
echo     Script Complete
echo ===================================================
pause
