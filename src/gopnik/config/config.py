"""
Main configuration class for Gopnik system.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
import os
import yaml
import json

from .settings import (
    WebSettings, CLISettings, APISettings, 
    AIEngineSettings, SecuritySettings
)


class DeploymentMode(Enum):
    """Deployment mode options."""
    WEB_DEMO = "web_demo"
    CLI_OFFLINE = "cli_offline"
    API_SERVER = "api_server"
    DESKTOP = "desktop"


@dataclass
class GopnikConfig:
    """
    Main configuration class for Gopnik system.
    
    Manages settings for different deployment modes and components.
    """
    deployment_mode: DeploymentMode = DeploymentMode.CLI_OFFLINE
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=lambda: Path.home() / ".gopnik")
    temp_dir: Optional[Path] = None
    
    # Component settings
    web_settings: WebSettings = field(default_factory=WebSettings)
    cli_settings: CLISettings = field(default_factory=CLISettings)
    api_settings: APISettings = field(default_factory=APISettings)
    ai_engine_settings: AIEngineSettings = field(default_factory=AIEngineSettings)
    security_settings: SecuritySettings = field(default_factory=SecuritySettings)
    
    # Custom configuration
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize configuration after creation."""
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default temp directory if not specified
        if self.temp_dir is None:
            self.temp_dir = self.data_dir / "temp"
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'GopnikConfig':
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            
        Returns:
            GopnikConfig instance
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load configuration data
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        return cls._from_dict(data)
    
    @classmethod
    def from_environment(cls) -> 'GopnikConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            GopnikConfig instance with environment-based settings
        """
        config = cls()
        
        # Override with environment variables
        if 'GOPNIK_DEPLOYMENT_MODE' in os.environ:
            try:
                config.deployment_mode = DeploymentMode(os.environ['GOPNIK_DEPLOYMENT_MODE'])
            except ValueError:
                pass
        
        if 'GOPNIK_DEBUG' in os.environ:
            config.debug = os.environ['GOPNIK_DEBUG'].lower() in ['true', '1', 'yes']
        
        if 'GOPNIK_LOG_LEVEL' in os.environ:
            config.log_level = os.environ['GOPNIK_LOG_LEVEL'].upper()
        
        if 'GOPNIK_DATA_DIR' in os.environ:
            config.data_dir = Path(os.environ['GOPNIK_DATA_DIR'])
        
        if 'GOPNIK_TEMP_DIR' in os.environ:
            config.temp_dir = Path(os.environ['GOPNIK_TEMP_DIR'])
        
        return config
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'GopnikConfig':
        """Create configuration from dictionary data."""
        # Parse deployment mode
        deployment_mode = DeploymentMode.CLI_OFFLINE
        if 'deployment_mode' in data:
            try:
                deployment_mode = DeploymentMode(data['deployment_mode'])
            except ValueError:
                pass
        
        # Parse paths
        data_dir = Path(data.get('data_dir', Path.home() / ".gopnik"))
        temp_dir = None
        if 'temp_dir' in data:
            temp_dir = Path(data['temp_dir'])
        
        # Create component settings
        web_settings = WebSettings.from_dict(data.get('web_settings', {}))
        cli_settings = CLISettings.from_dict(data.get('cli_settings', {}))
        api_settings = APISettings.from_dict(data.get('api_settings', {}))
        ai_engine_settings = AIEngineSettings.from_dict(data.get('ai_engine_settings', {}))
        security_settings = SecuritySettings.from_dict(data.get('security_settings', {}))
        
        return cls(
            deployment_mode=deployment_mode,
            debug=data.get('debug', False),
            log_level=data.get('log_level', 'INFO'),
            data_dir=data_dir,
            temp_dir=temp_dir,
            web_settings=web_settings,
            cli_settings=cli_settings,
            api_settings=api_settings,
            ai_engine_settings=ai_engine_settings,
            security_settings=security_settings,
            custom_settings=data.get('custom_settings', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'deployment_mode': self.deployment_mode.value,
            'debug': self.debug,
            'log_level': self.log_level,
            'data_dir': str(self.data_dir),
            'temp_dir': str(self.temp_dir) if self.temp_dir else None,
            'web_settings': self.web_settings.to_dict(),
            'cli_settings': self.cli_settings.to_dict(),
            'api_settings': self.api_settings.to_dict(),
            'ai_engine_settings': self.ai_engine_settings.to_dict(),
            'security_settings': self.security_settings.to_dict(),
            'custom_settings': self.custom_settings
        }
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Path where to save configuration
        """
        config_data = self.to_dict()
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    def get_profiles_dir(self) -> Path:
        """Get directory for redaction profiles."""
        profiles_dir = self.data_dir / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        return profiles_dir
    
    def get_audit_logs_dir(self) -> Path:
        """Get directory for audit logs."""
        audit_dir = self.data_dir / "audit_logs"
        audit_dir.mkdir(parents=True, exist_ok=True)
        return audit_dir
    
    def get_cache_dir(self) -> Path:
        """Get directory for caching."""
        cache_dir = self.data_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def is_web_mode(self) -> bool:
        """Check if running in web demo mode."""
        return self.deployment_mode == DeploymentMode.WEB_DEMO
    
    def is_cli_mode(self) -> bool:
        """Check if running in CLI offline mode."""
        return self.deployment_mode == DeploymentMode.CLI_OFFLINE
    
    def is_api_mode(self) -> bool:
        """Check if running in API server mode."""
        return self.deployment_mode == DeploymentMode.API_SERVER
    
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode."""
        return self.deployment_mode == DeploymentMode.DESKTOP