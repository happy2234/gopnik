# Audit Trail Analysis

Gopnik provides comprehensive audit trail capabilities for tracking all document processing activities, ensuring compliance, and enabling forensic analysis. This guide covers the complete audit system from logging to analysis.

## 📊 Overview

The audit system in Gopnik captures:

- **Document Operations**: Upload, processing, redaction, download
- **User Activities**: Authentication, authorization, actions
- **System Events**: Startup, shutdown, errors, warnings
- **Processing Metrics**: Performance, memory usage, timing
- **Security Events**: Signature validation, integrity checks

## 🔍 Audit Log Structure

### Core Audit Log Fields

Every audit log entry contains comprehensive information:

```python
from gopnik.models.audit import AuditLog, AuditOperation, AuditLevel

# Example audit log structure
audit_log = AuditLog(
    id="unique_audit_id",                    # Unique identifier
    operation=AuditOperation.DOCUMENT_REDACTION,  # Operation type
    timestamp=datetime.now(timezone.utc),    # UTC timestamp
    level=AuditLevel.INFO,                   # Severity level
    
    # Document context
    document_id="doc_123",                   # Document identifier
    user_id="user_456",                      # User performing action
    session_id="session_789",                # Session identifier
    
    # Processing details
    profile_name="healthcare_hipaa",         # Redaction profile used
    detections_summary={"ssn": 3, "email": 1},  # PII detections found
    input_hash="abc123...",                  # Original document hash
    output_hash="def456...",                 # Processed document hash
    
    # Performance metrics
    processing_time=2.5,                     # Processing time in seconds
    memory_usage=128.5,                      # Peak memory usage in MB
    
    # Error handling
    error_message=None,                      # Error message if failed
    warning_messages=[],                     # List of warnings
    
    # Security
    signature="cryptographic_signature",     # Digital signature
    
    # System context
    system_info=SystemInfo(),                # System information
    
    # Audit chain
    chain_id="chain_abc",                    # Audit chain identifier
    parent_id="parent_log_id"                # Parent audit log ID
)
```

### Operation Types

The system tracks various operation types:

```python
# Document operations
AuditOperation.DOCUMENT_UPLOAD
AuditOperation.DOCUMENT_DOWNLOAD
AuditOperation.PII_DETECTION
AuditOperation.DOCUMENT_REDACTION

# Profile operations
AuditOperation.PROFILE_CREATION
AuditOperation.PROFILE_MODIFICATION

# System operations
AuditOperation.SYSTEM_STARTUP
AuditOperation.SYSTEM_SHUTDOWN
AuditOperation.USER_LOGIN
AuditOperation.USER_LOGOUT

# Processing operations
AuditOperation.BATCH_PROCESSING
AuditOperation.INTEGRITY_VALIDATION
AuditOperation.ERROR_OCCURRED
```

## 🗄️ Audit Logging System

### Setting Up Audit Logging

```python
from gopnik.utils import AuditLogger
from pathlib import Path

# Initialize audit logger with comprehensive settings
audit_logger = AuditLogger(
    storage_path=Path("./audit_logs"),       # Storage location
    enable_signing=True,                     # Enable cryptographic signing
    auto_sign=True,                          # Automatically sign logs
    max_logs_per_file=10000,                # Log rotation threshold
    retention_days=2555                      # 7 years retention (compliance)
)
```

### Creating Audit Trails

```python
# Create audit trail for document processing workflow
trail = audit_logger.create_audit_trail(
    name="Document Processing - Batch 2024-001",
    metadata={
        "batch_id": "batch_2024_001",
        "processing_profile": "healthcare_hipaa",
        "user_department": "medical_records"
    }
)

print(f"Created audit trail: {trail.id}")
```

### Logging Operations

