# GitHub Repository Setup Guide

This guide will help you create a GitHub repository for the visibility prediction model.

## 📋 Pre-Setup Checklist

✅ All files organized in `visibility_prediction_pipeline/` folder  
✅ Model files in `models/` directory  
✅ Dataset in `stormglass_output/` directory  
✅ Documentation in `docs/` directory  
✅ `.gitignore` file created  
✅ `README.md` file created  

## 🚀 Step-by-Step GitHub Setup

### Option 1: Using GitHub Desktop (Easiest)

1. **Download GitHub Desktop**
   - Go to: https://desktop.github.com/
   - Install and sign in with your GitHub account

2. **Create Repository**
   - File → New Repository
   - Name: `visibility-prediction` (or your preferred name)
   - Local Path: Choose `visibility_prediction_pipeline` folder
   - Check "Initialize with README" (we already have one)
   - Click "Create Repository"

3. **Publish to GitHub**
   - Click "Publish repository" button
   - Choose whether to make it Public or Private
   - Uncheck "Keep this code private" if you want it public
   - Click "Publish Repository"

4. **Done!** Your repository is now on GitHub

### Option 2: Using Command Line (Git Bash/Terminal)

1. **Navigate to your project folder**
   ```bash
   cd "C:\Users\sunga\Desktop\Launchlab AI\Data analysis\visibility_prediction_pipeline"
   ```

2. **Initialize Git repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Visibility prediction model v1"
   ```

3. **Create repository on GitHub**
   - Go to https://github.com/new
   - Repository name: `visibility-prediction`
   - Description: "Hierarchical Bayesian model for underwater visibility prediction"
   - Choose Public or Private
   - **DO NOT** initialize with README (we have one)
   - Click "Create repository"

4. **Link local repository to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/visibility-prediction.git
   git branch -M main
   git push -u origin main
   ```

5. **Done!** Your code is now on GitHub

### Option 3: Using VS Code (If you have VS Code)

1. **Open folder in VS Code**
   - File → Open Folder → Select `visibility_prediction_pipeline`

2. **Initialize Git**
   - Click Source Control icon (left sidebar)
   - Click "Initialize Repository"

3. **Commit files**
   - Stage all files (+ icon)
   - Enter commit message: "Initial commit: Visibility prediction model v1"
   - Click ✓ (checkmark) to commit

4. **Publish to GitHub**
   - Click "Publish to GitHub" button
   - Choose repository name and visibility
   - Click "Publish"

5. **Done!** Repository is live

## 📦 Large Files? Use Git LFS

If you encounter errors about file sizes (files > 50MB):

### Install Git LFS (Large File Storage)

```bash
# Download and install Git LFS
# From: https://git-lfs.github.com/

# Initialize LFS
git lfs install

# Track large files
git lfs track "*.nc"
git lfs track "*.pkl"

# Add the tracking file
git add .gitattributes

# Commit and push
git add .
git commit -m "Add Git LFS for large model files"
git push
```

## 🔒 Private vs Public Repository

### Make it **Public** if:
- ✅ You want to share with the dive community
- ✅ You want others to contribute improvements
- ✅ You want it on your portfolio
- ✅ Data/model can be openly shared

### Make it **Private** if:
- 🔒 Model/data is proprietary
- 🔒 Still in development/testing
- 🔒 For internal use only
- 🔒 Contains sensitive location data

*You can always change this later in Settings*

## 📝 After Publishing

### 1. Add Repository Description
- Go to your GitHub repository
- Click ⚙️ (Settings gear) next to About
- Add description: "Hierarchical Bayesian model for underwater visibility prediction at Western Australian dive sites"
- Add topics: `machine-learning`, `bayesian`, `diving`, `visibility`, `pymc`, `python`

### 2. Enable Issues (Optional)
- Settings → Features → Check "Issues"
- This allows others to report bugs or ask questions

### 3. Add a License
- Click "Add file" → "Create new file"
- Name it `LICENSE`
- Choose MIT License (or your preference)
- Click "Commit new file"

### 4. Create Releases (Optional)
- Go to Releases → "Create a new release"
- Tag: `v1.0.0`
- Title: "Version 1.0.0 - Initial Release"
- Description: Model performance metrics
- Attach any additional files
- Click "Publish release"

## 🔄 Updating Your Repository

After making changes locally:

```bash
# Add changed files
git add .

# Commit with descriptive message
git commit -m "Update: Retrained model with new data"

# Push to GitHub
git push
```

## 👥 Sharing Your Repository

Share the link:
```
https://github.com/YOUR-USERNAME/visibility-prediction
```

Others can:
- **Clone** it: `git clone https://github.com/YOUR-USERNAME/visibility-prediction.git`
- **Download** as ZIP: Click "Code" → "Download ZIP"
- **Fork** it to their own account
- **Star** it to bookmark

## 📊 Repository Stats

Your repository will automatically show:
- Programming languages used (Python)
- Number of commits
- Contributors
- Stars/Forks
- Last update date

## 🎯 Recommended Repository Settings

1. **Branch Protection** (for collaboration):
   - Settings → Branches → Add rule
   - Protect `main` branch
   - Require pull request reviews

2. **Topics** (for discoverability):
   - Add: `diving`, `bayesian-inference`, `pymc`, `visibility-prediction`, `machine-learning`, `oceanography`

3. **Social Image** (optional):
   - Settings → Social preview
   - Upload one of your plots

## ✅ Final Checklist

After setup, verify:
- [ ] Repository is accessible at github.com/YOUR-USERNAME/visibility-prediction
- [ ] README.md displays correctly on main page
- [ ] Model files are uploaded (check `models/` folder)
- [ ] Dataset is present (`stormglass_output/`)
- [ ] Documentation is readable (`docs/` folder)
- [ ] Plots are visible in `plots/` folder
- [ ] `.gitignore` is working (no unnecessary files uploaded)
- [ ] License is added
- [ ] Repository description and topics are set

## 🆘 Troubleshooting

### "Repository not found" error
- Check you're logged into correct GitHub account
- Verify repository name spelling
- Make sure repository was created successfully

### "File too large" error (>100MB)
- Use Git LFS (see above)
- Or compress large files
- Or use GitHub Releases for large files

### "Permission denied" error
- Check your GitHub credentials
- Generate Personal Access Token if needed
- Use SSH instead of HTTPS

### Files not showing up
- Check `.gitignore` - make sure files aren't ignored
- Run `git status` to see untracked files
- Make sure you committed and pushed

## 📚 Resources

- [GitHub Documentation](https://docs.github.com/)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [GitHub Desktop Guide](https://docs.github.com/en/desktop)
- [Markdown Guide](https://www.markdownguide.org/)

---

**Need help?** Open an issue in the repository or contact the maintainer.

Happy Coding! 🚀

