"""
Processing result and document data models.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
import json
import hashlib
import mimetypes
import os

from .pii import PIIDetection, PIIDetectionCollection
from .audit import AuditLog


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    TIFF = "tiff"
    BMP = "bmp"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_path(cls, file_path: Union[str, Path]) -> 'DocumentFormat':
        """Determine format from file path."""
        path = Path(file_path)
        extension = path.suffix.lower().lstrip('.')
        
        format_mapping = {
            'pdf': cls.PDF,
            'png': cls.PNG,
            'jpeg': cls.JPEG,
            'jpg': cls.JPG,
            'tiff': cls.TIFF,
            'tif': cls.TIFF,
            'bmp': cls.BMP
        }
        
        return format_mapping.get(extension, cls.UNKNOWN)
    
    @classmethod
    def from_mime_type(cls, mime_type: str) -> 'DocumentFormat':
        """Determine format from MIME type."""
        mime_mapping = {
            'application/pdf': cls.PDF,
            'image/png': cls.PNG,
            'image/jpeg': cls.JPEG,
            'image/tiff': cls.TIFF,
            'image/bmp': cls.BMP
        }
        
        return mime_mapping.get(mime_type, cls.UNKNOWN)


@dataclass
class PageInfo:
    """
    Information about a document page.
    
    Attributes:
        page_number: Page number (0-indexed)
        width: Page width in pixels
        height: Page height in pixels
        dpi: Dots per inch resolution
        rotation: Page rotation in degrees
        text_content: Extracted text content
        image_data: Base64 encoded image data (optional)
        metadata: Additional page metadata
    """
    page_number: int
    width: int
    height: int
    dpi: float = 72.0
    rotation: int = 0
    text_content: Optional[str] = None
    image_data: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate page information."""
        if self.page_number < 0:
            raise ValueError(f"Page number cannot be negative: {self.page_number}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Page dimensions must be positive: {self.width}x{self.height}")
        if self.dpi <= 0:
            raise ValueError(f"DPI must be positive: {self.dpi}")
        if self.rotation not in [0, 90, 180, 270]:
            raise ValueError(f"Rotation must be 0, 90, 180, or 270 degrees: {self.rotation}")
    
    @property
    def aspect_ratio(self) -> float:
        """Get page aspect ratio."""
        return self.width / self.height
    
    @property
    def area(self) -> int:
        """Get page area in pixels."""
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'page_number': self.page_number,
            'width': self.width,
            'height': self.height,
            'dpi': self.dpi,
            'rotation': self.rotation,
            'text_content': self.text_content,
            'image_data': self.image_data,
            'metadata': self.metadata,
            'aspect_ratio': self.aspect_ratio,
            'area': self.area
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PageInfo':
        """Create from dictionary data."""
        return cls(
            page_number=data['page_number'],
            width=data['width'],
            height=data['height'],
            dpi=data.get('dpi', 72.0),
            rotation=data.get('rotation', 0),
            text_content=data.get('text_content'),
            image_data=data.get('image_data'),
            metadata=data.get('metadata', {})
        )


