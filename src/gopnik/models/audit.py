"""
Audit log and integrity validation data models.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
import uuid
import json
import hashlib
import platform
import os
from pathlib import Path


class AuditOperation(Enum):
    """Types of operations that can be audited."""
    DOCUMENT_UPLOAD = "document_upload"
    PII_DETECTION = "pii_detection"
    DOCUMENT_REDACTION = "document_redaction"
    DOCUMENT_DOWNLOAD = "document_download"
    PROFILE_CREATION = "profile_creation"
    PROFILE_MODIFICATION = "profile_modification"
    BATCH_PROCESSING = "batch_processing"
    INTEGRITY_VALIDATION = "integrity_validation"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR_OCCURRED = "error_occurred"


class AuditLevel(Enum):
    """Audit log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemInfo:
    """
    System information for audit context.
    
    Attributes:
        hostname: System hostname
        platform: Operating system platform
        python_version: Python version
        gopnik_version: Gopnik version
        cpu_count: Number of CPU cores
        memory_total: Total system memory in MB
        disk_space: Available disk space in MB
        timezone: System timezone
    """
    hostname: str = field(default_factory=lambda: platform.node())
    platform: str = field(default_factory=lambda: platform.platform())
    python_version: str = field(default_factory=lambda: platform.python_version())
    gopnik_version: str = "0.1.0"  # Will be updated by version system
    cpu_count: int = field(default_factory=lambda: os.cpu_count() or 1)
    memory_total: float = 0.0  # Will be set by system monitor
    disk_space: float = 0.0  # Will be set by system monitor
    timezone: str = field(default_factory=lambda: str(datetime.now().astimezone().tzinfo))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'hostname': self.hostname,
            'platform': self.platform,
            'python_version': self.python_version,
            'gopnik_version': self.gopnik_version,
            'cpu_count': self.cpu_count,
            'memory_total': self.memory_total,
            'disk_space': self.disk_space,
            'timezone': self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemInfo':
        """Create from dictionary data."""
        return cls(
            hostname=data.get('hostname', platform.node()),
            platform=data.get('platform', platform.platform()),
            python_version=data.get('python_version', platform.python_version()),
            gopnik_version=data.get('gopnik_version', '0.1.0'),
            cpu_count=data.get('cpu_count', os.cpu_count() or 1),
            memory_total=data.get('memory_total', 0.0),
            disk_space=data.get('disk_space', 0.0),
            timezone=data.get('timezone', str(datetime.now().astimezone().tzinfo))
        )


