# CLI Quick Start Guide

Get up and running with the Gopnik CLI in just a few minutes. This guide will walk you through the essential commands to start processing documents.

## Installation

First, install Gopnik with CLI support:

```bash
pip install gopnik
```

Verify the installation:

```bash
gopnik --version
```

## Your First Document

Let's process a simple document with the default profile:

```bash
# Process a single document
gopnik process document.pdf

# This creates document_redacted.pdf with PII redacted
```

## Basic Commands

### 1. Process a Single Document

```bash
# Basic processing
gopnik process document.pdf

# Specify output location
gopnik process document.pdf --output /secure/redacted.pdf

# Use a specific profile
gopnik process document.pdf --profile healthcare
```

### 2. Preview Before Processing (Dry Run)

```bash
# See what would be processed without actually processing
gopnik process document.pdf --dry-run --profile healthcare
```

Output:
```
=== DRY RUN MODE ===
Input: document.pdf
Output: document_redacted.pdf
Profile: healthcare

Profile Details:
  Name: healthcare
  Description: HIPAA-compliant healthcare profile
  PII Types: name, email, phone, ssn, medical_record_number
  Redaction Style: solid_black

Dry run completed. Use without --dry-run to execute.
```

### 3. Batch Process Multiple Documents

```bash
# Process all documents in a directory
gopnik batch /path/to/documents

# With progress tracking
gopnik batch /path/to/documents --progress

# Recursive processing
gopnik batch /path/to/documents --recursive --progress
```

### 4. Validate Processed Documents

```bash
# Validate a processed document
gopnik validate document_redacted.pdf

# With detailed information
gopnik validate document_redacted.pdf --verbose
```

## Working with Profiles

### List Available Profiles

```bash
# List all profiles
gopnik profile list

# With detailed information
gopnik profile list --verbose
```

### View Profile Details

```bash
# Show profile configuration
gopnik profile show healthcare
```

### Create a Custom Profile

```bash
# Create a new profile
gopnik profile create \
  --name "my-custom" \
  --description "My custom redaction profile" \
  --pii-types name email phone \
  --redaction-style solid
```

## Common Workflows

### Workflow 1: Single Document Processing

```bash
# 1. Preview what will be processed
gopnik process sensitive-doc.pdf --profile healthcare --dry-run

# 2. Process the document
gopnik process sensitive-doc.pdf --profile healthcare --output redacted-doc.pdf

# 3. Validate the result
gopnik validate redacted-doc.pdf --verbose
```

### Workflow 2: Batch Processing with Validation

```bash
# 1. See what files would be processed
gopnik batch /documents --dry-run --recursive

# 2. Process all documents
gopnik batch /documents --profile healthcare --recursive --progress

# 3. Validate all processed documents
for file in /documents_redacted/*.pdf; do
    gopnik validate "$file" --format json
done
```

### Workflow 3: Custom Profile Creation and Use

```bash
# 1. Create a custom profile based on existing one
gopnik profile create \
  --name "strict-legal" \
  --based-on default \
  --description "Strict legal document redaction"

# 2. Customize the profile
gopnik profile edit strict-legal \
  --add-pii-types ssn passport_number driver_license \
  --redaction-style blur

# 3. Validate the profile
gopnik profile validate strict-legal

# 4. Use the profile
gopnik process legal-document.pdf --profile strict-legal
```

## Output Formats

### Human-Readable Output (Default)

```bash
gopnik process document.pdf
```

Output:
```
Success: Document processed successfully (output=document_redacted.pdf, detections=3, time=1.45s)
```

### JSON Output for Automation

```bash
gopnik process document.pdf --format json
```

Output:
```json
{
  "status": "success",
  "input": "document.pdf",
  "output": "document_redacted.pdf",
  "detections_found": 3,
  "processing_time": 1.45
}
```

## Error Handling

### Common Errors and Solutions

#### File Not Found
```bash
$ gopnik process nonexistent.pdf
Error: Document not found: nonexistent.pdf
```

**Solution**: Check the file path and ensure the file exists.

#### Permission Denied
```bash
$ gopnik process document.pdf --output /root/redacted.pdf
Error: Permission denied: /root/redacted.pdf
```

**Solution**: Use a writable output directory or run with appropriate permissions.

#### Profile Not Found
```bash
$ gopnik process document.pdf --profile nonexistent
Error: Profile 'nonexistent' not found
```

**Solution**: List available profiles with `gopnik profile list` or create the profile.

### Getting Help

```bash
# General help
gopnik --help

# Command-specific help
gopnik process --help
gopnik batch --help
gopnik profile --help

# Verbose output for debugging
gopnik process document.pdf --verbose
```

## Tips for Success

### 1. Start with Dry Runs
Always use `--dry-run` first to preview what will be processed:

```bash
gopnik process document.pdf --profile healthcare --dry-run
```

### 2. Use Progress Tracking for Large Batches
Enable progress bars for batch operations:

```bash
gopnik batch /large-directory --progress --recursive
```

### 3. Validate Your Results
Always validate processed documents:

```bash
gopnik validate processed-document.pdf --verbose
```

### 4. Create Custom Profiles
Create profiles tailored to your specific needs:

```bash
gopnik profile create --name "my-org" --based-on default --pii-types name email phone
```

### 5. Use JSON Output for Automation
Use JSON output when integrating with scripts:

```bash
result=$(gopnik process document.pdf --format json)
echo "$result" | jq '.detections_found'
```

## Next Steps

Now that you're familiar with the basics, explore these advanced features:

- **[Full CLI Reference](cli-reference.md)**: Complete documentation of all commands and options
- **[CLI Examples](cli-examples.md)**: Real-world usage examples and scripts
- **[Profile Configuration](profiles.md)**: Advanced profile customization
- **[Batch Processing](batch-processing.md)**: Large-scale document processing
- **[Audit Trails](audit-trails.md)**: Forensic-grade audit logging

## Need Help?

- **[CLI Reference](cli-reference.md)**: Complete command documentation
- **[FAQ](../faq.md)**: Frequently asked questions
- **[GitHub Discussions](https://github.com/happy2234/gopnik/discussions)**: Community support
- **[Issues](https://github.com/happy2234/gopnik/issues)**: Bug reports and feature requests