```python
# Log document upload
upload_log = audit_logger.log_document_operation(
    operation=AuditOperation.DOCUMENT_UPLOAD,
    document_id="patient_record_123",
    user_id="dr_smith",
    profile_name="healthcare_hipaa",
    input_hash="original_document_hash",
    file_paths=["/uploads/patient_record_123.pdf"]
)

# Log PII detection
detection_log = audit_logger.log_document_operation(
    operation=AuditOperation.PII_DETECTION,
    document_id="patient_record_123",
    user_id="dr_smith",
    profile_name="healthcare_hipaa",
    detections_summary={"ssn": 2, "phone": 1, "email": 1},
    processing_time=1.5,
    memory_usage=64.2
)

# Log redaction
redaction_log = audit_logger.log_document_operation(
    operation=AuditOperation.DOCUMENT_REDACTION,
    document_id="patient_record_123",
    user_id="dr_smith",
    profile_name="healthcare_hipaa",
    input_hash="original_document_hash",
    output_hash="redacted_document_hash",
    processing_time=3.2,
    memory_usage=128.5
)

# Log errors
error_log = audit_logger.log_error(
    error_message="Failed to process document: Invalid PDF format",
    document_id="corrupted_doc_456",
    user_id="dr_smith",
    details={"error_code": "PDF_INVALID", "file_size": 0}
)
```

## 🔍 Querying Audit Logs

### Basic Queries

```python
# Query by operation type
upload_logs = audit_logger.query_logs(
    operation=AuditOperation.DOCUMENT_UPLOAD,
    limit=100
)

# Query by user
user_logs = audit_logger.query_logs(
    user_id="dr_smith",
    start_time=datetime.now() - timedelta(days=7)
)

# Query by document
document_logs = audit_logger.query_logs(
    document_id="patient_record_123"
)

# Query errors and warnings
error_logs = audit_logger.query_logs(
    level=AuditLevel.ERROR,
    start_time=datetime.now() - timedelta(hours=24)
)
```

### Advanced Queries

```python
# Complex query with multiple filters
recent_redactions = audit_logger.query_logs(
    operation=AuditOperation.DOCUMENT_REDACTION,
    level=AuditLevel.INFO,
    start_time=datetime.now() - timedelta(days=30),
    end_time=datetime.now(),
    limit=1000
)

# Analyze processing performance
slow_operations = [
    log for log in recent_redactions 
    if log.processing_time and log.processing_time > 10.0
]

print(f"Found {len(slow_operations)} slow operations")
for log in slow_operations:
    print(f"Document {log.document_id}: {log.processing_time}s")
```

### Audit Trail Retrieval

```python
# Get complete audit trail
trail = audit_logger.get_audit_trail("trail_id_here")

print(f"Trail: {trail.name}")
print(f"Created: {trail.created_at}")
print(f"Total logs: {len(trail.logs)}")

# Analyze trail statistics
stats = trail.get_statistics()
print(f"Operations: {stats['operations']}")
print(f"Error count: {stats['error_count']}")
print(f"Timespan: {stats['timespan']}")
```

## 📈 Audit Analysis and Reporting

### Statistical Analysis

```python
# Get comprehensive audit statistics
stats = audit_logger.get_statistics()

print(f"📊 Audit Statistics:")
print(f"Total logs: {stats['total_logs']}")
print(f"Recent activity (24h): {stats['recent_logs_24h']}")
print(f"Error logs: {stats['error_logs']}")
print(f"Signed logs: {stats['signed_logs']}")
print(f"Database size: {stats['database_size_mb']:.1f} MB")

# Operation breakdown
print(f"\n🔄 Operations:")
for operation, count in stats['operations'].items():
    print(f"  {operation}: {count}")

# Level breakdown
print(f"\n📊 Levels:")
for level, count in stats['levels'].items():
    print(f"  {level}: {count}")
```

### Performance Analysis

```python
def analyze_processing_performance(audit_logger, days=30):
    """Analyze processing performance over time"""
    
    # Get recent processing logs
    start_time = datetime.now(timezone.utc) - timedelta(days=days)
    processing_logs = audit_logger.query_logs(
        operation=AuditOperation.DOCUMENT_REDACTION,
        start_time=start_time
    )
    
    # Calculate metrics
    processing_times = [log.processing_time for log in processing_logs if log.processing_time]
    memory_usage = [log.memory_usage for log in processing_logs if log.memory_usage]
    
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        print(f"📈 Processing Performance ({days} days):")
        print(f"  Documents processed: {len(processing_logs)}")
        print(f"  Average time: {avg_time:.2f}s")
        print(f"  Max time: {max_time:.2f}s")
        print(f"  Min time: {min_time:.2f}s")
    
    if memory_usage:
        avg_memory = sum(memory_usage) / len(memory_usage)
        max_memory = max(memory_usage)
        
        print(f"  Average memory: {avg_memory:.1f} MB")
        print(f"  Peak memory: {max_memory:.1f} MB")
    
    return {
        'total_documents': len(processing_logs),
        'avg_processing_time': avg_time if processing_times else 0,
        'avg_memory_usage': avg_memory if memory_usage else 0
    }

# Run performance analysis
performance = analyze_processing_performance(audit_logger)
```

