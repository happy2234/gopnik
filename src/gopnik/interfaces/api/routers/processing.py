"""
Document processing endpoints.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse

from ....core.processor import DocumentProcessor
from ....models.profiles import ProfileManager
from ..models import (
    ProcessingRequest, ProcessingResponse, BatchProcessingRequest, BatchProcessingResponse,
    JobResponse, JobListResponse, ErrorResponse, PIIDetectionResponse, ProcessingMetricsResponse
)
from ..dependencies import get_document_processor, get_profile_manager, get_validated_profile
from ..job_manager import job_manager, JobType


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process", response_model=ProcessingResponse, summary="Process single document")
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to process"),
    profile_name: str = Form("default", description="Redaction profile to use"),
    confidence_threshold: Optional[float] = Form(None, description="Override confidence threshold"),
    output_format: Optional[str] = Form(None, description="Desired output format"),
    processor: DocumentProcessor = Depends(get_document_processor),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Process a single document for PII detection and redaction.
    
    This endpoint accepts a document file and processes it asynchronously.
    Returns a job ID that can be used to track processing status.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (limit to 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Load and validate profile
        try:
            profile = profile_manager.load_profile(profile_name)
        except FileNotFoundError:
            available_profiles = profile_manager.list_profiles()
            raise HTTPException(
                status_code=404,
                detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading profile: {str(e)}")
        
        # Override confidence threshold if provided
        if confidence_threshold is not None:
            profile.confidence_threshold = confidence_threshold
        
        # Create temporary file
        temp_dir = Path(tempfile.mkdtemp(prefix="gopnik_api_"))
        input_path = temp_dir / file.filename
        
        try:
            # Save uploaded file
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Check if file format is supported
            if not processor.document_analyzer.is_supported_format(input_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {input_path.suffix}"
                )
            
            # Create job for async processing
            job_id = job_manager.create_job(JobType.SINGLE_DOCUMENT)
            
            # Submit job for background processing
            background_tasks.add_task(
                job_manager.submit_single_document_job,
                job_id,
                processor,
                input_path,
                profile
            )
            
            # Add cleanup task
            background_tasks.add_task(_cleanup_temp_dir, temp_dir)
            
            # Return job information
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=500, detail="Failed to create processing job")
            
            return ProcessingResponse(
                id=job_id,
                document_id=file.filename,
                status="pending",
                success=False,
                detections=[],
                errors=[],
                warnings=[],
                profile_name=profile_name,
                started_at=job.created_at,
                completed_at=None,
                output_available=False
            )
            
        except HTTPException:
            # Clean up temp directory on HTTP exceptions
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        except Exception as e:
            # Clean up temp directory on other exceptions
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Document processing setup failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Processing setup failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process document endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchProcessingResponse, summary="Process multiple documents")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Document files to process"),
    profile_name: str = Form("default", description="Redaction profile to use"),
    confidence_threshold: Optional[float] = Form(None, description="Override confidence threshold"),
    output_format: Optional[str] = Form(None, description="Desired output format"),
    processor: DocumentProcessor = Depends(get_document_processor),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Process multiple documents for PII detection and redaction.
    
    This endpoint accepts multiple document files and processes them asynchronously.
    Returns a job ID that can be used to track batch processing status.
    """
    try:
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Too many files (max 20 per batch)")
        
        # Check total size
        total_size = sum(file.size or 0 for file in files)
        if total_size > 200 * 1024 * 1024:  # 200MB total limit
            raise HTTPException(status_code=413, detail="Total file size too large (max 200MB)")
        
        # Load and validate profile
        try:
            profile = profile_manager.load_profile(profile_name)
        except FileNotFoundError:
            available_profiles = profile_manager.list_profiles()
            raise HTTPException(
                status_code=404,
                detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading profile: {str(e)}")
        
        # Override confidence threshold if provided
        if confidence_threshold is not None:
            profile.confidence_threshold = confidence_threshold
        
        # Create temporary directory for batch
        temp_dir = Path(tempfile.mkdtemp(prefix="gopnik_batch_"))
        
        try:
            # Save all uploaded files
            saved_files = []
            for file in files:
                if not file.filename:
                    continue
                
                file_path = temp_dir / file.filename
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                saved_files.append(file_path)
            
            if not saved_files:
                raise HTTPException(status_code=400, detail="No valid files to process")
            
            # Check supported formats
            unsupported_files = []
            for file_path in saved_files:
                if not processor.document_analyzer.is_supported_format(file_path):
                    unsupported_files.append(file_path.name)
            
            if unsupported_files:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file formats: {', '.join(unsupported_files)}"
                )
            
            # Create job for async batch processing
            job_id = job_manager.create_job(JobType.BATCH_PROCESSING)
            
            # Submit job for background processing
            background_tasks.add_task(
                job_manager.submit_batch_processing_job,
                job_id,
                processor,
                temp_dir,
                profile
            )
            
            # Add cleanup task
            background_tasks.add_task(_cleanup_temp_dir, temp_dir)
            
            # Return job information
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=500, detail="Failed to create batch processing job")
            
            return BatchProcessingResponse(
                id=job_id,
                total_documents=len(saved_files),
                processed_documents=0,
                failed_documents=0,
                success_rate=0.0,
                results=[],
                started_at=job.created_at,
                completed_at=None,
                is_completed=False
            )
            
        except HTTPException:
            # Clean up temp directory on HTTP exceptions
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        except Exception as e:
            # Clean up temp directory on other exceptions
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Batch processing setup failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Batch processing setup failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process batch endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get job status")
async def get_job_status(job_id: str):
    """
    Get the status of a processing job.
    
    Returns detailed information about the job including progress,
    results (if completed), and any errors.
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return job.to_response()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=JobListResponse, summary="List processing jobs")
async def list_jobs(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """
    List processing jobs with pagination.
    
    Returns a paginated list of jobs, sorted by creation time (newest first).
    """
    try:
        jobs = job_manager.list_jobs(limit=limit, offset=offset)
        total = job_manager.get_job_count()
        
        job_responses = [job.to_response() for job in jobs]
        
        return JobListResponse(
            jobs=job_responses,
            total=total,
            page=offset // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}", summary="Cancel processing job")
async def cancel_job(job_id: str):
    """
    Cancel a processing job.
    
    Only pending or running jobs can be cancelled.
    """
    try:
        success = job_manager.cancel_job(job_id)
        if not success:
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job '{job_id}' cannot be cancelled (status: {job.status})"
                )
        
        return {"message": f"Job '{job_id}' cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel job error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/download", summary="Download processed document")
async def download_processed_document(job_id: str):
    """
    Download the processed document from a completed job.
    
    Only available for successfully completed single document processing jobs.
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        if job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed (status: {job.status})"
            )
        
        if not job.result or not job.result.success:
            raise HTTPException(status_code=400, detail="Job did not complete successfully")
        
        if not hasattr(job.result, 'output_path') or not job.result.output_path:
            raise HTTPException(status_code=404, detail="No output file available")
        
        output_path = Path(job.result.output_path)
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")
        
        return FileResponse(
            path=str(output_path),
            filename=f"redacted_{output_path.name}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download processed document error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _cleanup_temp_dir(temp_dir: Path):
    """Clean up temporary directory after processing."""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory {temp_dir}: {str(e)}")