"""
Main document processor - orchestrates the entire processing pipeline.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import time
import traceback
from datetime import datetime, timezone

from .interfaces import DocumentProcessorInterface, AIEngineInterface, AuditSystemInterface, RedactionEngineInterface
from .analyzer import DocumentAnalyzer
from .redaction import RedactionEngine
from ..models.processing import ProcessingResult, ProcessingStatus, ProcessingMetrics, BatchProcessingResult, Document
from ..models.profiles import RedactionProfile
from ..models.pii import PIIDetectionCollection
from ..models.audit import AuditLog
from ..models.errors import DocumentProcessingError
from ..config import GopnikConfig
from ..utils.audit_logger import AuditLogger
from ..utils.integrity_validator import IntegrityValidator


class DocumentProcessor(DocumentProcessorInterface):
    """
    Central orchestrator for document processing operations.
    
    Coordinates AI engines, audit systems, and redaction engines to process
    documents according to specified profiles.
    """
    
    def __init__(self, config: Optional[GopnikConfig] = None):
        self.config = config or GopnikConfig()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.document_analyzer = DocumentAnalyzer()
        self.redaction_engine = RedactionEngine()
        self.audit_logger = AuditLogger()
        self.integrity_validator = IntegrityValidator()
        
        # Optional components (set via dependency injection)
        self._ai_engine: Optional[AIEngineInterface] = None
        self._audit_system: Optional[AuditSystemInterface] = None
        
        # Processing statistics
        self._processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'total_processing_time': 0.0
        }
    
    def set_ai_engine(self, ai_engine: AIEngineInterface) -> None:
        """Set the AI engine for PII detection."""
        self._ai_engine = ai_engine
        self.logger.info(f"AI engine set: {type(ai_engine).__name__}")
    
    def set_audit_system(self, audit_system: AuditSystemInterface) -> None:
        """Set the audit system for logging and validation."""
        self._audit_system = audit_system
        self.logger.info(f"Audit system set: {type(audit_system).__name__}")
    
    def process_document(self, input_path: Path, profile: RedactionProfile) -> ProcessingResult:
        """
        Process a single document with the given redaction profile.
        
        Args:
            input_path: Path to input document
            profile: Redaction profile to apply
            
        Returns:
            ProcessingResult with details of the operation
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting document processing: {input_path}")
            
            # Validate inputs
            if not input_path.exists():
                raise DocumentProcessingError(f"Input document not found: {input_path}")
            
            if not self.document_analyzer.is_supported_format(input_path):
                raise DocumentProcessingError(f"Unsupported document format: {input_path.suffix}")
            
            # Step 1: Analyze document structure
            self.logger.debug("Analyzing document structure...")
            analysis_start = time.time()
            document = self.document_analyzer.analyze_document(input_path)
            analysis_time = time.time() - analysis_start
            
            # Step 2: Create audit log
            from ..models.audit import AuditOperation
            audit_log = self.audit_logger.log_operation(
                operation=AuditOperation.DOCUMENT_REDACTION,
                details={
                    'input_path': str(input_path),
                    'profile_name': profile.name,
                    'document_id': document.id,
                    'document_format': document.format.value,
                    'page_count': document.page_count
                }
            )
            
            # Step 3: Detect PII using AI engine
            detection_start = time.time()
            detections = self._detect_pii(document)
            detection_time = time.time() - detection_start
            
            # Step 4: Apply redactions
            redaction_start = time.time()
            output_path = None
            if detections:
                output_path = self.redaction_engine.apply_redactions(input_path, detections.detections, profile)
            else:
                # No PII detected, create a copy
                output_path = self.redaction_engine._create_copy(input_path)
            redaction_time = time.time() - redaction_start
            
            # Step 5: Calculate metrics
            total_time = time.time() - start_time
            metrics = ProcessingMetrics(
                total_time=total_time,
                detection_time=detection_time,
                redaction_time=redaction_time,
                io_time=analysis_time,
                pages_processed=document.page_count,
                detections_found=len(detections) if detections else 0
            )
            
            # Step 6: Create processing result
            result = ProcessingResult(
                document_id=document.id,
                input_document=document,
                output_path=output_path,
                detections=detections or PIIDetectionCollection(),
                audit_log=audit_log,
                status=ProcessingStatus.COMPLETED,
                metrics=metrics,
                profile_name=profile.name
            )
            
            result.mark_completed(success=True)
            
            # Update statistics
            self._update_processing_stats(success=True, processing_time=total_time)
            
            self.logger.info(f"Document processing completed successfully in {total_time:.2f}s")
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = f"Document processing failed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")
            
            # Create error result
            try:
                # Try to create a minimal document object for error reporting
                from ..models.processing import DocumentFormat
                document = Document(path=input_path, format=DocumentFormat.from_path(input_path))
            except:
                # If that fails, create a basic document
                from ..models.processing import DocumentFormat
                document = Document(path=input_path, format=DocumentFormat.UNKNOWN)
            
            from ..models.audit import AuditOperation
            audit_log = self.audit_logger.log_error(
                error_message=error_msg,
                details={'input_path': str(input_path)}
            )
            
            result = ProcessingResult(
                document_id=document.id,
                input_document=document,
                detections=PIIDetectionCollection(),
                audit_log=audit_log,
                status=ProcessingStatus.FAILED,
                profile_name=profile.name
            )
            
            result.mark_failed(error_msg)
            
            # Update statistics
            self._update_processing_stats(success=False, processing_time=total_time)
            
            return result
    
    def validate_document(self, document_path: Path, audit_path: Path) -> bool:
        """
        Validate document integrity using audit trail.
        
        Args:
            document_path: Path to document to validate
            audit_path: Path to audit log file
            
        Returns:
            True if document is valid, False otherwise
        """
        try:
            self.logger.info(f"Validating document: {document_path}")
            
            # Use integrity validator
            is_valid = self.integrity_validator.validate_document_integrity(document_path, audit_path)
            
            if is_valid:
                self.logger.info("Document validation passed")
            else:
                self.logger.warning("Document validation failed")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Document validation error: {str(e)}")
            return False
    
    def batch_process(self, input_dir: Path, profile: RedactionProfile) -> BatchProcessingResult:
        """
        Process multiple documents in a directory.
        
        Args:
            input_dir: Directory containing documents to process
            profile: Redaction profile to apply to all documents
            
        Returns:
            BatchProcessingResult with details of all operations
            
        Raises:
            DocumentProcessingError: If batch processing setup fails
        """
        try:
            self.logger.info(f"Starting batch processing: {input_dir}")
            
            # Validate input directory
            if not input_dir.exists():
                raise DocumentProcessingError(f"Input directory not found: {input_dir}")
            
            if not input_dir.is_dir():
                raise DocumentProcessingError(f"Input path is not a directory: {input_dir}")
            
            # Find all supported documents
            supported_files = []
            for file_path in input_dir.rglob('*'):
                if file_path.is_file() and self.document_analyzer.is_supported_format(file_path):
                    supported_files.append(file_path)
            
            if not supported_files:
                self.logger.warning(f"No supported documents found in {input_dir}")
            
            # Create output directory
            output_dir = input_dir.parent / f"{input_dir.name}_redacted"
            output_dir.mkdir(exist_ok=True)
            
            # Initialize batch result
            batch_result = BatchProcessingResult(
                input_directory=input_dir,
                output_directory=output_dir,
                results=[],
                started_at=datetime.now(timezone.utc),
                total_documents=len(supported_files)
            )
            
            # Process each document
            for i, file_path in enumerate(supported_files, 1):
                self.logger.info(f"Processing document {i}/{len(supported_files)}: {file_path.name}")
                
                try:
                    # Process individual document
                    result = self.process_document(file_path, profile)
                    
                    # Move output to batch output directory if successful
                    if result.success and result.output_path:
                        batch_output_path = output_dir / result.output_path.name
                        result.output_path.rename(batch_output_path)
                        result.output_path = batch_output_path
                    
                    batch_result.add_result(result)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {str(e)}")
                    # Create error result for this document
                    from ..models.processing import DocumentFormat
                    error_result = ProcessingResult(
                        document_id=f"error_{file_path.name}",
                        input_document=Document(path=file_path, format=DocumentFormat.UNKNOWN),
                        detections=PIIDetectionCollection(),
                        audit_log=self.audit_logger.log_error("batch_processing_error", {'error': str(e)}),
                        status=ProcessingStatus.FAILED
                    )
                    error_result.mark_failed(str(e))
                    batch_result.add_result(error_result)
            
            batch_result.mark_completed()
            
            self.logger.info(f"Batch processing completed: {batch_result.processed_documents}/{batch_result.total_documents} successful")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise DocumentProcessingError(f"Batch processing failed: {str(e)}") from e
    
    def _detect_pii(self, document: Document) -> Optional[PIIDetectionCollection]:
        """Detect PII in document using configured AI engine."""
        if not self._ai_engine:
            self.logger.warning("No AI engine configured, skipping PII detection")
            return PIIDetectionCollection(document_id=document.id, total_pages=document.page_count)
        
        try:
            self.logger.debug("Running PII detection...")
            
            # For now, pass the document object to the AI engine
            # The AI engine should handle extracting the necessary data
            detections = self._ai_engine.detect_pii(document)
            
            # Create detection collection
            collection = PIIDetectionCollection(
                detections=detections,
                document_id=document.id,
                total_pages=document.page_count,
                processing_metadata={
                    'ai_engine': type(self._ai_engine).__name__,
                    'detection_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            self.logger.debug(f"PII detection completed: {len(detections)} detections found")
            return collection
            
        except Exception as e:
            self.logger.error(f"PII detection failed: {str(e)}")
            # Return empty collection on error
            return PIIDetectionCollection(document_id=document.id, total_pages=document.page_count)
    
    def _update_processing_stats(self, success: bool, processing_time: float) -> None:
        """Update internal processing statistics."""
        self._processing_stats['total_processed'] += 1
        self._processing_stats['total_processing_time'] += processing_time
        
        if success:
            self._processing_stats['successful_processed'] += 1
        else:
            self._processing_stats['failed_processed'] += 1
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self._processing_stats.copy()
        
        if stats['total_processed'] > 0:
            stats['success_rate'] = (stats['successful_processed'] / stats['total_processed']) * 100
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_processed']
        else:
            stats['success_rate'] = 0.0
            stats['average_processing_time'] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'total_processing_time': 0.0
        }
        self.logger.info("Processing statistics reset")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        return self.document_analyzer.supported_formats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on processor components."""
        health = {
            'status': 'healthy',
            'components': {
                'document_analyzer': 'available',
                'redaction_engine': 'available',
                'audit_logger': 'available',
                'integrity_validator': 'available',
                'ai_engine': 'available' if self._ai_engine else 'not_configured',
                'audit_system': 'available' if self._audit_system else 'not_configured'
            },
            'supported_formats': self.get_supported_formats(),
            'statistics': self.get_processing_statistics()
        }
        
        # Check if any critical components are missing
        if not self._ai_engine:
            health['status'] = 'degraded'
            health['warnings'] = ['AI engine not configured - PII detection will be skipped']
        
        return health