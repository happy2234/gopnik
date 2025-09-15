# CLI Examples and Use Cases

This page provides real-world examples and use cases for the Gopnik CLI, organized by industry and scenario.

## Healthcare (HIPAA Compliance)

### Medical Records Processing

```bash
#!/bin/bash
# Healthcare document processing workflow

# Set up variables
MEDICAL_RECORDS_DIR="/secure/medical-records"
REDACTED_DIR="/secure/redacted-records"
AUDIT_DIR="/secure/audit-logs"
PROFILE="healthcare_hipaa"

# Create directories
mkdir -p "$REDACTED_DIR" "$AUDIT_DIR"

echo "Starting HIPAA-compliant medical records processing..."

# 1. Validate the healthcare profile
if ! gopnik profile validate "$PROFILE"; then
    echo "ERROR: Healthcare profile validation failed"
    exit 1
fi

# 2. Process all medical records
gopnik batch "$MEDICAL_RECORDS_DIR" \
    --output "$REDACTED_DIR" \
    --profile "$PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > "$AUDIT_DIR/processing_log_$(date +%Y%m%d_%H%M%S).json"

# 3. Validate all processed documents
echo "Validating processed medical records..."
validation_failures=0

for record in "$REDACTED_DIR"/*.pdf; do
    if [ -f "$record" ]; then
        if ! gopnik validate "$record" --verify-signatures --format json > "$AUDIT_DIR/validation_$(basename "$record").json"; then
            echo "VALIDATION FAILED: $(basename "$record")"
            ((validation_failures++))
        fi
    fi
done

# 4. Generate compliance report
cat > "$AUDIT_DIR/compliance_report_$(date +%Y%m%d).txt" << EOF
HIPAA Compliance Report
Generated: $(date)
Profile Used: $PROFILE
Records Processed: $(find "$REDACTED_DIR" -name "*.pdf" | wc -l)
Validation Failures: $validation_failures
Status: $([ $validation_failures -eq 0 ] && echo "COMPLIANT" || echo "NON-COMPLIANT")
EOF

echo "Healthcare processing completed. See $AUDIT_DIR for compliance documentation."
```

### Patient Data Anonymization

```bash
#!/bin/bash
# Anonymize patient data for research

PATIENT_DATA="/research/patient-files"
ANONYMIZED_DATA="/research/anonymized"
RESEARCH_PROFILE="research_anonymization"

# Create custom research profile
gopnik profile create \
    --name "$RESEARCH_PROFILE" \
    --based-on healthcare_hipaa \
    --description "Research data anonymization profile" \
    --pii-types name ssn medical_record_number date_of_birth address phone email

# Process patient files for research
gopnik batch "$PATIENT_DATA" \
    --output "$ANONYMIZED_DATA" \
    --profile "$RESEARCH_PROFILE" \
    --recursive \
    --progress \
    --pattern "*.pdf" \
    --format json > research_processing_log.json

# Validate anonymization quality
echo "Validating anonymization quality..."
for file in "$ANONYMIZED_DATA"/*.pdf; do
    gopnik validate "$file" --strict --verify-signatures
done
```

## Legal Industry

### Attorney-Client Privilege Protection

