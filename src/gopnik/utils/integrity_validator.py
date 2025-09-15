"""
Document integrity validation system for Gopnik deidentification toolkit.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .crypto import CryptographicUtils
from .audit_logger import AuditLogger
from ..models.audit import AuditLog, AuditOperation, AuditLevel


class ValidationResult(Enum):
    """Validation result status."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING_DATA = "missing_data"
    CORRUPTED = "corrupted"
    SIGNATURE_MISMATCH = "signature_mismatch"
    HASH_MISMATCH = "hash_mismatch"
    AUDIT_TRAIL_BROKEN = "audit_trail_broken"


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found during integrity checking.
    
    Attributes:
        type: Type of validation issue
        severity: Severity level (error, warning, info)
        message: Human-readable description
        details: Additional technical details
        affected_component: Component that has the issue
        recommendation: Suggested action to resolve
    """
    type: str
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_component: Optional[str] = None
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'type': self.type,
            'severity': self.severity,
            'message': self.message,
            'details': self.details,
            'affected_component': self.affected_component,
            'recommendation': self.recommendation
        }


@dataclass
class IntegrityReport:
    """
    Comprehensive integrity validation report.
    
    Attributes:
        document_id: ID of validated document
        validation_timestamp: When validation was performed
        overall_result: Overall validation result
        document_hash: Current document hash
        expected_hash: Expected document hash from audit
        signature_valid: Whether cryptographic signature is valid
        audit_trail_valid: Whether audit trail is intact
        issues: List of validation issues found
        metadata: Additional validation metadata
        processing_time: Time taken for validation
    """
    document_id: str
    validation_timestamp: datetime
    overall_result: ValidationResult
    document_hash: Optional[str] = None
    expected_hash: Optional[str] = None
    signature_valid: Optional[bool] = None
    audit_trail_valid: Optional[bool] = None
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: Optional[float] = None
    
    def add_issue(
        self,
        issue_type: str,
        severity: str,
        message: str,
        **kwargs
    ) -> None:
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            type=issue_type,
            severity=severity,
            message=message,
            **kwargs
        )
        self.issues.append(issue)
    
    def has_errors(self) -> bool:
        """Check if report contains any error-level issues."""
        return any(issue.severity == 'error' for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if report contains any warning-level issues."""
        return any(issue.severity == 'warning' for issue in self.issues)
    
    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get all issues of a specific severity level."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation report."""
        return {
            'document_id': self.document_id,
            'overall_result': self.overall_result.value,
            'total_issues': len(self.issues),
            'errors': len(self.get_issues_by_severity('error')),
            'warnings': len(self.get_issues_by_severity('warning')),
            'info': len(self.get_issues_by_severity('info')),
            'signature_valid': self.signature_valid,
            'audit_trail_valid': self.audit_trail_valid,
            'processing_time': self.processing_time
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'document_id': self.document_id,
            'validation_timestamp': self.validation_timestamp.isoformat(),
            'overall_result': self.overall_result.value,
            'document_hash': self.document_hash,
            'expected_hash': self.expected_hash,
            'signature_valid': self.signature_valid,
            'audit_trail_valid': self.audit_trail_valid,
            'issues': [issue.to_dict() for issue in self.issues],
            'metadata': self.metadata,
            'processing_time': self.processing_time,
            'summary': self.get_summary()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class IntegrityValidator:
    """
    Document integrity validation system using cryptographic hashes and audit trails.
    
    Features:
    - Document hash verification
    - Cryptographic signature validation
    - Audit trail integrity checking
    - Detailed validation reporting
    - CLI integration support
    """
    
    def __init__(
        self,
        crypto_utils: Optional[CryptographicUtils] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize integrity validator.
        
        Args:
            crypto_utils: Cryptographic utilities instance
            audit_logger: Audit logger instance
        """
        self.crypto = crypto_utils or CryptographicUtils()
        self.audit_logger = audit_logger
        self.logger = logging.getLogger(__name__)
    
    def validate_document_integrity(
        self,
        document_path: Path,
        audit_log_path: Optional[Path] = None,
        expected_hash: Optional[str] = None,
        audit_log_data: Optional[AuditLog] = None
    ) -> IntegrityReport:
        """
        Validate the integrity of a document using cryptographic verification.
        
        Args:
            document_path: Path to document to validate
            audit_log_path: Path to audit log file (JSON)
            expected_hash: Expected document hash
            audit_log_data: Audit log data object
            
        Returns:
            Comprehensive integrity validation report
        """
        start_time = datetime.now(timezone.utc)
        document_id = document_path.stem
        
        report = IntegrityReport(
            document_id=document_id,
            validation_timestamp=start_time,
            overall_result=ValidationResult.VALID
        )
        
        try:
            # Step 1: Calculate current document hash
            if not document_path.exists():
                report.add_issue(
                    'missing_document',
                    'error',
                    f"Document file not found: {document_path}",
                    affected_component='document_file',
                    recommendation='Ensure the document file exists and is accessible'
                )
                report.overall_result = ValidationResult.MISSING_DATA
                return report
            
            try:
                current_hash = self.crypto.generate_sha256_hash(document_path)
                report.document_hash = current_hash
                self.logger.debug(f"Calculated document hash: {current_hash}")
            except Exception as e:
                report.add_issue(
                    'hash_calculation_failed',
                    'error',
                    f"Failed to calculate document hash: {str(e)}",
                    details={'error': str(e)},
                    affected_component='document_file',
                    recommendation='Check file permissions and integrity'
                )
                report.overall_result = ValidationResult.CORRUPTED
                return report
            
            # Step 2: Load audit log data
            audit_log = None
            if audit_log_data:
                audit_log = audit_log_data
            elif audit_log_path and audit_log_path.exists():
                try:
                    with open(audit_log_path, 'r') as f:
                        audit_data = json.load(f)
                    audit_log = AuditLog.from_dict(audit_data)
                except Exception as e:
                    report.add_issue(
                        'audit_log_load_failed',
                        'error',
                        f"Failed to load audit log: {str(e)}",
                        details={'error': str(e), 'audit_log_path': str(audit_log_path)},
                        affected_component='audit_log',
                        recommendation='Check audit log file format and permissions'
                    )
            
            # Step 3: Validate against expected hash
            if expected_hash:
                report.expected_hash = expected_hash
                if current_hash != expected_hash:
                    report.add_issue(
                        'hash_mismatch',
                        'error',
                        f"Document hash mismatch. Expected: {expected_hash}, Got: {current_hash}",
                        details={
                            'expected_hash': expected_hash,
                            'actual_hash': current_hash
                        },
                        affected_component='document_integrity',
                        recommendation='Document may have been modified or corrupted'
                    )
                    report.overall_result = ValidationResult.HASH_MISMATCH
            elif audit_log and audit_log.output_hash:
                report.expected_hash = audit_log.output_hash
                if current_hash != audit_log.output_hash:
                    report.add_issue(
                        'hash_mismatch_audit',
                        'error',
                        f"Document hash does not match audit log. Expected: {audit_log.output_hash}, Got: {current_hash}",
                        details={
                            'expected_hash': audit_log.output_hash,
                            'actual_hash': current_hash,
                            'audit_log_id': audit_log.id
                        },
                        affected_component='document_integrity',
                        recommendation='Document may have been modified after processing'
                    )
                    report.overall_result = ValidationResult.HASH_MISMATCH
            
            # Step 4: Validate cryptographic signature
            if audit_log and audit_log.is_signed():
                try:
                    signature_valid = self._validate_audit_signature(audit_log)
                    report.signature_valid = signature_valid
                    
                    if not signature_valid:
                        report.add_issue(
                            'invalid_signature',
                            'error',
                            'Audit log cryptographic signature is invalid',
                            details={'audit_log_id': audit_log.id},
                            affected_component='audit_signature',
                            recommendation='Audit log may have been tampered with'
                        )
                        report.overall_result = ValidationResult.SIGNATURE_MISMATCH
                    else:
                        report.add_issue(
                            'signature_valid',
                            'info',
                            'Audit log cryptographic signature is valid',
                            details={'audit_log_id': audit_log.id},
                            affected_component='audit_signature'
                        )
                except Exception as e:
                    report.add_issue(
                        'signature_validation_failed',
                        'warning',
                        f"Failed to validate signature: {str(e)}",
                        details={'error': str(e)},
                        affected_component='audit_signature',
                        recommendation='Check cryptographic key availability'
                    )
            elif audit_log:
                report.add_issue(
                    'no_signature',
                    'warning',
                    'Audit log is not cryptographically signed',
                    details={'audit_log_id': audit_log.id},
                    affected_component='audit_signature',
                    recommendation='Enable signing for enhanced security'
                )
            
            # Step 5: Validate audit trail integrity
            if audit_log:
                trail_valid = self._validate_audit_trail_integrity(audit_log, report)
                report.audit_trail_valid = trail_valid
                
                if not trail_valid and report.overall_result == ValidationResult.VALID:
                    report.overall_result = ValidationResult.AUDIT_TRAIL_BROKEN
            
            # Step 6: Additional metadata validation
            self._validate_metadata(document_path, audit_log, report)
            
        except Exception as e:
            report.add_issue(
                'validation_error',
                'error',
                f"Unexpected error during validation: {str(e)}",
                details={'error': str(e)},
                recommendation='Contact system administrator'
            )
            report.overall_result = ValidationResult.INVALID
        
        finally:
            # Calculate processing time
            end_time = datetime.now(timezone.utc)
            report.processing_time = (end_time - start_time).total_seconds()
            
            # Log validation to audit system if available
            if self.audit_logger:
                self._log_validation_result(report)
        
        return report
    
    def _validate_audit_signature(self, audit_log: AuditLog) -> bool:
        """
        Validate the cryptographic signature of an audit log.
        
        Args:
            audit_log: Audit log to validate
            
        Returns:
            True if signature is valid
        """
        try:
            if not audit_log.is_signed():
                return False
            
            # Get content hash
            content_hash = audit_log.get_content_hash()
            
            # Verify signature
            return self.crypto.verify_signature_rsa(content_hash, audit_log.signature)
        except Exception as e:
            self.logger.error(f"Signature validation failed: {e}")
            return False
    
    def _validate_audit_trail_integrity(
        self,
        audit_log: AuditLog,
        report: IntegrityReport
    ) -> bool:
        """
        Validate the integrity of the audit trail.
        
        Args:
            audit_log: Primary audit log
            report: Validation report to add issues to
            
        Returns:
            True if audit trail is valid
        """
        is_valid = True
        
        # Check required fields
        if not audit_log.id:
            report.add_issue(
                'missing_audit_id',
                'error',
                'Audit log missing required ID field',
                affected_component='audit_log',
                recommendation='Regenerate audit log with proper ID'
            )
            is_valid = False
        
        if not audit_log.timestamp:
            report.add_issue(
                'missing_timestamp',
                'error',
                'Audit log missing timestamp',
                affected_component='audit_log',
                recommendation='Regenerate audit log with proper timestamp'
            )
            is_valid = False
        
        # Check timestamp is reasonable (not in future, not too old)
        if audit_log.timestamp:
            now = datetime.now(timezone.utc)
            if audit_log.timestamp > now:
                report.add_issue(
                    'future_timestamp',
                    'warning',
                    'Audit log timestamp is in the future',
                    details={
                        'audit_timestamp': audit_log.timestamp.isoformat(),
                        'current_time': now.isoformat()
                    },
                    affected_component='audit_log',
                    recommendation='Check system clock synchronization'
                )
            
            # Check if timestamp is more than 1 year old
            one_year_ago = now.replace(year=now.year - 1)
            if audit_log.timestamp < one_year_ago:
                report.add_issue(
                    'old_timestamp',
                    'info',
                    'Audit log is more than one year old',
                    details={'audit_timestamp': audit_log.timestamp.isoformat()},
                    affected_component='audit_log'
                )
        
        # Check operation type is valid
        if not audit_log.operation:
            report.add_issue(
                'missing_operation',
                'error',
                'Audit log missing operation type',
                affected_component='audit_log',
                recommendation='Regenerate audit log with proper operation type'
            )
            is_valid = False
        
        # Check document-specific requirements
        if audit_log.operation in [AuditOperation.DOCUMENT_REDACTION, AuditOperation.PII_DETECTION]:
            if not audit_log.document_id:
                report.add_issue(
                    'missing_document_id',
                    'error',
                    f'Document ID required for {audit_log.operation.value} operation',
                    affected_component='audit_log',
                    recommendation='Regenerate audit log with document ID'
                )
                is_valid = False
        
        # Check hash consistency
        if audit_log.input_hash and audit_log.output_hash:
            if audit_log.input_hash == audit_log.output_hash:
                # This might be suspicious for redaction operations
                if audit_log.operation == AuditOperation.DOCUMENT_REDACTION:
                    report.add_issue(
                        'suspicious_hash_match',
                        'warning',
                        'Input and output hashes are identical for redaction operation',
                        details={
                            'input_hash': audit_log.input_hash,
                            'output_hash': audit_log.output_hash
                        },
                        affected_component='audit_log',
                        recommendation='Verify that redaction actually occurred'
                    )
        
        return is_valid
    
    def _validate_metadata(
        self,
        document_path: Path,
        audit_log: Optional[AuditLog],
        report: IntegrityReport
    ) -> None:
        """
        Validate additional metadata and consistency checks.
        
        Args:
            document_path: Path to document
            audit_log: Audit log data
            report: Validation report to add issues to
        """
        # Check file size consistency
        try:
            file_size = document_path.stat().st_size
            report.metadata['file_size_bytes'] = file_size
            
            if file_size == 0:
                report.add_issue(
                    'empty_file',
                    'error',
                    'Document file is empty',
                    details={'file_size': file_size},
                    affected_component='document_file',
                    recommendation='Check if file was properly created'
                )
            elif file_size > 100 * 1024 * 1024:  # 100MB
                report.add_issue(
                    'large_file',
                    'info',
                    'Document file is very large',
                    details={'file_size_mb': file_size / (1024 * 1024)},
                    affected_component='document_file'
                )
        except Exception as e:
            report.add_issue(
                'file_stat_failed',
                'warning',
                f'Failed to get file statistics: {str(e)}',
                details={'error': str(e)},
                affected_component='document_file'
            )
        
        # Check file extension consistency
        file_extension = document_path.suffix.lower()
        report.metadata['file_extension'] = file_extension
        
        if audit_log and audit_log.file_paths:
            # Check if file paths in audit log match current document
            audit_paths = [Path(p) for p in audit_log.file_paths]
            if not any(p.name == document_path.name for p in audit_paths):
                report.add_issue(
                    'filename_mismatch',
                    'warning',
                    'Document filename does not match audit log file paths',
                    details={
                        'current_filename': document_path.name,
                        'audit_file_paths': audit_log.file_paths
                    },
                    affected_component='audit_log',
                    recommendation='Verify document identity'
                )
    
    def _log_validation_result(self, report: IntegrityReport) -> None:
        """
        Log validation result to audit system.
        
        Args:
            report: Validation report to log
        """
        try:
            level = AuditLevel.INFO
            if report.has_errors():
                level = AuditLevel.ERROR
            elif report.has_warnings():
                level = AuditLevel.WARNING
            
            self.audit_logger.log_operation(
                operation=AuditOperation.INTEGRITY_VALIDATION,
                level=level,
                document_id=report.document_id,
                details={
                    'validation_result': report.overall_result.value,
                    'issues_count': len(report.issues),
                    'processing_time': report.processing_time,
                    'signature_valid': report.signature_valid,
                    'audit_trail_valid': report.audit_trail_valid
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to log validation result: {e}")
    
    def validate_batch_documents(
        self,
        document_dir: Path,
        audit_dir: Optional[Path] = None,
        file_pattern: str = "*"
    ) -> List[IntegrityReport]:
        """
        Validate integrity of multiple documents in a directory.
        
        Args:
            document_dir: Directory containing documents to validate
            audit_dir: Directory containing audit logs (optional)
            file_pattern: File pattern to match (default: all files)
            
        Returns:
            List of validation reports
        """
        reports = []
        
        if not document_dir.exists():
            self.logger.error(f"Document directory does not exist: {document_dir}")
            return reports
        
        # Find all matching files
        document_files = list(document_dir.glob(file_pattern))
        self.logger.info(f"Found {len(document_files)} documents to validate")
        
        for doc_path in document_files:
            if doc_path.is_file():
                # Look for corresponding audit log
                audit_log_path = None
                if audit_dir and audit_dir.exists():
                    audit_log_path = audit_dir / f"{doc_path.stem}_audit.json"
                    if not audit_log_path.exists():
                        audit_log_path = None
                
                # Validate document
                report = self.validate_document_integrity(
                    document_path=doc_path,
                    audit_log_path=audit_log_path
                )
                reports.append(report)
                
                self.logger.info(
                    f"Validated {doc_path.name}: {report.overall_result.value} "
                    f"({len(report.issues)} issues)"
                )
        
        return reports
    
    def generate_validation_summary(
        self,
        reports: List[IntegrityReport]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics from multiple validation reports.
        
        Args:
            reports: List of validation reports
            
        Returns:
            Summary statistics dictionary
        """
        if not reports:
            return {
                'total_documents': 0,
                'valid_documents': 0,
                'invalid_documents': 0,
                'total_issues': 0,
                'validation_results': {},
                'issue_types': {},
                'average_processing_time': 0
            }
        
        # Count results by type
        result_counts = {}
        for result_type in ValidationResult:
            result_counts[result_type.value] = sum(
                1 for r in reports if r.overall_result == result_type
            )
        
        # Count issues by type
        issue_type_counts = {}
        total_issues = 0
        for report in reports:
            total_issues += len(report.issues)
            for issue in report.issues:
                issue_type_counts[issue.type] = issue_type_counts.get(issue.type, 0) + 1
        
        # Calculate processing time statistics
        processing_times = [r.processing_time for r in reports if r.processing_time]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_documents': len(reports),
            'valid_documents': result_counts.get('valid', 0),
            'invalid_documents': len(reports) - result_counts.get('valid', 0),
            'total_issues': total_issues,
            'validation_results': result_counts,
            'issue_types': issue_type_counts,
            'average_processing_time': avg_processing_time,
            'reports_with_errors': len([r for r in reports if r.has_errors()]),
            'reports_with_warnings': len([r for r in reports if r.has_warnings()]),
            'signed_documents': len([r for r in reports if r.signature_valid is True]),
            'unsigned_documents': len([r for r in reports if r.signature_valid is False])
        }
    
    def export_validation_report(
        self,
        reports: Union[IntegrityReport, List[IntegrityReport]],
        output_path: Path,
        format: str = 'json'
    ) -> None:
        """
        Export validation report(s) to file.
        
        Args:
            reports: Single report or list of reports
            output_path: Output file path
            format: Export format ('json' or 'csv')
        """
        if isinstance(reports, IntegrityReport):
            reports = [reports]
        
        if format.lower() == 'json':
            export_data = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_reports': len(reports),
                'summary': self.generate_validation_summary(reports),
                'reports': [report.to_dict() for report in reports]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = [
                    'Document ID', 'Validation Result', 'Document Hash', 'Expected Hash',
                    'Signature Valid', 'Audit Trail Valid', 'Total Issues', 'Errors',
                    'Warnings', 'Processing Time', 'Validation Timestamp'
                ]
                writer.writerow(headers)
                
                # Write data
                for report in reports:
                    writer.writerow([
                        report.document_id,
                        report.overall_result.value,
                        report.document_hash or '',
                        report.expected_hash or '',
                        report.signature_valid if report.signature_valid is not None else '',
                        report.audit_trail_valid if report.audit_trail_valid is not None else '',
                        len(report.issues),
                        len(report.get_issues_by_severity('error')),
                        len(report.get_issues_by_severity('warning')),
                        report.processing_time or '',
                        report.validation_timestamp.isoformat()
                    ])
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self.logger.info(f"Exported {len(reports)} validation reports to {output_path}")


# CLI integration functions

def create_cli_validator(
    storage_path: Optional[Path] = None,
    enable_signing: bool = True
) -> IntegrityValidator:
    """
    Create an integrity validator configured for CLI usage.
    
    Args:
        storage_path: Path for audit storage
        enable_signing: Enable cryptographic signing
        
    Returns:
        Configured IntegrityValidator instance
    """
    crypto = CryptographicUtils()
    audit_logger = None
    
    if storage_path:
        audit_logger = AuditLogger(
            storage_path=storage_path,
            enable_signing=enable_signing
        )
    
    return IntegrityValidator(
        crypto_utils=crypto,
        audit_logger=audit_logger
    )


def validate_document_cli(
    document_path: str,
    audit_log_path: Optional[str] = None,
    expected_hash: Optional[str] = None,
    output_path: Optional[str] = None,
    verbose: bool = False
) -> int:
    """
    CLI function for document validation.
    
    Args:
        document_path: Path to document to validate
        audit_log_path: Path to audit log file
        expected_hash: Expected document hash
        output_path: Path to save validation report
        verbose: Enable verbose output
        
    Returns:
        Exit code (0 for success, 1 for validation failure, 2 for error)
    """
    try:
        validator = create_cli_validator()
        
        # Perform validation
        report = validator.validate_document_integrity(
            document_path=Path(document_path),
            audit_log_path=Path(audit_log_path) if audit_log_path else None,
            expected_hash=expected_hash
        )
        
        # Print results
        print(f"Validation Result: {report.overall_result.value.upper()}")
        print(f"Document: {document_path}")
        print(f"Document Hash: {report.document_hash}")
        
        if report.expected_hash:
            print(f"Expected Hash: {report.expected_hash}")
        
        if report.signature_valid is not None:
            print(f"Signature Valid: {report.signature_valid}")
        
        if report.audit_trail_valid is not None:
            print(f"Audit Trail Valid: {report.audit_trail_valid}")
        
        print(f"Issues Found: {len(report.issues)}")
        
        if verbose or report.has_errors():
            for issue in report.issues:
                severity_symbol = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
                print(f"  {severity_symbol} {issue.message}")
                if verbose and issue.recommendation:
                    print(f"    Recommendation: {issue.recommendation}")
        
        # Save report if requested
        if output_path:
            validator.export_validation_report(report, Path(output_path))
            print(f"Report saved to: {output_path}")
        
        # Return appropriate exit code
        if report.overall_result == ValidationResult.VALID:
            return 0
        else:
            return 1
    
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return 2