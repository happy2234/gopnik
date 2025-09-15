# CLI Quick Examples

Quick reference for common Gopnik CLI operations. Copy and paste these examples to get started quickly.

## Basic Operations

### Process Single Document
```bash
# Basic processing
gopnik process document.pdf

# With specific profile
gopnik process document.pdf --profile healthcare

# Custom output location
gopnik process document.pdf --output /secure/redacted.pdf

# Preview before processing
gopnik process document.pdf --dry-run --profile healthcare
```

### Batch Processing
```bash
# Process directory
gopnik batch /documents --profile default

# Recursive with progress
gopnik batch /documents --recursive --progress

# Filter by file type
gopnik batch /documents --pattern "*.pdf" --recursive

# Limit files and continue on errors
gopnik batch /documents --max-files 50 --continue-on-error
```

### Document Validation
```bash
# Basic validation
gopnik validate document.pdf

# With signature verification
gopnik validate document.pdf --verify-signatures --verbose

# Search for audit log
gopnik validate document.pdf --audit-dir /audit/logs
```

## Profile Management

### List and View Profiles
```bash
# List all profiles
gopnik profile list

# Detailed list
gopnik profile list --verbose

# Show specific profile
gopnik profile show healthcare

# JSON output
gopnik profile list --format json
```

### Create Profiles
```bash
# Create basic profile
gopnik profile create --name "custom" --pii-types name email phone

# Create from existing profile
gopnik profile create --name "strict" --based-on healthcare --redaction-style blur

# Create with description
gopnik profile create --name "legal" --description "Legal document redaction" --pii-types name email ssn
```

### Edit Profiles
```bash
# Add PII types
gopnik profile edit healthcare --add-pii-types ssn medical_record_number

# Remove PII types
gopnik profile edit healthcare --remove-pii-types phone

# Change redaction style
gopnik profile edit healthcare --redaction-style blur
```

## Output Formats

### Human-Readable Output
```bash
gopnik process document.pdf --profile healthcare
# Output: Success: Document processed successfully (output=document_redacted.pdf, detections=3, time=1.45s)
```

### JSON Output for Automation
```bash
gopnik process document.pdf --format json
# Output: {"status": "success", "input": "document.pdf", "output": "document_redacted.pdf", "detections_found": 3}
```

## Common Workflows

### Healthcare Document Processing
```bash
# 1. Validate profile
gopnik profile validate healthcare_hipaa

# 2. Process with audit trail
gopnik process medical-record.pdf --profile healthcare_hipaa --output redacted-record.pdf

# 3. Validate result
gopnik validate redacted-record.pdf --verify-signatures --verbose
```

### Legal Document Redaction
```bash
# 1. Create legal profile if needed
gopnik profile create --name "legal-strict" --based-on default --pii-types name email phone ssn case_number

# 2. Process document
gopnik process legal-doc.pdf --profile legal-strict --output redacted-legal.pdf

# 3. Validate with strict checking
gopnik validate redacted-legal.pdf --strict --verify-signatures
```

### Batch Processing with Quality Control
```bash
# 1. Dry run to check files
gopnik batch /documents --dry-run --recursive --pattern "*.pdf"

# 2. Process with progress tracking
gopnik batch /documents --profile default --recursive --progress --continue-on-error

# 3. Validate all results
for file in /documents_redacted/*.pdf; do
    gopnik validate "$file" --format json >> validation_results.json
done
```

## Automation Scripts

### Simple Processing Script
```bash
#!/bin/bash
# Process all PDFs in a directory

INPUT_DIR="$1"
PROFILE="${2:-default}"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Usage: $0 <input_directory> [profile]"
    exit 1
fi

echo "Processing documents in $INPUT_DIR with profile $PROFILE"

gopnik batch "$INPUT_DIR" \
    --profile "$PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > results.json

echo "Processing completed. Results saved to results.json"
```

### Validation Script
```bash
#!/bin/bash
# Validate all processed documents

DOCS_DIR="$1"

if [ ! -d "$DOCS_DIR" ]; then
    echo "Usage: $0 <documents_directory>"
    exit 1
fi

echo "Validating documents in $DOCS_DIR"

for doc in "$DOCS_DIR"/*.pdf; do
    if [ -f "$doc" ]; then
        echo "Validating: $(basename "$doc")"
        gopnik validate "$doc" --verify-signatures --format json
    fi
done
```

### Profile Setup Script
```bash
#!/bin/bash
# Set up organization profiles

ORG="$1"

if [ -z "$ORG" ]; then
    echo "Usage: $0 <organization_name>"
    exit 1
fi

# Create base profile
gopnik profile create --name "${ORG}_base" --based-on default --description "Base profile for $ORG"

# Create department profiles
gopnik profile create --name "${ORG}_hr" --based-on "${ORG}_base" --add-pii-types ssn employee_id
gopnik profile create --name "${ORG}_legal" --based-on "${ORG}_base" --redaction-style solid
gopnik profile create --name "${ORG}_finance" --based-on "${ORG}_base" --add-pii-types account_number credit_card

echo "Created profiles for $ORG:"
gopnik profile list | grep "$ORG"
```

