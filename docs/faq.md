# Frequently Asked Questions (FAQ)

## 📖 Documentation Quick Links

Before diving into the FAQ, check out our comprehensive documentation:
- **[CLI Manual](../MANUAL_CLI.md)**: Complete command-line interface guide
- **[Web Manual](../MANUAL_WEB.md)**: Web interface documentation
- **[API Manual](../MANUAL_API.md)**: REST API reference and integration guide
- **[Usage Scenarios](../SCENARIOS.md)**: Real-world examples and test cases
- **[Deployment Guide](user-guide/deployment.md)**: Production deployment guide

## 🔍 General Questions

### What is Gopnik?

Gopnik is an AI-powered forensic-grade deidentification toolkit that automatically detects and redacts Personally Identifiable Information (PII) from complex, visually-rich documents while preserving document structure and providing verifiable audit trails.

### What makes Gopnik different from other redaction tools?

- **AI-Powered**: Uses advanced computer vision and NLP models for accurate PII detection
- **Forensic-Grade**: Provides cryptographic audit trails and integrity validation
- **Layout Preservation**: Maintains document structure during redaction
- **Multi-Modal**: Combines visual and text-based PII detection
- **Open Source**: Fully open-source with transparent algorithms

### What types of documents does Gopnik support?

- **PDF documents**: Text and image-based PDFs
- **Image formats**: PNG, JPEG, TIFF, BMP
- **Multi-page documents**: Batch processing support
- **Complex layouts**: Tables, forms, and mixed content

### What PII types can Gopnik detect?

**Visual PII:**
- Faces and photographs
- Signatures
- Barcodes and QR codes

**Text PII:**
- Names and personal identifiers
- Email addresses and phone numbers
- Addresses and locations
- Social Security Numbers (SSN)
- Credit card numbers
- Medical record numbers
- And many more...

## 📚 Documentation and Learning

### Where can I find complete documentation?

Gopnik provides comprehensive documentation across multiple formats:

**User Manuals:**
- **[CLI Manual](../MANUAL_CLI.md)**: 50+ page comprehensive guide covering installation, usage, configuration, troubleshooting, and advanced scenarios
- **[Web Manual](../MANUAL_WEB.md)**: Complete web interface documentation with tutorials and best practices
- **[API Manual](../MANUAL_API.md)**: Detailed REST API reference with client libraries and integration examples

