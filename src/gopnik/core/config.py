"""Configuration management for Gopnik - Python 3.11 Compatible."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, Field


class Config(BaseSettings):
    """Application configuration."""

    # Application
    APP_NAME: str = "Gopnik"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # OCR Settings - Windows specific
    TESSERACT_CMD: Optional[str] = Field(
        default=None, description="Path to tesseract executable"
    )
    OCR_LANGUAGES: str = "eng+hin+ben+tel+tam+guj+mar"

    # Auto-detect Tesseract installation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.TESSERACT_CMD is None:
            self.TESSERACT_CMD = self._find_tesseract()

    def _find_tesseract(self) -> str:
        """Auto-detect Tesseract installation on Windows."""
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\ProgramData\chocolatey\bin\tesseract.exe",
            "tesseract",  # If in PATH
        ]

        for path in possible_paths:
            if Path(path).exists() or path == "tesseract":
                return path

        return r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Default

    # Model Settings
    DEFAULT_BATCH_SIZE: int = 8
    MAX_IMAGE_SIZE: int = 2048

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security
    ENABLE_AUDIT_LOG: bool = True
    HASH_ALGORITHM: str = "sha256"

    class Config:
        env_file = ".env"
        case_sensitive = True


config = Config()
