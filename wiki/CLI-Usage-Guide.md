# CLI Usage Guide

The Gopnik Command Line Interface (CLI) provides powerful document processing capabilities directly from your terminal. This guide covers practical usage examples and workflows.

## Quick Start

### Installation and Setup

```bash
# Install Gopnik
pip install gopnik

# Verify installation
gopnik --version

# Get help
gopnik --help
```

### Your First Document

```bash
# Process a document with default settings
gopnik process document.pdf

# This creates document_redacted.pdf
```

## Essential Commands

### 1. Document Processing

#### Basic Processing
```bash
# Process with default profile
gopnik process document.pdf

# Specify output location
gopnik process document.pdf --output /secure/redacted.pdf

# Use specific profile
gopnik process document.pdf --profile healthcare
```

#### Advanced Processing Options
```bash
# Dry run (preview without processing)
gopnik process document.pdf --dry-run --profile healthcare

# Force overwrite existing files
gopnik process document.pdf --output existing.pdf --force

# Use custom profile file
gopnik process document.pdf --profile-file /path/to/custom.yaml

# JSON output for automation
gopnik process document.pdf --format json
```

### 2. Batch Processing

#### Basic Batch Operations
```bash
# Process all documents in directory
gopnik batch /path/to/documents

# Recursive processing with progress
gopnik batch /documents --recursive --progress

# Process only specific file types
gopnik batch /documents --pattern "*.pdf"
```

#### Advanced Batch Options
```bash
# Limit number of files
gopnik batch /documents --max-files 50

# Continue on errors
gopnik batch /documents --continue-on-error

# Custom output directory
gopnik batch /input --output /output --profile healthcare

# Dry run for large batches
gopnik batch /documents --dry-run --recursive
```

### 3. Document Validation

#### Basic Validation
```bash
# Validate with explicit audit log
gopnik validate document.pdf audit.json

# Auto-find audit log
gopnik validate document.pdf

# Search in specific directory
gopnik validate document.pdf --audit-dir /audit/logs
```

#### Advanced Validation
```bash
# Strict validation with signatures
gopnik validate document.pdf --strict --verify-signatures

# Verbose output
gopnik validate document.pdf --verbose

# JSON output
gopnik validate document.pdf --format json
```

### 4. Profile Management

#### Listing and Viewing Profiles
```bash
# List all profiles
gopnik profile list

# Detailed profile list
gopnik profile list --verbose --format json

# Show specific profile
gopnik profile show healthcare
```

#### Creating Profiles
```bash
# Create from scratch
gopnik profile create \
  --name "custom" \
  --description "Custom redaction profile" \
  --pii-types name email phone \
  --redaction-style solid

# Create based on existing profile
gopnik profile create \
  --name "strict-healthcare" \
  --based-on healthcare \
  --description "Strict healthcare compliance"
```

#### Editing Profiles
```bash
# Add PII types
gopnik profile edit healthcare --add-pii-types ssn medical_record_number

# Remove PII types
gopnik profile edit healthcare --remove-pii-types phone

# Change redaction style
gopnik profile edit healthcare --redaction-style blur

# Update description
gopnik profile edit healthcare --description "Updated healthcare profile"
```

#### Profile Validation and Management
```bash
# Validate profile
gopnik profile validate healthcare

# Delete profile (with confirmation)
gopnik profile delete old-profile

# Force delete
gopnik profile delete old-profile --force
```

## Real-World Workflows

### Workflow 1: Healthcare Document Processing

```bash
#!/bin/bash
# Healthcare document processing workflow

DOCS_DIR="/medical/documents"
OUTPUT_DIR="/medical/redacted"
PROFILE="healthcare_hipaa"

echo "Starting healthcare document processing..."

# 1. Validate profile
gopnik profile validate $PROFILE
if [ $? -ne 0 ]; then
    echo "Profile validation failed"
    exit 1
fi

# 2. Dry run to check what will be processed
gopnik batch $DOCS_DIR --profile $PROFILE --dry-run --recursive

# 3. Process documents with progress tracking
gopnik batch $DOCS_DIR \
    --output $OUTPUT_DIR \
    --profile $PROFILE \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > processing_results.json

# 4. Validate all processed documents
echo "Validating processed documents..."
for file in $OUTPUT_DIR/*.pdf; do
    gopnik validate "$file" --verify-signatures --format json
done

echo "Healthcare processing workflow completed"
```

