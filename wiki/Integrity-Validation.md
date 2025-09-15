# Document Integrity Validation

Gopnik's integrity validation system provides forensic-grade verification of document authenticity, completeness, and audit trail integrity. This comprehensive guide covers all aspects of document validation workflows.

## 🎯 Overview

The integrity validation system ensures:

- **Document Authenticity**: Cryptographic verification of document integrity
- **Audit Trail Validation**: Complete audit chain verification
- **Forensic Reporting**: Detailed analysis with actionable recommendations
- **Batch Processing**: Efficient validation of multiple documents
- **Compliance Support**: Meeting legal and regulatory requirements

## 🔍 Validation Components

### 1. Document Hash Verification
Validates that documents haven't been modified since processing:

```python
from gopnik.utils import IntegrityValidator
from pathlib import Path

validator = IntegrityValidator()

# Basic hash validation
report = validator.validate_document_integrity(
    document_path=Path("processed_document.pdf"),
    expected_hash="sha256_hash_here"
)

print(f"Hash validation: {report.overall_result}")
print(f"Current hash: {report.document_hash}")
print(f"Expected hash: {report.expected_hash}")
```

### 2. Cryptographic Signature Validation
Verifies the authenticity of audit logs and processing records:

```python
# Validation with audit log
report = validator.validate_document_integrity(
    document_path=Path("document.pdf"),
    audit_log_path=Path("document_audit.json")
)

print(f"Signature valid: {report.signature_valid}")
print(f"Audit trail valid: {report.audit_trail_valid}")
```

### 3. Audit Trail Integrity
Comprehensive validation of the complete audit chain:

```python
# Detailed audit trail analysis
for issue in report.issues:
    severity = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
    print(f"{severity} {issue.message}")
    if issue.recommendation:
        print(f"   → {issue.recommendation}")
```

## 📊 Validation Results

### Result Types

The validation system returns detailed results:

```python
from gopnik.utils import ValidationResult

# Possible validation results
ValidationResult.VALID                # Document is authentic and complete
ValidationResult.INVALID             # General validation failure
ValidationResult.MISSING_DATA         # Required data is missing
ValidationResult.CORRUPTED           # Document appears corrupted
ValidationResult.SIGNATURE_MISMATCH  # Cryptographic signature invalid
ValidationResult.HASH_MISMATCH       # Document hash doesn't match expected
ValidationResult.AUDIT_TRAIL_BROKEN  # Audit trail has integrity issues
```

### Validation Report Structure

```python
# Comprehensive validation report
report = validator.validate_document_integrity(document_path)

print(f"Document ID: {report.document_id}")
print(f"Validation Time: {report.validation_timestamp}")
print(f"Overall Result: {report.overall_result}")
print(f"Processing Time: {report.processing_time}s")

# Issue analysis
print(f"Total Issues: {len(report.issues)}")
print(f"Errors: {len(report.get_issues_by_severity('error'))}")
print(f"Warnings: {len(report.get_issues_by_severity('warning'))}")
print(f"Info: {len(report.get_issues_by_severity('info'))}")
```

## 🔄 Batch Validation Workflows

### Directory-Based Validation

```python
# Validate all documents in a directory
reports = validator.validate_batch_documents(
    document_dir=Path("./processed_documents"),
    audit_dir=Path("./audit_logs"),
    file_pattern="*.pdf"
)

print(f"Validated {len(reports)} documents")

# Process results
for report in reports:
    if report.overall_result != ValidationResult.VALID:
        print(f"⚠️ Issues with {report.document_id}")
        for issue in report.get_issues_by_severity('error'):
            print(f"   ❌ {issue.message}")
```

### Validation Summary

```python
# Generate comprehensive summary
summary = validator.generate_validation_summary(reports)

print(f"📊 Validation Summary:")
print(f"   Total Documents: {summary['total_documents']}")
print(f"   Valid Documents: {summary['valid_documents']}")
print(f"   Invalid Documents: {summary['invalid_documents']}")
print(f"   Total Issues: {summary['total_issues']}")
print(f"   Average Processing Time: {summary['average_processing_time']:.2f}s")

# Detailed breakdown
print(f"\n📈 Results Breakdown:")
for result_type, count in summary['validation_results'].items():
    print(f"   {result_type}: {count}")

print(f"\n🔍 Issue Types:")
for issue_type, count in summary['issue_types'].items():
    print(f"   {issue_type}: {count}")
```

## 📄 Reporting and Export

### JSON Export

```python
# Export detailed validation report
validator.export_validation_report(
    reports=reports,
    output_path=Path("validation_report.json"),
    format="json"
)

# The JSON report includes:
# - Complete validation results
# - Detailed issue analysis
# - Processing statistics
# - Recommendations for each issue
```