```bash
#!/bin/bash
# Legal document redaction with privilege protection

CASE_NUMBER="$1"
CLIENT_NAME="$2"
DOCUMENT_PATH="$3"

if [ $# -ne 3 ]; then
    echo "Usage: $0 <case_number> <client_name> <document_path>"
    echo "Example: $0 CASE-2024-001 'John Doe' /legal/docs/contract.pdf"
    exit 1
fi

# Set up case directory structure
CASE_DIR="/legal/cases/$CASE_NUMBER"
REDACTED_DIR="$CASE_DIR/redacted"
AUDIT_DIR="$CASE_DIR/audit"
WORK_PRODUCT_DIR="$CASE_DIR/work-product"

mkdir -p "$REDACTED_DIR" "$AUDIT_DIR" "$WORK_PRODUCT_DIR"

echo "Processing legal document for Case: $CASE_NUMBER, Client: $CLIENT_NAME"

# Create case-specific profile if needed
CASE_PROFILE="legal_${CASE_NUMBER,,}"
gopnik profile create \
    --name "$CASE_PROFILE" \
    --based-on legal \
    --description "Legal profile for case $CASE_NUMBER"

# Process the document
BASENAME=$(basename "$DOCUMENT_PATH" .pdf)
OUTPUT_FILE="$REDACTED_DIR/${BASENAME}_redacted_$(date +%Y%m%d).pdf"

gopnik process "$DOCUMENT_PATH" \
    --profile "$CASE_PROFILE" \
    --output "$OUTPUT_FILE" \
    --format json > "$AUDIT_DIR/processing_$(basename "$DOCUMENT_PATH").json"

# Validate the redacted document
gopnik validate "$OUTPUT_FILE" \
    --verify-signatures \
    --verbose \
    --format json > "$AUDIT_DIR/validation_$(basename "$OUTPUT_FILE").json"

# Generate case documentation
cat > "$WORK_PRODUCT_DIR/redaction_certificate_$(date +%Y%m%d).txt" << EOF
REDACTION CERTIFICATE

Case Number: $CASE_NUMBER
Client: $CLIENT_NAME
Original Document: $DOCUMENT_PATH
Redacted Document: $OUTPUT_FILE
Processing Date: $(date)
Profile Used: $CASE_PROFILE
Processed By: $(whoami)

This document has been processed using Gopnik deidentification toolkit
with forensic-grade audit trails and cryptographic verification.

Digital Signature: [Audit log contains cryptographic signature]
EOF

echo "Legal document processing completed."
echo "Redacted document: $OUTPUT_FILE"
echo "Audit trail: $AUDIT_DIR"
echo "Certificate: $WORK_PRODUCT_DIR/redaction_certificate_$(date +%Y%m%d).txt"
```

### Discovery Document Processing

```bash
#!/bin/bash
# Mass discovery document processing

DISCOVERY_DIR="/legal/discovery/incoming"
PROCESSED_DIR="/legal/discovery/processed"
PRIVILEGED_DIR="/legal/discovery/privileged"
PRODUCIBLE_DIR="/legal/discovery/producible"

# Create processing directories
mkdir -p "$PROCESSED_DIR" "$PRIVILEGED_DIR" "$PRODUCIBLE_DIR"

echo "Starting discovery document processing..."

# Process all discovery documents
gopnik batch "$DISCOVERY_DIR" \
    --output "$PROCESSED_DIR" \
    --profile legal \
    --recursive \
    --progress \
    --continue-on-error \
    --max-files 1000 \
    --format json > discovery_processing_log.json

# Separate privileged vs producible documents based on redaction results
while IFS= read -r result_line; do
    if echo "$result_line" | jq -e '.detections_found > 5' > /dev/null; then
        # High PII content - likely privileged
        input_file=$(echo "$result_line" | jq -r '.input')
        output_file=$(echo "$result_line" | jq -r '.output')
        mv "$output_file" "$PRIVILEGED_DIR/"
        echo "PRIVILEGED: $(basename "$input_file")" >> privilege_log.txt
    else
        # Low PII content - potentially producible
        output_file=$(echo "$result_line" | jq -r '.output')
        mv "$output_file" "$PRODUCIBLE_DIR/"
        echo "PRODUCIBLE: $(basename "$output_file")" >> producible_log.txt
    fi
done < <(jq -c '.[]' discovery_processing_log.json 2>/dev/null || echo '{}')

echo "Discovery processing completed."
echo "Privileged documents: $(ls "$PRIVILEGED_DIR" | wc -l)"
echo "Producible documents: $(ls "$PRODUCIBLE_DIR" | wc -l)"
```

## Financial Services (PCI DSS)

### Credit Card Data Protection