### Workflow 2: Legal Document Redaction

```bash
#!/bin/bash
# Legal document redaction with audit trails

INPUT_FILE="$1"
CLIENT_NAME="$2"
CASE_NUMBER="$3"

if [ -z "$INPUT_FILE" ] || [ -z "$CLIENT_NAME" ] || [ -z "$CASE_NUMBER" ]; then
    echo "Usage: $0 <input_file> <client_name> <case_number>"
    exit 1
fi

# Create case-specific output directory
OUTPUT_DIR="./cases/${CASE_NUMBER}/redacted"
mkdir -p "$OUTPUT_DIR"

# Generate output filename
BASENAME=$(basename "$INPUT_FILE" .pdf)
OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME}_redacted_${CLIENT_NAME}.pdf"

echo "Processing legal document for case $CASE_NUMBER"

# 1. Process with legal profile
gopnik process "$INPUT_FILE" \
    --profile legal \
    --output "$OUTPUT_FILE" \
    --format json > "${OUTPUT_DIR}/processing_log.json"

# 2. Validate the result
gopnik validate "$OUTPUT_FILE" \
    --verify-signatures \
    --verbose \
    --format json > "${OUTPUT_DIR}/validation_log.json"

# 3. Generate case summary
echo "Case: $CASE_NUMBER" > "${OUTPUT_DIR}/case_summary.txt"
echo "Client: $CLIENT_NAME" >> "${OUTPUT_DIR}/case_summary.txt"
echo "Original: $INPUT_FILE" >> "${OUTPUT_DIR}/case_summary.txt"
echo "Redacted: $OUTPUT_FILE" >> "${OUTPUT_DIR}/case_summary.txt"
echo "Processed: $(date)" >> "${OUTPUT_DIR}/case_summary.txt"

echo "Legal document processing completed"
echo "Files saved to: $OUTPUT_DIR"
```

### Workflow 3: Automated Quality Assurance

```bash
#!/bin/bash
# Quality assurance workflow for processed documents

QA_DIR="/qa/documents"
RESULTS_FILE="/qa/qa_results_$(date +%Y%m%d_%H%M%S).json"

echo "Starting QA workflow..."

# Initialize results array
echo "[]" > "$RESULTS_FILE"

# Process each document in QA directory
for doc in "$QA_DIR"/*.pdf; do
    if [ ! -f "$doc" ]; then
        continue
    fi
    
    echo "QA processing: $(basename "$doc")"
    
    # 1. Process with multiple profiles for comparison
    for profile in default healthcare legal; do
        output_file="${doc%.pdf}_${profile}_redacted.pdf"
        
        # Process document
        result=$(gopnik process "$doc" \
            --profile "$profile" \
            --output "$output_file" \
            --format json)
        
        # Validate result
        validation=$(gopnik validate "$output_file" \
            --verify-signatures \
            --format json)
        
        # Combine results
        combined=$(echo "$result $validation" | jq -s '.[0] + .[1] + {"profile": "'$profile'", "document": "'$(basename "$doc")'"}')
        
        # Append to results file
        jq ". += [$combined]" "$RESULTS_FILE" > "${RESULTS_FILE}.tmp" && mv "${RESULTS_FILE}.tmp" "$RESULTS_FILE"
    done
done

echo "QA workflow completed. Results saved to: $RESULTS_FILE"

# Generate summary report
jq '.[] | select(.status == "success") | .profile' "$RESULTS_FILE" | sort | uniq -c
```

## Advanced Usage Patterns

### 1. Custom Profile Creation Pipeline

