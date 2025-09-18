"""
Job management for async processing operations.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Callable, Any
from enum import Enum
import logging
from pathlib import Path
import traceback

from ...models.processing import ProcessingResult, BatchProcessingResult
from ...models.profiles import RedactionProfile
from ...core.processor import DocumentProcessor
from .models import JobStatus, JobResponse, ProcessingResponse, BatchProcessingResponse


logger = logging.getLogger(__name__)


class JobType(str, Enum):
    """Job type enumeration."""
    SINGLE_DOCUMENT = "single_document"
    BATCH_PROCESSING = "batch_processing"


class Job:
    """Represents an async processing job."""
    
    def __init__(self, job_id: str, job_type: JobType, created_at: Optional[datetime] = None):
        self.job_id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.created_at = created_at or datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0
        self.result: Optional[Union[ProcessingResult, BatchProcessingResult]] = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None
    
    def start(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        logger.info(f"Job {self.job_id} started")
    
    def complete(self, result: Union[ProcessingResult, BatchProcessingResult]):
        """Mark job as completed with result."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress = 100.0
        self.result = result
        logger.info(f"Job {self.job_id} completed successfully")
    
    def fail(self, error: str):
        """Mark job as failed with error."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error
        logger.error(f"Job {self.job_id} failed: {error}")
    
    def cancel(self):
        """Cancel the job."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        if self.task and not self.task.done():
            self.task.cancel()
        logger.info(f"Job {self.job_id} cancelled")
    
    def update_progress(self, progress: float):
        """Update job progress."""
        self.progress = max(0.0, min(100.0, progress))
    
    def to_response(self) -> JobResponse:
        """Convert to API response model."""
        api_result = None
        if self.result:
            if isinstance(self.result, ProcessingResult):
                api_result = self._processing_result_to_response(self.result)
            elif isinstance(self.result, BatchProcessingResult):
                api_result = self._batch_result_to_response(self.result)
        
        return JobResponse(
            job_id=self.job_id,
            status=self.status,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            progress=self.progress,
            result=api_result,
            error=self.error
        )
    
    def _processing_result_to_response(self, result: ProcessingResult) -> ProcessingResponse:
        """Convert ProcessingResult to API response."""
        from .models import PIIDetectionResponse, ProcessingMetricsResponse
        
        # Convert detections
        detections = []
        if result.detections:
            for detection in result.detections.detections:
                detections.append(PIIDetectionResponse(
                    id=detection.id,
                    type=detection.type.value,
                    confidence=detection.confidence,
                    bounding_box={
                        'x': detection.bounding_box.x,
                        'y': detection.bounding_box.y,
                        'width': detection.bounding_box.width,
                        'height': detection.bounding_box.height
                    },
                    text_content=detection.text_content,
                    page_number=detection.page_number,
                    detection_method=detection.detection_method
                ))
        
        # Convert metrics
        metrics = None
        if result.metrics:
            metrics = ProcessingMetricsResponse(
                total_time=result.metrics.total_time,
                detection_time=result.metrics.detection_time,
                redaction_time=result.metrics.redaction_time,
                io_time=result.metrics.io_time,
                pages_processed=result.metrics.pages_processed,
                detections_found=result.metrics.detections_found,
                pages_per_second=result.metrics.pages_per_second
            )
        
        return ProcessingResponse(
            id=result.id,
            document_id=result.document_id,
            status=result.status.value,
            success=result.success,
            detections=detections,
            metrics=metrics,
            errors=result.errors,
            warnings=result.warnings,
            profile_name=result.profile_name,
            started_at=result.started_at,
            completed_at=result.completed_at,
            output_available=result.output_path is not None
        )
    
    def _batch_result_to_response(self, result: BatchProcessingResult) -> BatchProcessingResponse:
        """Convert BatchProcessingResult to API response."""
        # Convert individual results
        results = [self._processing_result_to_response(r) for r in result.results]
        
        return BatchProcessingResponse(
            id=result.id,
            total_documents=result.total_documents,
            processed_documents=result.processed_documents,
            failed_documents=result.failed_documents,
            success_rate=result.success_rate,
            results=results,
            started_at=result.started_at,
            completed_at=result.completed_at,
            is_completed=result.is_completed
        )


