# GitHub Personal Access Token Setup Guide

This guide helps you create and configure a Personal Access Token (PAT) to resolve GitHub Actions permission issues.

## 🚨 **Problem**
GitHub Actions workflows are failing with:
```
remote: Permission to happy2234/gopnik.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/happy2234/gopnik.git/': The requested URL returned error: 403
```

## ✅ **Solution: Personal Access Token**

### **Step 1: Create Personal Access Token**

1. **Navigate to GitHub Token Settings**:
   - Go to: https://github.com/settings/tokens
   - Or: GitHub → Profile Picture → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click "Generate new token" → "Generate new token (classic)"
   - **Note**: `Gopnik Repository Automation`
   - **Expiration**: Choose `90 days` or `No expiration`

3. **Select Required Scopes**:
   ```
   ✅ repo (Full control of private repositories)
     ✅ repo:status (Access commit status)
     ✅ repo_deployment (Access deployment status)
     ✅ public_repo (Access public repositories)
     ✅ repo:invite (Access repository invitations)
     ✅ security_events (Read and write security events)
   
   ✅ workflow (Update GitHub Action workflows)
   
   ✅ write:packages (Upload packages to GitHub Package Registry)
   ✅ read:packages (Download packages from GitHub Package Registry)
   ```

4. **Generate and Copy Token**:
   - Click "Generate token"
   - **⚠️ CRITICAL**: Copy the token immediately (it won't be shown again!)
   - Save it temporarily in a secure location

### **Step 2: Add Token to Repository Secrets**

1. **Go to Repository Secrets**:
   - Visit: https://github.com/happy2234/gopnik/settings/secrets/actions
   - Or: Repository → Settings → Secrets and variables → Actions

2. **Create New Repository Secret**:
   - Click "New repository secret"
   - **Name**: `PAT_TOKEN`
   - **Secret**: Paste your personal access token
   - Click "Add secret"

### **Step 3: Verify Token Permissions**

The token should have these capabilities:
- ✅ Read and write access to repository code
- ✅ Read and write access to repository wiki
- ✅ Ability to push commits and create branches
- ✅ Access to GitHub Actions workflows
- ✅ Read repository metadata and settings

### **Step 4: Test the Setup**

1. **Trigger a Workflow**:
   - Go to: https://github.com/happy2234/gopnik/actions
   - Find "Setup GitHub Wiki" workflow
   - Click "Run workflow" → "Run workflow"

2. **Check for Success**:
   - Workflow should complete without permission errors
   - Wiki should be updated successfully
   - Status files should be committed to repository

## 🔧 **Troubleshooting**

### **Token Not Working**
- Verify token has `repo` and `workflow` scopes
- Check token hasn't expired
- Ensure token is added as `PAT_TOKEN` (exact name)

### **Still Getting 403 Errors**
- Token might not have sufficient permissions
- Try regenerating token with all `repo` permissions
- Verify you're the repository owner or have admin access

### **Wiki Clone Fails**
- Ensure wiki is enabled in repository settings
- Check that wiki has at least one page created
- Verify token has access to wiki repository

## 🔒 **Security Best Practices**

1. **Token Expiration**:
   - Set reasonable expiration dates (90 days recommended)
   - Set calendar reminders to renew tokens

2. **Scope Limitation**:
   - Only grant minimum required permissions
   - Regularly review and audit token usage

3. **Token Storage**:
   - Never commit tokens to code
   - Use GitHub Secrets for secure storage
   - Rotate tokens regularly

## 📊 **Expected Results**

After setup, workflows should:
- ✅ Successfully clone wiki repository
- ✅ Push changes to main repository
- ✅ Update wiki content automatically
- ✅ Create status files and commit them
- ✅ Complete without permission errors

## 🆘 **Getting Help**

If you continue to have issues:

1. **Check Token Scopes**: Ensure all required permissions are granted
2. **Verify Secret Name**: Must be exactly `PAT_TOKEN`
3. **Test Manually**: Try cloning repository with token locally
4. **Repository Settings**: Verify you have admin access to the repository

## 📝 **Token Renewal Process**

When your token expires:

1. Generate new token with same scopes
2. Update `PAT_TOKEN` secret in repository settings
3. Test workflows to ensure they work
4. Delete old token from GitHub settings

---

**🎯 Once completed, your GitHub Actions workflows will have the necessary permissions to manage the repository and wiki automatically!**