```bash
#!/bin/bash
# Create organization-specific profiles

ORG_NAME="$1"
BASE_PROFILE="$2"

if [ -z "$ORG_NAME" ] || [ -z "$BASE_PROFILE" ]; then
    echo "Usage: $0 <org_name> <base_profile>"
    exit 1
fi

# Create base profile
gopnik profile create \
    --name "${ORG_NAME}_base" \
    --based-on "$BASE_PROFILE" \
    --description "Base profile for $ORG_NAME"

# Create department-specific profiles
for dept in hr legal finance it; do
    gopnik profile create \
        --name "${ORG_NAME}_${dept}" \
        --based-on "${ORG_NAME}_base" \
        --description "$ORG_NAME $dept department profile"
    
    # Customize based on department
    case $dept in
        hr)
            gopnik profile edit "${ORG_NAME}_${dept}" \
                --add-pii-types ssn employee_id salary
            ;;
        legal)
            gopnik profile edit "${ORG_NAME}_${dept}" \
                --add-pii-types case_number attorney_client \
                --redaction-style solid
            ;;
        finance)
            gopnik profile edit "${ORG_NAME}_${dept}" \
                --add-pii-types account_number routing_number credit_card
            ;;
        it)
            gopnik profile edit "${ORG_NAME}_${dept}" \
                --add-pii-types ip_address server_name password
            ;;
    esac
    
    # Validate each profile
    gopnik profile validate "${ORG_NAME}_${dept}"
done

echo "Created profiles for $ORG_NAME:"
gopnik profile list | grep "$ORG_NAME"
```

### 2. Monitoring and Alerting

```bash
#!/bin/bash
# Monitor processing results and send alerts

WATCH_DIR="/incoming/documents"
ALERT_EMAIL="admin@company.com"
LOG_FILE="/var/log/gopnik_monitor.log"

while inotifywait -e create "$WATCH_DIR"; do
    for new_file in "$WATCH_DIR"/*.pdf; do
        if [ ! -f "$new_file" ]; then
            continue
        fi
        
        echo "$(date): Processing new file: $new_file" >> "$LOG_FILE"
        
        # Process with error handling
        result=$(gopnik process "$new_file" \
            --profile default \
            --format json 2>&1)
        
        if [ $? -eq 0 ]; then
            echo "$(date): Successfully processed: $new_file" >> "$LOG_FILE"
            
            # Validate result
            output_file="${new_file%.pdf}_redacted.pdf"
            validation=$(gopnik validate "$output_file" --format json)
            
            if [ $? -eq 0 ]; then
                echo "$(date): Validation passed: $output_file" >> "$LOG_FILE"
            else
                echo "$(date): Validation failed: $output_file" >> "$LOG_FILE"
                echo "Validation failed for $output_file" | mail -s "Gopnik Alert" "$ALERT_EMAIL"
            fi
        else
            echo "$(date): Processing failed: $new_file - $result" >> "$LOG_FILE"
            echo "Processing failed for $new_file: $result" | mail -s "Gopnik Error" "$ALERT_EMAIL"
        fi
        
        # Move processed file
        mv "$new_file" "/processed/"
    done
done
```

### 3. Performance Benchmarking

```bash
#!/bin/bash
# Benchmark different profiles and configurations

BENCHMARK_DIR="/benchmark/documents"
RESULTS_FILE="/benchmark/results_$(date +%Y%m%d_%H%M%S).csv"

echo "profile,document,file_size,processing_time,detections,success" > "$RESULTS_FILE"

for profile in default healthcare legal finance; do
    echo "Benchmarking profile: $profile"
    
    for doc in "$BENCHMARK_DIR"/*.pdf; do
        if [ ! -f "$doc" ]; then
            continue
        fi
        
        file_size=$(stat -f%z "$doc" 2>/dev/null || stat -c%s "$doc")
        doc_name=$(basename "$doc")
        
        # Time the processing
        start_time=$(date +%s.%N)
        
        result=$(gopnik process "$doc" \
            --profile "$profile" \
            --format json 2>/dev/null)
        
        end_time=$(date +%s.%N)
        processing_time=$(echo "$end_time - $start_time" | bc)
        
        if [ $? -eq 0 ]; then
            detections=$(echo "$result" | jq -r '.detections_found // 0')
            success="true"
        else
            detections="0"
            success="false"
        fi
        
        echo "$profile,$doc_name,$file_size,$processing_time,$detections,$success" >> "$RESULTS_FILE"
    done
done

echo "Benchmark completed. Results saved to: $RESULTS_FILE"

# Generate summary statistics
echo "Summary by profile:"
awk -F, 'NR>1 {sum[$1]+=$4; count[$1]++} END {for(p in sum) print p": avg=" sum[p]/count[p] "s, count=" count[p]}' "$RESULTS_FILE"
```

