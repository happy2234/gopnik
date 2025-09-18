# Installation Guide

This guide covers all installation methods for Gopnik across different platforms and use cases.

## 📖 Complete Documentation Suite

Before installation, explore our comprehensive documentation:
- **[CLI Manual](../MANUAL_CLI.md)**: Complete command-line interface guide with examples
- **[Web Manual](../MANUAL_WEB.md)**: Web interface documentation and tutorials
- **[API Manual](../MANUAL_API.md)**: REST API reference and integration guide
- **[Usage Scenarios](../SCENARIOS.md)**: Real-world examples and comprehensive test cases
- **[Deployment Guide](../scripts/deploy.sh)**: Production deployment automation

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
# Check version and basic functionality
gopnik --version
gopnik --help

# Test CLI commands
gopnik profile list
gopnik process --help
gopnik batch --help
gopnik validate --help
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
# Pull official images
docker pull gopnik/cli:latest
docker pull gopnik/api:latest
docker pull gopnik/web:latest

# Run CLI container
docker run --rm -v $(pwd):/home/gopnik/data gopnik/cli process document.pdf

# Run API server
docker run -p 8000:80 gopnik/api

# Run web interface
docker run -p 8080:80 gopnik/web
```

### 4. Docker Compose (Recommended for Development)

Complete development environment:

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Start development stack
docker-compose up -d

# Access services:
# - API: http://localhost:8000/docs
# - Web: http://localhost:8080
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

### 5. Production Deployment

Automated production deployment:

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Deploy production stack
./scripts/deploy.sh

# Or use production compose file
docker-compose -f docker-compose.prod.yml up -d
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
# Create a simple test document
echo "Test document with PII: John Doe, john@example.com, 555-123-4567" > test.txt

# Process with CLI
gopnik process test.txt --profile default --dry-run

# Process for real
gopnik process test.txt --profile default --output redacted.txt

# Validate the result
gopnik validate redacted.txt

# Check available profiles
gopnik profile list --verbose
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