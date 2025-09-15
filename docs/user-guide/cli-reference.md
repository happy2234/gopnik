# CLI Reference Guide

The Gopnik CLI provides a comprehensive command-line interface for document deidentification, validation, and profile management. This guide covers all available commands and their options.

## Installation

```bash
# Install Gopnik with CLI support
pip install gopnik

# Verify installation
gopnik --version
```

## Global Options

All commands support these global options:

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version information | - |
| `--config PATH` | Path to configuration file | `config/default.yaml` |
| `--log-level LEVEL` | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `--log-file PATH` | Path to log file | stderr |
| `--quiet` | Suppress all output except errors | False |
| `--verbose` | Enable verbose output | False |

## Commands Overview

| Command | Description |
|---------|-------------|
| [`process`](#process-command) | Process a single document for PII redaction |
| [`batch`](#batch-command) | Process multiple documents in a directory |
| [`validate`](#validate-command) | Validate document integrity using audit trails |
| [`profile`](#profile-command) | Manage redaction profiles |

## Process Command

Process a single document to detect and redact PII according to a specified profile.

### Syntax

```bash
gopnik process INPUT [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `INPUT` | Input document path | Yes |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o PATH` | Output document path | `<input>_redacted.<ext>` |
| `--profile`, `-p NAME` | Redaction profile name | `default` |
| `--profile-file PATH` | Path to custom profile file | - |
| `--dry-run` | Show what would be processed without processing | False |
| `--force` | Overwrite output file if it exists | False |
| `--no-audit` | Skip audit log creation | False |
| `--format FORMAT` | Output format (text, json) | `text` |

### Examples

```bash
# Basic processing
gopnik process document.pdf

# Use specific profile and output location
gopnik process document.pdf --profile healthcare --output /secure/redacted.pdf

# Use custom profile file
gopnik process document.pdf --profile-file /profiles/custom.yaml

# Dry run to preview processing
gopnik process document.pdf --profile healthcare --dry-run

# Force overwrite existing output
gopnik process document.pdf --output existing.pdf --force

# JSON output for automation
gopnik process document.pdf --format json
```

### Output Formats

#### Text Format
```
Success: Document processed successfully (output=redacted.pdf, detections=5, time=2.34s)
```

#### JSON Format
```json
{
  "status": "success",
  "input": "document.pdf",
  "output": "redacted.pdf",
  "detections_found": 5,
  "processing_time": 2.34
}
```

## Batch Command

Process multiple documents in a directory for PII redaction.

### Syntax

```bash
gopnik batch INPUT_DIR [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `INPUT_DIR` | Input directory containing documents | Yes |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o PATH` | Output directory | `<input_dir>_redacted` |
| `--profile`, `-p NAME` | Redaction profile name | `default` |
| `--profile-file PATH` | Path to custom profile file | - |
| `--recursive`, `-r` | Process subdirectories recursively | False |
| `--pattern PATTERN` | File pattern to match (e.g., "*.pdf") | All supported formats |
| `--dry-run` | Show what would be processed without processing | False |
| `--force` | Overwrite output files if they exist | False |
| `--continue-on-error` | Continue processing other files if one fails | False |
| `--max-files N` | Maximum number of files to process | Unlimited |
| `--format FORMAT` | Output format (text, json) | `text` |
| `--progress` | Show progress bar during processing | False |

### Examples

```bash
# Process all documents in a directory
gopnik batch /path/to/documents --profile default

# Recursive processing with progress bar
gopnik batch /path/to/documents --recursive --progress --profile healthcare

# Process only PDF files
gopnik batch /documents --pattern "*.pdf" --profile default

# Limit number of files and continue on errors
gopnik batch /documents --max-files 100 --continue-on-error

# Dry run to see what would be processed
gopnik batch /documents --dry-run --recursive

# Custom output directory
gopnik batch /input --output /output --profile healthcare
```

### Progress Display

When `--progress` is enabled, you'll see a progress bar:

```
Processing documents [████████████████████████████████] 100.0% (25/25) ETA: 00:00
```

### Output Summary

```
Batch processing completed:
  Total files: 25
  Successful: 23
  Failed: 2
  Total time: 45.67s
  Output directory: /output
```

## Validate Command

Validate document integrity and audit trail authenticity.

### Syntax

```bash
gopnik validate DOCUMENT [AUDIT_LOG] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `DOCUMENT` | Document path to validate | Yes |
| `AUDIT_LOG` | Audit log file path (optional, will search if not provided) | No |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--audit-dir PATH` | Directory to search for audit logs | - |
| `--strict` | Enable strict validation mode | False |
| `--verify-signatures` | Verify cryptographic signatures in audit logs | False |
| `--format FORMAT` | Output format (text, json) | `text` |
| `--verbose`, `-v` | Show detailed validation information | False |

### Examples

```bash
# Validate with explicit audit log
gopnik validate document.pdf audit.json

# Auto-find audit log in same directory
gopnik validate document.pdf

# Search for audit log in specific directory
gopnik validate document.pdf --audit-dir /audit/logs

# Strict validation with signature verification
gopnik validate document.pdf --strict --verify-signatures

# Verbose output with detailed information
gopnik validate document.pdf --verbose

# JSON output for automation
gopnik validate document.pdf --format json
```

### Validation Results

#### Valid Document (Text)
```
Validation Result: ✓ VALID
Document: document.pdf
Audit Log: document_audit.json
Document Hash: ✓ Match
Signatures: 1/1 valid
```

#### Invalid Document (Text)
```
Validation Result: ✗ INVALID
Document: document.pdf
Audit Log: document_audit.json
Document Hash: ✗ Mismatch
  Current:  abc123def456
  Expected: def456abc123

Recommendations:
  • Document has been modified since processing
  • Verify document source and integrity
```

#### JSON Output
```json
{
  "document": "document.pdf",
  "audit_log": "document_audit.json",
  "valid": true,
  "details": {
    "hash_match": true,
    "current_document_hash": "abc123def456",
    "expected_document_hash": "abc123def456",
    "signature_verification": {
      "signatures_found": 1,
      "signatures_valid": 1,
      "signatures_invalid": 0
    }
  }
}
```

## Profile Command

Manage redaction profiles for different use cases and compliance requirements.

### Syntax

```bash
gopnik profile ACTION [OPTIONS]
```

### Actions

| Action | Description |
|--------|-------------|
| `list` | List available profiles |
| `show NAME` | Show profile details |
| `create` | Create a new profile |
| `edit NAME` | Edit an existing profile |
| `validate PROFILE` | Validate a profile |
| `delete NAME` | Delete a profile |

### List Profiles

```bash
gopnik profile list [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format FORMAT` | Output format (text, json) | `text` |
| `--verbose`, `-v` | Show detailed profile information | False |

#### Examples

```bash
# List all profiles
gopnik profile list

# List with detailed information
gopnik profile list --verbose

# JSON output
gopnik profile list --format json
```

### Show Profile

```bash
gopnik profile show NAME [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format FORMAT` | Output format (text, json) | `text` |

#### Examples

```bash
# Show profile details
gopnik profile show healthcare

# JSON output
gopnik profile show healthcare --format json
```

### Create Profile

```bash
gopnik profile create [OPTIONS]
```

#### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name NAME` | Profile name | Yes |
| `--description DESC` | Profile description | No |
| `--based-on PROFILE` | Base profile to copy from | No |
| `--pii-types TYPES` | PII types to detect (space-separated) | No |
| `--redaction-style STYLE` | Redaction style (solid, pattern, blur) | No |
| `--output PATH` | Output file path | No |

#### Available PII Types

- **Visual**: `face`, `signature`, `barcode`, `qr_code`
- **Text**: `name`, `email`, `phone`, `address`, `ssn`, `id_number`, `credit_card`, `date_of_birth`, `passport_number`, `driver_license`, `medical_record_number`, `insurance_id`, `bank_account`, `ip_address`

#### Examples

```bash
# Create new profile from scratch
gopnik profile create --name custom --description "Custom profile" \
  --pii-types name email phone --redaction-style solid

# Create profile based on existing one
gopnik profile create --name strict-healthcare --based-on healthcare \
  --description "Strict healthcare profile"

# Create with custom output location
gopnik profile create --name test --output /profiles/test.yaml
```

### Edit Profile

```bash
gopnik profile edit NAME [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--description DESC` | New profile description |
| `--add-pii-types TYPES` | PII types to add (space-separated) |
| `--remove-pii-types TYPES` | PII types to remove (space-separated) |
| `--redaction-style STYLE` | New redaction style |

#### Examples

```bash
# Add PII types
gopnik profile edit healthcare --add-pii-types ssn id_number

# Remove PII types
gopnik profile edit healthcare --remove-pii-types phone

# Change redaction style
gopnik profile edit healthcare --redaction-style blur

# Update description
gopnik profile edit healthcare --description "Updated healthcare profile"
```

### Validate Profile

```bash
gopnik profile validate PROFILE [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format FORMAT` | Output format (text, json) | `text` |

#### Examples

```bash
# Validate profile by name
gopnik profile validate healthcare

# Validate profile file
gopnik profile validate /path/to/profile.yaml

# JSON output
gopnik profile validate healthcare --format json
```

### Delete Profile

```bash
gopnik profile delete NAME [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--force` | Delete without confirmation | False |

#### Examples

```bash
# Delete with confirmation
gopnik profile delete old-profile

# Force delete without confirmation
gopnik profile delete old-profile --force
```

## Error Handling

The CLI provides comprehensive error handling with appropriate exit codes:

| Exit Code | Description |
|-----------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments or file not found |
| 3 | Processing error |
| 4 | Profile error |
| 5 | Validation error |
| 13 | Permission denied |
| 130 | Interrupted by user (Ctrl+C) |

### Error Output

#### Text Format
```
Error: Document not found: nonexistent.pdf
```

#### JSON Format
```json
{
  "error": true,
  "type": "FileNotFoundError",
  "message": "Document not found: nonexistent.pdf",
  "exit_code": 2
}
```

## Configuration

### Configuration File

Create a configuration file to set default options:

```yaml
# config/custom.yaml
logging:
  level: INFO
  format: detailed

processing:
  default_profile: healthcare
  enable_audit: true
  
profiles:
  directories:
    - ./profiles
    - /etc/gopnik/profiles
```

Use with:
```bash
gopnik --config config/custom.yaml process document.pdf
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOPNIK_CONFIG` | Default configuration file | `config/default.yaml` |
| `GOPNIK_LOG_LEVEL` | Default log level | `INFO` |
| `GOPNIK_PROFILES_DIR` | Default profiles directory | `./profiles` |

## Tips and Best Practices

### Performance Optimization

1. **Use batch processing** for multiple documents
2. **Enable progress bars** for long operations: `--progress`
3. **Use appropriate profiles** to avoid unnecessary processing
4. **Limit file counts** for testing: `--max-files 10`

### Automation

1. **Use JSON output** for scripting: `--format json`
2. **Use dry-run mode** to test configurations: `--dry-run`
3. **Enable continue-on-error** for batch processing: `--continue-on-error`
4. **Use force flag** to avoid prompts: `--force`

### Security

1. **Always validate** processed documents: `gopnik validate`
2. **Enable signature verification**: `--verify-signatures`
3. **Use audit trails** for compliance
4. **Store profiles securely** and validate them regularly

### Troubleshooting

1. **Use verbose mode** for debugging: `--verbose`
2. **Check log files** for detailed error information
3. **Validate profiles** before using them
4. **Test with dry-run** before actual processing

## Integration Examples

### Shell Scripts

```bash
#!/bin/bash
# Process all PDFs in a directory with error handling

INPUT_DIR="$1"
OUTPUT_DIR="$2"
PROFILE="${3:-default}"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory does not exist"
    exit 1
fi

echo "Processing documents in $INPUT_DIR with profile $PROFILE"

gopnik batch "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --profile "$PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > processing_results.json

if [ $? -eq 0 ]; then
    echo "Processing completed successfully"
    gopnik validate "$OUTPUT_DIR"/*.pdf --format json > validation_results.json
else
    echo "Processing failed"
    exit 1
fi
```

### Python Integration

```python
import subprocess
import json
from pathlib import Path

def process_document(input_path, profile="default", output_path=None):
    """Process a document using Gopnik CLI."""
    
    cmd = ["gopnik", "process", str(input_path), "--format", "json"]
    
    if profile:
        cmd.extend(["--profile", profile])
    
    if output_path:
        cmd.extend(["--output", str(output_path)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        error_data = json.loads(result.stdout) if result.stdout else {"error": result.stderr}
        raise Exception(f"Processing failed: {error_data}")

# Usage
try:
    result = process_document("document.pdf", "healthcare")
    print(f"Processing successful: {result['output']}")
except Exception as e:
    print(f"Processing failed: {e}")
```

## See Also

- [User Guide](index.md) - Complete user documentation
- [Developer Guide](../developer-guide/index.md) - API reference and development docs
- [FAQ](../faq.md) - Frequently asked questions
- [Profile Configuration](profiles.md) - Detailed profile configuration guide