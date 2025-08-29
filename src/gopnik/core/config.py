"""Configuration management for Gopnik."""

import os
from pathlib import Path
from typing import Any, Dict

from pydantic_settings import BaseSettings


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

    # OCR Settings
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_LANGUAGES: str = "eng+hin+ben+tel+tam+guj+mar"

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