### CSV Export

```python
# Export summary for spreadsheet analysis
validator.export_validation_report(
    reports=reports,
    output_path=Path("validation_summary.csv"),
    format="csv"
)

# CSV includes key metrics:
# - Document ID, Result, Hashes
# - Signature/Audit validity
# - Issue counts, Processing time
```

### Custom Reporting

```python
# Create custom reports
def create_compliance_report(reports):
    compliant_docs = []
    non_compliant_docs = []
    
    for report in reports:
        if (report.overall_result == ValidationResult.VALID and 
            report.signature_valid and 
            report.audit_trail_valid):
            compliant_docs.append(report.document_id)
        else:
            non_compliant_docs.append({
                'document_id': report.document_id,
                'issues': [issue.message for issue in report.issues if issue.severity == 'error']
            })
    
    return {
        'compliant_documents': compliant_docs,
        'non_compliant_documents': non_compliant_docs,
        'compliance_rate': len(compliant_docs) / len(reports) * 100
    }

compliance_report = create_compliance_report(reports)
print(f"Compliance Rate: {compliance_report['compliance_rate']:.1f}%")
```

## 🖥️ Command Line Interface

### Basic Validation

```bash
# Validate single document
python -c "
from gopnik.utils.integrity_validator import validate_document_cli
exit_code = validate_document_cli('document.pdf', verbose=True)
"

# Exit codes:
# 0 = Valid document
# 1 = Validation failed
# 2 = Error occurred
```

### Advanced CLI Usage

```bash
# Validation with expected hash
python -c "
from gopnik.utils.integrity_validator import validate_document_cli
validate_document_cli(
    document_path='document.pdf',
    expected_hash='abc123def456...',
    output_path='validation_report.json',
    verbose=True
)
"
```

### Batch CLI Validation

```bash
# Create batch validation script
cat > validate_batch.py << 'EOF'
from gopnik.utils import IntegrityValidator
from pathlib import Path
import sys

validator = IntegrityValidator()
reports = validator.validate_batch_documents(
    document_dir=Path(sys.argv[1]),
    audit_dir=Path(sys.argv[2]) if len(sys.argv) > 2 else None
)

# Export results
validator.export_validation_report(
    reports, 
    Path("batch_validation_report.json")
)

# Print summary
summary = validator.generate_validation_summary(reports)
print(f"Validated {summary['total_documents']} documents")
print(f"Valid: {summary['valid_documents']}")
print(f"Invalid: {summary['invalid_documents']}")
print(f"Issues: {summary['total_issues']}")
EOF

# Run batch validation
python validate_batch.py ./documents ./audit_logs
```

## 🚨 Common Validation Issues

### Hash Mismatch

**Issue**: Document hash doesn't match expected value
```
❌ Document hash mismatch
Expected: abc123def456789...
Actual:   def456abc123789...
```

**Causes**:
- Document modified after processing
- File corruption during transfer
- Incorrect expected hash value

**Resolution**:
1. Verify document source and transfer integrity
2. Check audit logs for processing history
3. Re-process document if necessary

### Invalid Signature

**Issue**: Cryptographic signature validation fails
```
❌ Audit log cryptographic signature is invalid
Audit Log ID: audit_123456
```

**Causes**:
- Audit log tampered with
- Wrong verification key
- Signature corruption

**Resolution**:
1. Verify cryptographic keys are correct
2. Check audit log integrity
3. Investigate potential tampering

### Broken Audit Trail

**Issue**: Audit trail has missing or inconsistent entries
```
⚠️ Missing parent logs in chain: chain_789
❌ Audit log missing required ID field
```

**Causes**:
- Incomplete audit logging
- Database corruption
- Missing audit entries

**Resolution**:
1. Check audit database integrity
2. Verify audit logging configuration
3. Restore from backup if necessary

### Missing Data

**Issue**: Required validation data is missing
```
❌ Document file not found: /path/to/document.pdf
❌ Audit log missing timestamp
```

**Causes**:
- File system issues
- Incomplete processing
- Configuration problems

**Resolution**:
1. Verify file paths and permissions
2. Check processing completion
3. Review system configuration

## 🔧 Advanced Configuration

### Custom Validation Rules

