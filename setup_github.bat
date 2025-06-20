@echo off
echo 🚀 Real Debrid Media Manager - GitHub Setup
echo ============================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first:
    echo    📥 Download from: https://git-scm.com/downloads
    echo.
    pause
    exit /b 1
)

echo ✅ Git is installed
echo.

REM Initialize repository
echo 📂 Initializing Git repository...
git init

REM Configure git (you'll need to set your own details)
echo 🔧 Setting up Git configuration...
echo ⚠️  Please set your GitHub username and email:
echo    git config --global user.name "Your Name"
echo    git config --global user.email "your.email@example.com"
echo.

REM Create .gitignore if it doesn't exist
if not exist .gitignore (
    echo 📝 Creating .gitignore file...
    echo # Environment Variables > .gitignore
    echo .env >> .gitignore
    echo .env.* >> .gitignore
    echo. >> .gitignore
    echo # Logs and Output >> .gitignore
    echo logs/ >> .gitignore
    echo output/ >> .gitignore
    echo media/ >> .gitignore
    echo *.log >> .gitignore
    echo. >> .gitignore
    echo # Python >> .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pyc >> .gitignore
    echo *.pyo >> .gitignore
    echo *.pyd >> .gitignore
    echo. >> .gitignore
    echo # IDE >> .gitignore
    echo .vscode/ >> .gitignore
    echo .idea/ >> .gitignore
    echo. >> .gitignore
    echo # OS >> .gitignore
    echo .DS_Store >> .gitignore
    echo Thumbs.db >> .gitignore
)

REM Add all files
echo 📁 Adding all files to Git...
git add .

REM Initial commit
echo 💾 Creating initial commit...
git commit -m "🎉 Initial commit: Real Debrid Media Manager v2.0

✨ Features:
- 🔄 20-minute intelligent cycles
- 🛡️ Smart error handling (503/429 retries)
- 📅 14-day file expiration system
- ⏭️ Skip existing files until expiry
- 📁 Organized output in /unorganized/
- 🎯 Smart filtering (≥300MB videos)
- 🔧 Configurable via environment variables

🚀 Ready for production deployment with Docker Compose"

echo.
echo ✅ Git repository initialized and committed!
echo.
echo 📋 Next Steps:
echo 1. Create repository on GitHub.com
echo 2. Copy the GitHub repository URL
echo 3. Run: git remote add origin [YOUR_GITHUB_URL]
echo 4. Run: git branch -M main
echo 5. Run: git push -u origin main
echo.
echo 📖 Example:
echo    git remote add origin https://github.com/yourusername/realdebrid-media-manager.git
echo    git branch -M main
echo    git push -u origin main
echo.
pause 