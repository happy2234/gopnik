# Gopnik CLI Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Command Reference](#command-reference)
5. [Configuration](#configuration)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)

## Overview

The Gopnik CLI provides a powerful command-line interface for AI-powered document deidentification. It offers comprehensive PII detection and redaction capabilities with forensic-grade audit trails.

### Key Features
- Multi-format document processing (PDF, PNG, JPEG, TIFF, BMP)
- Advanced AI-powered PII detection (faces, text, signatures, barcodes)
- Customizable redaction profiles
- Batch processing with progress tracking
- Cryptographic audit trails and integrity validation
- Memory-efficient processing for large documents

## Installation

### Basic Installation
```bash
pip install gopnik
```

### Full Installation with AI Engines
```bash
pip install gopnik[all]
```

### Development Installation
```bash
git clone https://github.com/happy2234/gopnik.git
cd gopnik
pip install -e .[all,dev]
```

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for large documents)
- 2GB free disk space for AI models

## Quick Start

### Process a Single Document
```bash
# Basic processing with default profile
gopnik process document.pdf --output redacted.pdf

# Process with specific profile
gopnik process document.pdf --profile healthcare --output redacted.pdf

# Dry run to preview detections
gopnik process document.pdf --profile default --dry-run
```

### Batch Processing
```bash
# Process all PDFs in a directory
gopnik batch /path/to/documents --pattern "*.pdf" --profile default

# Recursive processing with progress tracking
gopnik batch /docs --recursive --progress --max-files 100
```

### Validate Document Integrity
```bash
# Validate with audit log
gopnik validate document.pdf audit.json --verify-signatures

# Auto-find audit logs
gopnik validate document.pdf --audit-dir /audit/logs
```

## Command Reference

### Main Commands

#### `gopnik process`
Process a single document for PII detection and redaction.

**Syntax:**
```bash
gopnik process INPUT_FILE [OPTIONS]
```

**Options:**
- `--output, -o PATH`: Output file path (default: adds '_redacted' suffix)
- `--profile, -p NAME`: Redaction profile name (default: 'default')
- `--profile-file PATH`: Custom profile file path
- `--dry-run`: Preview detections without creating output
- `--confidence FLOAT`: Minimum confidence threshold (0.0-1.0)
- `--audit-dir PATH`: Directory for audit logs
- `--no-audit`: Disable audit logging
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Basic processing
gopnik process document.pdf

# Custom output location
gopnik process document.pdf --output /secure/redacted.pdf

# Use healthcare profile with high confidence
gopnik process medical_record.pdf --profile healthcare --confidence 0.9

# Dry run to preview detections
gopnik process document.pdf --dry-run --verbose
```

#### `gopnik batch`
Process multiple documents in batch mode.

**Syntax:**
```bash
gopnik batch INPUT_DIR [OPTIONS]
```

**Options:**
- `--output-dir, -o PATH`: Output directory (default: INPUT_DIR/redacted)
- `--profile, -p NAME`: Redaction profile name
- `--pattern GLOB`: File pattern to match (e.g., "*.pdf")
- `--recursive, -r`: Process subdirectories recursively
- `--max-files INT`: Maximum number of files to process
- `--progress`: Show progress bar
- `--continue-on-error`: Continue processing if individual files fail
- `--parallel INT`: Number of parallel workers (default: CPU count)

**Examples:**
```bash
# Process all PDFs in directory
gopnik batch /documents --pattern "*.pdf" --progress

# Recursive processing with limits
gopnik batch /docs --recursive --max-files 50 --parallel 4

# Continue on errors with custom output
gopnik batch /input --output-dir /output --continue-on-error
```

#### `gopnik validate`
Validate document integrity and audit trails.

**Syntax:**
```bash
gopnik validate DOCUMENT_FILE [AUDIT_FILE] [OPTIONS]
```

**Options:**
- `--audit-dir PATH`: Directory containing audit logs
- `--verify-signatures`: Verify cryptographic signatures
- `--verbose, -v`: Detailed validation output
- `--format FORMAT`: Output format (text, json, yaml)

**Examples:**
```bash
# Validate with specific audit file
gopnik validate document.pdf audit.json --verify-signatures

