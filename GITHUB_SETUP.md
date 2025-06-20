# 🚀 GitHub Setup Guide

Quick guide to upload **Real Debrid Media Manager v2.0** to GitHub.

## 📋 Prerequisites

1. **Git installed** on your machine
   - Download: [git-scm.com](https://git-scm.com/downloads)
   - Windows: Download and run the installer
   - Verify: `git --version`

2. **GitHub account**
   - Sign up: [github.com](https://github.com)

## 🛠️ Step-by-Step Setup

### 1️⃣ **Create GitHub Repository**

1. Go to **[GitHub.com](https://github.com)**
2. Click **"New repository"** (green button)
3. Fill in repository details:
   ```
   Repository name: realdebrid-media-manager
   Description: 🔄 Intelligent Cycle-Based Real Debrid Media Processor v2.0
   Visibility: Public (or Private)
   
   ⚠️ DO NOT CHECK:
   - Add a README file
   - Add .gitignore  
   - Choose a license
   ```
4. Click **"Create repository"**
5. **Copy the repository URL** (you'll need this)

### 2️⃣ **Configure Git (First Time Only)**

```bash
# Set your GitHub username and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3️⃣ **Use Automated Setup**

Run the provided setup script:

```cmd
# Windows
setup_github.bat
```

**OR** manually run these commands:

```bash
# Initialize Git repository
git init

# Add all files
git add .

# Create initial commit
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

# Connect to GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

### 4️⃣ **Replace YOUR_USERNAME and YOUR_REPO_NAME**

Example:
```bash
git remote add origin https://github.com/banana123/realdebrid-media-manager.git
```

## 🎉 Success!

Your repository should now be live on GitHub with:

- ✅ **Complete source code**
- ✅ **Documentation** (README.md, DOCUMENTATION.md, TrueNAS-DEPLOY.md)
- ✅ **Docker configuration** (Dockerfile, docker-compose.yml)
- ✅ **Security** (.gitignore excludes .env and sensitive files)

## 🔒 Security Notes

The `.gitignore` file automatically excludes:
- ❌ `.env` files (contains your API key)
- ❌ `logs/` and `output/` directories
- ❌ `media/` directory
- ❌ Real Debrid data files (`realdebrid_*.json`)

**Your API key will NOT be uploaded to GitHub!** ✅

## 📱 Next Steps

1. **Star your repository** ⭐
2. **Add topics/tags**: `real-debrid`, `media-manager`, `docker`, `strm`, `jellyfin`
3. **Write a good README** (already included!)
4. **Set up GitHub Actions** for automated builds (optional)

## 🛠️ Future Updates

To update your repository:

```bash
# Make changes to your code
git add .
git commit -m "✨ Add new feature: description"
git push
```

## 🆘 Troubleshooting

### Common Issues:

**❌ "Git not recognized"**
```
Install Git from git-scm.com and restart your terminal
```

**❌ "Permission denied"**
```
# Set up SSH key or use HTTPS with token
# See: https://docs.github.com/en/authentication
```

**❌ "Repository already exists"**
```
git remote set-url origin https://github.com/USERNAME/REPO.git
```

---

**Happy coding!** 🚀 