@dataclass
class AuditLog:
    """
    Comprehensive audit log entry for tracking all system operations.
    
    Attributes:
        id: Unique audit log identifier
        operation: Type of operation performed
        timestamp: When operation occurred (UTC)
        level: Audit log severity level
        document_id: ID of document being processed (if applicable)
        user_id: ID of user performing operation
        session_id: Session identifier
        ip_address: Client IP address (for web operations)
        user_agent: Client user agent (for web operations)
        profile_name: Name of redaction profile used
        detections_summary: Summary of PII detections
        input_hash: Hash of original document
        output_hash: Hash of processed document
        file_paths: Paths of files involved in operation
        processing_time: Time taken for operation in seconds
        memory_usage: Peak memory usage during operation
        error_message: Error message if operation failed
        warning_messages: List of warning messages
        signature: Cryptographic signature for integrity
        details: Additional operation-specific details
        system_info: System information at time of operation
        chain_id: ID linking related audit entries
        parent_id: ID of parent audit entry (for nested operations)
    """
    operation: AuditOperation
    timestamp: datetime
    level: AuditLevel = AuditLevel.INFO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    profile_name: Optional[str] = None
    detections_summary: Dict[str, int] = field(default_factory=dict)
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    file_paths: List[str] = field(default_factory=list)
    processing_time: Optional[float] = None
    memory_usage: Optional[float] = None
    error_message: Optional[str] = None
    warning_messages: List[str] = field(default_factory=list)
    signature: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    system_info: SystemInfo = field(default_factory=SystemInfo)
    chain_id: Optional[str] = None
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize audit log after creation."""
        # Ensure timestamp is UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        elif self.timestamp.tzinfo != timezone.utc:
            self.timestamp = self.timestamp.astimezone(timezone.utc)
        
        # Convert string enums if needed
        if isinstance(self.operation, str):
            self.operation = AuditOperation(self.operation)
        if isinstance(self.level, str):
            self.level = AuditLevel(self.level)
    
    @classmethod
    def create_document_operation(
        cls,
        operation: AuditOperation,
        document_id: str,
        user_id: Optional[str] = None,
        profile_name: Optional[str] = None,
        **kwargs
    ) -> 'AuditLog':
        """Create audit log for document operation."""
        return cls(
            operation=operation,
            timestamp=datetime.now(timezone.utc),
            document_id=document_id,
            user_id=user_id,
            profile_name=profile_name,
            **kwargs
        )
    
    @classmethod
    def create_system_operation(
        cls,
        operation: AuditOperation,
        level: AuditLevel = AuditLevel.INFO,
        **kwargs
    ) -> 'AuditLog':
        """Create audit log for system operation."""
        return cls(
            operation=operation,
            timestamp=datetime.now(timezone.utc),
            level=level,
            **kwargs
        )
    
    @classmethod
    def create_error_log(
        cls,
        error_message: str,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> 'AuditLog':
        """Create audit log for error."""
        return cls(
            operation=AuditOperation.ERROR_OCCURRED,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.ERROR,
            document_id=document_id,
            user_id=user_id,
            error_message=error_message,
            **kwargs
        )
    
    def add_detection_summary(self, detections: List[Any]) -> None:
        """
        Add detection summary to audit log.
        
        Args:
            detections: List of PII detections
        """
        summary = {}
        for detection in detections:
            pii_type = detection.type.value if hasattr(detection.type, 'value') else str(detection.type)
            summary[pii_type] = summary.get(pii_type, 0) + 1
        
        self.detections_summary = summary
    
    def add_file_path(self, file_path: Union[str, Path]) -> None:
        """Add a file path to the audit log."""
        path_str = str(file_path)
        if path_str not in self.file_paths:
            self.file_paths.append(path_str)
    
    def add_warning(self, warning_message: str) -> None:
        """Add a warning message."""
        if warning_message not in self.warning_messages:
            self.warning_messages.append(warning_message)
    
    def set_processing_metrics(self, processing_time: float, memory_usage: Optional[float] = None) -> None:
        """Set processing performance metrics."""
        self.processing_time = processing_time
        if memory_usage is not None:
            self.memory_usage = memory_usage
    
    def create_child_log(self, operation: AuditOperation, **kwargs) -> 'AuditLog':
        """Create a child audit log linked to this one."""
        child_log = AuditLog(
            operation=operation,
            timestamp=datetime.now(timezone.utc),
            parent_id=self.id,
            chain_id=self.chain_id or self.id,
            document_id=self.document_id,
            user_id=self.user_id,
            session_id=self.session_id,
            **kwargs
        )
        return child_log
    
    def get_content_hash(self) -> str:
        """
        Generate hash of audit log content (excluding signature).
        
        Returns:
            SHA-256 hash of audit log content
        """
        # Create a copy without signature for hashing
        content = self.to_dict()
        content.pop('signature', None)
        
        # Sort keys for consistent hashing
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def is_signed(self) -> bool:
        """Check if audit log has been cryptographically signed."""
        return self.signature is not None and len(self.signature) > 0
    
    def is_error(self) -> bool:
        """Check if this is an error audit log."""
        return self.level in [AuditLevel.ERROR, AuditLevel.CRITICAL]
    
    def is_warning(self) -> bool:
        """Check if this is a warning audit log."""
        return self.level == AuditLevel.WARNING or len(self.warning_messages) > 0
    
    def get_duration_since(self, other_log: 'AuditLog') -> float:
        """Get duration in seconds since another audit log."""
        return (self.timestamp - other_log.timestamp).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary format."""
        return {
            'id': self.id,
            'operation': self.operation.value,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'profile_name': self.profile_name,
            'detections_summary': self.detections_summary,
            'input_hash': self.input_hash,
            'output_hash': self.output_hash,
            'file_paths': self.file_paths,
            'processing_time': self.processing_time,
            'memory_usage': self.memory_usage,
            'error_message': self.error_message,
            'warning_messages': self.warning_messages,
            'signature': self.signature,
            'details': self.details,
            'system_info': self.system_info.to_dict(),
            'chain_id': self.chain_id,
            'parent_id': self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLog':
        """Create audit log from dictionary data."""
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Parse system info
        system_info_data = data.get('system_info', {})
        system_info = SystemInfo.from_dict(system_info_data)
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            operation=AuditOperation(data['operation']),
            timestamp=timestamp,
            level=AuditLevel(data.get('level', 'info')),
            document_id=data.get('document_id'),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            profile_name=data.get('profile_name'),
            detections_summary=data.get('detections_summary', {}),
            input_hash=data.get('input_hash'),
            output_hash=data.get('output_hash'),
            file_paths=data.get('file_paths', []),
            processing_time=data.get('processing_time'),
            memory_usage=data.get('memory_usage'),
            error_message=data.get('error_message'),
            warning_messages=data.get('warning_messages', []),
            signature=data.get('signature'),
            details=data.get('details', {}),
            system_info=system_info,
            chain_id=data.get('chain_id'),
            parent_id=data.get('parent_id')
        )
    
    def to_json(self) -> str:
        """Convert audit log to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AuditLog':
        """Create audit log from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_csv_row(self) -> List[str]:
        """Convert audit log to CSV row format."""
        return [
            self.id,
            self.operation.value,
            self.timestamp.isoformat(),
            self.level.value,
            self.document_id or '',
            self.user_id or '',
            self.session_id or '',
            self.ip_address or '',
            self.profile_name or '',
            str(len(self.detections_summary)),
            self.input_hash or '',
            self.output_hash or '',
            str(self.processing_time) if self.processing_time else '',
            str(self.memory_usage) if self.memory_usage else '',
            self.error_message or '',
            str(len(self.warning_messages)),
            'Yes' if self.is_signed() else 'No',
            self.chain_id or '',
            self.parent_id or ''
        ]
    
    @classmethod
    def get_csv_headers(cls) -> List[str]:
        """Get CSV headers for audit log export."""
        return [
            'ID', 'Operation', 'Timestamp', 'Level', 'Document ID', 'User ID',
            'Session ID', 'IP Address', 'Profile Name', 'Detection Count',
            'Input Hash', 'Output Hash', 'Processing Time', 'Memory Usage',
            'Error Message', 'Warning Count', 'Signed', 'Chain ID', 'Parent ID'
        ]
