"""
Unit tests for cryptographic utilities.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.gopnik.utils.crypto import CryptographicUtils


class TestCryptographicUtils:
    """Test suite for CryptographicUtils class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.crypto = CryptographicUtils()
    
    def test_generate_sha256_hash_from_bytes(self):
        """Test SHA-256 hash generation from bytes."""
        test_data = b"Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        result = self.crypto.generate_sha256_hash_from_bytes(test_data)
        
        assert result == expected_hash
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64-character hex string
    
    def test_generate_sha256_hash_from_file(self):
        """Test SHA-256 hash generation from file."""
        test_content = b"Test file content for hashing"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = Path(temp_file.name)
        
        try:
            result = self.crypto.generate_sha256_hash(temp_file_path)
            expected_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
            
            assert result == expected_hash
            assert isinstance(result, str)
            assert len(result) == 64
        finally:
            os.unlink(temp_file_path)
    
    def test_generate_secure_id(self):
        """Test secure ID generation."""
        id1 = self.crypto.generate_secure_id()
        id2 = self.crypto.generate_secure_id()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) == 32  # 16 bytes = 32 hex characters
        assert len(id2) == 32
        assert id1 != id2  # Should be unique
        
        # Test multiple generations for uniqueness
        ids = [self.crypto.generate_secure_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All should be unique
    
    def test_generate_secure_bytes(self):
        """Test secure bytes generation."""
        length = 32
        bytes1 = self.crypto.generate_secure_bytes(length)
        bytes2 = self.crypto.generate_secure_bytes(length)
        
        assert isinstance(bytes1, bytes)
        assert isinstance(bytes2, bytes)
        assert len(bytes1) == length
        assert len(bytes2) == length
        assert bytes1 != bytes2  # Should be unique
    
    def test_rsa_key_generation(self):
        """Test RSA key pair generation."""
        private_pem, public_pem = self.crypto.generate_rsa_key_pair()
        
        assert isinstance(private_pem, bytes)
        assert isinstance(public_pem, bytes)
        assert b"BEGIN PRIVATE KEY" in private_pem
        assert b"END PRIVATE KEY" in private_pem
        assert b"BEGIN PUBLIC KEY" in public_pem
        assert b"END PUBLIC KEY" in public_pem
        
        # Test different key sizes
        private_pem_4096, public_pem_4096 = self.crypto.generate_rsa_key_pair(4096)
        assert len(private_pem_4096) > len(private_pem)  # Larger key should be longer
    
    def test_ecdsa_key_generation(self):
        """Test ECDSA key pair generation."""
        private_pem, public_pem = self.crypto.generate_ec_key_pair()
        
        assert isinstance(private_pem, bytes)
        assert isinstance(public_pem, bytes)
        assert b"BEGIN PRIVATE KEY" in private_pem
        assert b"END PRIVATE KEY" in private_pem
        assert b"BEGIN PUBLIC KEY" in public_pem
        assert b"END PUBLIC KEY" in public_pem
    
    def test_rsa_signing_and_verification(self):
        """Test RSA digital signature generation and verification."""
        # Generate key pair
        self.crypto.generate_rsa_key_pair()
        
        test_data = "This is test data for signing"
        
        # Sign the data
        signature = self.crypto.sign_data_rsa(test_data)
        
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Verify the signature
        is_valid = self.crypto.verify_signature_rsa(test_data, signature)
        assert is_valid is True
        
        # Test with modified data (should fail)
        modified_data = "This is modified test data"
        is_valid_modified = self.crypto.verify_signature_rsa(modified_data, signature)
        assert is_valid_modified is False
        
        # Test with bytes input
        test_bytes = b"Test bytes data"
        signature_bytes = self.crypto.sign_data_rsa(test_bytes)
        is_valid_bytes = self.crypto.verify_signature_rsa(test_bytes, signature_bytes)
        assert is_valid_bytes is True
    
    def test_ecdsa_signing_and_verification(self):
        """Test ECDSA digital signature generation and verification."""
        # Generate key pair
        self.crypto.generate_ec_key_pair()
        
        test_data = "This is test data for ECDSA signing"
        
        # Sign the data
        signature = self.crypto.sign_data_ecdsa(test_data)
        
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Verify the signature
        is_valid = self.crypto.verify_signature_ecdsa(test_data, signature)
        assert is_valid is True
        
        # Test with modified data (should fail)
        modified_data = "This is modified test data"
        is_valid_modified = self.crypto.verify_signature_ecdsa(modified_data, signature)
        assert is_valid_modified is False
        
        # Test with bytes input
        test_bytes = b"Test bytes data for ECDSA"
        signature_bytes = self.crypto.sign_data_ecdsa(test_bytes)
        is_valid_bytes = self.crypto.verify_signature_ecdsa(test_bytes, signature_bytes)
        assert is_valid_bytes is True
    
    def test_rsa_key_loading(self):
        """Test RSA key loading from PEM format."""
        # Generate and extract keys
        private_pem, public_pem = self.crypto.generate_rsa_key_pair()
        
        # Create new instance and load keys
        crypto2 = CryptographicUtils()
        crypto2.load_rsa_private_key(private_pem)
        crypto2.load_rsa_public_key(public_pem)
        
        # Test signing with original and verification with loaded keys
        test_data = "Cross-instance key test"
        signature = self.crypto.sign_data_rsa(test_data)
        is_valid = crypto2.verify_signature_rsa(test_data, signature)
        assert is_valid is True
        
        # Test with string input
        crypto3 = CryptographicUtils()
        crypto3.load_rsa_private_key(private_pem.decode())
        crypto3.load_rsa_public_key(public_pem.decode())
        
        signature2 = crypto3.sign_data_rsa(test_data)
        is_valid2 = self.crypto.verify_signature_rsa(test_data, signature2)
        assert is_valid2 is True
    
    def test_ecdsa_key_loading(self):
        """Test ECDSA key loading from PEM format."""
        # Generate and extract keys
        private_pem, public_pem = self.crypto.generate_ec_key_pair()
        
        # Create new instance and load keys
        crypto2 = CryptographicUtils()
        crypto2.load_ec_private_key(private_pem)
        crypto2.load_ec_public_key(public_pem)
        
        # Test signing with original and verification with loaded keys
        test_data = "Cross-instance ECDSA key test"
        signature = self.crypto.sign_data_ecdsa(test_data)
        is_valid = crypto2.verify_signature_ecdsa(test_data, signature)
        assert is_valid is True
        
        # Test with string input
        crypto3 = CryptographicUtils()
        crypto3.load_ec_private_key(private_pem.decode())
        crypto3.load_ec_public_key(public_pem.decode())
        
        signature2 = crypto3.sign_data_ecdsa(test_data)
        is_valid2 = self.crypto.verify_signature_ecdsa(test_data, signature2)
        assert is_valid2 is True
    
    def test_legacy_methods(self):
        """Test legacy signing methods for backward compatibility."""
        # Generate RSA key pair for legacy methods
        self.crypto.generate_rsa_key_pair()
        
        test_data = "Legacy method test"
        
        # Test legacy sign_data method
        signature = self.crypto.sign_data(test_data)
        assert isinstance(signature, str)
        
        # Test legacy verify_signature method
        is_valid = self.crypto.verify_signature(test_data, signature)
        assert is_valid is True
    
    def test_error_handling_no_keys(self):
        """Test error handling when keys are not loaded."""
        test_data = "Test data"
        
        # Test RSA without keys
        with pytest.raises(ValueError, match="RSA private key not loaded"):
            self.crypto.sign_data_rsa(test_data)
        
        with pytest.raises(ValueError, match="RSA public key not loaded"):
            self.crypto.verify_signature_rsa(test_data, "fake_signature")
        
        # Test ECDSA without keys
        with pytest.raises(ValueError, match="ECDSA private key not loaded"):
            self.crypto.sign_data_ecdsa(test_data)
        
        with pytest.raises(ValueError, match="ECDSA public key not loaded"):
            self.crypto.verify_signature_ecdsa(test_data, "fake_signature")
    
    def test_invalid_signature_verification(self):
        """Test verification with invalid signatures."""
        # Generate keys
        self.crypto.generate_rsa_key_pair()
        
        test_data = "Test data"
        invalid_signature = "invalid_base64_signature"
        
        # Should return False for invalid signature
        is_valid = self.crypto.verify_signature_rsa(test_data, invalid_signature)
        assert is_valid is False
        
        # Test with ECDSA
        self.crypto.generate_ec_key_pair()
        is_valid_ecdsa = self.crypto.verify_signature_ecdsa(test_data, invalid_signature)
        assert is_valid_ecdsa is False
    
    def test_large_file_hashing(self):
        """Test SHA-256 hashing with large files."""
        # Create a large temporary file
        large_content = b"A" * (1024 * 1024)  # 1MB of 'A' characters
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(large_content)
            temp_file_path = Path(temp_file.name)
        
        try:
            result = self.crypto.generate_sha256_hash(temp_file_path)
            expected_hash = self.crypto.generate_sha256_hash_from_bytes(large_content)
            
            assert result == expected_hash
            assert len(result) == 64
        finally:
            os.unlink(temp_file_path)
    
    def test_signature_determinism(self):
        """Test that signatures are different for the same data (due to randomness in padding)."""
        self.crypto.generate_rsa_key_pair()
        
        test_data = "Same data for multiple signatures"
        
        # Generate multiple signatures for the same data
        signature1 = self.crypto.sign_data_rsa(test_data)
        signature2 = self.crypto.sign_data_rsa(test_data)
        
        # Signatures should be different due to PSS padding randomness
        assert signature1 != signature2
        
        # But both should verify correctly
        assert self.crypto.verify_signature_rsa(test_data, signature1) is True
        assert self.crypto.verify_signature_rsa(test_data, signature2) is True