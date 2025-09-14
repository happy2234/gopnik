# Gopnik - AI-Powered Deidentification Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/happy2234/gopnik)](https://github.com/happy2234/gopnik/issues)
[![GitHub Stars](https://img.shields.io/github/stars/happy2234/gopnik)](https://github.com/happy2234/gopnik/stargazers)

Gopnik is an open-source, AI-powered forensic-grade deidentification toolkit that automatically detects and redacts Personally Identifiable Information (PII) from complex, visually-rich documents while preserving document structure and providing verifiable audit trails.

🚀 **[Try the Web Demo](https://gopnik-demo.example.com)** | 📖 **[Documentation](https://gopnik.readthedocs.io/)** | 💬 **[Discussions](https://github.com/happy2234/gopnik/discussions)**

## ✨ Features

- 🔍 **Multi-Modal PII Detection**: Combines computer vision and NLP for comprehensive detection
- 🚀 **Three Deployment Options**: Web demo, CLI tool, and REST API
- 🔒 **Forensic-Grade Auditing**: Cryptographic audit trails and integrity validation
- ⚙️ **Custom Redaction Profiles**: Configurable rules for different use cases
- 📄 **Layout Preservation**: Maintains document structure during redaction
- 🌍 **Multilingual Support**: Handles multiple languages including Indic scripts
- 🛡️ **Privacy-First**: No data leaves your environment in CLI mode
- 📊 **Comprehensive Reporting**: Detailed audit logs and processing statistics

## 🎯 Use Cases

- **Healthcare**: HIPAA-compliant document redaction
- **Legal**: Attorney-client privilege protection
- **Financial**: PCI DSS compliance for financial documents
- **Government**: Classified information protection
- **Research**: Data anonymization for studies
- **Corporate**: Employee data protection

## Quick Start

### Installation

```bash
# Basic installation
pip install gopnik

# With web interface
pip install gopnik[web]

# With AI engines
pip install gopnik[ai]

# Full installation
pip install gopnik[all]
```

### CLI Usage

```bash
# Process a single document
gopnik process --input document.pdf --profile healthcare --output redacted.pdf

# Validate document integrity
gopnik validate --document redacted.pdf --audit audit.json

# Batch processing
gopnik batch --input-dir ./documents --profile legal --output-dir ./redacted
```

### Web Demo

```bash
# Start web demo
gopnik web --host localhost --port 8000
```

### API Server

```bash
# Start API server
gopnik api --host localhost --port 8080
```

## Project Structure

```
src/gopnik/
├── core/                 # Core processing engine
│   ├── interfaces.py     # Abstract interfaces
│   ├── processor.py      # Main document processor
│   ├── analyzer.py       # Document analysis
│   └── redaction.py      # Redaction engine
├── models/               # Data models
│   ├── pii.py           # PII detection models
│   ├── processing.py    # Processing results
│   ├── profiles.py      # Redaction profiles
│   ├── audit.py         # Audit logging
│   └── errors.py        # Error handling
├── interfaces/           # User interfaces
│   ├── web/             # Web demo interface
│   ├── cli/             # Command-line interface
│   └── api/             # REST API interface
├── ai/                  # AI engine components
├── utils/               # Utility functions
│   ├── crypto.py        # Cryptographic utilities
│   ├── file_utils.py    # File handling
│   └── logging_utils.py # Logging configuration
└── config/              # Configuration management
    ├── config.py        # Main configuration
    └── settings.py      # Component settings
```

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black src/
flake8 src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## 📚 Documentation

- **[User Guide](https://gopnik.readthedocs.io/en/latest/user-guide/)**: Complete user documentation
- **[Developer Guide](https://gopnik.readthedocs.io/en/latest/developer-guide/)**: API reference and development docs
- **[Tutorials](https://gopnik.readthedocs.io/en/latest/tutorials/)**: Step-by-step tutorials
- **[FAQ](https://gopnik.readthedocs.io/en/latest/faq/)**: Frequently asked questions

## 🤝 Community & Support

- 💬 **[GitHub Discussions](https://github.com/happy2234/gopnik/discussions)**: Community support and feature requests
- 🐛 **[Issues](https://github.com/happy2234/gopnik/issues)**: Bug reports and feature requests
- 📖 **[Wiki](https://github.com/happy2234/gopnik/wiki)**: Community-maintained documentation
- 📧 **Email**: support@gopnik.ai

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by the Gopnik development team
- Special thanks to all contributors and the open-source community
- Powered by state-of-the-art AI models and computer vision techniques

---

**⭐ Star this repository if you find it useful!**