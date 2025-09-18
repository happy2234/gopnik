# Publishing Gopnik to PyPI

This guide covers how to publish Gopnik to the Python Package Index (PyPI) so users can install it with `pip install gopnik`.

## Prerequisites

### 1. PyPI Account Setup

1. **Create PyPI Account**: Register at [pypi.org](https://pypi.org/account/register/)
2. **Create Test PyPI Account**: Register at [test.pypi.org](https://test.pypi.org/account/register/)
3. **Enable 2FA**: Enable two-factor authentication on both accounts
4. **Create API Tokens**:
   - Go to Account Settings → API tokens
   - Create tokens for both PyPI and Test PyPI
   - Store tokens securely

### 2. PyPI Trusted Publishing Setup (Recommended)

**Modern Approach**: Use PyPI Trusted Publishing with OpenID Connect (OIDC) for secure, token-free publishing.

#### Quick Setup:
1. **Configure PyPI Trusted Publisher**:
   - **PyPI Project Name**: `gopnik`
   - **Owner**: `happy2234`
   - **Repository name**: `gopnik`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`

2. **See detailed setup guide**: [PyPI Trusted Publishing Setup](docs/PYPI_TRUSTED_PUBLISHING_SETUP.md)

#### Legacy Approach (API Tokens):
If you prefer API tokens, add these secrets to your GitHub repository:
- `PYPI_API_TOKEN`: Your PyPI API token
- `TEST_PYPI_API_TOKEN`: Your Test PyPI API token
- `PAT_TOKEN`: GitHub Personal Access Token (for creating releases)

## Publishing Methods

### Method 1: Automated Publishing via GitHub Actions (Recommended)

#### Option A: Manual Workflow Trigger

1. Go to GitHub Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Enter version number (e.g., `0.1.0`)
4. Choose whether to test on Test PyPI first
5. Click "Run workflow"

The workflow will:
- Build the package
- Test installation on multiple Python versions
- Publish to Test PyPI (if selected)
- Publish to PyPI
- Create a GitHub release

#### Option B: Release-Triggered Publishing

1. Create a new release on GitHub:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
2. Go to GitHub → Releases → "Create a new release"
3. Choose the tag `v0.1.0`
4. Fill in release details
5. Publish release

This automatically triggers the PyPI publishing workflow.

### Method 2: Local Publishing

#### Step 1: Build the Package

```bash
# Run the build script
./scripts/build-package.sh

# Or build manually
pip install build twine
python -m build
python -m twine check dist/*
```

#### Step 2: Test on Test PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gopnik

# Test the CLI
gopnik --version
gopnik --help
```

#### Step 3: Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Test installation
pip install gopnik
gopnik --version
```

## Version Management

### Updating Version Numbers

The version is managed in multiple places:

1. **`src/gopnik/_version.py`**: Main version file
2. **`setup.py`**: Fallback version
3. **`pyproject.toml`**: Uses setuptools_scm for dynamic versioning

To update the version:

```bash
# Update version file
echo '__version__ = "0.2.0"' > src/gopnik/_version.py

# Update setup.py
sed -i 's/version = "0.1.0"/version = "0.2.0"/g' setup.py

# Commit changes
git add .
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

### Version Numbering Scheme

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `0.1.0`: Initial release
- `0.1.1`: Bug fix
- `0.2.0`: New CLI features
- `1.0.0`: First stable release

## Package Structure

The published package includes:

```
gopnik/
├── src/gopnik/           # Main package code
├── config/               # Default configurations
├── profiles/             # Default redaction profiles
├── examples/             # Usage examples
├── docs/                 # Documentation
├── README.md             # Package description
├── LICENSE               # MIT license
├── pyproject.toml        # Modern Python packaging
└── setup.py              # Legacy packaging support
```

## Testing the Published Package

### Test Installation

```bash
# Install from PyPI
pip install gopnik

# Test CLI
gopnik --version
gopnik --help
gopnik profile list

# Test Python API
python -c "import gopnik; print(gopnik.__version__)"
```

### Test in Different Environments

```bash
# Test with different Python versions
python3.8 -m pip install gopnik
python3.9 -m pip install gopnik
python3.10 -m pip install gopnik
python3.11 -m pip install gopnik

# Test in virtual environment
python -m venv test_env
source test_env/bin/activate
pip install gopnik
gopnik --version
deactivate
```

## Troubleshooting

### Common Issues

#### 1. Package Name Already Exists
```
ERROR: The name 'gopnik' is already in use
```
**Solution**: Choose a different package name or contact PyPI support if you own the name.

#### 2. Authentication Failed
```
ERROR: Invalid credentials
```
**Solution**: 
- Check API token is correct
- Ensure 2FA is enabled
- Use `__token__` as username with API token as password

#### 3. Version Already Exists
```
ERROR: Version 0.1.0 already exists
```
**Solution**: Increment version number and rebuild package.

#### 4. Package Validation Failed
```
ERROR: Package validation failed
```
**Solution**: 
- Run `twine check dist/*` to see specific issues
- Fix metadata in `setup.py` or `pyproject.toml`
- Ensure README.md is valid markdown

### Debugging Steps

1. **Check package contents**:
   ```bash
   tar -tzf dist/gopnik-0.1.0.tar.gz
   unzip -l dist/gopnik-0.1.0-py3-none-any.whl
   ```

2. **Validate package**:
   ```bash
   twine check dist/*
   ```

3. **Test local installation**:
   ```bash
   pip install dist/gopnik-0.1.0-py3-none-any.whl
   ```

4. **Check package metadata**:
   ```bash
   python setup.py check --metadata --strict
   ```

## Post-Publication

### Update Documentation

After publishing, update:

1. **README.md**: Update installation instructions
2. **Documentation**: Update version references
3. **Wiki**: Add installation guide
4. **Release Notes**: Document changes

### Monitor Package

1. **PyPI Statistics**: Check download stats on PyPI
2. **GitHub Issues**: Monitor for installation issues
3. **User Feedback**: Respond to questions and bug reports

### Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Security Patches**: Address security vulnerabilities quickly
3. **Bug Fixes**: Release patch versions for critical bugs
4. **Feature Releases**: Plan minor/major version releases

## Automation

The GitHub Actions workflow handles:

- ✅ Building packages
- ✅ Testing on multiple Python versions
- ✅ Publishing to Test PyPI
- ✅ Publishing to PyPI
- ✅ Creating GitHub releases
- ✅ Updating documentation
- ✅ **Secure OIDC authentication** (no API tokens needed)
- ✅ **Environment-based protection** (additional security layer)

This ensures consistent, reliable, and secure releases with minimal manual intervention.

## Resources

- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [setuptools_scm](https://github.com/pypa/setuptools_scm)
- [GitHub Actions for PyPI](https://github.com/pypa/gh-action-pypi-publish)
- [Semantic Versioning](https://semver.org/)

---

**Ready to publish? Run the GitHub Actions workflow or use the local build script!** 🚀