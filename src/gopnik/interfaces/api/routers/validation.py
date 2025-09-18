"""
Document validation endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List
from pathlib import Path
import logging

from ....utils.integrity_validator import IntegrityValidator, IntegrityReport
from ....utils.crypto import CryptographicUtils
from ....utils.audit_logger import AuditLogger
from ..models import ValidationResponse, ErrorResponse
from ..dependencies import get_config


logger = logging.getLogger(__name__)
router = APIRouter()


def get_integrity_validator() -> IntegrityValidator:
    """Get integrity validator instance."""
    crypto_utils = CryptographicUtils()
    audit_logger = AuditLogger()
    return IntegrityValidator(crypto_utils=crypto_utils, audit_logger=audit_logger)


@router.get("/validate/{document_id}", response_model=ValidationResponse)
async def validate_document_integrity(
    document_id: str,
    document_path: Optional[str] = Query(None, description="Path to document file"),
    audit_log_path: Optional[str] = Query(None, description="Path to audit log file"),
    expected_hash: Optional[str] = Query(None, description="Expected document hash"),
    validator: IntegrityValidator = Depends(get_integrity_validator)
):
    """
    Validate the integrity of a processed document.
    
    Args:
        document_id: ID of the document to validate
        document_path: Optional path to document file
        audit_log_path: Optional path to audit log file
        expected_hash: Optional expected hash for validation
        
    Returns:
        Document validation results
    """
    try:
        # Determine document path
        if document_path:
            doc_path = Path(document_path)
        else:
            # Try to find document in common locations
            doc_path = _find_document_by_id(document_id)
            if not doc_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{document_id}' not found. Please provide document_path parameter."
                )
        
        # Determine audit log path
        audit_path = None
        if audit_log_path:
            audit_path = Path(audit_log_path)
        else:
            # Try to find audit log in common locations
            audit_path = _find_audit_log_by_id(document_id)
        
        # Perform validation
        report = validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_path=audit_path,
            expected_hash=expected_hash
        )
        
        # Convert to API response
        response = _report_to_response(document_id, report)
        
        logger.info(f"Validated document '{document_id}': {report.overall_result.value}")
        return response
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to validate document '{document_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/validate/batch", response_model=List[ValidationResponse])
async def validate_batch_documents(
    document_dir: str = Query(..., description="Directory containing documents to validate"),
    audit_dir: Optional[str] = Query(None, description="Directory containing audit logs"),
    file_pattern: str = Query("*", description="File pattern to match"),
    validator: IntegrityValidator = Depends(get_integrity_validator)
):
    """
    Validate integrity of multiple documents in a directory.
    
    Args:
        document_dir: Directory containing documents to validate
        audit_dir: Optional directory containing audit logs
        file_pattern: File pattern to match (default: all files)
        
    Returns:
        List of validation results for all documents
    """
    try:
        doc_dir_path = Path(document_dir)
        audit_dir_path = Path(audit_dir) if audit_dir else None
        
        if not doc_dir_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document directory not found: {document_dir}"
            )
        
        if audit_dir and audit_dir_path and not audit_dir_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit directory not found: {audit_dir}"
            )
        
        # Perform batch validation
        reports = validator.validate_batch_documents(
            document_dir=doc_dir_path,
            audit_dir=audit_dir_path,
            file_pattern=file_pattern
        )
        
        # Convert to API responses
        responses = []
        for report in reports:
            response = _report_to_response(report.document_id, report)
            responses.append(response)
        
        logger.info(f"Validated {len(reports)} documents in batch")
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate batch documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation failed: {str(e)}"
        )


@router.get("/validate/{document_id}/report", response_model=dict)
async def get_detailed_validation_report(
    document_id: str,
    document_path: Optional[str] = Query(None, description="Path to document file"),
    audit_log_path: Optional[str] = Query(None, description="Path to audit log file"),
    expected_hash: Optional[str] = Query(None, description="Expected document hash"),
    validator: IntegrityValidator = Depends(get_integrity_validator)
):
    """
    Get detailed validation report for a document.
    
    Args:
        document_id: ID of the document to validate
        document_path: Optional path to document file
        audit_log_path: Optional path to audit log file
        expected_hash: Optional expected hash for validation
        
    Returns:
        Detailed validation report with all issues and metadata
    """
    try:
        # Determine document path
        if document_path:
            doc_path = Path(document_path)
        else:
            doc_path = _find_document_by_id(document_id)
            if not doc_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{document_id}' not found. Please provide document_path parameter."
                )
        
        # Determine audit log path
        audit_path = None
        if audit_log_path:
            audit_path = Path(audit_log_path)
        else:
            audit_path = _find_audit_log_by_id(document_id)
        
        # Perform validation
        report = validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_path=audit_path,
            expected_hash=expected_hash
        )
        
        # Return full report as dictionary
        detailed_report = report.to_dict()
        
        logger.info(f"Generated detailed validation report for '{document_id}'")
        return detailed_report
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to generate validation report for '{document_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


# Helper functions

def _find_document_by_id(document_id: str) -> Optional[Path]:
    """
    Try to find document file by ID in common locations.
    
    Args:
        document_id: Document ID to search for
        
    Returns:
        Path to document if found, None otherwise
    """
    # Common document locations and extensions
    search_paths = [
        Path("."),  # Current directory
        Path("output"),  # Output directory
        Path("documents"),  # Documents directory
        Path("processed"),  # Processed directory
    ]
    
    extensions = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for ext in extensions:
            doc_path = search_path / f"{document_id}{ext}"
            if doc_path.exists():
                return doc_path
    
    return None


def _find_audit_log_by_id(document_id: str) -> Optional[Path]:
    """
    Try to find audit log file by document ID in common locations.
    
    Args:
        document_id: Document ID to search for
        
    Returns:
        Path to audit log if found, None otherwise
    """
    # Common audit log locations
    search_paths = [
        Path("."),  # Current directory
        Path("audit_logs"),  # Audit logs directory
        Path("logs"),  # Logs directory
        Path("output"),  # Output directory
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        # Try different audit log naming patterns
        patterns = [
            f"{document_id}_audit.json",
            f"{document_id}.audit.json",
            f"audit_{document_id}.json",
        ]
        
        for pattern in patterns:
            audit_path = search_path / pattern
            if audit_path.exists():
                return audit_path
    
    return None


def _report_to_response(document_id: str, report: IntegrityReport) -> ValidationResponse:
    """Convert IntegrityReport to API response model."""
    # Extract error and warning messages
    errors = [issue.message for issue in report.issues if issue.severity == 'error']
    warnings = [issue.message for issue in report.issues if issue.severity == 'warning']
    
    return ValidationResponse(
        document_id=document_id,
        is_valid=(report.overall_result.value == 'valid'),
        validation_timestamp=report.validation_timestamp,
        integrity_check=(report.document_hash == report.expected_hash if report.expected_hash else True),
        audit_trail_valid=(report.audit_trail_valid if report.audit_trail_valid is not None else True),
        errors=errors,
        warnings=warnings
    )