### Security Analysis

```python
def analyze_security_events(audit_logger, days=7):
    """Analyze security-related events"""
    
    start_time = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get validation events
    validation_logs = audit_logger.query_logs(
        operation=AuditOperation.INTEGRITY_VALIDATION,
        start_time=start_time
    )
    
    # Get error events
    error_logs = audit_logger.query_logs(
        level=AuditLevel.ERROR,
        start_time=start_time
    )
    
    # Analyze signature validation
    total_validations, valid_signatures, issues = audit_logger.validate_all_logs()
    
    print(f"🔒 Security Analysis ({days} days):")
    print(f"  Integrity validations: {len(validation_logs)}")
    print(f"  Error events: {len(error_logs)}")
    print(f"  Signature validation: {valid_signatures}/{total_validations} valid")
    
    if issues:
        print(f"  ⚠️ Signature issues found: {len(issues)}")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"    - {issue}")
    
    return {
        'validation_events': len(validation_logs),
        'error_events': len(error_logs),
        'signature_validity_rate': valid_signatures / total_validations if total_validations > 0 else 0
    }

# Run security analysis
security = analyze_security_events(audit_logger)
```

## 📤 Export and Reporting

### JSON Export

```python
# Export audit logs to JSON
count = audit_logger.export_logs_to_json(
    output_path=Path("audit_export.json"),
    operation=AuditOperation.DOCUMENT_REDACTION,
    start_time=datetime.now() - timedelta(days=30)
)

print(f"Exported {count} audit logs to JSON")
```

### CSV Export

```python
# Export to CSV for spreadsheet analysis
count = audit_logger.export_logs_to_csv(
    output_path=Path("audit_summary.csv"),
    start_time=datetime.now() - timedelta(days=7)
)

print(f"Exported {count} audit logs to CSV")
```

### Custom Reports

```python
def generate_compliance_report(audit_logger, start_date, end_date):
    """Generate compliance report for audit period"""
    
    # Query all logs in period
    logs = audit_logger.query_logs(
        start_time=start_date,
        end_time=end_date
    )
    
    # Categorize by operation
    operations = {}
    for log in logs:
        op = log.operation.value
        operations[op] = operations.get(op, 0) + 1
    
    # Check for required operations
    required_ops = [
        'document_upload', 'pii_detection', 
        'document_redaction', 'integrity_validation'
    ]
    
    compliance_score = sum(1 for op in required_ops if op in operations) / len(required_ops)
    
    # Generate report
    report = {
        'period': f"{start_date.date()} to {end_date.date()}",
        'total_operations': len(logs),
        'operation_breakdown': operations,
        'compliance_score': compliance_score,
        'signed_logs': len([log for log in logs if log.is_signed()]),
        'error_rate': len([log for log in logs if log.is_error()]) / len(logs) if logs else 0
    }
    
    return report

# Generate monthly compliance report
start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
end_date = datetime.now()
compliance_report = generate_compliance_report(audit_logger, start_date, end_date)

print(f"📋 Compliance Report:")
print(f"Period: {compliance_report['period']}")
print(f"Compliance Score: {compliance_report['compliance_score']:.1%}")
print(f"Total Operations: {compliance_report['total_operations']}")
print(f"Signed Logs: {compliance_report['signed_logs']}")
print(f"Error Rate: {compliance_report['error_rate']:.2%}")
```

## 🔧 Audit Trail Maintenance

### Log Cleanup

