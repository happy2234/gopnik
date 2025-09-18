"""
Web interface routes for Gopnik deidentification system.

Provides web-based interface with welcome page and demo functionality.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Get the web interface directory
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Initialize templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create router
router = APIRouter()

# Include processing endpoints
from .endpoints import router as processing_router
router.include_router(processing_router, prefix="/api/web", tags=["web-processing"])


@router.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request):
    """
    Serve the welcome/landing page.
    
    Returns:
        HTML response with welcome page
    """
    try:
        return templates.TemplateResponse(request, "welcome.html")
    except Exception as e:
        logger.error(f"Error serving welcome page: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading welcome page")


@router.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """
    Serve the demo page with Cardio-based interface.
    
    Returns:
        HTML response with demo page
    """
    try:
        return templates.TemplateResponse(request, "demo.html")
    except Exception as e:
        logger.error(f"Error serving demo page: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading demo page")


@router.get("/docs/{path:path}")
async def docs_redirect(path: str):
    """
    Redirect documentation requests to appropriate endpoints.
    
    Args:
        path: Documentation path
        
    Returns:
        Redirect response
    """
    # Map common documentation paths
    doc_mappings = {
        "quickstart": "/docs",
        "cli": "/docs",
        "api": "/docs",
        "security": "/docs",
        "faq": "/docs"
    }
    
    if path in doc_mappings:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=doc_mappings[path])
    
    raise HTTPException(status_code=404, detail="Documentation page not found")


def mount_static_files(app):
    """
    Mount static files for the web interface.
    
    Args:
        app: FastAPI application instance
    """
    try:
        # Mount static files
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
        logger.info(f"Mounted static files from {STATIC_DIR}")
    except Exception as e:
        logger.error(f"Error mounting static files: {str(e)}")
        # Create static directories if they don't exist
        os.makedirs(STATIC_DIR / "css", exist_ok=True)
        os.makedirs(STATIC_DIR / "js", exist_ok=True)
        os.makedirs(STATIC_DIR / "images", exist_ok=True)
        
        try:
            app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
            logger.info(f"Created and mounted static files from {STATIC_DIR}")
        except Exception as e2:
            logger.error(f"Failed to create static file mount: {str(e2)}")


def get_version_info():
    """
    Get version information for the welcome page.
    
    Returns:
        Dictionary with version information
    """
    try:
        from ....._version import __version__
        return {
            "version": __version__,
            "api_version": "v1"
        }
    except ImportError:
        return {
            "version": "1.0.0",
            "api_version": "v1"
        }


# Add template globals
templates.env.globals.update({
    "get_version_info": get_version_info
})


def create_demo_app():
    """
    Create FastAPI application for web demo.
    
    Returns:
        FastAPI application instance
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="Gopnik Web Demo",
        description="AI-powered document deidentification web interface",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware for demo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router)
    
    # Mount static files
    mount_static_files(app)
    
    return app