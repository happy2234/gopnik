# Installation Guide

This guide covers all installation methods for Gopnik across different platforms and use cases.

## 🚀 Quick Installation

### Python Package (Recommended)

```bash
# Basic installation
pip install gopnik

# With web interface support
pip install gopnik[web]

# With AI engines
pip install gopnik[ai]

# Full installation (all features)
pip install gopnik[all]
```

### Verify Installation

```bash
gopnik --version
gopnik --help
```

## 📦 Installation Methods

### 1. PyPI Package

The easiest way to install Gopnik:

```bash
# Latest stable version
pip install gopnik

# Specific version
pip install gopnik==1.0.0

# Development version
pip install --pre gopnik
```

### 2. From Source

For developers or latest features:

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Install in development mode
pip install -e .

# Install with all dependencies
pip install -e .[all,dev]
```

### 3. Docker Container

For containerized deployment:

```bash
# Pull official image
docker pull gopnik/gopnik:latest

# Run CLI
docker run --rm -v $(pwd):/data gopnik/gopnik process /data/document.pdf

# Run web demo
docker run -p 8000:8000 gopnik/gopnik:web
```

### 4. Desktop Application

Download platform-specific installers:

- **Windows**: [gopnik-desktop-1.0.0-windows.exe](https://github.com/happy2234/gopnik/releases)
- **macOS**: [gopnik-desktop-1.0.0-macos.dmg](https://github.com/happy2234/gopnik/releases)
- **Linux**: [gopnik-desktop-1.0.0-linux.AppImage](https://github.com/happy2234/gopnik/releases)

## 🖥️ Platform-Specific Instructions

### Windows

#### Prerequisites
```powershell
# Install Python 3.8+
winget install Python.Python.3.11

# Install Git (optional, for source installation)
winget install Git.Git
```

#### Installation
```powershell
# Using pip
pip install gopnik[all]

# Using conda
conda install -c conda-forge gopnik
```

### macOS

#### Prerequisites
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Git (optional)
brew install git
```

#### Installation
```bash
# Using pip
pip3 install gopnik[all]

# Using Homebrew (when available)
brew install gopnik
```

### Linux (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install Git (optional)
sudo apt install git

# Install system dependencies for AI features
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

#### Installation
```bash
# Create virtual environment (recommended)
python3 -m venv gopnik-env
source gopnik-env/bin/activate

# Install Gopnik
pip install gopnik[all]
```

### Linux (CentOS/RHEL/Fedora)

#### Prerequisites
```bash
# CentOS/RHEL
sudo yum install python3 python3-pip git

# Fedora
sudo dnf install python3 python3-pip git

# Install system dependencies
sudo yum install mesa-libGL glib2 libSM libXext libXrender libgomp
```

#### Installation
```bash
# Create virtual environment
python3 -m venv gopnik-env
source gopnik-env/bin/activate

# Install Gopnik
pip install gopnik[all]
```

## 🔧 Configuration

### Initial Setup

```bash
# Create configuration directory
mkdir -p ~/.gopnik

# Generate default configuration
gopnik config init

# Edit configuration
gopnik config edit
```

### Environment Variables

```bash
# Set data directory
export GOPNIK_DATA_DIR=~/.gopnik

# Set log level
export GOPNIK_LOG_LEVEL=INFO

# Enable GPU (if available)
export GOPNIK_USE_GPU=true
```

## 🧪 Verify Installation

### Basic Functionality Test

```bash
# Check version
gopnik --version

# Test CLI
gopnik process --help

# Test configuration
gopnik config show

# Test AI engines (if installed)
gopnik test ai-engines
```

### Process Test Document

```bash
# Download test document
curl -O https://github.com/happy2234/gopnik/raw/main/tests/data/sample.pdf

# Process with default profile
gopnik process sample.pdf --output redacted.pdf

# Verify output
ls -la redacted.pdf
```

## 🚨 Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Use user installation
pip install --user gopnik

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
pip install gopnik
```

#### Missing Dependencies
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-dev build-essential

# Install AI dependencies separately
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### GPU Support Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Getting Help

If you encounter issues:

1. **Check the [FAQ](FAQ)**
2. **Search [existing issues](https://github.com/happy2234/gopnik/issues)**
3. **Ask in [Discussions](https://github.com/happy2234/gopnik/discussions)**
4. **Create a [new issue](https://github.com/happy2234/gopnik/issues/new)**

## 📚 Next Steps

After installation:

1. **[First Steps](First-Steps)**: Process your first document
2. **[Configuration](Configuration)**: Customize Gopnik for your needs
3. **[CLI Usage Examples](CLI-Usage-Examples)**: Learn command-line usage
4. **[Web Demo Tutorial](Web-Demo-Tutorial)**: Try the web interface

---

**Installation complete! 🎉 Ready to start deidentifying documents!**