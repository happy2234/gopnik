"""
Processing result and document data models.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .pii import PIIDetection
from .audit import AuditLog


@dataclass
class Document:
    """
    Represents a document with its content and structure.
    
    Attributes:
        path: Path to the document file
        format: Document format (pdf, image, etc.)
        pages: List of page data
        metadata: Document metadata
        structure: Document structure information
    """
    path: Path
    format: str
    pages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def page_count(self) -> int:
        """Get number of pages in document."""
        return len(self.pages)
    
    @property
    def file_size(self) -> int:
        """Get file size in bytes."""
        return self.path.stat().st_size if self.path.exists() else 0


@dataclass
class ProcessingResult:
    """
    Result of document processing operation.
    
    Attributes:
        document_id: Unique identifier for this processing operation
        input_path: Path to original document
        output_path: Path to processed document
        detections: List of PII detections found
        audit_log: Audit log for this operation
        processing_time: Time taken to process in seconds
        success: Whether processing completed successfully
        errors: List of error messages if any
        profile_name: Name of redaction profile used
        timestamp: When processing was completed
    """
    document_id: str
    input_path: Path
    output_path: Optional[Path]
    detections: List[PIIDetection]
    audit_log: AuditLog
    processing_time: float
    success: bool
    errors: List[str] = field(default_factory=list)
    profile_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Generate document ID if not provided."""
        if not self.document_id:
            self.document_id = str(uuid.uuid4())
    
    @property
    def detection_count(self) -> int:
        """Get total number of detections."""
        return len(self.detections)
    
    @property
    def detection_types(self) -> List[str]:
        """Get list of unique detection types found."""
        return list(set(detection.type.value for detection in self.detections))
    
    def get_detections_by_type(self, pii_type: str) -> List[PIIDetection]:
        """
        Get all detections of a specific type.
        
        Args:
            pii_type: PII type to filter by
            
        Returns:
            List of detections matching the type
        """
        return [d for d in self.detections if d.type.value == pii_type]
    
    def get_high_confidence_detections(self, threshold: float = 0.8) -> List[PIIDetection]:
        """
        Get detections above confidence threshold.
        
        Args:
            threshold: Minimum confidence score
            
        Returns:
            List of high-confidence detections
        """
        return [d for d in self.detections if d.confidence >= threshold]