@dataclass
class AuditTrail:
    """
    Collection of audit logs forming a complete audit trail.
    
    Attributes:
        id: Unique audit trail identifier
        name: Human-readable name for the trail
        logs: List of audit log entries
        created_at: When audit trail was created
        metadata: Additional trail metadata
    """
    id: str
    name: str
    logs: List[AuditLog] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize audit trail."""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def add_log(self, audit_log: AuditLog) -> None:
        """Add an audit log to the trail."""
        self.logs.append(audit_log)
    
    def get_logs_by_operation(self, operation: AuditOperation) -> List[AuditLog]:
        """Get all logs for a specific operation type."""
        return [log for log in self.logs if log.operation == operation]
    
    def get_logs_by_document(self, document_id: str) -> List[AuditLog]:
        """Get all logs for a specific document."""
        return [log for log in self.logs if log.document_id == document_id]
    
    def get_logs_by_user(self, user_id: str) -> List[AuditLog]:
        """Get all logs for a specific user."""
        return [log for log in self.logs if log.user_id == user_id]
    
    def get_logs_by_level(self, level: AuditLevel) -> List[AuditLog]:
        """Get all logs at a specific level."""
        return [log for log in self.logs if log.level == level]
    
    def get_error_logs(self) -> List[AuditLog]:
        """Get all error logs."""
        return [log for log in self.logs if log.is_error()]
    
    def get_warning_logs(self) -> List[AuditLog]:
        """Get all warning logs."""
        return [log for log in self.logs if log.is_warning()]
    
    def get_logs_in_timeframe(self, start_time: datetime, end_time: datetime) -> List[AuditLog]:
        """Get logs within a specific timeframe."""
        return [
            log for log in self.logs 
            if start_time <= log.timestamp <= end_time
        ]
    
    def get_chain_logs(self, chain_id: str) -> List[AuditLog]:
        """Get all logs in a specific chain."""
        return [log for log in self.logs if log.chain_id == chain_id]
    
    def get_document_processing_chain(self, document_id: str) -> List[AuditLog]:
        """Get complete processing chain for a document."""
        doc_logs = self.get_logs_by_document(document_id)
        doc_logs.sort(key=lambda x: x.timestamp)
        return doc_logs
    
    def validate_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validate the integrity of the audit trail.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for duplicate IDs
        log_ids = [log.id for log in self.logs]
        if len(log_ids) != len(set(log_ids)):
            issues.append("Duplicate audit log IDs found")
        
        # Check chronological order
        timestamps = [log.timestamp for log in self.logs]
        if timestamps != sorted(timestamps):
            issues.append("Audit logs are not in chronological order")
        
        # Check for broken chains
        chain_ids = set(log.chain_id for log in self.logs if log.chain_id)
        for chain_id in chain_ids:
            chain_logs = self.get_chain_logs(chain_id)
            parent_ids = set(log.parent_id for log in chain_logs if log.parent_id)
            log_ids_in_chain = set(log.id for log in chain_logs)
            
            # Check if all parent IDs exist in the chain
            missing_parents = parent_ids - log_ids_in_chain
            if missing_parents:
                issues.append(f"Missing parent logs in chain {chain_id}: {missing_parents}")
        
        # Check signature integrity
        signed_logs = [log for log in self.logs if log.is_signed()]
        for log in signed_logs:
            # This would verify the actual signature in a real implementation
            # For now, just check that signed logs have content hashes
            if not log.get_content_hash():
                issues.append(f"Signed log {log.id} has invalid content hash")
        
        return len(issues) == 0, issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the audit trail."""
        if not self.logs:
            return {
                'total_logs': 0,
                'operations': {},
                'levels': {},
                'users': {},
                'documents': {},
                'timespan': None,
                'error_count': 0,
                'warning_count': 0,
                'signed_count': 0
            }
        
        # Count by operation
        operations = {}
        for log in self.logs:
            op = log.operation.value
            operations[op] = operations.get(op, 0) + 1
        
        # Count by level
        levels = {}
        for log in self.logs:
            level = log.level.value
            levels[level] = levels.get(level, 0) + 1
        
        # Count by user
        users = {}
        for log in self.logs:
            if log.user_id:
                users[log.user_id] = users.get(log.user_id, 0) + 1
        
        # Count by document
        documents = {}
        for log in self.logs:
            if log.document_id:
                documents[log.document_id] = documents.get(log.document_id, 0) + 1
        
        # Calculate timespan
        timestamps = [log.timestamp for log in self.logs]
        timespan = None
        if timestamps:
            timespan = {
                'start': min(timestamps).isoformat(),
                'end': max(timestamps).isoformat(),
                'duration_seconds': (max(timestamps) - min(timestamps)).total_seconds()
            }
        
        return {
            'total_logs': len(self.logs),
            'operations': operations,
            'levels': levels,
            'users': users,
            'documents': documents,
            'timespan': timespan,
            'error_count': len(self.get_error_logs()),
            'warning_count': len(self.get_warning_logs()),
            'signed_count': len([log for log in self.logs if log.is_signed()])
        }
    
    def export_to_csv(self, file_path: Path) -> None:
        """Export audit trail to CSV file."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(AuditLog.get_csv_headers())
            
            # Write data rows
            for log in sorted(self.logs, key=lambda x: x.timestamp):
                writer.writerow(log.to_csv_row())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit trail to dictionary format."""
        return {
            'id': self.id,
            'name': self.name,
            'logs': [log.to_dict() for log in self.logs],
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditTrail':
        """Create audit trail from dictionary data."""
        # Parse timestamp
        created_at_str = data.get('created_at')
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = datetime.now(timezone.utc)
        
        # Parse logs
        logs = [AuditLog.from_dict(log_data) for log_data in data.get('logs', [])]
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            logs=logs,
            created_at=created_at,
            metadata=data.get('metadata', {})
        )
    
    def to_json(self) -> str:
        """Convert audit trail to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AuditTrail':
        """Create audit trail from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Utility functions for audit operations

