"""
Web interface components for Gopnik deidentification system.

Provides a web-based interface with welcome page and demo functionality.
"""

from .routes import router, mount_static_files

__all__ = ["router", "mount_static_files"]