@dataclass
class Document:
    """
    Represents a document with its content and structure.
    
    Attributes:
        id: Unique document identifier
        path: Path to the document file
        format: Document format
        pages: List of page information
        metadata: Document metadata
        structure: Document structure information
        created_at: When document was created/loaded
        file_hash: SHA-256 hash of the file
    """
    path: Path
    format: DocumentFormat
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pages: List[PageInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_hash: Optional[str] = None
    
    def __post_init__(self):
        """Initialize document after creation."""
        # Auto-detect format if not provided
        if isinstance(self.format, str):
            self.format = DocumentFormat.from_path(self.path)
        
        # Generate file hash if not provided
        if self.file_hash is None and self.path.exists():
            self.file_hash = self._calculate_file_hash()
        
        # Extract basic metadata
        if not self.metadata and self.path.exists():
            self._extract_basic_metadata()
    
    def _calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _extract_basic_metadata(self) -> None:
        """Extract basic file metadata."""
        stat = self.path.stat()
        mime_type, _ = mimetypes.guess_type(str(self.path))
        
        self.metadata.update({
            'filename': self.path.name,
            'file_size': stat.st_size,
            'mime_type': mime_type,
            'created_time': datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
            'modified_time': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            'format': self.format.value
        })
    
    @property
    def page_count(self) -> int:
        """Get number of pages in document."""
        return len(self.pages)
    
    @property
    def file_size(self) -> int:
        """Get file size in bytes."""
        if self.path.exists():
            return self.path.stat().st_size
        return self.metadata.get('file_size', 0)
    
    @property
    def filename(self) -> str:
        """Get document filename."""
        return self.path.name
    
    @property
    def is_multi_page(self) -> bool:
        """Check if document has multiple pages."""
        return self.page_count > 1
    
    @property
    def total_area(self) -> int:
        """Get total area of all pages."""
        return sum(page.area for page in self.pages)
    
    def add_page(self, page_info: PageInfo) -> None:
        """Add a page to the document."""
        if page_info.page_number != len(self.pages):
            raise ValueError(f"Page number {page_info.page_number} doesn't match expected {len(self.pages)}")
        self.pages.append(page_info)
    
    def get_page(self, page_number: int) -> Optional[PageInfo]:
        """Get page by number."""
        if 0 <= page_number < len(self.pages):
            return self.pages[page_number]
        return None
    
    def validate_integrity(self) -> bool:
        """Validate document file integrity using stored hash."""
        if not self.file_hash or not self.path.exists():
            return False
        
        current_hash = self._calculate_file_hash()
        return current_hash == self.file_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary format."""
        return {
            'id': self.id,
            'path': str(self.path),
            'format': self.format.value,
            'pages': [page.to_dict() for page in self.pages],
            'metadata': self.metadata,
            'structure': self.structure,
            'created_at': self.created_at.isoformat(),
            'file_hash': self.file_hash,
            'page_count': self.page_count,
            'file_size': self.file_size,
            'filename': self.filename,
            'is_multi_page': self.is_multi_page,
            'total_area': self.total_area
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary data."""
        # Parse timestamp
        created_at_str = data.get('created_at')
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = datetime.now(timezone.utc)
        
        # Parse pages
        pages = [PageInfo.from_dict(page_data) for page_data in data.get('pages', [])]
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            path=Path(data['path']),
            format=DocumentFormat(data['format']),
            pages=pages,
            metadata=data.get('metadata', {}),
            structure=data.get('structure', {}),
            created_at=created_at,
            file_hash=data.get('file_hash')
        )
    
    def to_json(self) -> str:
        """Convert document to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Document':
        """Create document from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ProcessingMetrics:
    """
    Performance metrics for processing operation.
    
    Attributes:
        total_time: Total processing time in seconds
        detection_time: Time spent on PII detection
        redaction_time: Time spent on redaction
        io_time: Time spent on file I/O
        memory_peak: Peak memory usage in MB
        cpu_usage: Average CPU usage percentage
        pages_processed: Number of pages processed
        detections_found: Number of PII detections found
    """
    total_time: float
    detection_time: float = 0.0
    redaction_time: float = 0.0
    io_time: float = 0.0
    memory_peak: float = 0.0
    cpu_usage: float = 0.0
    pages_processed: int = 0
    detections_found: int = 0
    
    def __post_init__(self):
        """Validate metrics."""
        if self.total_time < 0:
            raise ValueError(f"Total time cannot be negative: {self.total_time}")
        if any(t < 0 for t in [self.detection_time, self.redaction_time, self.io_time]):
            raise ValueError("Individual times cannot be negative")
        if self.pages_processed < 0:
            raise ValueError(f"Pages processed cannot be negative: {self.pages_processed}")
        if self.detections_found < 0:
            raise ValueError(f"Detections found cannot be negative: {self.detections_found}")
    
    @property
    def pages_per_second(self) -> float:
        """Get processing rate in pages per second."""
        return self.pages_processed / self.total_time if self.total_time > 0 else 0.0
    
    @property
    def detections_per_page(self) -> float:
        """Get average detections per page."""
        return self.detections_found / self.pages_processed if self.pages_processed > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_time': self.total_time,
            'detection_time': self.detection_time,
            'redaction_time': self.redaction_time,
            'io_time': self.io_time,
            'memory_peak': self.memory_peak,
            'cpu_usage': self.cpu_usage,
            'pages_processed': self.pages_processed,
            'detections_found': self.detections_found,
            'pages_per_second': self.pages_per_second,
            'detections_per_page': self.detections_per_page
        }