```bash
#!/bin/bash
# PCI DSS compliant financial document processing

FINANCIAL_DOCS="/finance/documents"
SECURE_VAULT="/finance/secure-vault"
COMPLIANCE_LOG="/finance/compliance/pci_compliance_$(date +%Y%m%d).log"

# Create PCI DSS profile
PCI_PROFILE="pci_dss_compliant"
gopnik profile create \
    --name "$PCI_PROFILE" \
    --description "PCI DSS compliant financial redaction" \
    --pii-types credit_card bank_account routing_number ssn name address phone email \
    --redaction-style solid

echo "Starting PCI DSS compliant processing..." | tee -a "$COMPLIANCE_LOG"

# Process financial documents
gopnik batch "$FINANCIAL_DOCS" \
    --output "$SECURE_VAULT" \
    --profile "$PCI_PROFILE" \
    --recursive \
    --progress \
    --force \
    --format json | tee -a "$COMPLIANCE_LOG"

# Validate all processed documents for PCI compliance
echo "Validating PCI DSS compliance..." | tee -a "$COMPLIANCE_LOG"
compliance_failures=0

for doc in "$SECURE_VAULT"/*.pdf; do
    if [ -f "$doc" ]; then
        if gopnik validate "$doc" --strict --verify-signatures; then
            echo "COMPLIANT: $(basename "$doc")" | tee -a "$COMPLIANCE_LOG"
        else
            echo "NON-COMPLIANT: $(basename "$doc")" | tee -a "$COMPLIANCE_LOG"
            ((compliance_failures++))
        fi
    fi
done

# Generate PCI compliance report
cat >> "$COMPLIANCE_LOG" << EOF

PCI DSS COMPLIANCE SUMMARY
==========================
Date: $(date)
Documents Processed: $(find "$SECURE_VAULT" -name "*.pdf" | wc -l)
Compliance Failures: $compliance_failures
Overall Status: $([ $compliance_failures -eq 0 ] && echo "COMPLIANT" || echo "NON-COMPLIANT")

Profile Used: $PCI_PROFILE
Redaction Types: Credit Card, Bank Account, SSN, Personal Information
Audit Trail: Cryptographically signed
EOF

echo "PCI DSS processing completed. Compliance log: $COMPLIANCE_LOG"
```

### Financial Report Sanitization

```bash
#!/bin/bash
# Sanitize financial reports for public disclosure

INTERNAL_REPORTS="/finance/internal-reports"
PUBLIC_REPORTS="/finance/public-reports"
SANITIZATION_PROFILE="financial_public_disclosure"

# Create sanitization profile
gopnik profile create \
    --name "$SANITIZATION_PROFILE" \
    --description "Financial report sanitization for public disclosure" \
    --pii-types name ssn account_number salary employee_id internal_code \
    --redaction-style blur

echo "Sanitizing financial reports for public disclosure..."

# Process reports with special handling for financial data
for report in "$INTERNAL_REPORTS"/*.pdf; do
    if [ -f "$report" ]; then
        report_name=$(basename "$report" .pdf)
        
        echo "Processing: $report_name"
        
        # Process with sanitization profile
        gopnik process "$report" \
            --profile "$SANITIZATION_PROFILE" \
            --output "$PUBLIC_REPORTS/${report_name}_public.pdf" \
            --format json > "sanitization_${report_name}.json"
        
        # Validate sanitization
        if gopnik validate "$PUBLIC_REPORTS/${report_name}_public.pdf" --verify-signatures; then
            echo "✓ Sanitization validated: ${report_name}_public.pdf"
        else
            echo "✗ Sanitization failed: ${report_name}_public.pdf"
        fi
    fi
done

echo "Financial report sanitization completed."
```

## Government and Defense

### Classified Document Redaction