**Practical Examples:**
- **[Usage Scenarios](../SCENARIOS.md)**: Real-world examples for healthcare, legal, financial, government, and research use cases
- **[Test Cases](../SCENARIOS.md#integration-test-cases)**: Comprehensive test scenarios and integration examples

**Deployment:**
- **[Docker Deployment](../docker-compose.yml)**: Development environment setup
- **[Production Deployment](../docker-compose.prod.yml)**: Production-ready container orchestration
- **[Deployment Scripts](../scripts/deploy.sh)**: Automated deployment and management tools

### How do I get started quickly?

1. **Choose your interface**: CLI, Web, or API
2. **Read the relevant manual**: Each interface has a comprehensive manual
3. **Try the examples**: Start with the usage scenarios that match your use case
4. **Deploy easily**: Use Docker Compose for quick setup

### What deployment options are available?

**Development:**
- Python package installation
- Docker containers
- Docker Compose development stack

**Production:**
- Automated deployment scripts
- Production Docker Compose configuration
- Kubernetes configurations (included)
- Load balancing and monitoring setup

## 🚀 Installation and Setup

### What are the system requirements?

**Minimum Requirements:**
- Python 3.8 or higher
- 4GB RAM
- 2GB free disk space

**Recommended:**
- Python 3.9+
- 8GB RAM
- GPU support for faster processing
- SSD storage for better performance

### How do I install Gopnik?

```bash
# Basic installation
pip install gopnik

# Full installation with all features
pip install gopnik[all]
```

See our [Installation Guide](user-guide/installation.md) for detailed instructions.

### Can I use Gopnik without an internet connection?

Yes! Gopnik supports offline operation:
- **CLI mode**: Fully offline processing
- **Desktop app**: Offline-first design
- **Web demo**: Requires internet for hosting but processes locally

## 💻 CLI Questions

### How do I get started with the CLI?

```bash
# Install Gopnik
pip install gopnik

# Process your first document
gopnik process document.pdf

# Get help
gopnik --help
gopnik process --help
```

See our [CLI Quick Start](user-guide/cli-quickstart.md) for a complete guide.

### What CLI commands are available?

- **`process`**: Process a single document
- **`batch`**: Process multiple documents in a directory
- **`validate`**: Validate document integrity using audit trails
- **`profile`**: Manage redaction profiles (list, create, edit, delete)

### How do I create and manage profiles via CLI?

```bash
# List available profiles
gopnik profile list --verbose

# Show profile details
gopnik profile show healthcare

# Create new profile
gopnik profile create --name custom --pii-types name email phone

# Edit existing profile
gopnik profile edit healthcare --add-pii-types ssn --redaction-style blur

# Validate profile
gopnik profile validate custom

# Delete profile
gopnik profile delete old-profile --force
```

### How do I use JSON output for automation?

```bash
# Process with JSON output
result=$(gopnik process document.pdf --format json)

# Extract information with jq
detections=$(echo "$result" | jq -r '.detections_found')
echo "Found $detections PII detections"

# Batch processing with JSON
gopnik batch /documents --format json > batch_results.json
```

### How do I validate processed documents?

```bash
# Basic validation
gopnik validate document_redacted.pdf

# With signature verification
gopnik validate document_redacted.pdf --verify-signatures --verbose

# Auto-find audit log
gopnik validate document_redacted.pdf --audit-dir /audit/logs

# JSON output for automation
gopnik validate document_redacted.pdf --format json
```

### Can I preview what will be processed without actually processing?

Yes! Use the `--dry-run` option:

```bash
# Preview single document processing
gopnik process document.pdf --profile healthcare --dry-run

# Preview batch processing
gopnik batch /documents --recursive --dry-run

# See what files would be processed
gopnik batch /documents --pattern "*.pdf" --dry-run
```

## 🔧 Usage Questions

### How accurate is Gopnik's PII detection?

Gopnik achieves high accuracy through:
- **Multi-model approach**: Combines multiple AI models
- **Confidence scoring**: Adjustable confidence thresholds
- **Human review**: Optional manual review workflow
- **Continuous improvement**: Models updated regularly

Typical accuracy rates:
- **Visual PII**: 95%+ for faces, 90%+ for signatures
- **Text PII**: 92%+ for emails, 88%+ for names
- **Overall**: 90%+ precision with proper configuration

### Can I customize what gets redacted?

Yes! Gopnik offers extensive customization:
- **Redaction profiles**: Pre-configured for different use cases
- **Custom rules**: Create your own detection rules
- **Confidence thresholds**: Adjust sensitivity
- **PII type selection**: Enable/disable specific PII types

### How do I create custom redaction profiles?

```yaml
# Example custom profile
name: healthcare_hipaa
description: HIPAA-compliant healthcare redaction

visual_rules:
  face: true
  signature: true

text_rules:
  name: true
  ssn: true
  medical_record_number: true

confidence_threshold: 0.8
```

See [Redaction Profiles](user-guide/redaction-profiles.md) for details.

### Can I process multiple documents at once?

Yes! Gopnik supports batch processing:

```bash
# Process entire directory
gopnik batch /documents --profile healthcare --recursive --progress

# Process with filtering
gopnik batch /documents --pattern "*.pdf" --max-files 100

# Dry run to preview
gopnik batch /documents --dry-run --recursive
```

## 🛡️ Security and Privacy

### Is my data secure when using Gopnik?

**CLI and Desktop modes:**
- All processing happens locally
- No data sent to external servers
- Secure temporary file handling
- Cryptographic audit trails

**Web demo:**
- Files processed in browser when possible
- Temporary files automatically deleted
- No permanent storage of user data
- Optional Cloudflare protection

### Does Gopnik comply with regulations like HIPAA?

Gopnik is designed with compliance in mind:
- **HIPAA**: Healthcare-specific redaction profiles
- **GDPR**: EU privacy regulation support
- **PCI DSS**: Financial data protection
- **SOX**: Corporate compliance features

However, compliance also depends on proper configuration and usage.

### What audit information does Gopnik provide?

Gopnik generates comprehensive audit trails:
- **Processing metadata**: Timestamps, versions, settings
- **Detection details**: What was found and redacted
- **Integrity hashes**: Document verification
- **Digital signatures**: Tamper-proof audit logs
- **Chain of custody**: Complete processing history

## 🔧 Technical Questions

### What AI models does Gopnik use?

**Computer Vision:**
- YOLOv8 for object detection
- Face detection models
- Custom signature detection

**Natural Language Processing:**
- LayoutLMv3 for document understanding
- Named Entity Recognition (NER) models
- Custom PII detection models

### Can I use my own AI models?

Yes! Gopnik supports custom models:
- **Plugin system**: Integrate custom detection engines
- **Model APIs**: Use external model services
- **Training data**: Fine-tune on your specific data
- **Hybrid approaches**: Combine multiple models

### Does Gopnik support GPU acceleration?

Yes, GPU acceleration is supported:
- **CUDA**: NVIDIA GPU support
- **Metal**: Apple Silicon support (planned)
- **OpenCL**: Cross-platform GPU support (planned)

Enable GPU support:
```bash
# Install with GPU support
pip install gopnik[ai,gpu]

# Enable in configuration
export GOPNIK_USE_GPU=true
```

### How can I improve processing speed?

**Hardware optimizations:**
- Use SSD storage
- Enable GPU acceleration
- Increase RAM allocation

**Configuration optimizations:**
- Adjust batch sizes
- Lower confidence thresholds
- Disable unnecessary PII types
- Use faster AI models

**Workflow optimizations:**
- Batch process multiple documents
- Use appropriate image resolutions
- Pre-filter document types

## 🌍 Deployment Questions

### Can I deploy Gopnik in the cloud?

Yes! Gopnik supports various deployment options:
- **Docker containers**: Easy containerized deployment
- **Kubernetes**: Scalable orchestration
- **Cloud platforms**: AWS, Azure, GCP support
- **Serverless**: Lambda/Functions deployment

### How do I integrate Gopnik with my existing system?

**REST API:**
```python
import requests

response = requests.post('http://localhost:8080/api/v1/process', 
                        files={'document': open('doc.pdf', 'rb')})
```

**Python SDK:**
```python
from gopnik import DocumentProcessor

processor = DocumentProcessor()
result = processor.process_document('document.pdf', profile='healthcare')
```

**CLI integration:**
```bash
# Process documents
gopnik process document.pdf --profile healthcare --output redacted.pdf

# Batch processing
gopnik batch /documents --recursive --progress --format json

# Validate results
gopnik validate redacted.pdf --verify-signatures --verbose

# Profile management
gopnik profile create --name custom --pii-types name email phone
```

### Can I run Gopnik as a service?

Yes! Multiple service options:
- **Web service**: FastAPI-based REST API
- **Background service**: Queue-based processing
- **Microservice**: Docker container deployment
- **Desktop service**: System tray application

## 🐛 Troubleshooting

### Gopnik is running slowly. How can I speed it up?

1. **Enable GPU acceleration** if available
2. **Increase batch size** in configuration
3. **Use faster AI models** (trade accuracy for speed)
4. **Process smaller image resolutions**
5. **Disable unnecessary PII detection types**

### I'm getting memory errors during processing

1. **Reduce batch size** in configuration
2. **Process documents individually** instead of batch
3. **Increase system RAM** or use swap
4. **Use CPU-only mode** to reduce memory usage
5. **Process smaller document sections**

### The detection accuracy is too low

1. **Adjust confidence thresholds** in profiles
2. **Enable more PII detection types**
3. **Use higher resolution images**
4. **Try different AI models**
5. **Provide training data** for custom models

### I can't install Gopnik

1. **Check Python version** (3.8+ required)
2. **Update pip**: `pip install --upgrade pip`
3. **Use virtual environment**: `python -m venv venv`
4. **Install system dependencies** for your platform
5. **Try user installation**: `pip install --user gopnik`

## 📞 Getting More Help

### Where can I get support?

- **Documentation**: [happy2234.github.io/gopnik](https://happy2234.github.io/gopnik/)
- **Community**: [GitHub Discussions](https://github.com/happy2234/gopnik/discussions)
- **Issues**: [GitHub Issues](https://github.com/happy2234/gopnik/issues)
- **Wiki**: [GitHub Wiki](https://github.com/happy2234/gopnik/wiki)

### How can I contribute to Gopnik?

- **Report bugs**: Create GitHub issues
- **Suggest features**: Use GitHub discussions
- **Contribute code**: Submit pull requests
- **Improve documentation**: Edit wiki pages
- **Share examples**: Add to community wiki

### Is commercial support available?

Community support is available through GitHub. For enterprise support, training, and custom development, contact: support@gopnik.ai

---

**Still have questions? Ask in our [GitHub Discussions](https://github.com/happy2234/gopnik/discussions)!**