## Integration Examples

### Python Integration

```python
#!/usr/bin/env python3
"""
Python wrapper for Gopnik CLI operations
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

class GopnikCLI:
    """Python wrapper for Gopnik CLI"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        logging.basicConfig(level=getattr(logging, log_level))
        self.logger = logging.getLogger(__name__)
    
    def process_document(self, input_path: Path, profile: str = "default", 
                        output_path: Optional[Path] = None, dry_run: bool = False) -> Dict:
        """Process a single document"""
        
        cmd = ["gopnik", "process", str(input_path), "--format", "json"]
        
        if profile:
            cmd.extend(["--profile", profile])
        
        if output_path:
            cmd.extend(["--output", str(output_path)])
        
        if dry_run:
            cmd.append("--dry-run")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Processing failed: {e.stderr}")
            raise
    
    def batch_process(self, input_dir: Path, profile: str = "default",
                     output_dir: Optional[Path] = None, recursive: bool = False,
                     pattern: Optional[str] = None) -> Dict:
        """Batch process documents"""
        
        cmd = ["gopnik", "batch", str(input_dir), "--format", "json"]
        
        if profile:
            cmd.extend(["--profile", profile])
        
        if output_dir:
            cmd.extend(["--output", str(output_dir)])
        
        if recursive:
            cmd.append("--recursive")
        
        if pattern:
            cmd.extend(["--pattern", pattern])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Batch processing failed: {e.stderr}")
            raise
    
    def validate_document(self, document_path: Path, audit_log: Optional[Path] = None,
                         verify_signatures: bool = False) -> Dict:
        """Validate document integrity"""
        
        cmd = ["gopnik", "validate", str(document_path), "--format", "json"]
        
        if audit_log:
            cmd.append(str(audit_log))
        
        if verify_signatures:
            cmd.append("--verify-signatures")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Validation failed: {e.stderr}")
            raise
    
    def list_profiles(self) -> List[Dict]:
        """List available profiles"""
        
        cmd = ["gopnik", "profile", "list", "--format", "json"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to list profiles: {e.stderr}")
            raise

# Usage example
if __name__ == "__main__":
    cli = GopnikCLI()
    
    # Process a document
    result = cli.process_document(
        input_path=Path("document.pdf"),
        profile="healthcare",
        output_path=Path("redacted.pdf")
    )
    
    print(f"Processing result: {result}")
    
    # Validate the result
    validation = cli.validate_document(
        document_path=Path("redacted.pdf"),
        verify_signatures=True
    )
    
    print(f"Validation result: {validation}")
```

### Node.js Integration

