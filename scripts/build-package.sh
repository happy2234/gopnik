#!/bin/bash
# Build and test Gopnik package for PyPI publication

set -e

echo "🏗️ Building Gopnik package for PyPI..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Install build dependencies
print_status "Installing build dependencies..."
pip install --upgrade pip build twine setuptools wheel setuptools_scm

# Build the package
print_status "Building source distribution and wheel..."
python -m build

# Check the built packages
print_status "Checking built packages..."
python -m twine check dist/*

# List built packages
print_status "Built packages:"
ls -la dist/

# Test installation in a virtual environment
print_status "Testing installation in virtual environment..."

# Create temporary virtual environment
TEMP_VENV=$(mktemp -d)
python -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

# Install from wheel
print_status "Installing from wheel..."
pip install dist/*.whl

# Test CLI
print_status "Testing CLI installation..."
if gopnik --version; then
    print_success "CLI installation test passed"
else
    print_error "CLI installation test failed"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Test Python import
print_status "Testing Python import..."
if python -c "import gopnik; print(f'Gopnik version: {gopnik.__version__}')"; then
    print_success "Python import test passed"
else
    print_error "Python import test failed"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Test basic CLI commands
print_status "Testing basic CLI commands..."
if gopnik --help > /dev/null; then
    print_success "CLI help command works"
else
    print_error "CLI help command failed"
fi

if gopnik profile list > /dev/null 2>&1; then
    print_success "CLI profile command works"
else
    print_warning "CLI profile command failed (expected if no profiles exist)"
fi

# Clean up
deactivate
rm -rf "$TEMP_VENV"

print_success "Package build and test completed successfully!"
print_status "Package files are ready in the dist/ directory:"
ls -la dist/

echo ""
print_status "Next steps:"
echo "1. Test upload to Test PyPI:"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "2. Test installation from Test PyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gopnik"
echo ""
echo "3. Upload to PyPI:"
echo "   twine upload dist/*"
echo ""
echo "4. Or use GitHub Actions workflow:"
echo "   Go to Actions → Publish to PyPI → Run workflow"