def create_document_processing_audit_chain(
    document_id: str,
    user_id: Optional[str] = None,
    profile_name: Optional[str] = None
) -> List[AuditLog]:
    """
    Create a complete audit chain for document processing.
    
    Args:
        document_id: ID of document being processed
        user_id: ID of user performing processing
        profile_name: Name of redaction profile used
        
    Returns:
        List of audit logs forming the processing chain
    """
    chain_id = str(uuid.uuid4())
    
    # Document upload
    upload_log = AuditLog.create_document_operation(
        operation=AuditOperation.DOCUMENT_UPLOAD,
        document_id=document_id,
        user_id=user_id,
        chain_id=chain_id
    )
    
    # PII detection
    detection_log = AuditLog.create_document_operation(
        operation=AuditOperation.PII_DETECTION,
        document_id=document_id,
        user_id=user_id,
        profile_name=profile_name,
        chain_id=chain_id,
        parent_id=upload_log.id
    )
    
    # Document redaction
    redaction_log = AuditLog.create_document_operation(
        operation=AuditOperation.DOCUMENT_REDACTION,
        document_id=document_id,
        user_id=user_id,
        profile_name=profile_name,
        chain_id=chain_id,
        parent_id=detection_log.id
    )
    
    return [upload_log, detection_log, redaction_log]


