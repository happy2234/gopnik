# Gopnik - AI-Powered Deidentification Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/happy2234/gopnik)](https://github.com/happy2234/gopnik/issues)
[![GitHub Stars](https://img.shields.io/github/stars/happy2234/gopnik)](https://github.com/happy2234/gopnik/stargazers)

Gopnik is an open-source, AI-powered forensic-grade deidentification toolkit that automatically detects and redacts Personally Identifiable Information (PII) from complex, visually-rich documents while preserving document structure and providing verifiable audit trails.

🚀 **[Get Started](https://happy2234.github.io/gopnik/user-guide/cli-quickstart/)** | 📖 **[Documentation](https://happy2234.github.io/gopnik/)** | 💬 **[Discussions](https://github.com/happy2234/gopnik/discussions)**

## ✨ Features

### 🔍 Advanced AI Detection
- **Multi-Modal PII Detection**: Combines computer vision and NLP for comprehensive detection
- **Hybrid AI Engine**: Intelligent fusion of CV and NLP results for maximum accuracy
- **Visual PII Detection**: Faces, signatures, barcodes, QR codes using computer vision
- **Text PII Detection**: Names, emails, phones, addresses, SSNs using advanced NLP
- **Confidence Scoring**: Adjustable thresholds for precision/recall optimization

### 📄 Document Processing Core
- **Multi-Format Support**: PDF, PNG, JPEG, TIFF, BMP with structure preservation
- **Page-by-Page Processing**: Efficient handling of multi-page documents
- **Layout Preservation**: Maintains original document formatting and structure
- **Batch Processing**: Process entire directories with progress tracking
- **Memory Efficient**: Optimized for large document processing

### 🎨 Flexible Redaction Styles
- **Solid Redaction**: Black/white blocks for complete obscuration
- **Pixelated Redaction**: Pixelation effect for partial visibility
- **Blur Redaction**: Gaussian blur for aesthetic redaction
- **Custom Patterns**: Configurable redaction styles per PII type

### 🚀 Deployment Options
- **CLI Tool**: Full-featured command-line interface with progress tracking
- **Web Demo**: Interactive browser-based interface
- **REST API**: Comprehensive programmatic integration with FastAPI
- **Docker Containers**: Production-ready containerized deployments
- **Docker Compose**: Complete orchestration for development and production
- **Kubernetes**: Scalable cloud-native deployments (configurations included)
- **Batch Processing**: Enterprise-scale document processing with filtering

### 🔒 Forensic-Grade Security
- **Cryptographic Signatures**: RSA/ECDSA digital signatures for audit logs
- **Document Integrity**: SHA-256 hashing and tamper detection
- **Audit Trails**: Comprehensive logging with cryptographic verification
- **Chain of Custody**: Verifiable document processing history

### ⚙️ Enterprise Features
- **Custom Redaction Profiles**: Industry-specific configurations (HIPAA, PCI DSS)
- **Multilingual Support**: Handles multiple languages including Indic scripts
- **Privacy-First**: No data leaves your environment in CLI mode
- **Performance Monitoring**: Built-in statistics and health checking

## 🎯 Use Cases

- **Healthcare**: HIPAA-compliant document redaction
- **Legal**: Attorney-client privilege protection
- **Financial**: PCI DSS compliance for financial documents
- **Government**: Classified information protection
- **Research**: Data anonymization for studies
- **Corporate**: Employee data protection

## Quick Start

### Installation

#### Python Package
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

#### Docker Deployment
```bash
# CLI container
docker run -v /path/to/docs:/home/gopnik/data gopnik/cli process document.pdf

# API server
docker run -p 8000:80 gopnik/api

# Web interface
docker run -p 8080:80 gopnik/web

# Complete stack with Docker Compose
docker-compose up -d
```

#### Production Deployment
```bash
# Deploy to production environment
./scripts/deploy.sh

# Deploy specific services
SERVICES="gopnik-api gopnik-web" ./scripts/deploy.sh

# Deploy with custom configuration
DEPLOYMENT_ENV=production ./scripts/deploy.sh
```

### CLI Usage

```bash
# Process a single document
gopnik process document.pdf --profile healthcare --output redacted.pdf

# Process with custom profile file
gopnik process document.pdf --profile-file custom_profile.yaml --dry-run

# Batch processing with progress tracking
gopnik batch /path/to/documents --profile default --recursive --progress

# Batch processing with filtering and limits
gopnik batch /docs --pattern "*.pdf" --max-files 100 --continue-on-error

# Document validation with audit trails
gopnik validate document.pdf audit.json --verify-signatures --verbose

# Auto-find audit logs for validation
gopnik validate document.pdf --audit-dir /audit/logs

# Profile management
gopnik profile list --verbose --format json
gopnik profile show healthcare
gopnik profile create --name custom --based-on default --pii-types name email phone
gopnik profile edit healthcare --add-pii-types ssn --redaction-style blur
gopnik profile validate custom
gopnik profile delete old-profile --force

# Start REST API server
gopnik api --host 0.0.0.0 --port 8000
gopnik api --reload  # Development mode

# Get help for any command
gopnik --help
gopnik process --help
gopnik profile --help
gopnik api --help
```

### Python API Usage

```python
from gopnik.core.processor import DocumentProcessor
from gopnik.models.profiles import RedactionProfile
from gopnik.ai.hybrid_engine import HybridAIEngine
from pathlib import Path

# Initialize processor with AI engine
processor = DocumentProcessor()
ai_engine = HybridAIEngine()
processor.set_ai_engine(ai_engine)

# Load redaction profile
profile = RedactionProfile.from_yaml(Path("profiles/healthcare_hipaa.yaml"))

# Process document
result = processor.process_document(
    input_path=Path("document.pdf"),
    profile=profile
)

print(f"Processing completed: {result.success}")
print(f"Detections found: {result.detection_count}")
print(f"Output saved to: {result.output_path}")
```

### Web Demo

```bash
# Start web demo
gopnik web --host localhost --port 8000
```

### REST API Server

```bash
# Start API server
gopnik api --host localhost --port 8080

# Development mode with auto-reload
gopnik api --reload --log-level debug

# Access interactive documentation
# Swagger UI: http://localhost:8080/docs
# ReDoc: http://localhost:8080/redoc
```

#### API Usage Examples

```python
import requests

# Health check
response = requests.get('http://localhost:8080/api/v1/health')
print(f"API Status: {response.json()['status']}")

# Process document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'profile_name': 'healthcare_hipaa'}
    
    response = requests.post(
        'http://localhost:8080/api/v1/process',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"Processing successful: {result['success']}")
    print(f"Detections found: {len(result['detections'])}")
```

```bash
# cURL examples
curl http://localhost:8080/api/v1/health

curl -X POST http://localhost:8080/api/v1/process \
  -F "file=@document.pdf" \
  -F "profile_name=default"
```

## 🏗️ Architecture

### Core Processing Engine
```
src/gopnik/core/
├── interfaces.py         # Abstract interfaces for extensibility
├── processor.py          # Main document processor coordinator
├── analyzer.py           # Document parsing and structure analysis
└── redaction.py          # Multi-style redaction engine
```

### AI Detection Engines
```
src/gopnik/ai/
├── cv_engine.py          # Computer vision PII detection
├── nlp_engine.py         # Natural language processing engine
└── hybrid_engine.py      # Intelligent fusion of CV + NLP
```

### Data Models
```
src/gopnik/models/
├── pii.py               # PII detection and bounding box models
├── processing.py        # Document and processing result models
├── profiles.py          # Redaction profile management
├── audit.py             # Audit logging and integrity models
└── errors.py            # Comprehensive error handling
```

### Enterprise Security
```
src/gopnik/utils/
├── crypto.py            # RSA/ECDSA signatures, SHA-256 hashing
├── audit_logger.py      # Cryptographically signed audit trails
├── integrity_validator.py # Forensic document validation
├── file_utils.py        # Secure file operations
└── logging_utils.py     # Structured logging configuration
```

### User Interfaces
```
src/gopnik/interfaces/
├── web/                 # Interactive web demo
├── cli/                 # Command-line interface
└── api/                 # FastAPI REST API server
    ├── app.py           # FastAPI application
    ├── models.py        # Pydantic request/response models
    ├── dependencies.py  # Dependency injection
    └── routers/         # API endpoint routers
```

## 🧪 Testing & Quality

- **63 Comprehensive Tests**: Full coverage of core functionality
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Memory and processing efficiency
- **Security Tests**: Cryptographic validation and integrity checks

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_document_processor.py -v
pytest tests/test_ai_integration.py -v
pytest tests/test_redaction_engine.py -v
```

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Install in development mode with all dependencies
pip install -e .[all,dev]

# Run tests
pytest

# Run API-specific tests
pytest tests/test_api_*.py -v

# Code formatting
black src/
flake8 src/
```

### Development Servers

```bash
# Start API server in development mode
gopnik api --reload --log-level debug

# Start web demo (when implemented)
gopnik web --reload

# Run CLI commands
gopnik process document.pdf --profile default
```

## License

MIT License - see LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## 📚 Documentation

### Complete Documentation Suite
- **[User Guide](https://happy2234.github.io/gopnik/user-guide/)**: Complete user documentation
- **[Developer Guide](https://happy2234.github.io/gopnik/developer-guide/)**: API reference and development docs
- **[CLI Manual](MANUAL_CLI.md)**: Comprehensive command-line interface guide
- **[Web Manual](MANUAL_WEB.md)**: Complete web interface documentation
- **[API Manual](MANUAL_API.md)**: Detailed REST API reference and integration guide
- **[Usage Scenarios](SCENARIOS.md)**: Real-world examples and test cases
- **[Deployment Guide](scripts/deploy.sh)**: Production deployment and Docker configurations
- **[FAQ](https://happy2234.github.io/gopnik/faq/)**: Frequently asked questions

## 🤝 Community & Support

- 💬 **[GitHub Discussions](https://github.com/happy2234/gopnik/discussions)**: Community support and feature requests
- 🐛 **[Issues](https://github.com/happy2234/gopnik/issues)**: Bug reports and feature requests
- 📖 **[Wiki](https://github.com/happy2234/gopnik/wiki)**: Community-maintained documentation (auto-setup available)
- 📧 **Email**: support@gopnik.ai

> 💡 **Wiki Setup**: Enable wiki in repository settings, then use our automated GitHub Actions workflow for instant setup!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by the Gopnik development team
- Special thanks to all contributors and the open-source community
- Powered by state-of-the-art AI models and computer vision techniques

---

**⭐ Star this repository if you find it useful!**