```javascript
#!/usr/bin/env node
/**
 * Node.js wrapper for Gopnik CLI operations
 */

const { spawn } = require('child_process');
const path = require('path');

class GopnikCLI {
    constructor(logLevel = 'INFO') {
        this.logLevel = logLevel;
    }
    
    async processDocument(inputPath, options = {}) {
        const cmd = ['gopnik', 'process', inputPath, '--format', 'json'];
        
        if (options.profile) {
            cmd.push('--profile', options.profile);
        }
        
        if (options.output) {
            cmd.push('--output', options.output);
        }
        
        if (options.dryRun) {
            cmd.push('--dry-run');
        }
        
        return this._runCommand(cmd);
    }
    
    async batchProcess(inputDir, options = {}) {
        const cmd = ['gopnik', 'batch', inputDir, '--format', 'json'];
        
        if (options.profile) {
            cmd.push('--profile', options.profile);
        }
        
        if (options.output) {
            cmd.push('--output', options.output);
        }
        
        if (options.recursive) {
            cmd.push('--recursive');
        }
        
        if (options.pattern) {
            cmd.push('--pattern', options.pattern);
        }
        
        return this._runCommand(cmd);
    }
    
    async validateDocument(documentPath, options = {}) {
        const cmd = ['gopnik', 'validate', documentPath, '--format', 'json'];
        
        if (options.auditLog) {
            cmd.push(options.auditLog);
        }
        
        if (options.verifySignatures) {
            cmd.push('--verify-signatures');
        }
        
        return this._runCommand(cmd);
    }
    
    async listProfiles() {
        const cmd = ['gopnik', 'profile', 'list', '--format', 'json'];
        return this._runCommand(cmd);
    }
    
    _runCommand(cmd) {
        return new Promise((resolve, reject) => {
            const process = spawn(cmd[0], cmd.slice(1));
            let stdout = '';
            let stderr = '';
            
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        resolve(JSON.parse(stdout));
                    } catch (e) {
                        resolve({ output: stdout });
                    }
                } else {
                    reject(new Error(`Command failed with code ${code}: ${stderr}`));
                }
            });
        });
    }
}

// Usage example
async function main() {
    const cli = new GopnikCLI();
    
    try {
        // Process a document
        const result = await cli.processDocument('document.pdf', {
            profile: 'healthcare',
            output: 'redacted.pdf'
        });
        
        console.log('Processing result:', result);
        
        // Validate the result
        const validation = await cli.validateDocument('redacted.pdf', {
            verifySignatures: true
        });
        
        console.log('Validation result:', validation);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

if (require.main === module) {
    main();
}

module.exports = GopnikCLI;
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Command Not Found
```bash
$ gopnik --version
bash: gopnik: command not found
```

**Solutions:**
- Ensure Gopnik is installed: `pip install gopnik`
- Check if pip bin directory is in PATH
- Try: `python -m gopnik --version`

#### 2. Permission Errors
```bash
$ gopnik process document.pdf --output /root/redacted.pdf
Error: Permission denied: /root/redacted.pdf
```

**Solutions:**
- Use a writable output directory
- Run with appropriate permissions
- Check file and directory ownership

#### 3. Profile Not Found
```bash
$ gopnik process document.pdf --profile custom
Error: Profile 'custom' not found
```

**Solutions:**
- List available profiles: `gopnik profile list`
- Create the profile: `gopnik profile create --name custom`
- Check profile file location and permissions

#### 4. Processing Failures
```bash
$ gopnik process document.pdf
Error: Unsupported document format: .docx
```

**Solutions:**
- Check supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP
- Convert document to supported format
- Use `--verbose` for detailed error information

### Getting Debug Information

```bash
# Enable verbose logging
gopnik --verbose --log-level DEBUG process document.pdf

# Save logs to file
gopnik --log-file gopnik.log process document.pdf

# Check system information
gopnik --version
python --version
pip list | grep gopnik
```

## Best Practices

### 1. Security
- Always validate processed documents
- Use appropriate profiles for sensitive data
- Enable audit trails for compliance
- Store profiles securely

### 2. Performance
- Use batch processing for multiple documents
- Enable progress tracking for long operations
- Limit file counts for testing
- Monitor system resources

### 3. Automation
- Use JSON output for scripting
- Implement error handling in scripts
- Use dry-run mode for testing
- Log all operations for audit trails

### 4. Maintenance
- Regularly update Gopnik
- Validate profiles after updates
- Monitor processing statistics
- Clean up temporary files

## See Also

- **[CLI Reference](CLI-Reference)**: Complete command documentation
- **[Profile Configuration](Profile-Configuration)**: Advanced profile setup
- **[Batch Processing](Batch-Processing)**: Large-scale processing
- **[Audit Trails](Audit-Trail-Analysis)**: Working with audit logs
- **[Troubleshooting](Troubleshooting-Guide)**: Common issues and solutions