```bash
#!/bin/bash
# Government classified document redaction

CLASSIFIED_DIR="/secure/classified"
DECLASSIFIED_DIR="/secure/declassified"
CLASSIFICATION_LEVEL="$1"

if [ -z "$CLASSIFICATION_LEVEL" ]; then
    echo "Usage: $0 <classification_level>"
    echo "Levels: confidential, secret, top_secret"
    exit 1
fi

# Create classification-specific profile
GOVT_PROFILE="government_${CLASSIFICATION_LEVEL}"
case "$CLASSIFICATION_LEVEL" in
    "confidential")
        PII_TYPES="name address phone email"
        ;;
    "secret")
        PII_TYPES="name address phone email ssn id_number location coordinates"
        ;;
    "top_secret")
        PII_TYPES="name address phone email ssn id_number location coordinates operation_name asset_id"
        ;;
    *)
        echo "Invalid classification level"
        exit 1
        ;;
esac

gopnik profile create \
    --name "$GOVT_PROFILE" \
    --description "Government redaction for $CLASSIFICATION_LEVEL documents" \
    --pii-types $PII_TYPES \
    --redaction-style solid

echo "Processing $CLASSIFICATION_LEVEL classified documents..."

# Process with strict validation
gopnik batch "$CLASSIFIED_DIR" \
    --output "$DECLASSIFIED_DIR" \
    --profile "$GOVT_PROFILE" \
    --recursive \
    --progress \
    --format json > "declassification_$(date +%Y%m%d_%H%M%S).json"

# Strict validation for government compliance
echo "Performing strict validation for government compliance..."
for doc in "$DECLASSIFIED_DIR"/*.pdf; do
    if [ -f "$doc" ]; then
        gopnik validate "$doc" \
            --strict \
            --verify-signatures \
            --verbose \
            --format json > "validation_$(basename "$doc").json"
    fi
done

echo "Classified document processing completed."
```

## Corporate HR

### Employee Records Processing

```bash
#!/bin/bash
# HR employee records processing

HR_RECORDS="/hr/employee-records"
PROCESSED_RECORDS="/hr/processed-records"
DEPARTMENT="$1"

if [ -z "$DEPARTMENT" ]; then
    echo "Usage: $0 <department>"
    echo "Departments: hr, finance, legal, it, operations"
    exit 1
fi

# Create department-specific HR profile
HR_PROFILE="hr_${DEPARTMENT}"
gopnik profile create \
    --name "$HR_PROFILE" \
    --based-on default \
    --description "HR profile for $DEPARTMENT department" \
    --pii-types name ssn employee_id salary address phone email date_of_birth

echo "Processing HR records for $DEPARTMENT department..."

# Process employee records by department
gopnik batch "$HR_RECORDS/$DEPARTMENT" \
    --output "$PROCESSED_RECORDS/$DEPARTMENT" \
    --profile "$HR_PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --format json > "hr_processing_${DEPARTMENT}_$(date +%Y%m%d).json"

# Generate HR compliance report
cat > "hr_compliance_${DEPARTMENT}_$(date +%Y%m%d).txt" << EOF
HR RECORDS PROCESSING REPORT

Department: $DEPARTMENT
Processing Date: $(date)
Profile Used: $HR_PROFILE
Records Processed: $(find "$PROCESSED_RECORDS/$DEPARTMENT" -name "*.pdf" | wc -l)

PII Types Redacted:
- Employee Names
- Social Security Numbers
- Employee IDs
- Salary Information
- Personal Addresses
- Phone Numbers
- Email Addresses
- Dates of Birth

Compliance Status: PROCESSED
Audit Trail: Available in processing log
EOF

echo "HR records processing completed for $DEPARTMENT department."
```

## Research and Academia

### Research Data Anonymization

