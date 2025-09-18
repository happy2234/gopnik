# Complete PyPI Setup Guide for Gopnik

## 🚨 Current Status: PyPI Not Set Up Yet

The PyPI publishing workflow is configured but **not yet functional** because the initial setup hasn't been completed. Here's what needs to be done:

## 📋 Required Setup Steps

### 1. **Create PyPI Account and Project**

#### Step 1.1: Create PyPI Account
1. Go to [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. Create an account with your email
3. Verify your email address

#### Step 1.2: Create Test PyPI Account (Optional but Recommended)
1. Go to [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
2. Create an account (can use same email)
3. Verify your email address

### 2. **Initial Package Upload (Manual)**

Since PyPI Trusted Publishing requires the project to exist first, you need to do an initial manual upload:

#### Step 2.1: Build the Package Locally
```bash
# Clone the repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Install build tools
pip install build twine

# Build the package
python -m build

# This creates dist/ directory with .whl and .tar.gz files
```

#### Step 2.2: Upload to Test PyPI First (Recommended)
```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for username and password
# Username: __token__
# Password: [your Test PyPI API token]
```

#### Step 2.3: Upload to Production PyPI
```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for username and password
# Username: __token__
# Password: [your PyPI API token]
```

### 3. **Configure PyPI Trusted Publishing**

After the initial upload, configure trusted publishing:

#### Step 3.1: Configure on PyPI
1. Go to [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)
2. Click "Add a new trusted publisher"
3. Fill in the form:
   - **PyPI Project Name**: `gopnik`
   - **Owner**: `happy2234`
   - **Repository name**: `gopnik`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`

#### Step 3.2: Configure on Test PyPI (Optional)
1. Go to [https://test.pypi.org/manage/account/publishing/](https://test.pypi.org/manage/account/publishing/)
2. Repeat the same process with environment name: `test-pypi`

### 4. **Create GitHub Environments**

#### Step 4.1: Create Environments
1. Go to your GitHub repository: `https://github.com/happy2234/gopnik`
2. Go to Settings → Environments
3. Create two environments:
   - **Name**: `pypi`
     - Add protection rules (optional): Require reviewers
     - Restrict to branches: `main`
   - **Name**: `test-pypi`
     - Add protection rules as needed

**Note**: The Environment URL field may not be visible - this is normal and doesn't affect functionality.

### 5. **Test the Workflow**

#### Step 5.1: Manual Workflow Trigger
1. Go to Actions → Publish to PyPI
2. Click "Run workflow"
3. Enter a version number (e.g., `0.1.0`)
4. Choose whether to test on Test PyPI first
5. Run the workflow

#### Step 5.2: Release-Based Trigger
1. Create a new release on GitHub
2. Tag it with a version (e.g., `v0.1.0`)
3. The workflow should trigger automatically

## 🔧 Current Workflow Configuration

The workflow is already configured with:
- ✅ PyPI Trusted Publishing (OIDC)
- ✅ Updated artifact actions (v4)
- ✅ Proper environment configuration
- ✅ Build and test steps
- ✅ Both Test PyPI and Production PyPI support

## 🚫 Why PyPI Workflow Fails Currently

The workflow fails because:
1. **No PyPI project exists yet** - needs initial manual upload
2. **Trusted publishing not configured** - needs PyPI account setup
3. **GitHub environments don't exist** - needs to be created in repo settings
4. **No release has been created** - workflow triggers on releases

## 📝 Quick Setup Checklist

- [ ] Create PyPI account
- [ ] Create Test PyPI account (optional)
- [ ] Generate API tokens for initial upload
- [ ] Build package locally (`python -m build`)
- [ ] Upload to Test PyPI (`twine upload --repository testpypi dist/*`)
- [ ] Upload to PyPI (`twine upload dist/*`)
- [ ] Configure PyPI Trusted Publishing
- [ ] Configure Test PyPI Trusted Publishing (optional)
- [ ] Create GitHub environments (`pypi`, `test-pypi`)
- [ ] Test workflow with manual trigger
- [ ] Create first release to test automatic trigger

## 🎯 Next Steps

1. **Complete the manual setup steps above**
2. **Test the workflow** with a manual trigger
3. **Create your first release** to test automatic publishing
4. **Monitor the workflow** for any remaining issues

## 📚 Additional Resources

- **[PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)**
- **[GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)**
- **[Twine Documentation](https://twine.readthedocs.io/)**
- **[Python Packaging Guide](https://packaging.python.org/)**

---

**Status**: ⚠️ **Setup Required** - PyPI workflow is configured but needs initial setup  
**Priority**: Medium - Can be completed when ready to publish  
**Estimated Time**: 30-60 minutes for complete setup