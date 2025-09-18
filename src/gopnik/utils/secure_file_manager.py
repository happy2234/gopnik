"""
Secure temporary file handling with encryption and access controls.
"""

import os
import stat
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO
from contextlib import contextmanager
import logging
import weakref
import atexit

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import base64

from .crypto import CryptographicUtils


class SecureFileManager:
    """
    Secure temporary file manager with encryption and access controls.
    
    Features:
    - Encrypted temporary file storage
    - Secure file deletion with cryptographic wiping
    - File access controls and permission management
    - Automatic cleanup on process exit
    """
    
    _instances: Dict[int, 'SecureFileManager'] = {}
    _lock = threading.Lock()
    
    def __init__(self, base_dir: Optional[Union[str, Path]] = None, 
                 encryption_key: Optional[bytes] = None):
        """
        Initialize secure file manager.
        
        Args:
            base_dir: Base directory for temporary files
            encryption_key: Optional encryption key (generated if not provided)
        """
        self.base_dir = Path(base_dir) if base_dir else None
        self.temp_files: List[Path] = []
        self.temp_dirs: List[Path] = []
        self.encrypted_files: Dict[Path, bytes] = {}  # Maps file path to encryption key
        self.logger = logging.getLogger(__name__)
        
        # Generate or use provided encryption key
        if encryption_key:
            self._encryption_key = encryption_key
        else:
            self._encryption_key = Fernet.generate_key()
        
        self._fernet = Fernet(self._encryption_key)
        self._crypto_utils = CryptographicUtils()
        
        # Register for cleanup on exit
        with self._lock:
            self._instances[id(self)] = self
            if len(self._instances) == 1:
                atexit.register(self._cleanup_all_instances)
        
        # Create weak reference for cleanup
        self._weakref = weakref.ref(self, self._cleanup_instance)
    
    @classmethod
    def _cleanup_all_instances(cls):
        """Clean up all instances on process exit."""
        with cls._lock:
            for instance in list(cls._instances.values()):
                try:
                    instance.cleanup_all()
                except Exception as e:
                    logging.getLogger(__name__).error(f"Error during cleanup: {e}")
            cls._instances.clear()
    
    @classmethod
    def _cleanup_instance(cls, weakref_obj):
        """Clean up specific instance."""
        with cls._lock:
            # Remove from instances dict
            to_remove = []
            for instance_id, instance in cls._instances.items():
                if weakref.ref(instance) == weakref_obj:
                    to_remove.append(instance_id)
            
            for instance_id in to_remove:
                cls._instances.pop(instance_id, None)
    
    def create_secure_temp_file(self, suffix: str = '', prefix: str = 'gopnik_secure_',
                               encrypted: bool = True, mode: int = 0o600) -> Path:
        """
        Create a secure temporary file with encryption and restricted permissions.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            encrypted: Whether to encrypt the file
            mode: File permissions (default: owner read/write only)
            
        Returns:
            Path to secure temporary file
        """
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=self.base_dir
        )
        
        temp_file = Path(temp_path)
        
        try:
            # Set restrictive permissions
            os.chmod(temp_file, mode)
            
            # Close the file descriptor
            os.close(fd)
            
            # Track the file
            self.temp_files.append(temp_file)
            
            # Store encryption info if encrypted
            if encrypted:
                self.encrypted_files[temp_file] = self._encryption_key
            
            self.logger.debug(f"Created secure temp file: {temp_file}")
            return temp_file
            
        except Exception as e:
            # Clean up on error
            try:
                os.close(fd)
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
            raise RuntimeError(f"Failed to create secure temp file: {e}")
    
    def create_secure_temp_dir(self, prefix: str = 'gopnik_secure_',
                              mode: int = 0o700) -> Path:
        """
        Create a secure temporary directory with restricted permissions.
        
        Args:
            prefix: Directory prefix
            mode: Directory permissions (default: owner access only)
            
        Returns:
            Path to secure temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.base_dir))
        
        try:
            # Set restrictive permissions
            os.chmod(temp_dir, mode)
            
            # Track the directory
            self.temp_dirs.append(temp_dir)
            
            self.logger.debug(f"Created secure temp dir: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            # Clean up on error
            try:
                if temp_dir.exists():
                    temp_dir.rmdir()
            except:
                pass
            raise RuntimeError(f"Failed to create secure temp dir: {e}")
    
    def write_encrypted_data(self, file_path: Path, data: Union[str, bytes]) -> None:
        """
        Write encrypted data to a file.
        
        Args:
            file_path: Path to file
            data: Data to encrypt and write
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self._fernet.encrypt(data)
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Ensure file has secure permissions
        os.chmod(file_path, 0o600)
        
        self.logger.debug(f"Wrote encrypted data to: {file_path}")
    
    def read_encrypted_data(self, file_path: Path) -> bytes:
        """
        Read and decrypt data from a file.
        
        Args:
            file_path: Path to encrypted file
            
        Returns:
            Decrypted data as bytes
        """
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self._fernet.decrypt(encrypted_data)
        
        self.logger.debug(f"Read encrypted data from: {file_path}")
        return decrypted_data
    
    @contextmanager
    def secure_temp_file(self, suffix: str = '', prefix: str = 'gopnik_secure_',
                        encrypted: bool = True, mode: int = 0o600):
        """
        Context manager for secure temporary file with auto-cleanup.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            encrypted: Whether to encrypt the file
            mode: File permissions
            
        Yields:
            Path to secure temporary file
        """
        temp_file = self.create_secure_temp_file(
            suffix=suffix, prefix=prefix, encrypted=encrypted, mode=mode
        )
        try:
            yield temp_file
        finally:
            self._secure_cleanup_file(temp_file)
    
    @contextmanager
    def secure_temp_dir(self, prefix: str = 'gopnik_secure_', mode: int = 0o700):
        """
        Context manager for secure temporary directory with auto-cleanup.
        
        Args:
            prefix: Directory prefix
            mode: Directory permissions
            
        Yields:
            Path to secure temporary directory
        """
        temp_dir = self.create_secure_temp_dir(prefix=prefix, mode=mode)
        try:
            yield temp_dir
        finally:
            self._secure_cleanup_dir(temp_dir)
    
    def secure_delete_file(self, file_path: Path, passes: int = 2) -> bool:
        """
        Securely delete a file with multiple overwrite passes.
        
        Args:
            file_path: Path to file to delete
            passes: Number of overwrite passes (default: 3)
            
        Returns:
            True if deletion was successful
        """
        if not file_path.exists():
            return True
        
        try:
            file_size = file_path.stat().st_size
            
            # Multiple overwrite passes with different patterns
            with open(file_path, 'r+b') as f:
                for pass_num in range(passes):
                    f.seek(0)
                    
                    if pass_num == 0:
                        # First pass: random data
                        f.write(secrets.token_bytes(file_size))
                    elif pass_num == 1:
                        # Second pass: all zeros
                        f.write(b'\x00' * file_size)
                    else:
                        # Final pass: all ones
                        f.write(b'\xFF' * file_size)
                    
                    f.flush()
                    os.fsync(f.fileno())
            
            # Remove the file
            file_path.unlink()
            
            self.logger.debug(f"Securely deleted file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to securely delete {file_path}: {e}")
            return False
    
    def set_file_permissions(self, file_path: Path, mode: int) -> bool:
        """
        Set file permissions.
        
        Args:
            file_path: Path to file
            mode: Permission mode (e.g., 0o600)
            
        Returns:
            True if successful
        """
        try:
            os.chmod(file_path, mode)
            self.logger.debug(f"Set permissions {oct(mode)} on: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set permissions on {file_path}: {e}")
            return False
    
    def verify_file_permissions(self, file_path: Path, expected_mode: int) -> bool:
        """
        Verify file has expected permissions.
        
        Args:
            file_path: Path to file
            expected_mode: Expected permission mode
            
        Returns:
            True if permissions match
        """
        try:
            current_mode = file_path.stat().st_mode & 0o777
            return current_mode == expected_mode
        except Exception as e:
            self.logger.error(f"Failed to verify permissions on {file_path}: {e}")
            return False
    
    def cleanup_all(self) -> None:
        """Clean up all temporary files and directories."""
        # Clean up files
        for temp_file in self.temp_files[:]:
            self._secure_cleanup_file(temp_file)
        
        # Clean up directories
        for temp_dir in self.temp_dirs[:]:
            self._secure_cleanup_dir(temp_dir)
        
        # Clear encryption keys from memory
        self.encrypted_files.clear()
        
        self.logger.debug("Completed cleanup of all temporary files and directories")
    
    def _secure_cleanup_file(self, file_path: Path) -> None:
        """Securely clean up a temporary file."""
        try:
            if file_path in self.temp_files:
                self.temp_files.remove(file_path)
            
            if file_path in self.encrypted_files:
                self.encrypted_files.pop(file_path, None)
            
            if file_path.exists():
                self.secure_delete_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp file {file_path}: {e}")
    
    def _secure_cleanup_dir(self, dir_path: Path) -> None:
        """Securely clean up a temporary directory."""
        try:
            if dir_path in self.temp_dirs:
                self.temp_dirs.remove(dir_path)
            
            if dir_path.exists():
                # Securely delete all files in directory first
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        self.secure_delete_file(file_path)
                
                # Remove directory structure
                import shutil
                shutil.rmtree(dir_path)
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp dir {dir_path}: {e}")
    
    def get_encryption_key(self) -> bytes:
        """
        Get the encryption key for this manager.
        
        Returns:
            Encryption key as bytes
        """
        return self._encryption_key
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.cleanup_all()
        except Exception:
            pass  # Ignore errors during destruction


