@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo     GitHub Authentication Setup
echo ===============================================
echo.
echo Choose authentication method:
echo.
echo   [1] Use Personal Access Token (Quick)
echo   [2] Setup SSH Key (Recommended, More Secure)
echo   [3] Use GitHub CLI (gh auth login)
echo.
set /p choice="Enter your choice (1-3): "
echo.

if "%choice%"=="1" goto token_setup
if "%choice%"=="2" goto ssh_setup  
if "%choice%"=="3" goto gh_cli_setup
goto invalid_choice

:token_setup
echo.
echo === Setting up Personal Access Token ===
echo.
echo Steps:
echo 1. Go to: https://github.com/settings/tokens/new
echo 2. Create a new token with 'repo' scope
echo 3. Copy the token (starts with ghp_)
echo.
set /p token="Paste your NEW token here: "
echo.
echo Updating remote URL with token...
git remote set-url origin https://%token%@github.com/icysaintdx/InvestMind-Pro.git
echo.
echo Testing connection...
git ls-remote --heads origin
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Token configured successfully!
    echo Now you can push with: git push -u origin main
) else (
    echo.
    echo ERROR: Token authentication failed. Please check your token.
)
goto end

:ssh_setup
echo.
echo === Setting up SSH Key ===
echo.
echo Checking for existing SSH keys...
if exist "%USERPROFILE%\.ssh\id_ed25519" (
    echo Found existing SSH key.
    set /p overwrite="Overwrite existing key? (y/n): "
    if /i not "%overwrite%"=="y" goto use_existing_ssh
)

echo.
echo Generating new SSH key...
ssh-keygen -t ed25519 -C "github-investmind" -f "%USERPROFILE%\.ssh\id_ed25519" -N ""
echo.

:use_existing_ssh
echo Your SSH public key:
echo ================================
type "%USERPROFILE%\.ssh\id_ed25519.pub"
echo ================================
echo.
echo Steps to add this key to GitHub:
echo 1. Copy the key above
echo 2. Go to: https://github.com/settings/ssh/new
echo 3. Paste the key and save
echo.
pause
echo.
echo Updating remote URL to use SSH...
git remote set-url origin git@github.com:icysaintdx/InvestMind-Pro.git
echo.
echo Testing SSH connection...
ssh -T git@github.com
echo.
echo If you see "Hi username!", SSH is configured correctly.
echo Now you can push with: git push -u origin main
goto end

:gh_cli_setup
echo.
echo === Using GitHub CLI ===
echo.
echo Checking if GitHub CLI is installed...
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo GitHub CLI not found. Please install it first:
    echo https://cli.github.com/
    echo.
    echo Or use winget: winget install GitHub.cli
    goto end
)
echo.
echo Starting GitHub CLI authentication...
gh auth login
echo.
echo After authentication, you can push normally.
goto end

:invalid_choice
echo Invalid choice. Please run the script again.
goto end

:end
echo.
echo ===============================================
echo.
pause
