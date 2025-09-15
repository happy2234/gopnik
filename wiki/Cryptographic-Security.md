# Cryptographic Security in Gopnik

Gopnik provides enterprise-grade cryptographic security features for document integrity, audit trail protection, and forensic validation. This guide covers the comprehensive security capabilities implemented in the system.

## 🔐 Overview

The cryptographic security system in Gopnik includes:

- **Document Integrity**: SHA-256 hashing for tamper detection
- **Digital Signatures**: RSA and ECDSA signing for authenticity
- **Audit Protection**: Cryptographically signed audit logs
- **Forensic Validation**: Comprehensive integrity verification
- **Key Management**: Secure key generation and storage

## 🛡️ Cryptographic Utilities

### Hash Generation

Gopnik uses SHA-256 for document integrity verification:

```python
from gopnik.utils import CryptographicUtils

crypto = CryptographicUtils()

# Hash a file
file_hash = crypto.generate_sha256_hash(Path("document.pdf"))
print(f"Document hash: {file_hash}")

# Hash bytes directly
content_hash = crypto.generate_sha256_hash_from_bytes(b"document content")
print(f"Content hash: {content_hash}")
```

### Digital Signatures

#### RSA Signatures

```python
# Generate RSA key pair
private_pem, public_pem = crypto.generate_rsa_key_pair(key_size=2048)

# Sign data
signature = crypto.sign_data_rsa("Important document content")
print(f"RSA Signature: {signature}")

# Verify signature
is_valid = crypto.verify_signature_rsa("Important document content", signature)
print(f"Signature valid: {is_valid}")
```

#### ECDSA Signatures

```python
# Generate ECDSA key pair (SECP256R1)
private_pem, public_pem = crypto.generate_ec_key_pair()

# Sign data
signature = crypto.sign_data_ecdsa("Document content")
print(f"ECDSA Signature: {signature}")

# Verify signature
is_valid = crypto.verify_signature_ecdsa("Document content", signature)
print(f"Signature valid: {is_valid}")
```

### Key Management

```python
# Load existing keys
crypto.load_rsa_private_key(private_key_pem)
crypto.load_rsa_public_key(public_key_pem)

# Generate secure random IDs
audit_id = crypto.generate_secure_id()
random_bytes = crypto.generate_secure_bytes(32)
```

## 📊 Audit System Security

### Signed Audit Logs

The audit system automatically signs all audit entries when enabled:

```python
from gopnik.utils import AuditLogger

# Initialize with signing enabled
audit_logger = AuditLogger(
    storage_path=Path("./audit_logs"),
    enable_signing=True,
    auto_sign=True
)

# Log operations (automatically signed)
audit_log = audit_logger.log_document_operation(
    operation=AuditOperation.DOCUMENT_REDACTION,
    document_id="sensitive_doc_123",
    user_id="user_456",
    profile_name="healthcare_hipaa"
)

print(f"Audit log signed: {audit_log.is_signed()}")
```

### Audit Trail Verification

```python
# Verify all audit logs
total, valid, issues = audit_logger.validate_all_logs()
print(f"Validated {total} logs: {valid} valid, {len(issues)} issues")

# Verify specific audit log
is_valid = audit_logger.verify_audit_log(audit_log)
print(f"Audit log valid: {is_valid}")
```

## 🔍 Integrity Validation

### Document Validation

The integrity validator provides forensic-grade document verification:

```python
from gopnik.utils import IntegrityValidator, ValidationResult

validator = IntegrityValidator()

# Validate document integrity
report = validator.validate_document_integrity(
    document_path=Path("processed_document.pdf"),
    expected_hash="abc123...",
    audit_log_path=Path("document_audit.json")
)

print(f"Validation result: {report.overall_result}")
print(f"Document hash: {report.document_hash}")
print(f"Signature valid: {report.signature_valid}")
print(f"Issues found: {len(report.issues)}")
```

### Batch Validation

```python
# Validate multiple documents
reports = validator.validate_batch_documents(
    document_dir=Path("./processed_documents"),
    audit_dir=Path("./audit_logs"),
    file_pattern="*.pdf"
)

# Generate summary
summary = validator.generate_validation_summary(reports)
print(f"Total documents: {summary['total_documents']}")
print(f"Valid documents: {summary['valid_documents']}")
print(f"Issues found: {summary['total_issues']}")
```

### Validation Reporting

