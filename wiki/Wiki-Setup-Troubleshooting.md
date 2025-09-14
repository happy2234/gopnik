# Wiki Setup Troubleshooting

## 🎉 **SUCCESS! Wiki is Now Live**

✅ **Wiki URL**: https://github.com/happy2234/gopnik.wiki.git  
✅ **Auto-sync**: Enabled and working  
✅ **Status**: All wiki content is published and accessible  

---

This guide helps resolve any issues you might encounter with the GitHub Wiki for Gopnik.

## 🚨 Common Issues and Solutions

### Issue 1: Wiki Not Enabled

**Problem**: "Wiki repository does not exist or is not accessible"

**Solution**:
1. Go to your repository settings: https://github.com/happy2234/gopnik/settings
2. Scroll down to the "Features" section
3. Check the ☑️ "Wikis" checkbox
4. Click "Save changes"
5. Wait 1-2 minutes for GitHub to initialize the wiki
6. Try the setup process again

### Issue 2: Permission Denied

**Problem**: "You don't have write access to the repository"

**Solutions**:
- **For repository owners**: Make sure you're logged into the correct GitHub account
- **For collaborators**: Ask the repository owner to give you write access
- **Authentication issues**: 
  ```bash
  # Check your git configuration
  git config --global user.name
  git config --global user.email
  
  # Re-authenticate with GitHub
  gh auth login
  ```

### Issue 3: Wiki Clone Fails

**Problem**: `git clone https://github.com/happy2234/gopnik.wiki.git` fails

**Solutions**:
1. **Check if wiki exists**: Visit https://github.com/happy2234/gopnik/wiki
2. **Enable wiki first**: Follow Issue 1 solution above
3. **Authentication**: Make sure you're authenticated with GitHub
4. **Network issues**: Try again after a few minutes

### Issue 4: Empty Wiki After Setup

**Problem**: Wiki exists but shows no content

**Solutions**:
1. **Check the wiki directory**: Make sure `wiki/` folder exists in your repository
2. **Verify file names**: Wiki files should be named correctly (e.g., `Home.md`, `Installation-Guide.md`)
3. **Re-run setup**: Use the automated GitHub Actions workflow
4. **Manual verification**:
   ```bash
   # Check if files exist
   ls -la wiki/
   
   # Verify file content
   cat wiki/Home.md
   ```

### Issue 5: GitHub Actions Workflow Fails

**Problem**: "Setup GitHub Wiki" workflow fails

**Solutions**:
1. **Check workflow logs**: Go to Actions tab and view the failed run
2. **Enable wiki first**: Make sure wiki is enabled in repository settings
3. **Check permissions**: Ensure GitHub Actions has write permissions
4. **Re-run workflow**: Click "Re-run all jobs" in the Actions tab

### Issue 6: Wiki Pages Not Linking Correctly

**Problem**: Internal wiki links are broken

**Solutions**:
1. **Use correct link format**: `[Page Title](Page-Name)` (no `.md` extension)
2. **Check file names**: Ensure files are named with hyphens instead of spaces
3. **Case sensitivity**: GitHub wiki is case-sensitive
4. **Example correct links**:
   ```markdown
   [Installation Guide](Installation-Guide)
   [Data Models Guide](Data-Models-Guide)
   [AI Training Guide](AI-Training-Guide)
   ```

## 🔧 Manual Setup Steps

If automated setup fails, follow these manual steps:

### Step 1: Enable Wiki
1. Go to https://github.com/happy2234/gopnik/settings
2. Enable "Wikis" in Features section
3. Wait for initialization

### Step 2: Clone Wiki Repository
```bash
git clone https://github.com/happy2234/gopnik.wiki.git
cd gopnik.wiki
```

### Step 3: Copy Content
```bash
# Copy all wiki files from main repository
cp ../wiki/*.md .

# Verify files are copied
ls -la *.md
```

### Step 4: Commit and Push
```bash
# Add all files
git add .

# Configure git (if needed)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Commit changes
git commit -m "Initial wiki setup"

# Push to wiki
git push origin master
```