def validate_audit_log_integrity(audit_log: AuditLog) -> Tuple[bool, List[str]]:
    """
    Validate the integrity of a single audit log.
    
    Args:
        audit_log: Audit log to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required fields
    if not audit_log.id:
        issues.append("Audit log ID is missing")
    
    if not audit_log.operation:
        issues.append("Operation type is missing")
    
    if not audit_log.timestamp:
        issues.append("Timestamp is missing")
    
    # Check timestamp is in UTC
    if audit_log.timestamp.tzinfo != timezone.utc:
        issues.append("Timestamp is not in UTC")
    
    # Check operation-specific requirements
    if audit_log.operation in [AuditOperation.PII_DETECTION, AuditOperation.DOCUMENT_REDACTION]:
        if not audit_log.document_id:
            issues.append(f"Document ID required for {audit_log.operation.value}")
    
    # Check signature integrity if signed
    if audit_log.is_signed():
        content_hash = audit_log.get_content_hash()
        if not content_hash:
            issues.append("Signed audit log has invalid content hash")
    
    # Check error logs have error messages
    if audit_log.is_error() and not audit_log.error_message:
        issues.append("Error audit log missing error message")
    
    return len(issues) == 0, issues


def merge_audit_trails(trails: List[AuditTrail]) -> AuditTrail:
    """
    Merge multiple audit trails into a single trail.
    
    Args:
        trails: List of audit trails to merge
        
    Returns:
        Merged audit trail
    """
    if not trails:
        return AuditTrail(
            id=str(uuid.uuid4()),
            name="Empty Merged Trail"
        )
    
    merged_trail = AuditTrail(
        id=str(uuid.uuid4()),
        name=f"Merged Trail ({len(trails)} trails)",
        created_at=datetime.now(timezone.utc)
    )
    
    # Collect all logs
    all_logs = []
    for trail in trails:
        all_logs.extend(trail.logs)
    
    # Sort by timestamp
    all_logs.sort(key=lambda x: x.timestamp)
    
    # Add to merged trail
    merged_trail.logs = all_logs
    
    # Add metadata about source trails
    merged_trail.metadata = {
        'source_trails': [trail.id for trail in trails],
        'source_count': len(trails),
        'total_logs': len(all_logs)
    }
    
    return merged_trail


def filter_audit_logs(
    logs: List[AuditLog],
    operation: Optional[AuditOperation] = None,
    level: Optional[AuditLevel] = None,
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[AuditLog]:
    """
    Filter audit logs based on various criteria.
    
    Args:
        logs: List of audit logs to filter
        operation: Filter by operation type
        level: Filter by audit level
        document_id: Filter by document ID
        user_id: Filter by user ID
        start_time: Filter by start time (inclusive)
        end_time: Filter by end time (inclusive)
        
    Returns:
        Filtered list of audit logs
    """
    filtered_logs = logs
    
    if operation:
        filtered_logs = [log for log in filtered_logs if log.operation == operation]
    
    if level:
        filtered_logs = [log for log in filtered_logs if log.level == level]
    
    if document_id:
        filtered_logs = [log for log in filtered_logs if log.document_id == document_id]
    
    if user_id:
        filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
    
    if start_time:
        filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
    
    if end_time:
        filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
    
    return filtered_logs