@dataclass
class ProcessingResult:
    """
    Result of document processing operation.
    
    Attributes:
        id: Unique identifier for this processing result
        document_id: ID of the document that was processed
        input_document: Original document information
        output_path: Path to processed document
        detections: Collection of PII detections found
        audit_log: Audit log for this operation
        status: Processing status
        metrics: Performance metrics
        errors: List of error messages if any
        warnings: List of warning messages
        profile_name: Name of redaction profile used
        started_at: When processing started
        completed_at: When processing completed
        version_info: Version information of processing components
    """
    document_id: str
    input_document: Document
    detections: PIIDetectionCollection
    audit_log: AuditLog
    status: ProcessingStatus
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    output_path: Optional[Path] = None
    metrics: Optional[ProcessingMetrics] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    profile_name: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    version_info: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize processing result."""
        # Ensure document_id matches input document
        if self.document_id != self.input_document.id:
            self.document_id = self.input_document.id
        
        # Set detections document_id if not set
        if self.detections.document_id is None:
            self.detections.document_id = self.document_id
        
        # Initialize metrics if not provided
        if self.metrics is None and self.completed_at is not None:
            processing_time = (self.completed_at - self.started_at).total_seconds()
            self.metrics = ProcessingMetrics(
                total_time=processing_time,
                pages_processed=self.input_document.page_count,
                detections_found=len(self.detections)
            )
    
    @property
    def processing_time(self) -> float:
        """Get total processing time in seconds."""
        if self.metrics:
            return self.metrics.total_time
        elif self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        else:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds()
    
    @property
    def success(self) -> bool:
        """Check if processing was successful."""
        return self.status == ProcessingStatus.COMPLETED and len(self.errors) == 0
    
    @property
    def detection_count(self) -> int:
        """Get total number of detections."""
        return len(self.detections)
    
    @property
    def detection_types(self) -> List[str]:
        """Get list of unique detection types found."""
        return list(set(detection.type.value for detection in self.detections))
    
    @property
    def has_output(self) -> bool:
        """Check if processing produced output."""
        return self.output_path is not None and self.output_path.exists()
    
    @property
    def output_file_size(self) -> int:
        """Get output file size in bytes."""
        if self.has_output:
            return self.output_path.stat().st_size
        return 0
    
    def mark_completed(self, success: bool = True) -> None:
        """Mark processing as completed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
        
        # Update metrics
        if self.metrics is None:
            self.metrics = ProcessingMetrics(
                total_time=self.processing_time,
                pages_processed=self.input_document.page_count,
                detections_found=len(self.detections)
            )
    
    def mark_failed(self, error_message: str) -> None:
        """Mark processing as failed with error."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = ProcessingStatus.FAILED
        if error_message not in self.errors:
            self.errors.append(error_message)
    
    def add_error(self, error_message: str) -> None:
        """Add an error message."""
        if error_message not in self.errors:
            self.errors.append(error_message)
    
    def add_warning(self, warning_message: str) -> None:
        """Add a warning message."""
        if warning_message not in self.warnings:
            self.warnings.append(warning_message)
    
    def get_detections_by_type(self, pii_type: str) -> List[PIIDetection]:
        """Get all detections of a specific type."""
        return self.detections.get_by_type(pii_type)
    
    def get_high_confidence_detections(self, threshold: float = 0.8) -> List[PIIDetection]:
        """Get detections above confidence threshold."""
        return self.detections.get_high_confidence(threshold)
    
    def get_detections_by_page(self, page_number: int) -> List[PIIDetection]:
        """Get detections for a specific page."""
        return self.detections.get_by_page(page_number)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'status': self.status.value,
            'success': self.success,
            'processing_time': self.processing_time,
            'detection_count': self.detection_count,
            'detection_types': self.detection_types,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'has_output': self.has_output,
            'output_file_size': self.output_file_size,
            'profile_name': self.profile_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert processing result to dictionary format."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'input_document': self.input_document.to_dict(),
            'output_path': str(self.output_path) if self.output_path else None,
            'detections': self.detections.to_dict(),
            'audit_log': self.audit_log.to_dict(),
            'status': self.status.value,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'errors': self.errors,
            'warnings': self.warnings,
            'profile_name': self.profile_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'version_info': self.version_info,
            'summary': self.get_summary()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingResult':
        """Create processing result from dictionary data."""
        # Parse timestamps
        started_at_str = data.get('started_at')
        if isinstance(started_at_str, str):
            started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
        else:
            started_at = datetime.now(timezone.utc)
        
        completed_at = None
        completed_at_str = data.get('completed_at')
        if isinstance(completed_at_str, str):
            completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
        
        # Parse components
        input_document = Document.from_dict(data['input_document'])
        detections = PIIDetectionCollection.from_dict(data['detections'])
        audit_log = AuditLog.from_dict(data['audit_log'])
        
        # Parse metrics
        metrics = None
        if data.get('metrics'):
            metrics_data = data['metrics']
            metrics = ProcessingMetrics(
                total_time=metrics_data['total_time'],
                detection_time=metrics_data.get('detection_time', 0.0),
                redaction_time=metrics_data.get('redaction_time', 0.0),
                io_time=metrics_data.get('io_time', 0.0),
                memory_peak=metrics_data.get('memory_peak', 0.0),
                cpu_usage=metrics_data.get('cpu_usage', 0.0),
                pages_processed=metrics_data.get('pages_processed', 0),
                detections_found=metrics_data.get('detections_found', 0)
            )
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            document_id=data['document_id'],
            input_document=input_document,
            output_path=Path(data['output_path']) if data.get('output_path') else None,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus(data['status']),
            metrics=metrics,
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            profile_name=data.get('profile_name'),
            started_at=started_at,
            completed_at=completed_at,
            version_info=data.get('version_info', {})
        )
    
    def to_json(self) -> str:
        """Convert processing result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProcessingResult':
        """Create processing result from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class BatchProcessingResult:
    """
    Result of batch document processing operation.
    
    Attributes:
        id: Unique batch processing identifier
        input_directory: Directory containing input documents
        output_directory: Directory for processed documents
        results: List of individual processing results
        started_at: When batch processing started
        completed_at: When batch processing completed
        total_documents: Total number of documents to process
        processed_documents: Number of documents processed
        failed_documents: Number of documents that failed
        profile_name: Redaction profile used for batch
        errors: List of batch-level errors
    """
    input_directory: Path
    output_directory: Path
    results: List[ProcessingResult]
    started_at: datetime
    total_documents: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    completed_at: Optional[datetime] = None
    processed_documents: int = 0
    failed_documents: int = 0
    profile_name: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize batch result."""
        self.processed_documents = len([r for r in self.results if r.success])
        self.failed_documents = len([r for r in self.results if not r.success])
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100
    
    @property
    def total_processing_time(self) -> float:
        """Get total processing time for all documents."""
        return sum(result.processing_time for result in self.results)
    
    @property
    def average_processing_time(self) -> float:
        """Get average processing time per document."""
        if not self.results:
            return 0.0
        return self.total_processing_time / len(self.results)
    
    @property
    def total_detections(self) -> int:
        """Get total number of detections across all documents."""
        return sum(result.detection_count for result in self.results)
    
    @property
    def is_completed(self) -> bool:
        """Check if batch processing is completed."""
        return self.completed_at is not None
    
    @property
    def batch_processing_time(self) -> float:
        """Get total batch processing time."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        else:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds()
    
    def add_result(self, result: ProcessingResult) -> None:
        """Add a processing result to the batch."""
        self.results.append(result)
        if result.success:
            self.processed_documents += 1
        else:
            self.failed_documents += 1
    
    def mark_completed(self) -> None:
        """Mark batch processing as completed."""
        self.completed_at = datetime.now(timezone.utc)
    
    def get_failed_results(self) -> List[ProcessingResult]:
        """Get all failed processing results."""
        return [result for result in self.results if not result.success]
    
    def get_successful_results(self) -> List[ProcessingResult]:
        """Get all successful processing results."""
        return [result for result in self.results if result.success]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        detection_types = {}
        for result in self.results:
            for detection_type in result.detection_types:
                detection_types[detection_type] = detection_types.get(detection_type, 0) + 1
        
        return {
            'total_documents': self.total_documents,
            'processed_documents': self.processed_documents,
            'failed_documents': self.failed_documents,
            'success_rate': self.success_rate,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': self.average_processing_time,
            'batch_processing_time': self.batch_processing_time,
            'total_detections': self.total_detections,
            'detection_types': detection_types,
            'error_count': len(self.errors)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch result to dictionary format."""
        return {
            'id': self.id,
            'input_directory': str(self.input_directory),
            'output_directory': str(self.output_directory),
            'results': [result.to_dict() for result in self.results],
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_documents': self.total_documents,
            'processed_documents': self.processed_documents,
            'failed_documents': self.failed_documents,
            'profile_name': self.profile_name,
            'errors': self.errors,
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchProcessingResult':
        """Create batch result from dictionary data."""
        # Parse timestamps
        started_at = datetime.fromisoformat(data['started_at'].replace('Z', '+00:00'))
        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
        
        # Parse results
        results = [ProcessingResult.from_dict(result_data) for result_data in data['results']]
        
        return cls(
            id=data['id'],
            input_directory=Path(data['input_directory']),
            output_directory=Path(data['output_directory']),
            results=results,
            started_at=started_at,
            completed_at=completed_at,
            total_documents=data['total_documents'],
            processed_documents=data.get('processed_documents', 0),
            failed_documents=data.get('failed_documents', 0),
            profile_name=data.get('profile_name'),
            errors=data.get('errors', [])
        )
    
    def to_json(self) -> str:
        """Convert batch result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BatchProcessingResult':
        """Create batch result from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Utility functions for processing results

def validate_processing_result(result: ProcessingResult) -> Tuple[bool, List[str]]:
    """
    Validate a processing result for completeness and consistency.
    
    Args:
        result: Processing result to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if not result.id:
        errors.append("Processing result ID is missing")
    
    if not result.document_id:
        errors.append("Document ID is missing")
    
    if not result.input_document:
        errors.append("Input document information is missing")
    
    if not result.audit_log:
        errors.append("Audit log is missing")
    
    # Check consistency
    if result.document_id != result.input_document.id:
        errors.append("Document ID mismatch between result and input document")
    
    if result.detections.document_id and result.detections.document_id != result.document_id:
        errors.append("Document ID mismatch in detections collection")
    
    # Check status consistency
    if result.status == ProcessingStatus.COMPLETED and result.completed_at is None:
        errors.append("Completed status but no completion timestamp")
    
    if result.status == ProcessingStatus.FAILED and not result.errors:
        errors.append("Failed status but no error messages")
    
    # Check output consistency
    if result.success and result.output_path is None:
        errors.append("Successful processing but no output path")
    
    if result.output_path and not result.output_path.exists():
        errors.append(f"Output file does not exist: {result.output_path}")
    
    # Check metrics consistency
    if result.metrics:
        if result.metrics.pages_processed != result.input_document.page_count:
            errors.append("Metrics pages processed doesn't match document page count")
        
        if result.metrics.detections_found != len(result.detections):
            errors.append("Metrics detections found doesn't match actual detections")
    
    return len(errors) == 0, errors


def merge_processing_results(results: List[ProcessingResult]) -> Dict[str, Any]:
    """
    Merge multiple processing results into summary statistics.
    
    Args:
        results: List of processing results to merge
        
    Returns:
        Dictionary with merged statistics
    """
    if not results:
        return {
            'total_results': 0,
            'successful_results': 0,
            'failed_results': 0,
            'total_detections': 0,
            'total_processing_time': 0.0,
            'detection_types': {},
            'error_summary': {}
        }
    
    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]
    
    # Aggregate detection types
    detection_types = {}
    for result in results:
        for detection_type in result.detection_types:
            detection_types[detection_type] = detection_types.get(detection_type, 0) + 1
    
    # Aggregate errors
    error_summary = {}
    for result in failed_results:
        for error in result.errors:
            error_summary[error] = error_summary.get(error, 0) + 1
    
    # Calculate timing statistics
    processing_times = [r.processing_time for r in results if r.processing_time > 0]
    
    return {
        'total_results': len(results),
        'successful_results': len(successful_results),
        'failed_results': len(failed_results),
        'success_rate': (len(successful_results) / len(results)) * 100,
        'total_detections': sum(r.detection_count for r in results),
        'total_processing_time': sum(processing_times),
        'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0.0,
        'min_processing_time': min(processing_times) if processing_times else 0.0,
        'max_processing_time': max(processing_times) if processing_times else 0.0,
        'detection_types': detection_types,
        'error_summary': error_summary,
        'total_pages_processed': sum(r.input_document.page_count for r in results),
        'total_file_size_processed': sum(r.input_document.file_size for r in results)
    }


def create_processing_summary_report(results: List[ProcessingResult]) -> str:
    """
    Create a human-readable summary report from processing results.
    
    Args:
        results: List of processing results
        
    Returns:
        Formatted summary report string
    """
    if not results:
        return "No processing results to summarize."
    
    stats = merge_processing_results(results)
    
    report = f"""
Processing Summary Report
========================

Overall Statistics:
- Total Documents: {stats['total_results']}
- Successful: {stats['successful_results']} ({stats['success_rate']:.1f}%)
- Failed: {stats['failed_results']}
- Total Detections: {stats['total_detections']}

Performance:
- Total Processing Time: {stats['total_processing_time']:.2f} seconds
- Average Time per Document: {stats['average_processing_time']:.2f} seconds
- Fastest Document: {stats['min_processing_time']:.2f} seconds
- Slowest Document: {stats['max_processing_time']:.2f} seconds

Data Processed:
- Total Pages: {stats['total_pages_processed']}
- Total File Size: {stats['total_file_size_processed'] / (1024*1024):.1f} MB

Detection Types Found:
"""
    
    for detection_type, count in sorted(stats['detection_types'].items()):
        report += f"- {detection_type}: {count}\n"
    
    if stats['error_summary']:
        report += "\nErrors Encountered:\n"
        for error, count in sorted(stats['error_summary'].items()):
            report += f"- {error}: {count} occurrences\n"
    
    return report