```bash
#!/bin/bash
# Research data anonymization for academic studies

RESEARCH_DATA="/research/raw-data"
ANONYMIZED_DATA="/research/anonymized-data"
STUDY_ID="$1"
IRB_NUMBER="$2"

if [ $# -ne 2 ]; then
    echo "Usage: $0 <study_id> <irb_number>"
    echo "Example: $0 STUDY-2024-001 IRB-2024-123"
    exit 1
fi

# Create research anonymization profile
RESEARCH_PROFILE="research_${STUDY_ID,,}"
gopnik profile create \
    --name "$RESEARCH_PROFILE" \
    --description "Research anonymization for study $STUDY_ID (IRB: $IRB_NUMBER)" \
    --pii-types name ssn date_of_birth address phone email medical_record_number \
    --redaction-style pixelated

echo "Anonymizing research data for Study: $STUDY_ID, IRB: $IRB_NUMBER"

# Process research documents
gopnik batch "$RESEARCH_DATA/$STUDY_ID" \
    --output "$ANONYMIZED_DATA/$STUDY_ID" \
    --profile "$RESEARCH_PROFILE" \
    --recursive \
    --progress \
    --format json > "research_anonymization_${STUDY_ID}.json"

# Validate anonymization for research compliance
echo "Validating research data anonymization..."
for data_file in "$ANONYMIZED_DATA/$STUDY_ID"/*.pdf; do
    if [ -f "$data_file" ]; then
        gopnik validate "$data_file" --verify-signatures --verbose
    fi
done

# Generate research compliance documentation
cat > "research_compliance_${STUDY_ID}.txt" << EOF
RESEARCH DATA ANONYMIZATION CERTIFICATE

Study ID: $STUDY_ID
IRB Number: $IRB_NUMBER
Anonymization Date: $(date)
Profile Used: $RESEARCH_PROFILE
Data Files Processed: $(find "$ANONYMIZED_DATA/$STUDY_ID" -name "*.pdf" | wc -l)

Anonymization Methods:
- Personal identifiers removed
- Dates shifted/generalized
- Geographic information redacted
- Medical record numbers anonymized

This data has been anonymized in accordance with IRB protocols
and is suitable for research use while protecting participant privacy.

Processed by: $(whoami)
System: Gopnik Deidentification Toolkit
Audit Trail: Available in processing logs
EOF

echo "Research data anonymization completed."
echo "Anonymized data: $ANONYMIZED_DATA/$STUDY_ID"
echo "Compliance certificate: research_compliance_${STUDY_ID}.txt"
```

## Quality Assurance and Testing

### Multi-Profile Quality Testing

```bash
#!/bin/bash
# Quality assurance testing across multiple profiles

TEST_DOCUMENTS="/qa/test-documents"
QA_RESULTS="/qa/results"
PROFILES=("default" "healthcare" "legal" "financial")

mkdir -p "$QA_RESULTS"

echo "Starting multi-profile quality assurance testing..."

# Test each profile against the same set of documents
for profile in "${PROFILES[@]}"; do
    echo "Testing profile: $profile"
    
    profile_results="$QA_RESULTS/${profile}_results"
    mkdir -p "$profile_results"
    
    # Process test documents with current profile
    gopnik batch "$TEST_DOCUMENTS" \
        --output "$profile_results" \
        --profile "$profile" \
        --recursive \
        --format json > "$QA_RESULTS/${profile}_processing.json"
    
    # Validate all results
    validation_summary="$QA_RESULTS/${profile}_validation_summary.txt"
    echo "Profile: $profile" > "$validation_summary"
    echo "Validation Results:" >> "$validation_summary"
    echo "==================" >> "$validation_summary"
    
    for result_file in "$profile_results"/*.pdf; do
        if [ -f "$result_file" ]; then
            if gopnik validate "$result_file" --verify-signatures; then
                echo "✓ $(basename "$result_file")" >> "$validation_summary"
            else
                echo "✗ $(basename "$result_file")" >> "$validation_summary"
            fi
        fi
    done
done

# Generate comparative analysis
echo "Generating comparative QA analysis..."
python3 << 'EOF'
import json
import os

profiles = ["default", "healthcare", "legal", "financial"]
qa_results = "/qa/results"

print("QA COMPARATIVE ANALYSIS")
print("=" * 50)

for profile in profiles:
    processing_file = f"{qa_results}/{profile}_processing.json"
    if os.path.exists(processing_file):
        with open(processing_file, 'r') as f:
            try:
                results = json.load(f)
                if isinstance(results, list):
                    total_docs = len(results)
                    successful = sum(1 for r in results if r.get('status') == 'success')
                    total_detections = sum(r.get('detections_found', 0) for r in results)
                    avg_time = sum(r.get('processing_time', 0) for r in results) / total_docs if total_docs > 0 else 0
                    
                    print(f"\nProfile: {profile}")
                    print(f"Documents: {total_docs}")
                    print(f"Success Rate: {successful}/{total_docs} ({100*successful/total_docs:.1f}%)")
                    print(f"Total Detections: {total_detections}")
                    print(f"Avg Processing Time: {avg_time:.2f}s")
            except json.JSONDecodeError:
                print(f"Error reading results for {profile}")
EOF

echo "Quality assurance testing completed. Results in: $QA_RESULTS"
```

