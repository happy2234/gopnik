"""
File handling utilities and temporary file management.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union
import logging
from contextlib import contextmanager


class FileUtils:
    """
    Utility functions for file operations and management.
    """
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            directory: Directory path to ensure
            
        Returns:
            Path object for the directory
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_file_extension(file_path: Union[str, Path]) -> str:
        """
        Get file extension in lowercase.
        
        Args:
            file_path: Path to file
            
        Returns:
            File extension including dot (e.g., '.pdf')
        """
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_supported_format(file_path: Union[str, Path], 
                           supported_formats: List[str]) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_path: Path to file
            supported_formats: List of supported extensions
            
        Returns:
            True if format is supported
        """
        extension = FileUtils.get_file_extension(file_path)
        return extension in [fmt.lower() for fmt in supported_formats]
    
    @staticmethod
    def secure_delete(file_path: Union[str, Path]) -> bool:
        """
        Securely delete a file by overwriting before removal.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deletion was successful
        """
        path = Path(file_path)
        
        if not path.exists():
            return True
        
        try:
            # Overwrite file with random data before deletion
            file_size = path.stat().st_size
            with open(path, 'r+b') as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            # Remove the file
            path.unlink()
            return True
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to securely delete {path}: {e}")
            return False
    
    @staticmethod
    def copy_file_safely(source: Union[str, Path], 
                        destination: Union[str, Path]) -> bool:
        """
        Copy file with error handling.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if copy was successful
        """
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to copy {source} to {destination}: {e}")
            return False


class TempFileManager:
    """
    Manager for temporary file operations with automatic cleanup.
    """
    
    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        self.base_dir = Path(base_dir) if base_dir else None
        self.temp_files: List[Path] = []
        self.temp_dirs: List[Path] = []
        self.logger = logging.getLogger(__name__)
    
    def create_temp_file(self, suffix: str = '', prefix: str = 'gopnik_') -> Path:
        """
        Create a temporary file.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path to temporary file
        """
        fd, temp_path = tempfile.mkstemp(
            suffix=suffix, 
            prefix=prefix, 
            dir=self.base_dir
        )
        os.close(fd)  # Close file descriptor, keep file
        
        temp_file = Path(temp_path)
        self.temp_files.append(temp_file)
        return temp_file
    
    def create_temp_dir(self, prefix: str = 'gopnik_') -> Path:
        """
        Create a temporary directory.
        
        Args:
            prefix: Directory prefix
            
        Returns:
            Path to temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.base_dir))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    @contextmanager
    def temp_file(self, suffix: str = '', prefix: str = 'gopnik_'):
        """
        Context manager for temporary file that auto-cleans up.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Yields:
            Path to temporary file
        """
        temp_file = self.create_temp_file(suffix=suffix, prefix=prefix)
        try:
            yield temp_file
        finally:
            self._cleanup_file(temp_file)
    
    @contextmanager
    def temp_dir(self, prefix: str = 'gopnik_'):
        """
        Context manager for temporary directory that auto-cleans up.
        
        Args:
            prefix: Directory prefix
            
        Yields:
            Path to temporary directory
        """
        temp_dir = self.create_temp_dir(prefix=prefix)
        try:
            yield temp_dir
        finally:
            self._cleanup_dir(temp_dir)
    
    def cleanup_all(self) -> None:
        """Clean up all temporary files and directories."""
        # Clean up files
        for temp_file in self.temp_files[:]:
            self._cleanup_file(temp_file)
        
        # Clean up directories
        for temp_dir in self.temp_dirs[:]:
            self._cleanup_dir(temp_dir)
    
    def _cleanup_file(self, file_path: Path) -> None:
        """Securely clean up a temporary file."""
        try:
            if file_path in self.temp_files:
                self.temp_files.remove(file_path)
            
            if file_path.exists():
                FileUtils.secure_delete(file_path)
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp file {file_path}: {e}")
    
    def _cleanup_dir(self, dir_path: Path) -> None:
        """Clean up a temporary directory."""
        try:
            if dir_path in self.temp_dirs:
                self.temp_dirs.remove(dir_path)
            
            if dir_path.exists():
                shutil.rmtree(dir_path)
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp dir {dir_path}: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup_all()