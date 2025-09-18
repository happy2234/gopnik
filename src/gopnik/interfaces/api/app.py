"""
FastAPI application for Gopnik deidentification system.

Provides REST API endpoints for document processing, profile management,
and integrity validation.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, Optional
import uvicorn

from ...core.processor import DocumentProcessor
from ...models.profiles import ProfileManager
from ...config import GopnikConfig
from .models import (
    HealthResponse, ProcessingResponse, ProfileResponse,
    ValidationResponse, ErrorResponse
)
from .dependencies import get_document_processor, get_profile_manager
from .job_manager import job_manager


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Gopnik API server...")
    
    # Initialize core components
    config = GopnikConfig()
    
    # Store in app state for dependency injection
    app.state.config = config
    app.state.document_processor = DocumentProcessor(config)
    app.state.profile_manager = ProfileManager()
    
    # Start job manager cleanup task
    job_manager.start_cleanup_task()
    
    logger.info("Gopnik API server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gopnik API server...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Gopnik Deidentification API",
        description="AI-powered forensic-grade deidentification toolkit REST API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add security middleware
    from ..web.security import RateLimitMiddleware, SecurityHeaders, security_manager
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, calls=100, period=3600)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        # Security checks
        security_manager.check_request_security(request)
        
        response = await call_next(request)
        return SecurityHeaders.add_security_headers(response)
    
    # Include API routers
    from .routers import health, processing, profiles, validation
    
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(processing.router, prefix="/api/v1", tags=["processing"])
    app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
    app.include_router(validation.router, prefix="/api/v1", tags=["validation"])
    
    # Include web interface
    from ..web import router as web_router, mount_static_files
    app.include_router(web_router, tags=["web"])
    mount_static_files(app)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                message="An internal server error occurred",
                details={"type": type(exc).__name__}
            ).dict()
        )
    
    return app


# Create the application instance
app = create_app()


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "gopnik.interfaces.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)