```python
class CustomIntegrityValidator(IntegrityValidator):
    def _validate_custom_requirements(self, document_path, audit_log, report):
        """Add custom validation rules"""
        
        # Example: Require specific file extensions
        if document_path.suffix.lower() not in ['.pdf', '.docx']:
            report.add_issue(
                'unsupported_format',
                'error',
                f'Unsupported file format: {document_path.suffix}',
                recommendation='Convert to supported format'
            )
        
        # Example: Require minimum processing time
        if audit_log and audit_log.processing_time and audit_log.processing_time < 1.0:
            report.add_issue(
                'suspicious_processing_time',
                'warning',
                f'Processing time unusually short: {audit_log.processing_time}s',
                recommendation='Verify processing completed properly'
            )

# Use custom validator
custom_validator = CustomIntegrityValidator()
```

### Performance Tuning

```python
# Optimize for large-scale validation
import concurrent.futures
from pathlib import Path

def validate_document_parallel(document_paths, max_workers=4):
    validator = IntegrityValidator()
    reports = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit validation tasks
        future_to_path = {
            executor.submit(validator.validate_document_integrity, path): path 
            for path in document_paths
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                report = future.result()
                reports.append(report)
            except Exception as e:
                print(f"Validation failed for {path}: {e}")
    
    return reports

# Parallel validation
document_paths = list(Path("./documents").glob("*.pdf"))
reports = validate_document_parallel(document_paths, max_workers=8)
```

## 📋 Compliance and Legal Considerations

### Regulatory Requirements

Different industries have specific validation requirements:

**Healthcare (HIPAA)**:
- Complete audit trails required
- Cryptographic signatures mandatory
- Long-term retention (6+ years)

**Financial (SOX)**:
- Document integrity verification
- Non-repudiation through signatures
- Detailed audit logging

**Legal (eDiscovery)**:
- Chain of custody documentation
- Forensic-grade validation
- Tamper-evident storage

### Implementation Example

```python
def hipaa_compliant_validation(document_path, audit_log_path):
    """HIPAA-compliant document validation"""
    validator = IntegrityValidator()
    
    report = validator.validate_document_integrity(
        document_path=document_path,
        audit_log_path=audit_log_path
    )
    
    # HIPAA-specific checks
    compliance_issues = []
    
    if not report.signature_valid:
        compliance_issues.append("HIPAA requires cryptographic signatures")
    
    if not report.audit_trail_valid:
        compliance_issues.append("HIPAA requires complete audit trails")
    
    # Check retention requirements
    if report.validation_timestamp:
        age_days = (datetime.now(timezone.utc) - report.validation_timestamp).days
        if age_days > 2555:  # 7 years
            compliance_issues.append("Document exceeds HIPAA retention period")
    
    return {
        'validation_report': report,
        'hipaa_compliant': len(compliance_issues) == 0,
        'compliance_issues': compliance_issues
    }
```

## 🔗 Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
from gopnik.utils import IntegrityValidator

app = Flask(__name__)
validator = IntegrityValidator()

@app.route('/validate', methods=['POST'])
def validate_document():
    file_path = request.json.get('file_path')
    expected_hash = request.json.get('expected_hash')
    
    report = validator.validate_document_integrity(
        document_path=Path(file_path),
        expected_hash=expected_hash
    )
    
    return jsonify({
        'valid': report.overall_result == ValidationResult.VALID,
        'result': report.overall_result.value,
        'issues': len(report.issues),
        'signature_valid': report.signature_valid,
        'processing_time': report.processing_time
    })
```

### Automated Monitoring

```python
import schedule
import time
from pathlib import Path

def daily_validation_check():
    """Daily automated validation of processed documents"""
    validator = IntegrityValidator()
    
    # Validate documents processed in last 24 hours
    document_dir = Path("./processed_documents")
    reports = validator.validate_batch_documents(document_dir)
    
    # Check for issues
    failed_validations = [r for r in reports if r.overall_result != ValidationResult.VALID]
    
    if failed_validations:
        # Send alert (email, Slack, etc.)
        send_validation_alert(failed_validations)
    
    # Export daily report
    validator.export_validation_report(
        reports,
        Path(f"daily_validation_{datetime.now().strftime('%Y%m%d')}.json")
    )

# Schedule daily validation
schedule.every().day.at("02:00").do(daily_validation_check)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## 📞 Support and Troubleshooting

### Common Issues

1. **Performance**: Use batch validation and parallel processing
2. **Memory usage**: Process documents in smaller batches
3. **Key management**: Ensure proper key storage and access
4. **Database issues**: Regular database maintenance and backups

### Getting Help

- **Documentation**: Check the official documentation
- **GitHub Issues**: Report bugs and request features
- **Community**: Join discussions for help and tips
- **Security Issues**: Use GitHub Security Advisories

---

**🔍 Integrity validation is crucial for maintaining trust in document processing systems. Always validate your documents and maintain comprehensive audit trails.**