```python
# Clean up old audit logs (respecting retention policy)
deleted_count = audit_logger.cleanup_old_logs(retention_days=365)
print(f"Cleaned up {deleted_count} old audit logs")

# Custom cleanup with specific criteria
from datetime import datetime, timezone, timedelta

cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
old_error_logs = audit_logger.query_logs(
    level=AuditLevel.ERROR,
    end_time=cutoff_date
)

print(f"Found {len(old_error_logs)} old error logs for review")
```

### Database Maintenance

```python
# Get database statistics
stats = audit_logger.get_statistics()
db_size_mb = stats['database_size_mb']

if db_size_mb > 1000:  # 1GB threshold
    print(f"⚠️ Large audit database: {db_size_mb:.1f} MB")
    print("Consider archiving old logs or increasing cleanup frequency")

# Validate audit log integrity
total, valid, issues = audit_logger.validate_all_logs()
if issues:
    print(f"⚠️ Found {len(issues)} audit integrity issues:")
    for issue in issues[:10]:  # Show first 10
        print(f"  - {issue}")
```

### Backup and Archival

```python
def backup_audit_logs(audit_logger, backup_path):
    """Create backup of audit logs"""
    
    # Export all logs
    all_logs = audit_logger.query_logs()
    
    # Create backup with metadata
    backup_data = {
        'backup_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_logs': len(all_logs),
        'logs': [log.to_dict() for log in all_logs],
        'statistics': audit_logger.get_statistics()
    }
    
    # Write backup file
    with open(backup_path, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)
    
    print(f"Backed up {len(all_logs)} audit logs to {backup_path}")
    return backup_data

# Create monthly backup
backup_path = Path(f"audit_backup_{datetime.now().strftime('%Y%m')}.json")
backup_data = backup_audit_logs(audit_logger, backup_path)
```

## 🚨 Monitoring and Alerting

### Real-time Monitoring

```python
def monitor_audit_events(audit_logger, check_interval=300):
    """Monitor audit events for anomalies"""
    
    last_check = datetime.now(timezone.utc) - timedelta(seconds=check_interval)
    
    while True:
        current_time = datetime.now(timezone.utc)
        
        # Check for recent errors
        recent_errors = audit_logger.query_logs(
            level=AuditLevel.ERROR,
            start_time=last_check
        )
        
        if recent_errors:
            print(f"🚨 {len(recent_errors)} new errors detected:")
            for error in recent_errors:
                print(f"  - {error.error_message} (Doc: {error.document_id})")
        
        # Check for signature validation failures
        recent_validations = audit_logger.query_logs(
            operation=AuditOperation.INTEGRITY_VALIDATION,
            start_time=last_check
        )
        
        failed_validations = [
            log for log in recent_validations 
            if log.level == AuditLevel.ERROR
        ]
        
        if failed_validations:
            print(f"🔒 {len(failed_validations)} validation failures detected")
        
        last_check = current_time
        time.sleep(check_interval)

# Start monitoring (run in background)
import threading
monitor_thread = threading.Thread(
    target=monitor_audit_events, 
    args=(audit_logger, 300),  # Check every 5 minutes
    daemon=True
)
monitor_thread.start()
```

### Automated Alerts

```python
def setup_audit_alerts(audit_logger):
    """Setup automated alerts for audit events"""
    
    def check_error_threshold():
        """Alert if error rate exceeds threshold"""
        recent_logs = audit_logger.query_logs(
            start_time=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        if recent_logs:
            error_rate = len([log for log in recent_logs if log.is_error()]) / len(recent_logs)
            
            if error_rate > 0.1:  # 10% error rate threshold
                send_alert(f"High error rate detected: {error_rate:.1%}")
    
    def check_signature_failures():
        """Alert on signature validation failures"""
        total, valid, issues = audit_logger.validate_all_logs()
        
        if issues:
            send_alert(f"Signature validation issues: {len(issues)} problems detected")
    
    def send_alert(message):
        """Send alert (implement your preferred method)"""
        print(f"🚨 ALERT: {message}")
        # Implement: email, Slack, SMS, etc.
    
    # Schedule checks
    import schedule
    schedule.every(15).minutes.do(check_error_threshold)
    schedule.every().hour.do(check_signature_failures)
    
    return schedule

# Setup alerts
alert_schedule = setup_audit_alerts(audit_logger)
```