### Step 5: Verify Setup
1. Visit https://github.com/happy2234/gopnik/wiki
2. Check that all pages are available
3. Test internal links

## 🔄 Force Wiki Sync

If the automatic sync isn't working or you need to force-update the wiki content:

### Using the Force Sync Script
```bash
# Run from repository root
./scripts/force-wiki-sync.sh
```

**Features:**
- ✅ Forces update of all wiki content
- ✅ Overwrites any manual wiki edits
- ✅ Works even when auto-sync fails
- ✅ Provides detailed progress feedback
- ✅ Handles authentication automatically

**When to use:**
- Auto-sync workflow fails
- Wiki shows outdated content
- Manual wiki edits need to be overwritten
- Initial wiki setup issues

## 🤖 Automated Setup via GitHub Actions

### Triggering the Workflow
1. Go to https://github.com/happy2234/gopnik/actions
2. Find "Setup GitHub Wiki" workflow
3. Click "Run workflow"
4. Select branch (usually `main`)
5. Click "Run workflow" button

### Workflow Features
- ✅ Automatically enables wiki if possible
- ✅ Copies all content from `wiki/` directory
- ✅ Creates proper page structure
- ✅ Handles file naming conventions
- ✅ Provides detailed logs and status
- ✅ Creates status tracking file

### Monitoring Progress
1. Watch the workflow run in the Actions tab
2. Check logs for any errors or warnings
3. Verify completion status
4. Visit wiki to confirm setup

## 🔍 Verification Checklist

After setup, verify these items:

### Wiki Accessibility
- [ ] Wiki is accessible at https://github.com/happy2234/gopnik/wiki
- [ ] Home page loads correctly
- [ ] All expected pages are present

### Content Verification
- [ ] Home.md displays properly
- [ ] Installation-Guide.md has complete content
- [ ] Data-Models-Guide.md shows all model information
- [ ] AI-Training-Guide.md includes SignVeRod dataset info

### Navigation Testing
- [ ] Internal links work correctly
- [ ] Page titles display properly
- [ ] Sidebar navigation functions

### Editing Permissions
- [ ] You can edit pages (if you have permissions)
- [ ] Changes save correctly
- [ ] Edit history is tracked

## 📞 Getting Additional Help

If you're still experiencing issues:

### Community Support
- **GitHub Discussions**: https://github.com/happy2234/gopnik/discussions
- **Issues**: https://github.com/happy2234/gopnik/issues
- **Wiki Help**: https://docs.github.com/en/communities/documenting-your-project-with-wikis

### Debugging Information to Provide
When asking for help, include:
1. **Error messages**: Copy exact error text
2. **Steps taken**: What you tried to do
3. **Environment**: Operating system, git version
4. **Repository access**: Your role (owner, collaborator, etc.)
5. **Workflow logs**: If using GitHub Actions

### Quick Diagnostic Commands
```bash
# Check git configuration
git config --list | grep user

# Check repository access
git ls-remote https://github.com/happy2234/gopnik.git

# Check wiki repository access
git ls-remote https://github.com/happy2234/gopnik.wiki.git

# Verify local wiki files
ls -la wiki/
```

## 🎯 Success Indicators

You'll know the setup is successful when:

✅ **Wiki URL works**: https://github.com/happy2234/gopnik/wiki  
✅ **Home page displays**: Shows welcome message and navigation  
✅ **All pages accessible**: Installation, Data Models, AI Training guides  
✅ **Links function**: Internal navigation works properly  
✅ **Content complete**: All expected information is present  

## 🔄 Keeping Wiki Updated

### Automatic Updates
- The GitHub Actions workflow will automatically sync changes from the `wiki/` directory
- Any updates to wiki files in the main repository will be reflected in the wiki

### Manual Updates
- Edit pages directly in the GitHub wiki interface
- Changes made in the wiki won't automatically sync back to the main repository
- For major updates, prefer updating files in the main repository

---

**💡 Pro Tip**: Use the automated GitHub Actions workflow for the most reliable setup experience!