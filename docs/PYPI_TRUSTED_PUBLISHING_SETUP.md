# PyPI Trusted Publishing Setup Guide

This guide explains how to set up PyPI Trusted Publishing with OpenID Connect (OIDC) for the Gopnik project, eliminating the need for API tokens.

## 🔐 What is PyPI Trusted Publishing?

PyPI Trusted Publishing allows you to publish packages to PyPI directly from GitHub Actions without storing long-lived API tokens. It uses OpenID Connect (OIDC) to establish trust between GitHub and PyPI.

## 📋 Setup Instructions

### Step 1: Configure PyPI Trusted Publisher

1. **Go to PyPI**: Visit [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)

2. **Add a new trusted publisher** with these details:

   **PyPI Project Name (required):**
   ```
   gopnik
   ```

   **Owner (required):**
   ```
   happy2234
   ```

   **Repository name (required):**
   ```
   gopnik
   ```

   **Workflow name (required):**
   ```
   publish-pypi.yml
   ```

   **Environment name (optional but recommended):**
   ```
   pypi
   ```

### Step 2: Configure Test PyPI (Optional)

For testing, also set up trusted publishing on Test PyPI:

1. **Go to Test PyPI**: Visit [https://test.pypi.org/manage/account/publishing/](https://test.pypi.org/manage/account/publishing/)

2. **Add a new trusted publisher** with these details:

   **PyPI Project Name (required):**
   ```
   gopnik
   ```

   **Owner (required):**
   ```
   happy2234
   ```

   **Repository name (required):**
   ```
   gopnik
   ```

   **Workflow name (required):**
   ```
   publish-pypi.yml
   ```

   **Environment name (optional but recommended):**
   ```
   test-pypi
   ```

### Step 3: Configure GitHub Environments

1. **Go to your GitHub repository**: `https://github.com/happy2234/gopnik`

2. **Navigate to Settings > Environments**

3. **Create `pypi` environment**:
   - Click "New environment"
   - Name: `pypi`
   - **Note**: The Environment URL field may not be visible in newer GitHub UI versions - this is normal
   - If the Environment URL field is visible, you can optionally set it to: `https://pypi.org/p/gopnik`
   - Add protection rules (recommended):
     - Required reviewers: Add trusted maintainers
     - Restrict to selected branches: `main`

4. **Create `test-pypi` environment** (optional):
   - Click "New environment"
   - Name: `test-pypi`
   - **Note**: Environment URL field may not be visible - this doesn't affect functionality
   - If visible, you can optionally set it to: `https://test.pypi.org/p/gopnik`
   - Add protection rules as needed

### Step 4: Update Workflow (Already Done)

The workflow has been updated to use OIDC instead of API tokens:

```yaml
permissions:
  contents: read
  id-token: write  # For trusted publishing

jobs:
  publish-pypi:
    environment:
      name: pypi
      url: https://pypi.org/p/gopnik
    steps:
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        verbose: true
        # No username/password needed with trusted publishing!
```

## 🔧 Key Changes Made

### Removed API Token Dependencies
- ❌ `${{ secrets.PYPI_API_TOKEN }}`
- ❌ `${{ secrets.TEST_PYPI_API_TOKEN }}`
- ❌ `username: __token__`
- ❌ `password: ${{ secrets.* }}`

### Added OIDC Support
- ✅ `permissions.id-token: write`
- ✅ Environment-based publishing
- ✅ Automatic trust establishment

## 🚀 Benefits

### Security
- **No long-lived tokens**: Eliminates the risk of token compromise
- **Automatic rotation**: OIDC tokens are short-lived and auto-generated
- **Scoped access**: Limited to specific repository and workflow

### Maintenance
- **No token management**: No need to rotate or update API tokens
- **Simplified setup**: One-time configuration on PyPI
- **Better audit trail**: Clear connection between GitHub and PyPI

### Reliability
- **No token expiration**: OIDC tokens don't expire like API tokens
- **Automatic renewal**: Tokens are generated fresh for each run
- **Reduced failures**: No more "invalid token" errors

## 📊 Workflow Triggers

The publishing workflow is triggered by:

1. **GitHub Releases**: Automatically publishes when you create a release
2. **Manual Dispatch**: Allows manual publishing with version control
3. **Environment Protection**: Uses GitHub environments for additional security

## 🔍 Verification Steps

After setup, verify the configuration:

### 1. Check PyPI Configuration
- Visit [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)
- Verify the `gopnik` project is listed with correct details

### 2. Test the Workflow
```bash
# Create a test release or use workflow dispatch
gh workflow run publish-pypi.yml --ref main
```

### 3. Monitor the Run
- Check GitHub Actions for successful execution
- Verify no authentication errors
- Confirm package appears on PyPI

## 🛠️ Troubleshooting

### Common Issues

**"Trusted publishing exchange failure"**
- Verify all publisher details match exactly
- Check that the workflow file exists at `.github/workflows/publish-pypi.yml`
- Ensure the environment name matches (case-sensitive)

**"Permission denied"**
- Verify `id-token: write` permission is set
- Check that the repository owner matches the publisher configuration
- Ensure the workflow is running from the correct branch

**"Environment not found"**
- Create the GitHub environment in repository settings
- Verify the environment name matches the workflow configuration
- **Note**: Missing Environment URL field in GitHub UI is normal and doesn't affect functionality

### Debug Steps

1. **Check workflow permissions**:
   ```yaml
   permissions:
     contents: read
     id-token: write
   ```

2. **Verify environment configuration**:
   ```yaml
   environment:
     name: pypi  # Must match PyPI publisher config
     url: https://pypi.org/p/gopnik
   ```

3. **Review PyPI publisher settings**:
   - Owner: `happy2234`
   - Repository: `gopnik`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi`

## 📚 Additional Resources

- **[PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)**
- **[GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)**
- **[PyPA Publish Action](https://github.com/pypa/gh-action-pypi-publish)**

## 🔗 Quick Links

- **[PyPI Project](https://pypi.org/project/gopnik/)**
- **[Test PyPI Project](https://test.pypi.org/project/gopnik/)**
- **[GitHub Repository](https://github.com/happy2234/gopnik)**
- **[Publishing Workflow](https://github.com/happy2234/gopnik/actions/workflows/publish-pypi.yml)**

---

**Status**: ✅ Ready for PyPI Trusted Publishing setup

Follow the steps above to complete the configuration and enjoy secure, token-free publishing!