## Error Handling Examples

### Check Command Success
```bash
if gopnik process document.pdf --profile healthcare; then
    echo "Processing successful"
    gopnik validate document_redacted.pdf
else
    echo "Processing failed"
    exit 1
fi
```

### Capture JSON Output
```bash
result=$(gopnik process document.pdf --format json)
if [ $? -eq 0 ]; then
    echo "Success: $result"
    detections=$(echo "$result" | jq -r '.detections_found')
    echo "Found $detections PII detections"
else
    echo "Failed: $result"
fi
```

### Batch Processing with Error Handling
```bash
#!/bin/bash
# Robust batch processing

INPUT_DIR="$1"
OUTPUT_DIR="$2"
PROFILE="${3:-default}"

# Validate inputs
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory does not exist: $INPUT_DIR"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Process with error handling
echo "Starting batch processing..."

if gopnik batch "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --profile "$PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > processing_results.json; then
    
    echo "Batch processing completed successfully"
    
    # Validate results
    echo "Validating processed documents..."
    validation_errors=0
    
    for file in "$OUTPUT_DIR"/*.pdf; do
        if [ -f "$file" ]; then
            if ! gopnik validate "$file" --format json > /dev/null; then
                echo "Validation failed for: $(basename "$file")"
                ((validation_errors++))
            fi
        fi
    done
    
    if [ $validation_errors -eq 0 ]; then
        echo "All documents validated successfully"
    else
        echo "Warning: $validation_errors documents failed validation"
    fi
    
else
    echo "Batch processing failed"
    exit 1
fi
```

## Integration with Other Tools

### Using with jq for JSON Processing
```bash
# Extract specific information from results
result=$(gopnik process document.pdf --format json)
detections=$(echo "$result" | jq -r '.detections_found')
processing_time=$(echo "$result" | jq -r '.processing_time')

echo "Found $detections detections in ${processing_time}s"
```

### Using with find for Complex File Selection
```bash
# Process files modified in last 24 hours
find /documents -name "*.pdf" -mtime -1 -exec gopnik process {} --profile healthcare \;

# Process files larger than 1MB
find /documents -name "*.pdf" -size +1M -exec gopnik process {} --profile default \;
```

### Using with parallel for Concurrent Processing
```bash
# Process multiple files in parallel (be careful with system resources)
find /documents -name "*.pdf" | parallel -j 4 gopnik process {} --profile default
```

### Integration with Monitoring Tools
```bash
# Send results to monitoring system
result=$(gopnik process document.pdf --format json)
if [ $? -eq 0 ]; then
    # Send success metric
    echo "gopnik.processing.success:1|c" | nc -u monitoring-server 8125
else
    # Send failure metric
    echo "gopnik.processing.failure:1|c" | nc -u monitoring-server 8125
fi
```

## Performance Tips

### Optimize for Large Batches
```bash
# Use appropriate batch size
gopnik batch /large-directory --max-files 100 --continue-on-error

# Process in chunks
for i in {1..10}; do
    gopnik batch /documents/chunk_$i --profile default --progress
done
```

### Monitor Resource Usage
```bash
# Monitor memory and CPU during processing
(gopnik batch /documents --profile healthcare --progress) &
PID=$!

while kill -0 $PID 2>/dev/null; do
    ps -p $PID -o pid,pcpu,pmem,time
    sleep 5
done
```

### Parallel Processing with Resource Limits
```bash
# Limit concurrent processes
sem --jobs 2 gopnik process doc1.pdf --profile healthcare
sem --jobs 2 gopnik process doc2.pdf --profile healthcare
sem --jobs 2 gopnik process doc3.pdf --profile healthcare
sem --wait  # Wait for all to complete
```

## Debugging and Troubleshooting

### Enable Verbose Logging
```bash
# Debug processing issues
gopnik --verbose --log-level DEBUG process document.pdf

# Save debug logs
gopnik --log-file debug.log --log-level DEBUG process document.pdf
```

### Test Profile Configuration
```bash
# Validate profile before use
gopnik profile validate healthcare

# Test with dry run
gopnik process document.pdf --profile healthcare --dry-run
```

### Check System Status
```bash
# Verify installation
gopnik --version

# Check available profiles
gopnik profile list

# Test with simple document
echo "test" > test.txt
gopnik process test.txt --dry-run
```

## See Also

- **[CLI Usage Guide](CLI-Usage-Guide)**: Complete CLI documentation
- **[Profile Configuration](Profile-Configuration)**: Advanced profile setup
- **[Batch Processing](Batch-Processing)**: Large-scale processing strategies
- **[Troubleshooting Guide](Troubleshooting-Guide)**: Common issues and solutions