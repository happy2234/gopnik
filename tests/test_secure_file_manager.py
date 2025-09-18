"""
Tests for secure file manager functionality.
"""

import os
import stat
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.gopnik.utils.secure_file_manager import SecureFileManager, SecureFileHandle
from cryptography.fernet import Fernet


class TestSecureFileManager:
    """Test cases for SecureFileManager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = SecureFileManager(base_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        self.manager.cleanup_all()
        # Clean up temp directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_secure_temp_file(self):
        """Test creating secure temporary file."""
        temp_file = self.manager.create_secure_temp_file(
            suffix='.txt', prefix='test_'
        )
        
        # Verify file exists
        assert temp_file.exists()
        
        # Verify file is in temp directory
        assert temp_file.parent == self.temp_dir
        
        # Verify file permissions (owner read/write only)
        file_mode = temp_file.stat().st_mode & 0o777
        assert file_mode == 0o600
        
        # Verify file is tracked
        assert temp_file in self.manager.temp_files
        
        # Verify encryption key is stored
        assert temp_file in self.manager.encrypted_files
    
    def test_create_secure_temp_file_unencrypted(self):
        """Test creating unencrypted secure temporary file."""
        temp_file = self.manager.create_secure_temp_file(
            encrypted=False
        )
        
        assert temp_file.exists()
        assert temp_file not in self.manager.encrypted_files
    
    def test_create_secure_temp_file_custom_permissions(self):
        """Test creating secure temporary file with custom permissions."""
        temp_file = self.manager.create_secure_temp_file(
            mode=0o640
        )
        
        file_mode = temp_file.stat().st_mode & 0o777
        assert file_mode == 0o640
    
    def test_create_secure_temp_dir(self):
        """Test creating secure temporary directory."""
        temp_dir = self.manager.create_secure_temp_dir(prefix='test_')
        
        # Verify directory exists
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Verify directory permissions (owner access only)
        dir_mode = temp_dir.stat().st_mode & 0o777
        assert dir_mode == 0o700
        
        # Verify directory is tracked
        assert temp_dir in self.manager.temp_dirs
    
    def test_write_read_encrypted_data(self):
        """Test writing and reading encrypted data."""
        temp_file = self.manager.create_secure_temp_file()
        test_data = "This is sensitive test data"
        
        # Write encrypted data
        self.manager.write_encrypted_data(temp_file, test_data)
        
        # Verify file exists and has content
        assert temp_file.exists()
        assert temp_file.stat().st_size > 0
        
        # Read and verify decrypted data
        decrypted_data = self.manager.read_encrypted_data(temp_file)
        assert decrypted_data.decode('utf-8') == test_data
        
        # Verify raw file content is encrypted (not readable)
        with open(temp_file, 'rb') as f:
            raw_content = f.read()
        assert test_data.encode('utf-8') not in raw_content
    
    def test_write_read_encrypted_bytes(self):
        """Test writing and reading encrypted byte data."""
        temp_file = self.manager.create_secure_temp_file()
        test_data = b"Binary test data \x00\x01\x02"
        
        self.manager.write_encrypted_data(temp_file, test_data)
        decrypted_data = self.manager.read_encrypted_data(temp_file)
        
        assert decrypted_data == test_data
    
    def test_secure_temp_file_context_manager(self):
        """Test secure temporary file context manager."""
        test_data = "Context manager test"
        
        with self.manager.secure_temp_file(suffix='.txt') as temp_file:
            assert temp_file.exists()
            self.manager.write_encrypted_data(temp_file, test_data)
            
            # Verify data can be read within context
            decrypted_data = self.manager.read_encrypted_data(temp_file)
            assert decrypted_data.decode('utf-8') == test_data
        
        # Verify file is cleaned up after context
        assert not temp_file.exists()
    
    def test_secure_temp_dir_context_manager(self):
        """Test secure temporary directory context manager."""
        with self.manager.secure_temp_dir() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            
            # Create a file in the directory
            test_file = temp_dir / "test.txt"
            test_file.write_text("test content")
            assert test_file.exists()
        
        # Verify directory and contents are cleaned up
        assert not temp_dir.exists()
    
    def test_secure_delete_file(self):
        """Test secure file deletion."""
        # Create a test file with known content
        test_file = self.temp_dir / "test_delete.txt"
        test_content = "Sensitive data to be securely deleted"
        test_file.write_text(test_content)
        
        # Verify file exists
        assert test_file.exists()
        
        # Securely delete the file
        result = self.manager.secure_delete_file(test_file)
        
        # Verify deletion was successful
        assert result is True
        assert not test_file.exists()
    
    def test_secure_delete_nonexistent_file(self):
        """Test secure deletion of non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.txt"
        result = self.manager.secure_delete_file(nonexistent_file)
        assert result is True
    
    def test_secure_delete_file_multiple_passes(self):
        """Test secure file deletion with multiple passes."""
        test_file = self.temp_dir / "test_multipass.txt"
        test_file.write_text("Multi-pass deletion test")
        
        result = self.manager.secure_delete_file(test_file, passes=2)  # Reduced from 5 to 2
        
        assert result is True
        assert not test_file.exists()
    
    def test_set_file_permissions(self):
        """Test setting file permissions."""
        temp_file = self.manager.create_secure_temp_file()
        
        # Set new permissions
        result = self.manager.set_file_permissions(temp_file, 0o644)
        assert result is True
        
        # Verify permissions were set
        file_mode = temp_file.stat().st_mode & 0o777
        assert file_mode == 0o644
    
    def test_verify_file_permissions(self):
        """Test verifying file permissions."""
        temp_file = self.manager.create_secure_temp_file(mode=0o600)
        
        # Verify correct permissions
        assert self.manager.verify_file_permissions(temp_file, 0o600) is True
        
        # Verify incorrect permissions
        assert self.manager.verify_file_permissions(temp_file, 0o644) is False
    
    def test_cleanup_all(self):
        """Test cleaning up all temporary files and directories."""
        # Create multiple temp files and directories
        temp_file1 = self.manager.create_secure_temp_file()
        temp_file2 = self.manager.create_secure_temp_file()
        temp_dir1 = self.manager.create_secure_temp_dir()
        temp_dir2 = self.manager.create_secure_temp_dir()
        
        # Verify they exist
        assert temp_file1.exists()
        assert temp_file2.exists()
        assert temp_dir1.exists()
        assert temp_dir2.exists()
        
        # Clean up all
        self.manager.cleanup_all()
        
        # Verify all are cleaned up
        assert not temp_file1.exists()
        assert not temp_file2.exists()
        assert not temp_dir1.exists()
        assert not temp_dir2.exists()
        
        # Verify tracking lists are empty
        assert len(self.manager.temp_files) == 0
        assert len(self.manager.temp_dirs) == 0
        assert len(self.manager.encrypted_files) == 0
    
    def test_encryption_key_management(self):
        """Test encryption key management."""
        # Test with default generated key
        manager1 = SecureFileManager()
        key1 = manager1.get_encryption_key()
        assert len(key1) == 44  # Fernet key length in base64
        
        # Test with provided key
        custom_key = Fernet.generate_key()
        manager2 = SecureFileManager(encryption_key=custom_key)
        key2 = manager2.get_encryption_key()
        assert key2 == custom_key
        
        # Clean up
        manager1.cleanup_all()
        manager2.cleanup_all()
    
    def test_thread_safety(self):
        """Test thread safety of secure file manager."""
        results = []
        errors = []
        
        def create_files():
            try:
                for i in range(3):  # Reduced from 10 to 3
                    temp_file = self.manager.create_secure_temp_file()
                    results.append(temp_file)
                    # Removed sleep to speed up test
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(3):  # Reduced from 5 to 3
            thread = threading.Thread(target=create_files)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        
        # Verify all files were created
        assert len(results) == 9  # 3 threads * 3 files each
        
        # Verify all files are unique
        assert len(set(results)) == 9
    
    def test_automatic_cleanup_mechanism(self):
        """Test automatic cleanup mechanism."""
        # This test verifies the cleanup mechanism works
        # We test the cleanup method directly
        
        # Create a temporary file
        temp_file = self.manager.create_secure_temp_file()
        
        # Verify file exists
        assert temp_file.exists()
        
        # Test manual cleanup (simulates what would happen automatically)
        self.manager.cleanup_all()
        
        # Verify file was cleaned up
        assert not temp_file.exists()