```python
# Export detailed report
validator.export_validation_report(
    reports=reports,
    output_path=Path("validation_report.json"),
    format="json"
)

# Export CSV summary
validator.export_validation_report(
    reports=reports,
    output_path=Path("validation_summary.csv"),
    format="csv"
)
```

## 🖥️ CLI Integration

### Document Validation Command

```bash
# Basic validation
python -m gopnik.utils.integrity_validator validate document.pdf

# Validation with expected hash
python -m gopnik.utils.integrity_validator validate document.pdf \
    --expected-hash abc123def456... \
    --verbose

# Validation with audit log
python -m gopnik.utils.integrity_validator validate document.pdf \
    --audit-log document_audit.json \
    --output-report validation_report.json
```

### Batch Validation

```bash
# Validate all documents in directory
python -m gopnik.utils.integrity_validator validate-batch \
    --document-dir ./processed_documents \
    --audit-dir ./audit_logs \
    --output-report batch_validation.json
```

## 🔧 Configuration

### Security Settings

Configure cryptographic settings in your application:

```python
# High-security configuration
crypto = CryptographicUtils()
audit_logger = AuditLogger(
    storage_path=Path("./secure_audit"),
    enable_signing=True,
    auto_sign=True,
    retention_days=2555  # 7 years for compliance
)

validator = IntegrityValidator(
    crypto_utils=crypto,
    audit_logger=audit_logger
)
```

### Key Storage

Keys are automatically generated and stored securely:

```
audit_logs/
├── signing_keys/
│   ├── private_key.pem  (600 permissions)
│   └── public_key.pem   (644 permissions)
├── audit_logs.db
└── audit_trails/
```

## 🛡️ Security Best Practices

### 1. Key Management
- **Rotate keys regularly**: Generate new signing keys periodically
- **Secure storage**: Protect private keys with appropriate file permissions
- **Backup keys**: Maintain secure backups of cryptographic keys
- **Access control**: Limit access to signing keys

### 2. Audit Trail Protection
- **Enable signing**: Always enable cryptographic signing for audit logs
- **Regular validation**: Periodically validate audit trail integrity
- **Secure storage**: Store audit logs in tamper-evident storage
- **Retention policies**: Implement appropriate retention policies

### 3. Document Integrity
- **Hash verification**: Always verify document hashes after processing
- **Signature validation**: Validate cryptographic signatures
- **Chain of custody**: Maintain complete audit trails
- **Regular audits**: Perform regular integrity audits

### 4. Compliance Considerations
- **Legal requirements**: Ensure compliance with relevant regulations
- **Forensic readiness**: Maintain forensic-grade audit trails
- **Evidence preservation**: Preserve cryptographic evidence
- **Documentation**: Document all security procedures

## 🚨 Security Alerts

### Hash Mismatch
```
❌ Document hash mismatch detected
Expected: abc123def456...
Actual:   def456abc123...
Recommendation: Document may have been modified or corrupted
```

### Invalid Signature
```
❌ Cryptographic signature validation failed
Audit Log ID: audit_123456
Recommendation: Audit log may have been tampered with
```

### Broken Audit Trail
```
⚠️ Audit trail integrity issues detected
Missing parent logs in chain: chain_789
Recommendation: Investigate audit log completeness
```

## 📈 Performance Considerations

### Optimization Tips

1. **Batch operations**: Use batch validation for multiple documents
2. **Key caching**: Reuse loaded cryptographic keys
3. **Parallel processing**: Process multiple documents concurrently
4. **Storage optimization**: Use appropriate database indexes

### Benchmarks

Typical performance on modern hardware:
- **SHA-256 hashing**: ~500 MB/s
- **RSA signing**: ~1000 signatures/second
- **ECDSA signing**: ~2000 signatures/second
- **Signature verification**: ~5000 verifications/second

## 🔗 Related Documentation

- **[Audit Trail Analysis](Audit-Trail-Analysis)**: Working with audit logs
- **[Integrity Validation](Integrity-Validation)**: Forensic validation guide
- **[Security Configuration](Security-Configuration)**: Security best practices
- **[Troubleshooting Guide](Troubleshooting-Guide)**: Common security issues

## 📞 Support

For security-related questions or issues:
- **Security Issues**: Report via GitHub Security Advisories
- **General Questions**: Use GitHub Discussions
- **Documentation**: Check the official documentation

---

**🔒 Security is paramount in document processing. Always follow best practices and keep your cryptographic systems up to date.**