# Auto-find audit logs
gopnik validate document.pdf --audit-dir /audit/logs --verbose

# JSON output for automation
gopnik validate document.pdf --format json
```

#### `gopnik profile`
Manage redaction profiles.

**Subcommands:**
- `list`: List available profiles
- `show PROFILE`: Display profile details
- `create`: Create new profile
- `edit PROFILE`: Edit existing profile
- `validate PROFILE`: Validate profile syntax
- `delete PROFILE`: Delete profile

**Examples:**
```bash
# List all profiles
gopnik profile list --verbose

# Show profile details
gopnik profile show healthcare

# Create custom profile
gopnik profile create --name custom --based-on default --pii-types name email phone

# Edit profile
gopnik profile edit healthcare --add-pii-types ssn --redaction-style blur

# Validate profile
gopnik profile validate custom
```

#### `gopnik api`
Start REST API server.

**Syntax:**
```bash
gopnik api [OPTIONS]
```

**Options:**
- `--host HOST`: Host address (default: localhost)
- `--port PORT`: Port number (default: 8000)
- `--reload`: Enable auto-reload for development
- `--log-level LEVEL`: Logging level (debug, info, warning, error)
- `--workers INT`: Number of worker processes

**Examples:**
```bash
# Start API server
gopnik api --host 0.0.0.0 --port 8080

# Development mode
gopnik api --reload --log-level debug
```

### Global Options

Available for all commands:
- `--config PATH`: Configuration file path
- `--log-level LEVEL`: Set logging level
- `--help, -h`: Show help message
- `--version`: Show version information

## Configuration

### Configuration File

Gopnik uses YAML configuration files. Default location: `~/.gopnik/config.yaml`

```yaml
# Default configuration
processing:
  confidence_threshold: 0.7
  max_file_size: "100MB"
  temp_dir: "/tmp/gopnik"
  
ai_engines:
  cv_engine:
    model_path: "models/cv_model.pt"
    device: "auto"  # auto, cpu, cuda
  nlp_engine:
    model_path: "models/nlp_model.pt"
    batch_size: 32

audit:
  enabled: true
  audit_dir: "~/.gopnik/audit"
  sign_logs: true
  key_path: "~/.gopnik/keys"

security:
  secure_temp_files: true
  memory_protection: true
  auto_cleanup: true
```

### Environment Variables

- `GOPNIK_CONFIG`: Configuration file path
- `GOPNIK_AUDIT_DIR`: Audit log directory
- `GOPNIK_TEMP_DIR`: Temporary files directory
- `GOPNIK_LOG_LEVEL`: Logging level
- `GOPNIK_AI_DEVICE`: AI processing device (cpu, cuda)

### Redaction Profiles

Profiles define PII types to detect and redaction styles to apply.

**Built-in Profiles:**
- `default`: General-purpose PII detection
- `healthcare`: HIPAA-compliant medical document redaction
- `financial`: PCI DSS-compliant financial document redaction
- `legal`: Legal document redaction with attorney-client privilege

**Custom Profile Example:**
```yaml
name: "custom_profile"
description: "Custom redaction profile"
version: "1.0"

pii_types:
  - name: "person_name"
    enabled: true
    confidence_threshold: 0.8
    redaction_style: "solid"
  - name: "email_address"
    enabled: true
    confidence_threshold: 0.9
    redaction_style: "blur"

redaction_styles:
  solid:
    color: "black"
    opacity: 1.0
  blur:
    radius: 5
    iterations: 3
```

## Advanced Usage

### Batch Processing with Filtering

```bash
# Process only recent files
find /documents -name "*.pdf" -mtime -7 | xargs -I {} gopnik process {}

# Process with size limits
gopnik batch /docs --pattern "*.pdf" --max-size 50MB --progress

