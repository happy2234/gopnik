"""
Settings classes for different components and deployment modes.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class WebSettings:
    """Settings for web demo interface."""
    host: str = "localhost"
    port: int = 8000
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = field(default_factory=lambda: ['.pdf', '.png', '.jpg', '.jpeg'])
    session_timeout_minutes: int = 30
    enable_cloudflare: bool = False
    cloudflare_zone_id: Optional[str] = None
    rate_limit_requests_per_minute: int = 60
    temp_file_cleanup_minutes: int = 60
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSettings':
        """Create WebSettings from dictionary."""
        return cls(
            host=data.get('host', 'localhost'),
            port=data.get('port', 8000),
            max_file_size_mb=data.get('max_file_size_mb', 50),
            allowed_file_types=data.get('allowed_file_types', ['.pdf', '.png', '.jpg', '.jpeg']),
            session_timeout_minutes=data.get('session_timeout_minutes', 30),
            enable_cloudflare=data.get('enable_cloudflare', False),
            cloudflare_zone_id=data.get('cloudflare_zone_id'),
            rate_limit_requests_per_minute=data.get('rate_limit_requests_per_minute', 60),
            temp_file_cleanup_minutes=data.get('temp_file_cleanup_minutes', 60)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'max_file_size_mb': self.max_file_size_mb,
            'allowed_file_types': self.allowed_file_types,
            'session_timeout_minutes': self.session_timeout_minutes,
            'enable_cloudflare': self.enable_cloudflare,
            'cloudflare_zone_id': self.cloudflare_zone_id,
            'rate_limit_requests_per_minute': self.rate_limit_requests_per_minute,
            'temp_file_cleanup_minutes': self.temp_file_cleanup_minutes
        }


@dataclass
class CLISettings:
    """Settings for CLI interface."""
    default_profile: str = "default"
    batch_size: int = 10
    progress_bar: bool = True
    verbose_output: bool = False
    auto_cleanup: bool = True
    output_format: str = "json"  # json, yaml, text
    color_output: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CLISettings':
        """Create CLISettings from dictionary."""
        return cls(
            default_profile=data.get('default_profile', 'default'),
            batch_size=data.get('batch_size', 10),
            progress_bar=data.get('progress_bar', True),
            verbose_output=data.get('verbose_output', False),
            auto_cleanup=data.get('auto_cleanup', True),
            output_format=data.get('output_format', 'json'),
            color_output=data.get('color_output', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'default_profile': self.default_profile,
            'batch_size': self.batch_size,
            'progress_bar': self.progress_bar,
            'verbose_output': self.verbose_output,
            'auto_cleanup': self.auto_cleanup,
            'output_format': self.output_format,
            'color_output': self.color_output
        }


@dataclass
class APISettings:
    """Settings for REST API interface."""
    host: str = "localhost"
    port: int = 8080
    workers: int = 4
    max_request_size_mb: int = 100
    enable_docs: bool = True
    docs_url: str = "/docs"
    api_key_required: bool = False
    rate_limit_requests_per_minute: int = 100
    async_processing: bool = True
    webhook_timeout_seconds: int = 30
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APISettings':
        """Create APISettings from dictionary."""
        return cls(
            host=data.get('host', 'localhost'),
            port=data.get('port', 8080),
            workers=data.get('workers', 4),
            max_request_size_mb=data.get('max_request_size_mb', 100),
            enable_docs=data.get('enable_docs', True),
            docs_url=data.get('docs_url', '/docs'),
            api_key_required=data.get('api_key_required', False),
            rate_limit_requests_per_minute=data.get('rate_limit_requests_per_minute', 100),
            async_processing=data.get('async_processing', True),
            webhook_timeout_seconds=data.get('webhook_timeout_seconds', 30)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'workers': self.workers,
            'max_request_size_mb': self.max_request_size_mb,
            'enable_docs': self.enable_docs,
            'docs_url': self.docs_url,
            'api_key_required': self.api_key_required,
            'rate_limit_requests_per_minute': self.rate_limit_requests_per_minute,
            'async_processing': self.async_processing,
            'webhook_timeout_seconds': self.webhook_timeout_seconds
        }


@dataclass
class AIEngineSettings:
    """Settings for AI engine components."""
    cv_model: str = "yolov8"
    nlp_model: str = "layoutlmv3"
    model_cache_dir: Optional[Path] = None
    gpu_enabled: bool = False
    batch_processing: bool = True
    confidence_threshold: float = 0.7
    max_detections_per_page: int = 100
    model_download_timeout: int = 300
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIEngineSettings':
        """Create AIEngineSettings from dictionary."""
        model_cache_dir = None
        if 'model_cache_dir' in data and data['model_cache_dir']:
            model_cache_dir = Path(data['model_cache_dir'])
        
        return cls(
            cv_model=data.get('cv_model', 'yolov8'),
            nlp_model=data.get('nlp_model', 'layoutlmv3'),
            model_cache_dir=model_cache_dir,
            gpu_enabled=data.get('gpu_enabled', False),
            batch_processing=data.get('batch_processing', True),
            confidence_threshold=data.get('confidence_threshold', 0.7),
            max_detections_per_page=data.get('max_detections_per_page', 100),
            model_download_timeout=data.get('model_download_timeout', 300)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cv_model': self.cv_model,
            'nlp_model': self.nlp_model,
            'model_cache_dir': str(self.model_cache_dir) if self.model_cache_dir else None,
            'gpu_enabled': self.gpu_enabled,
            'batch_processing': self.batch_processing,
            'confidence_threshold': self.confidence_threshold,
            'max_detections_per_page': self.max_detections_per_page,
            'model_download_timeout': self.model_download_timeout
        }


@dataclass
class SecuritySettings:
    """Settings for security and cryptographic operations."""
    enable_encryption: bool = True
    encryption_algorithm: str = "AES-256"
    hash_algorithm: str = "SHA-256"
    signature_algorithm: str = "RSA-2048"
    key_rotation_days: int = 90
    audit_log_signing: bool = True
    secure_temp_files: bool = True
    memory_protection: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecuritySettings':
        """Create SecuritySettings from dictionary."""
        return cls(
            enable_encryption=data.get('enable_encryption', True),
            encryption_algorithm=data.get('encryption_algorithm', 'AES-256'),
            hash_algorithm=data.get('hash_algorithm', 'SHA-256'),
            signature_algorithm=data.get('signature_algorithm', 'RSA-2048'),
            key_rotation_days=data.get('key_rotation_days', 90),
            audit_log_signing=data.get('audit_log_signing', True),
            secure_temp_files=data.get('secure_temp_files', True),
            memory_protection=data.get('memory_protection', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enable_encryption': self.enable_encryption,
            'encryption_algorithm': self.encryption_algorithm,
            'hash_algorithm': self.hash_algorithm,
            'signature_algorithm': self.signature_algorithm,
            'key_rotation_days': self.key_rotation_days,
            'audit_log_signing': self.audit_log_signing,
            'secure_temp_files': self.secure_temp_files,
            'memory_protection': self.memory_protection
        }