### Performance Benchmarking

```bash
#!/bin/bash
# Performance benchmarking across different configurations

BENCHMARK_DOCS="/benchmark/documents"
BENCHMARK_RESULTS="/benchmark/results_$(date +%Y%m%d_%H%M%S)"
PROFILES=("default" "healthcare" "legal")
BATCH_SIZES=(1 5 10 20)

mkdir -p "$BENCHMARK_RESULTS"

echo "Starting performance benchmarking..."

# Benchmark different profiles and batch sizes
for profile in "${PROFILES[@]}"; do
    for batch_size in "${BATCH_SIZES[@]}"; do
        echo "Benchmarking: Profile=$profile, BatchSize=$batch_size"
        
        # Create subset of documents for batch size testing
        test_dir="$BENCHMARK_RESULTS/test_${profile}_${batch_size}"
        mkdir -p "$test_dir"
        
        # Copy limited number of files for testing
        find "$BENCHMARK_DOCS" -name "*.pdf" -type f | head -n "$batch_size" | while read -r file; do
            cp "$file" "$test_dir/"
        done
        
        # Time the processing
        start_time=$(date +%s.%N)
        
        gopnik batch "$test_dir" \
            --output "$BENCHMARK_RESULTS/output_${profile}_${batch_size}" \
            --profile "$profile" \
            --format json > "$BENCHMARK_RESULTS/benchmark_${profile}_${batch_size}.json"
        
        end_time=$(date +%s.%N)
        processing_time=$(echo "$end_time - $start_time" | bc)
        
        # Record benchmark results
        echo "$profile,$batch_size,$processing_time" >> "$BENCHMARK_RESULTS/benchmark_summary.csv"
        
        # Clean up test directory
        rm -rf "$test_dir"
    done
done

# Generate benchmark report
echo "profile,batch_size,processing_time" > "$BENCHMARK_RESULTS/benchmark_results.csv"
cat "$BENCHMARK_RESULTS/benchmark_summary.csv" >> "$BENCHMARK_RESULTS/benchmark_results.csv"

echo "Performance benchmarking completed."
echo "Results: $BENCHMARK_RESULTS/benchmark_results.csv"
```

## Monitoring and Alerting

### Automated Processing with Monitoring

