@echo off
REM Git Setup and GitHub Upload Script for Windows

echo ============================================
echo Invoice Management System
echo Git Setup and GitHub Upload
echo ============================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please download and install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] Checking Git configuration...
git config user.name >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Git is not configured yet. Let's set it up!
    set /p username="Enter your name: "
    set /p email="Enter your email: "
    git config --global user.name "%username%"
    git config --global user.email "%email%"
    echo Git configured successfully!
)
echo.

REM Check if already a git repository
if exist .git (
    echo [INFO] Git repository already initialized!
    echo.
    goto :commit
)

echo [2/5] Initializing Git repository...
git init
if %errorlevel% neq 0 (
    echo [ERROR] Failed to initialize Git repository
    pause
    exit /b 1
)
echo Git repository initialized!
echo.

:commit
echo [3/5] Adding all files to Git...
git add .
echo Files added!
echo.

echo [4/5] Creating initial commit...
git commit -m "Initial commit: Invoice Management System with CRUD and beautiful UI"
if %errorlevel% neq 0 (
    echo [WARNING] Nothing to commit or commit failed
    echo.
)
echo.

echo [5/5] Ready to push to GitHub!
echo.
echo ============================================
echo NEXT STEPS:
echo ============================================
echo.
echo 1. Create a new repository on GitHub:
echo    - Visit: https://github.com/new
echo    - Repository name: invoice-management-system
echo    - DO NOT initialize with README
echo    - Click "Create repository"
echo.
echo 2. Copy your repository URL (it will look like):
echo    https://github.com/YOUR-USERNAME/invoice-management-system.git
echo.
echo 3. Run these commands (replace with your URL):
echo.
echo    git remote add origin https://github.com/YOUR-USERNAME/invoice-management-system.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 4. For detailed instructions, see: GITHUB_DEPLOY_GUIDE.md
echo.
echo ============================================
echo.

pause