class SecureFileHandle:
    """
    Secure file handle wrapper that provides encrypted I/O operations.
    """
    
    def __init__(self, file_path: Path, mode: str = 'rb', 
                 encryption_key: Optional[bytes] = None):
        """
        Initialize secure file handle.
        
        Args:
            file_path: Path to file
            mode: File open mode
            encryption_key: Encryption key for encrypted operations
        """
        self.file_path = file_path
        self.mode = mode
        self._file_handle: Optional[BinaryIO] = None
        self._fernet = Fernet(encryption_key) if encryption_key else None
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Enter context manager."""
        self._file_handle = open(self.file_path, self.mode)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def write_encrypted(self, data: Union[str, bytes]) -> int:
        """
        Write encrypted data to file.
        
        Args:
            data: Data to encrypt and write
            
        Returns:
            Number of bytes written
        """
        if not self._fernet:
            raise ValueError("No encryption key provided")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self._fernet.encrypt(data)
        return self._file_handle.write(encrypted_data)
    
    def read_encrypted(self, size: int = -1) -> bytes:
        """
        Read and decrypt data from file.
        
        Args:
            size: Number of bytes to read (-1 for all)
            
        Returns:
            Decrypted data as bytes
        """
        if not self._fernet:
            raise ValueError("No encryption key provided")
        
        encrypted_data = self._file_handle.read(size)
        if not encrypted_data:
            return b''
        
        return self._fernet.decrypt(encrypted_data)
    
    def write(self, data: Union[str, bytes]) -> int:
        """
        Write data to file (unencrypted).
        
        Args:
            data: Data to write
            
        Returns:
            Number of bytes written
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return self._file_handle.write(data)
    
    def read(self, size: int = -1) -> bytes:
        """
        Read data from file (unencrypted).
        
        Args:
            size: Number of bytes to read (-1 for all)
            
        Returns:
            Data as bytes
        """
        return self._file_handle.read(size)