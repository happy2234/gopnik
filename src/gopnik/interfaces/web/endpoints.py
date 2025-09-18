"""
Web processing endpoints for file upload and job management.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import logging

from .processing import processing_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    profile: str = Form("default"),
    preview_mode: bool = Form(True),
    audit_trail: bool = Form(True)
):
    """
    Upload file and start processing.
    
    Args:
        file: Uploaded file
        profile: Redaction profile name
        preview_mode: Whether to generate preview
        audit_trail: Whether to generate audit trail
        
    Returns:
        Job information
    """
    try:
        job_id = await processing_manager.create_job(
            file=file,
            profile=profile,
            preview_mode=preview_mode,
            audit_trail=audit_trail
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "File uploaded successfully. Processing started."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process upload")


@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Get processing job status.
    
    Args:
        job_id: Job ID
        
    Returns:
        Job status information
    """
    return await processing_manager.get_job_status(job_id)


@router.get("/jobs/{job_id}/download")
async def download_result(job_id: str):
    """
    Download processed file.
    
    Args:
        job_id: Job ID
        
    Returns:
        File download response
    """
    try:
        file_path = await processing_manager.get_download_file(job_id)
        job_status = await processing_manager.get_job_status(job_id)
        
        filename = job_status.get("result", {}).get("filename", "redacted_document.pdf")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to download file")


@router.get("/jobs/{job_id}/audit")
async def download_audit_trail(job_id: str):
    """
    Download audit trail file.
    
    Args:
        job_id: Job ID
        
    Returns:
        Audit trail file download response
    """
    try:
        job_status = await processing_manager.get_job_status(job_id)
        
        if job_status["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        result = job_status.get("result", {})
        audit_file = result.get("audit_file")
        
        if not audit_file:
            raise HTTPException(status_code=404, detail="Audit trail not available")
        
        from pathlib import Path
        audit_path = Path(audit_file)
        
        if not audit_path.exists():
            raise HTTPException(status_code=404, detail="Audit trail file not found")
        
        return FileResponse(
            path=str(audit_path),
            filename=f"audit_trail_{job_id}.json",
            media_type='application/json'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit download error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to download audit trail")


@router.get("/profiles")
async def get_available_profiles():
    """
    Get list of available redaction profiles.
    
    Returns:
        List of available profiles with descriptions
    """
    try:
        profiles = {
            "default": {
                "name": "Default",
                "description": "Standard redaction for common PII types",
                "features": ["Names", "Emails", "Phone Numbers", "Addresses"],
                "icon": "fas fa-shield-alt"
            },
            "healthcare": {
                "name": "Healthcare (HIPAA)",
                "description": "HIPAA-compliant redaction for medical documents",
                "features": ["PHI", "Medical IDs", "Dates", "Names", "Addresses"],
                "icon": "fas fa-heartbeat"
            },
            "financial": {
                "name": "Financial",
                "description": "Financial data protection and compliance",
                "features": ["SSN", "Account Numbers", "Credit Cards", "Names"],
                "icon": "fas fa-university"
            }
        }
        
        return {"profiles": profiles}
        
    except Exception as e:
        logger.error(f"Profile listing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get profiles")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a processing job.
    
    Args:
        job_id: Job ID
        
    Returns:
        Cancellation confirmation
    """
    try:
        job_status = await processing_manager.get_job_status(job_id)
        
        if job_status["status"] in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
        
        # Note: In a real implementation, you would need to implement job cancellation
        # For now, we'll just return a message
        return {
            "message": "Job cancellation requested",
            "job_id": job_id,
            "note": "Job cancellation is not fully implemented in this demo"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job cancellation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")