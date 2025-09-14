# Gopnik - AI-Powered Deidentification Toolkit

Gopnik is an open-source, AI-powered forensic-grade deidentification toolkit that automatically detects and redacts Personally Identifiable Information (PII) from complex, visually-rich documents while preserving document structure and providing verifiable audit trails.

## Features

- **Multi-Modal PII Detection**: Combines computer vision and NLP for comprehensive detection
- **Three Deployment Options**: Web demo, CLI tool, and REST API
- **Forensic-Grade Auditing**: Cryptographic audit trails and integrity validation
- **Custom Redaction Profiles**: Configurable rules for different use cases
- **Layout Preservation**: Maintains document structure during redaction
- **Multilingual Support**: Handles multiple languages including Indic scripts

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
git clone https://github.com/gopnik/gopnik.git
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

## Support

- Documentation: https://gopnik.readthedocs.io/
- Issues: https://github.com/gopnik/gopnik/issues
- Discussions: https://github.com/gopnik/gopnik/discussions