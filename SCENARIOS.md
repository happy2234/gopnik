# Gopnik Usage Scenarios and Test Cases

## Table of Contents
1. [Healthcare Scenarios](#healthcare-scenarios)
2. [Legal Document Scenarios](#legal-document-scenarios)
3. [Financial Document Scenarios](#financial-document-scenarios)
4. [Government Document Scenarios](#government-document-scenarios)
5. [Corporate Document Scenarios](#corporate-document-scenarios)
6. [Research and Academic Scenarios](#research-and-academic-scenarios)
7. [Integration Test Cases](#integration-test-cases)
8. [Performance Test Cases](#performance-test-cases)
9. [Security Test Cases](#security-test-cases)
10. [Edge Cases and Error Scenarios](#edge-cases-and-error-scenarios)

## Healthcare Scenarios

### Scenario 1: HIPAA-Compliant Medical Records Processing

**Use Case:** Hospital needs to redact patient information from medical records for research purposes while maintaining HIPAA compliance.

**Documents:** Patient charts, lab results, discharge summaries, insurance forms

**PII Types to Detect:**
- Patient names
- Social Security Numbers
- Medical Record Numbers (MRN)
- Date of birth
- Phone numbers
- Addresses
- Insurance policy numbers
- Provider names (optional)

#### CLI Implementation
```bash
# Process single medical record
gopnik process patient_chart.pdf \
  --profile healthcare \
  --confidence 0.9 \
  --output redacted_chart.pdf \
  --audit-dir /secure/audit

# Batch process medical records directory
gopnik batch /medical_records \
  --profile healthcare \
  --pattern "*.pdf" \
  --recursive \
  --progress \
  --continue-on-error \
  --output-dir /redacted_records

# Validate processed documents
gopnik validate redacted_chart.pdf \
  --audit-dir /secure/audit \
  --verify-signatures \
  --verbose
```

**Expected Results:**
- Patient names redacted with solid black blocks
- SSNs completely obscured
- MRNs redacted while preserving document structure
- Audit trail with cryptographic signatures
- Processing time: ~5-15 seconds per page
- Detection accuracy: >95% for standard medical forms

## Legal Document Scenarios

### Scenario 2: Attorney-Client Privilege Protection

**Use Case:** Law firm needs to redact client information from legal documents for case studies and training materials.

**Documents:** Legal briefs, contracts, correspondence, court filings

**PII Types to Detect:**
- Client names
- Case numbers
- Social Security Numbers
- Financial information
- Personal addresses
- Phone numbers
- Email addresses

#### CLI Implementation
```bash
# Create custom legal profile
gopnik profile create \
  --name legal_privilege \
  --based-on legal \
  --add-pii-types case_number financial_account \
  --redaction-style blur \
  --confidence 0.85

# Process legal documents with custom profile
gopnik batch /legal_docs \
  --profile legal_privilege \
  --pattern "*.pdf" \
  --output-dir /redacted_legal \
  --audit-dir /legal_audit
```

## Financial Document Scenarios

### Scenario 3: PCI DSS Compliance for Payment Processing

**Use Case:** Payment processor needs to redact credit card information from transaction logs and customer communications.

**Documents:** Transaction receipts, customer service emails, payment forms

**PII Types to Detect:**
- Credit card numbers (PAN)
- CVV codes
- Expiration dates
- Cardholder names
- Billing addresses
- Bank account numbers

#### CLI Implementation
```bash
# Use financial profile with high confidence
gopnik process transaction_log.pdf \
  --profile financial \
  --confidence 0.95 \
  --output secure_log.pdf

# Batch process with PCI DSS requirements
gopnik batch /payment_docs \
  --profile financial \
  --pattern "*.pdf" \
  --max-files 1000 \
  --parallel 4 \
  --continue-on-error \
  --audit-dir /pci_audit
```

## Integration Test Cases

### Test Case 1: End-to-End CLI Workflow

**Objective:** Verify complete CLI workflow from document processing to validation.

```bash
#!/bin/bash
# Test script: test_cli_workflow.sh

set -e

# Setup test environment
TEST_DIR="/tmp/gopnik_test"
mkdir -p $TEST_DIR/{input,output,audit}

# Create test document
echo "Test document with John Doe (555-123-4567) and jane@example.com" > $TEST_DIR/input/test.txt

# Test 1: Process single document
echo "Testing single document processing..."
gopnik process $TEST_DIR/input/test.txt \
  --output $TEST_DIR/output/test_redacted.txt \
  --profile default \
  --audit-dir $TEST_DIR/audit \
  --verbose

# Verify output exists
if [ ! -f "$TEST_DIR/output/test_redacted.txt" ]; then
  echo "ERROR: Output file not created"
  exit 1
fi

# Test 2: Validate processed document
echo "Testing document validation..."
gopnik validate $TEST_DIR/output/test_redacted.txt \
  --audit-dir $TEST_DIR/audit \
  --verify-signatures \
  --verbose

echo "All CLI tests passed!"
```

---

**Version:** 1.0.0  
**Last Updated:** September 2025  
**License:** MIT