class JobManager:
    """Manages async processing jobs."""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: Dict[str, Job] = {}
        self.running_jobs = 0
        self._cleanup_interval = 3600  # 1 hour
        self._max_completed_jobs = 100  # Keep last 100 completed jobs
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def start_cleanup_task(self):
        """Start the periodic cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
            except RuntimeError:
                # No event loop running, cleanup task will be started later
                pass
    
    def create_job(self, job_type: JobType) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type)
        self.jobs[job_id] = job
        
        # Start cleanup task if not already running
        self.start_cleanup_task()
        
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def list_jobs(self, limit: int = 50, offset: int = 0) -> List[Job]:
        """List jobs with pagination."""
        all_jobs = list(self.jobs.values())
        # Sort by creation time, newest first
        all_jobs.sort(key=lambda j: j.created_at, reverse=True)
        return all_jobs[offset:offset + limit]
    
    def get_job_count(self) -> int:
        """Get total number of jobs."""
        return len(self.jobs)
    
    async def submit_single_document_job(
        self,
        job_id: str,
        processor: DocumentProcessor,
        input_path: Path,
        profile: RedactionProfile
    ) -> None:
        """Submit a single document processing job."""
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        if self.running_jobs >= self.max_concurrent_jobs:
            logger.warning(f"Max concurrent jobs reached, job {job_id} will wait")
        
        # Create and start the task
        job.task = asyncio.create_task(
            self._process_single_document(job, processor, input_path, profile)
        )
        
        try:
            await job.task
        except asyncio.CancelledError:
            job.cancel()
        except Exception as e:
            job.fail(f"Unexpected error: {str(e)}")
    
    async def submit_batch_processing_job(
        self,
        job_id: str,
        processor: DocumentProcessor,
        input_dir: Path,
        profile: RedactionProfile
    ) -> None:
        """Submit a batch processing job."""
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        if self.running_jobs >= self.max_concurrent_jobs:
            logger.warning(f"Max concurrent jobs reached, job {job_id} will wait")
        
        # Create and start the task
        job.task = asyncio.create_task(
            self._process_batch(job, processor, input_dir, profile)
        )
        
        try:
            await job.task
        except asyncio.CancelledError:
            job.cancel()
        except Exception as e:
            job.fail(f"Unexpected error: {str(e)}")
    
    async def _process_single_document(
        self,
        job: Job,
        processor: DocumentProcessor,
        input_path: Path,
        profile: RedactionProfile
    ) -> None:
        """Process a single document asynchronously."""
        try:
            self.running_jobs += 1
            job.start()
            
            # Run the synchronous processing in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                processor.process_document,
                input_path,
                profile
            )
            
            job.complete(result)
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(f"Job {job.job_id} error: {error_msg}")
            logger.debug(f"Error traceback: {traceback.format_exc()}")
            job.fail(error_msg)
        finally:
            self.running_jobs -= 1
    
    async def _process_batch(
        self,
        job: Job,
        processor: DocumentProcessor,
        input_dir: Path,
        profile: RedactionProfile
    ) -> None:
        """Process a batch of documents asynchronously."""
        try:
            self.running_jobs += 1
            job.start()
            
            # Run the synchronous batch processing in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                processor.batch_process,
                input_dir,
                profile
            )
            
            job.complete(result)
            
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            logger.error(f"Job {job.job_id} error: {error_msg}")
            logger.debug(f"Error traceback: {traceback.format_exc()}")
            job.fail(error_msg)
        finally:
            self.running_jobs -= 1
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.cancel()
            return True
        
        return False
    
    async def _periodic_cleanup(self):
        """Periodically clean up old completed jobs."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_jobs()
            except Exception as e:
                logger.error(f"Error during job cleanup: {str(e)}")
    
    async def _cleanup_old_jobs(self):
        """Clean up old completed jobs."""
        completed_jobs = [
            job for job in self.jobs.values()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        
        if len(completed_jobs) > self._max_completed_jobs:
            # Sort by completion time and remove oldest
            completed_jobs.sort(key=lambda j: j.completed_at or j.created_at)
            jobs_to_remove = completed_jobs[:-self._max_completed_jobs]
            
            for job in jobs_to_remove:
                del self.jobs[job.job_id]
                logger.debug(f"Cleaned up old job {job.job_id}")
            
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global job manager instance
job_manager = JobManager()