# Custom filtering with shell scripting
for file in /docs/*.pdf; do
    if [ $(stat -f%z "$file") -lt 10485760 ]; then  # < 10MB
        gopnik process "$file" --profile healthcare
    fi
done
```

### Integration with Other Tools

```bash
# Process and immediately validate
gopnik process document.pdf && gopnik validate document_redacted.pdf

# Batch processing with notification
gopnik batch /docs --progress && echo "Processing complete" | mail -s "Gopnik Job Done" user@example.com

# Integration with file monitoring
inotifywait -m /watch/dir -e create --format '%w%f' | while read file; do
    gopnik process "$file" --profile default
done
```

### Performance Optimization

```bash
# Use multiple workers for batch processing
gopnik batch /docs --parallel 8 --pattern "*.pdf"

# Process with memory limits
ulimit -v 4194304  # 4GB virtual memory limit
gopnik process large_document.pdf

# Use specific AI device
GOPNIK_AI_DEVICE=cuda gopnik process document.pdf
```

### Audit Trail Management

```bash
# Generate audit report
gopnik validate /processed/docs --audit-dir /audit --format json > audit_report.json

# Verify all documents in directory
find /processed -name "*.pdf" -exec gopnik validate {} --verify-signatures \;

# Archive old audit logs
find ~/.gopnik/audit -name "*.json" -mtime +30 -exec gzip {} \;
```

## Troubleshooting

### Common Issues

#### Installation Problems

**Issue:** `pip install gopnik` fails with dependency errors
**Solution:**
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools

# Install with specific Python version
python3.8 -m pip install gopnik

# Use conda for complex dependencies
conda install -c conda-forge gopnik
```

#### Memory Issues

**Issue:** Out of memory errors with large documents
**Solution:**
```bash
# Increase virtual memory limit
ulimit -v 8388608  # 8GB

# Use CPU instead of GPU
GOPNIK_AI_DEVICE=cpu gopnik process large_document.pdf

# Process in smaller batches
gopnik batch /docs --max-files 10 --parallel 2
```

#### Performance Issues

**Issue:** Slow processing speed
**Solution:**
```bash
# Use GPU acceleration
GOPNIK_AI_DEVICE=cuda gopnik process document.pdf

# Increase parallel workers
gopnik batch /docs --parallel 8

# Lower confidence threshold for faster processing
gopnik process document.pdf --confidence 0.6
```

#### Permission Issues

**Issue:** Cannot write to output directory
**Solution:**
```bash
# Check permissions
ls -la /output/directory

# Create directory with proper permissions
mkdir -p /output/directory
chmod 755 /output/directory

# Use different output location
gopnik process document.pdf --output ~/redacted.pdf
```

### Error Messages

#### `FileNotFoundError: AI model not found`
**Cause:** AI models not downloaded or incorrect path
**Solution:**
```bash
# Download models
gopnik download-models

# Check model path in config
gopnik config show ai_engines.cv_engine.model_path
```

#### `ValidationError: Invalid profile format`
**Cause:** Malformed profile YAML
**Solution:**
```bash
# Validate profile syntax
gopnik profile validate custom_profile

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('profile.yaml'))"
```

#### `CryptographicError: Signature verification failed`
**Cause:** Corrupted audit log or wrong key
**Solution:**
```bash
# Check key permissions
ls -la ~/.gopnik/keys/

# Regenerate keys if necessary
gopnik generate-keys --force

# Skip signature verification for testing
gopnik validate document.pdf --no-verify-signatures
```

### Getting Help

- **Documentation:** https://happy2234.github.io/gopnik/
- **GitHub Issues:** https://github.com/happy2234/gopnik/issues
- **Discussions:** https://github.com/happy2234/gopnik/discussions
- **Email Support:** support@gopnik.ai

### Debug Mode

Enable debug logging for troubleshooting:
```bash
# Enable debug logging
gopnik --log-level debug process document.pdf

# Save debug output to file
gopnik --log-level debug process document.pdf 2> debug.log

# Environment variable
export GOPNIK_LOG_LEVEL=debug
gopnik process document.pdf
```

---

**Version:** 1.0.0  
**Last Updated:** September 2025  
**License:** MIT