## 🔗 Integration Examples

### Web Dashboard Integration

```python
from flask import Flask, jsonify, request
from gopnik.utils import AuditLogger

app = Flask(__name__)
audit_logger = AuditLogger()

@app.route('/api/audit/stats')
def get_audit_stats():
    """Get audit statistics for dashboard"""
    stats = audit_logger.get_statistics()
    return jsonify(stats)

@app.route('/api/audit/recent')
def get_recent_logs():
    """Get recent audit logs"""
    hours = request.args.get('hours', 24, type=int)
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    logs = audit_logger.query_logs(start_time=start_time, limit=100)
    
    return jsonify([{
        'id': log.id,
        'operation': log.operation.value,
        'timestamp': log.timestamp.isoformat(),
        'level': log.level.value,
        'document_id': log.document_id,
        'user_id': log.user_id,
        'processing_time': log.processing_time
    } for log in logs])

@app.route('/api/audit/search')
def search_logs():
    """Search audit logs"""
    query_params = {
        'operation': request.args.get('operation'),
        'user_id': request.args.get('user_id'),
        'document_id': request.args.get('document_id'),
        'level': request.args.get('level'),
        'limit': request.args.get('limit', 100, type=int)
    }
    
    # Remove None values
    query_params = {k: v for k, v in query_params.items() if v is not None}
    
    logs = audit_logger.query_logs(**query_params)
    
    return jsonify([log.to_dict() for log in logs])
```

### Compliance Reporting Integration

```python
def generate_sox_compliance_report(audit_logger, quarter_start, quarter_end):
    """Generate SOX compliance report"""
    
    logs = audit_logger.query_logs(
        start_time=quarter_start,
        end_time=quarter_end
    )
    
    # SOX requirements analysis
    document_operations = [log for log in logs if log.document_id]
    signed_operations = [log for log in document_operations if log.is_signed()]
    
    compliance_metrics = {
        'reporting_period': f"Q{quarter_start.month//3 + 1} {quarter_start.year}",
        'total_document_operations': len(document_operations),
        'signed_operations': len(signed_operations),
        'signature_compliance_rate': len(signed_operations) / len(document_operations) if document_operations else 0,
        'audit_trail_completeness': calculate_trail_completeness(logs),
        'control_effectiveness': assess_control_effectiveness(logs)
    }
    
    return compliance_metrics

def calculate_trail_completeness(logs):
    """Calculate audit trail completeness score"""
    # Check for complete document processing chains
    document_chains = {}
    
    for log in logs:
        if log.document_id:
            if log.document_id not in document_chains:
                document_chains[log.document_id] = []
            document_chains[log.document_id].append(log.operation)
    
    complete_chains = 0
    required_operations = {
        AuditOperation.DOCUMENT_UPLOAD,
        AuditOperation.PII_DETECTION,
        AuditOperation.DOCUMENT_REDACTION
    }
    
    for doc_id, operations in document_chains.items():
        if required_operations.issubset(set(operations)):
            complete_chains += 1
    
    return complete_chains / len(document_chains) if document_chains else 0
```

## 📞 Support and Best Practices

### Best Practices

1. **Comprehensive Logging**: Log all significant operations
2. **Cryptographic Signing**: Always enable signing for audit logs
3. **Regular Validation**: Periodically validate audit log integrity
4. **Retention Policies**: Implement appropriate retention policies
5. **Monitoring**: Set up real-time monitoring and alerting
6. **Backup**: Regular backup of audit data
7. **Access Control**: Restrict access to audit logs
8. **Performance**: Monitor audit system performance

### Troubleshooting

**Common Issues**:
- Database performance degradation
- Signature validation failures
- Missing audit entries
- Storage space issues

**Solutions**:
- Regular database maintenance
- Key rotation and management
- Audit configuration review
- Storage monitoring and cleanup

### Getting Help

- **Documentation**: Official Gopnik documentation
- **GitHub Issues**: Report bugs and request features
- **Community**: Join discussions for help and tips
- **Security**: Use GitHub Security Advisories for security issues

---

**📊 Comprehensive audit trails are essential for compliance, security, and operational excellence. Always maintain complete and accurate audit records.**