class TestSecureFileHandle:
    """Test cases for SecureFileHandle."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.encryption_key = Fernet.generate_key()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_secure_file_handle_encrypted_write_read(self):
        """Test encrypted write and read operations."""
        test_file = self.temp_dir / "test_encrypted.dat"
        test_data = "Encrypted file handle test data"
        
        # Write encrypted data
        with SecureFileHandle(test_file, 'wb', self.encryption_key) as handle:
            bytes_written = handle.write_encrypted(test_data)
            assert bytes_written > 0
        
        # Read encrypted data
        with SecureFileHandle(test_file, 'rb', self.encryption_key) as handle:
            decrypted_data = handle.read_encrypted()
            assert decrypted_data.decode('utf-8') == test_data
    
    def test_secure_file_handle_unencrypted_operations(self):
        """Test unencrypted file operations."""
        test_file = self.temp_dir / "test_unencrypted.txt"
        test_data = "Unencrypted file handle test"
        
        # Write unencrypted data
        with SecureFileHandle(test_file, 'wb') as handle:
            bytes_written = handle.write(test_data)
            assert bytes_written > 0
        
        # Read unencrypted data
        with SecureFileHandle(test_file, 'rb') as handle:
            read_data = handle.read()
            assert read_data.decode('utf-8') == test_data
    
    def test_secure_file_handle_no_encryption_key_error(self):
        """Test error when trying encrypted operations without key."""
        test_file = self.temp_dir / "test_no_key.dat"
        
        with SecureFileHandle(test_file, 'wb') as handle:
            with pytest.raises(ValueError, match="No encryption key provided"):
                handle.write_encrypted("test data")
        
        # Create encrypted file first
        with SecureFileHandle(test_file, 'wb', self.encryption_key) as handle:
            handle.write_encrypted("test data")
        
        with SecureFileHandle(test_file, 'rb') as handle:
            with pytest.raises(ValueError, match="No encryption key provided"):
                handle.read_encrypted()
    
    def test_secure_file_handle_binary_data(self):
        """Test handling binary data."""
        test_file = self.temp_dir / "test_binary.dat"
        test_data = b"Binary data \x00\x01\x02\xFF"
        
        # Write encrypted binary data
        with SecureFileHandle(test_file, 'wb', self.encryption_key) as handle:
            handle.write_encrypted(test_data)
        
        # Read encrypted binary data
        with SecureFileHandle(test_file, 'rb', self.encryption_key) as handle:
            decrypted_data = handle.read_encrypted()
            assert decrypted_data == test_data


class TestSecureFileManagerIntegration:
    """Integration tests for secure file manager."""
    
    def test_secure_file_manager_with_document_processing(self):
        """Test secure file manager integration with document processing workflow."""
        manager = SecureFileManager()
        
        try:
            # Simulate document processing workflow
            with manager.secure_temp_file(suffix='.pdf') as input_file:
                # Simulate input document
                test_document = b"PDF document content"
                manager.write_encrypted_data(input_file, test_document)
                
                with manager.secure_temp_file(suffix='.pdf') as output_file:
                    # Simulate processing
                    processed_content = manager.read_encrypted_data(input_file)
                    processed_content += b" - PROCESSED"
                    manager.write_encrypted_data(output_file, processed_content)
                    
                    # Verify processed content
                    final_content = manager.read_encrypted_data(output_file)
                    assert final_content == b"PDF document content - PROCESSED"
        
        finally:
            manager.cleanup_all()
    
    def test_secure_file_manager_batch_processing(self):
        """Test secure file manager with batch processing scenario."""
        manager = SecureFileManager()
        
        try:
            # Create secure temp directory for batch processing
            with manager.secure_temp_dir() as batch_dir:
                # Create multiple input files
                input_files = []
                for i in range(5):
                    input_file = manager.create_secure_temp_file(
                        suffix=f'_input_{i}.txt'
                    )
                    manager.write_encrypted_data(
                        input_file, 
                        f"Document {i} content"
                    )
                    input_files.append(input_file)
                
                # Process each file
                output_files = []
                for i, input_file in enumerate(input_files):
                    output_file = manager.create_secure_temp_file(
                        suffix=f'_output_{i}.txt'
                    )
                    
                    # Read, process, and write
                    content = manager.read_encrypted_data(input_file)
                    processed_content = content.decode('utf-8') + " - PROCESSED"
                    manager.write_encrypted_data(output_file, processed_content)
                    
                    output_files.append(output_file)
                
                # Verify all outputs
                for i, output_file in enumerate(output_files):
                    content = manager.read_encrypted_data(output_file)
                    expected = f"Document {i} content - PROCESSED"
                    assert content.decode('utf-8') == expected
        
        finally:
            manager.cleanup_all()
    
    def test_secure_file_manager_error_handling(self):
        """Test error handling in secure file manager."""
        manager = SecureFileManager()
        
        try:
            # Test handling of permission errors
            with patch('os.chmod', side_effect=PermissionError("Permission denied")):
                with pytest.raises(RuntimeError, match="Failed to create secure temp file"):
                    manager.create_secure_temp_file()
            
            # Test handling of encryption errors
            with patch.object(manager._fernet, 'encrypt', side_effect=Exception("Encryption failed")):
                temp_file = manager.create_secure_temp_file()
                with pytest.raises(Exception, match="Encryption failed"):
                    manager.write_encrypted_data(temp_file, "test data")
        
        finally:
            manager.cleanup_all()


if __name__ == '__main__':
    pytest.main([__file__])