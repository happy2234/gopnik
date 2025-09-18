"""
Web processing workflow implementation.

Handles file uploads, processing jobs, and download management for the web interface.
"""

import os
import tempfile
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from fastapi import UploadFile, HTTPException
from pydantic import BaseModel

from ...core.processor import DocumentProcessor
from ...models.profiles import ProfileManager
from ...models.processing import ProcessingResult
from ...config import GopnikConfig
from .security import SecureFileHandler

logger = logging.getLogger(__name__)


class WebProcessingJob(BaseModel):
    """Web processing job model."""
    job_id: str
    filename: str
    profile: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int = 0
    current_step: str = 'upload'
    step_message: str = 'Initializing...'
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    temp_files: List[str] = []


class WebProcessingManager:
    """Manages web processing jobs and temporary files."""
    
    def __init__(self):
        self.jobs: Dict[str, WebProcessingJob] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "gopnik_web"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize core components
        self.config = GopnikConfig()
        self.processor = DocumentProcessor(self.config)
        self.profile_manager = ProfileManager()
        
        # Cleanup task will be started when needed
        self._cleanup_task = None
    
    def _ensure_cleanup_task(self):
        """Ensure cleanup task is running."""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self.cleanup_task())
            except RuntimeError:
                # No event loop running, cleanup task will be started later
                pass
    
    async def create_job(
        self,
        file: UploadFile,
        profile: str = "default",
        preview_mode: bool = True,
        audit_trail: bool = True
    ) -> str:
        """
        Create a new processing job.
        
        Args:
            file: Uploaded file
            profile: Redaction profile name
            preview_mode: Whether to generate preview
            audit_trail: Whether to generate audit trail
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        # Validate file
        await self._validate_file(file)
        
        # Save uploaded file temporarily with secure filename
        secure_name = SecureFileHandler.secure_filename(file.filename)
        temp_input_path = self.temp_dir / f"{job_id}_{secure_name}"
        temp_files = [str(temp_input_path)]
        
        try:
            with open(temp_input_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Validate file content
            if not SecureFileHandler.validate_file_content(temp_input_path, file.content_type):
                self._cleanup_temp_files(temp_files)
                raise HTTPException(status_code=400, detail="File content doesn't match expected type")
            
            # Create job
            job = WebProcessingJob(
                job_id=job_id,
                filename=file.filename,
                profile=profile,
                status='pending',
                created_at=datetime.now(),
                temp_files=temp_files
            )
            
            self.jobs[job_id] = job
            
            # Ensure cleanup task is running
            self._ensure_cleanup_task()
            
            # Start processing in background
            asyncio.create_task(self._process_job(job_id, temp_input_path, profile, preview_mode, audit_trail))
            
            return job_id
            
        except Exception as e:
            # Cleanup on error
            self._cleanup_temp_files(temp_files)
            raise HTTPException(status_code=500, detail=f"Failed to create processing job: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status information
        """
        if job_id not in self.jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = self.jobs[job_id]
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "step_message": job.step_message,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error
        }
    
    async def get_download_file(self, job_id: str) -> Path:
        """
        Get download file path for completed job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Path to download file
        """
        if job_id not in self.jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = self.jobs[job_id]
        
        if job.status != 'completed':
            raise HTTPException(status_code=400, detail="Job not completed")
        
        if not job.result or 'output_file' not in job.result:
            raise HTTPException(status_code=404, detail="Download file not available")
        
        output_path = Path(job.result['output_file'])
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Download file not found")
        
        return output_path
    
    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file."""
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Check file type
        allowed_types = {
            'application/pdf': ['.pdf'],
            'image/png': ['.png'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/tiff': ['.tiff', '.tif']
        }
        
        file_ext = Path(file.filename).suffix.lower()
        content_type = file.content_type
        
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF, PNG, JPG, or TIFF files."
            )
        
        if file_ext not in allowed_types[content_type]:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {file_ext} doesn't match content type {content_type}"
            )
    
    async def _process_job(
        self,
        job_id: str,
        input_path: Path,
        profile: str,
        preview_mode: bool,
        audit_trail: bool
    ):
        """Process a job in the background."""
        job = self.jobs[job_id]
        
        try:
            # Update status
            job.status = 'processing'
            job.current_step = 'analyze'
            job.step_message = 'Analyzing document structure...'
            job.progress = 20
            
            # Load profile
            profile_config = self.profile_manager.load_profile(profile)
            
            # Update status
            job.current_step = 'detect'
            job.step_message = 'Detecting PII with AI models...'
            job.progress = 40
            
            # Process document
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.processor.process_document,
                str(input_path),
                profile_config
            )
            
            # Update status
            job.current_step = 'redact'
            job.step_message = 'Applying redactions...'
            job.progress = 70
            
            # Generate output file
            output_path = self.temp_dir / f"{job_id}_output{Path(input_path).suffix}"
            job.temp_files.append(str(output_path))
            
            # Save processed document
            result.save_redacted_document(str(output_path))
            
            # Update status
            job.current_step = 'complete'
            job.step_message = 'Finalizing...'
            job.progress = 90
            
            # Generate audit trail if requested
            audit_file = None
            if audit_trail:
                audit_file = self.temp_dir / f"{job_id}_audit.json"
                job.temp_files.append(str(audit_file))
                result.save_audit_trail(str(audit_file))
            
            # Complete job
            job.status = 'completed'
            job.progress = 100
            job.completed_at = datetime.now()
            job.result = {
                'pii_detected': len(result.detections),
                'redactions_applied': len([d for d in result.detections if d.redacted]),
                'average_confidence': sum(d.confidence for d in result.detections) / len(result.detections) if result.detections else 0,
                'output_file': str(output_path),
                'audit_file': str(audit_file) if audit_file else None,
                'filename': f"redacted_{job.filename}",
                'processing_time': (job.completed_at - job.created_at).total_seconds()
            }
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            job.status = 'failed'
            job.error = str(e)
            job.completed_at = datetime.now()
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files securely."""
        for file_path in file_paths:
            try:
                SecureFileHandler.secure_delete(Path(file_path))
            except Exception as e:
                logger.warning(f"Failed to securely cleanup temp file {file_path}: {str(e)}")
                # Fallback to regular deletion
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception:
                    pass
    
    async def cleanup_task(self):
        """Background task to clean up old jobs and temp files."""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=1)  # Clean up jobs older than 1 hour
                
                jobs_to_remove = []
                for job_id, job in self.jobs.items():
                    if job.created_at < cutoff_time:
                        # Clean up temp files
                        self._cleanup_temp_files(job.temp_files)
                        jobs_to_remove.append(job_id)
                
                # Remove old jobs
                for job_id in jobs_to_remove:
                    del self.jobs[job_id]
                    logger.info(f"Cleaned up old job {job_id}")
                
                # Sleep for 10 minutes before next cleanup
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(60)  # Retry after 1 minute on error


# Global processing manager instance
processing_manager = WebProcessingManager()