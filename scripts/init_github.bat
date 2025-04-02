@echo off
echo ===================================
echo Crawl4AI GitHub Initialization Tool
echo ===================================
echo.

echo This script will initialize a new Git repository for Crawl4AI
echo and prepare it for the first commit.
echo.

REM Change to the project root directory
cd ..

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH.
    echo Please install Git from https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Check if .git directory already exists
if exist .git (
    echo Git repository already initialized.
    echo Using existing repository.
    echo.
) else (
    echo Initializing new Git repository...
    git init
    echo.
)

REM Setting up default branch as main
git checkout -b main

echo Adding GitHub-specific files...
REM Copy GitHub README to root
copy README_GITHUB.md ..\README.md

echo.
echo Staging files for commit...
git add .gitignore
git add LICENSE
git add README.md
git add CONTRIBUTING.md
git add requirements.txt
git add .github
git add api
git add core
git add docs
git add frontend
git add scripts
git add tests
git add utils

echo.
echo Files staged for commit. 
echo.
echo Next steps:
echo 1. Run 'git commit -m "Initial commit"'
echo 2. Create a repository on GitHub
echo 3. Run the following commands:
echo    git remote add origin https://github.com/USERNAME/REPOSITORY.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo NOTE: Replace USERNAME/REPOSITORY with your actual GitHub username and repository name.
echo.

pause 