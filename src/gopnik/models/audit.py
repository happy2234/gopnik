"""
Audit log and integrity validation data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import json


@dataclass
class AuditLog:
    """
    Audit log entry for tracking processing operations.
    
    Attributes:
        id: Unique audit log identifier
        document_id: ID of document being processed
        operation: Type of operation performed
        timestamp: When operation occurred
        profile_name: Name of redaction profile used
        detections_summary: Summary of PII detections
        input_hash: Hash of original document
        output_hash: Hash of processed document
        signature: Cryptographic signature
        details: Additional operation details
        user_id: ID of user performing operation
        system_info: System information
    """
    id: str
    document_id: str
    operation: str
    timestamp: datetime
    profile_name: Optional[str] = None
    detections_summary: Dict[str, int] = field(default_factory=dict)
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    signature: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    system_info: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate audit ID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert audit log to dictionary format.
        
        Returns:
            Dictionary representation of audit log
        """
        return {
            'id': self.id,
            'document_id': self.document_id,
            'operation': self.operation,
            'timestamp': self.timestamp.isoformat(),
            'profile_name': self.profile_name,
            'detections_summary': self.detections_summary,
            'input_hash': self.input_hash,
            'output_hash': self.output_hash,
            'signature': self.signature,
            'details': self.details,
            'user_id': self.user_id,
            'system_info': self.system_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLog':
        """
        Create audit log from dictionary data.
        
        Args:
            data: Dictionary containing audit log data
            
        Returns:
            AuditLog instance
        """
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        return cls(
            id=data.get('id', ''),
            document_id=data.get('document_id', ''),
            operation=data.get('operation', ''),
            timestamp=timestamp,
            profile_name=data.get('profile_name'),
            detections_summary=data.get('detections_summary', {}),
            input_hash=data.get('input_hash'),
            output_hash=data.get('output_hash'),
            signature=data.get('signature'),
            details=data.get('details', {}),
            user_id=data.get('user_id'),
            system_info=data.get('system_info', {})
        )
    
    def to_json(self) -> str:
        """
        Convert audit log to JSON string.
        
        Returns:
            JSON representation of audit log
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AuditLog':
        """
        Create audit log from JSON string.
        
        Args:
            json_str: JSON string containing audit log data
            
        Returns:
            AuditLog instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
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
    
    def is_signed(self) -> bool:
        """
        Check if audit log has been cryptographically signed.
        
        Returns:
            True if audit log is signed
        """
        return self.signature is not None and len(self.signature) > 0