```bash
#!/bin/bash
# Automated document processing with monitoring and alerting

WATCH_DIR="/incoming/documents"
PROCESSED_DIR="/processed/documents"
ERROR_DIR="/errors/documents"
ALERT_EMAIL="admin@company.com"
LOG_FILE="/var/log/gopnik_monitor.log"
PROFILE="default"

# Function to send alerts
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
    echo "$(date): ALERT - $subject: $message" >> "$LOG_FILE"
}

# Function to log events
log_event() {
    echo "$(date): $1" >> "$LOG_FILE"
}

log_event "Starting Gopnik monitoring service"

# Monitor directory for new files
while inotifywait -e create,moved_to "$WATCH_DIR" 2>/dev/null; do
    # Process new files
    for new_file in "$WATCH_DIR"/*.pdf; do
        if [ ! -f "$new_file" ]; then
            continue
        fi
        
        filename=$(basename "$new_file")
        log_event "Processing new file: $filename"
        
        # Process the document
        if gopnik process "$new_file" \
            --profile "$PROFILE" \
            --output "$PROCESSED_DIR/${filename%.pdf}_redacted.pdf" \
            --format json > "/tmp/processing_$$.json"; then
            
            log_event "Successfully processed: $filename"
            
            # Validate the result
            if gopnik validate "$PROCESSED_DIR/${filename%.pdf}_redacted.pdf" \
                --verify-signatures --format json > "/tmp/validation_$$.json"; then
                
                log_event "Validation passed: ${filename%.pdf}_redacted.pdf"
                
                # Move original to processed directory
                mv "$new_file" "$PROCESSED_DIR/originals/"
                
            else
                log_event "Validation failed: ${filename%.pdf}_redacted.pdf"
                send_alert "Gopnik Validation Failed" "Validation failed for $filename"
                mv "$new_file" "$ERROR_DIR/"
            fi
            
        else
            log_event "Processing failed: $filename"
            send_alert "Gopnik Processing Failed" "Processing failed for $filename"
            mv "$new_file" "$ERROR_DIR/"
        fi
        
        # Clean up temporary files
        rm -f "/tmp/processing_$$.json" "/tmp/validation_$$.json"
    done
done
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/document-processing.yml
name: Document Processing Pipeline

on:
  push:
    paths:
      - 'documents/**'

jobs:
  process-documents:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Gopnik
      run: |
        pip install gopnik
    
    - name: Validate profiles
      run: |
        gopnik profile validate default
        gopnik profile validate healthcare
    
    - name: Process documents
      run: |
        mkdir -p processed-docs
        gopnik batch documents/ \
          --output processed-docs/ \
          --profile default \
          --recursive \
          --format json > processing-results.json
    
    - name: Validate processed documents
      run: |
        for doc in processed-docs/*.pdf; do
          if [ -f "$doc" ]; then
            gopnik validate "$doc" --verify-signatures
          fi
        done
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: processed-documents
        path: processed-docs/
```

### Docker Integration

```dockerfile
# Dockerfile for Gopnik processing service
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Gopnik
RUN pip install gopnik[all]

# Create processing directories
RUN mkdir -p /app/input /app/output /app/profiles /app/logs

# Copy custom profiles
COPY profiles/ /app/profiles/

# Set working directory
WORKDIR /app

# Create processing script
COPY << 'EOF' /app/process.sh
#!/bin/bash
set -e

INPUT_DIR=${INPUT_DIR:-/app/input}
OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
PROFILE=${PROFILE:-default}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Starting Gopnik processing service..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Profile: $PROFILE"

# Process documents
gopnik batch "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --profile "$PROFILE" \
    --recursive \
    --progress \
    --continue-on-error \
    --log-level "$LOG_LEVEL" \
    --format json > /app/logs/processing.json

echo "Processing completed. Results in $OUTPUT_DIR"
EOF

RUN chmod +x /app/process.sh

# Expose volumes
VOLUME ["/app/input", "/app/output", "/app/logs"]

# Run processing script
CMD ["/app/process.sh"]
```

```bash
# Docker usage example
docker build -t gopnik-processor .

# Run processing
docker run -v /host/documents:/app/input \
           -v /host/processed:/app/output \
           -v /host/logs:/app/logs \
           -e PROFILE=healthcare \
           gopnik-processor
```

These examples demonstrate the versatility and power of the Gopnik CLI across various industries and use cases. Each example can be adapted to specific organizational needs and compliance requirements.

## See Also

- **[CLI Reference](cli-reference.md)**: Complete command documentation
- **[CLI Quick Start](cli-quickstart.md)**: Get started quickly
- **[Profile Configuration](profiles.md)**: Advanced profile setup
- **[Batch Processing](batch-processing.md)**: Large-scale processing
- **[Security Features](security.md)**: Cryptographic security and audit trails