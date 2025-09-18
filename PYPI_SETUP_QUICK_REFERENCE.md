# PyPI Trusted Publishing - Quick Reference

## 🚀 Setup Information for PyPI

Copy and paste these values into the PyPI Trusted Publisher form:

### **Production PyPI** (https://pypi.org/manage/account/publishing/)

| Field | Value |
|-------|-------|
| **PyPI Project Name** | `gopnik` |
| **Owner** | `happy2234` |
| **Repository name** | `gopnik` |
| **Workflow name** | `publish-pypi.yml` |
| **Environment name** | `pypi` |

### **Test PyPI** (https://test.pypi.org/manage/account/publishing/)

| Field | Value |
|-------|-------|
| **PyPI Project Name** | `gopnik` |
| **Owner** | `happy2234` |
| **Repository name** | `gopnik` |
| **Workflow name** | `publish-pypi.yml` |
| **Environment name** | `test-pypi` |

## 🔧 GitHub Environment Setup

Create these environments in your GitHub repository settings:

1. **Environment**: `pypi`
   - **URL**: `https://pypi.org/p/gopnik` *(Note: URL field may not be visible in newer GitHub UI - this is normal)*
   - **Protection**: Require reviewers (recommended)
   - **Branches**: Restrict to `main` branch

2. **Environment**: `test-pypi`
   - **URL**: `https://test.pypi.org/p/gopnik` *(Note: URL field may not be visible - this doesn't affect functionality)*
   - **Protection**: Optional

## ✅ Verification Checklist

- [ ] PyPI trusted publisher configured
- [ ] Test PyPI trusted publisher configured (optional)
- [ ] GitHub environments created
- [ ] Workflow file exists at `.github/workflows/publish-pypi.yml`
- [ ] Workflow has `id-token: write` permission
- [ ] Test run successful

## 🔗 Quick Links

- **[PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)**
- **[Test PyPI Trusted Publishers](https://test.pypi.org/manage/account/publishing/)**
- **[GitHub Repository Settings](https://github.com/happy2234/gopnik/settings)**
- **[GitHub Environments](https://github.com/happy2234/gopnik/settings/environments)**
- **[Publishing Workflow](https://github.com/happy2234/gopnik/actions/workflows/publish-pypi.yml)**

## 📋 Benefits

✅ **No API tokens to manage**  
✅ **Automatic security rotation**  
✅ **Scoped access permissions**  
✅ **Better audit trail**  
✅ **Reduced security risks**  

---

**Need help?** See the [complete setup guide](docs/PYPI_TRUSTED_PUBLISHING_SETUP.md)