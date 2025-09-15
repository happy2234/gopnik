"""
Cryptographic utilities for hashing, signing, and validation.
"""

import hashlib
import secrets
import base64
from pathlib import Path
from typing import Optional, Tuple, Union
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature


class CryptographicUtils:
    """
    Provides cryptographic operations for document integrity and audit trails.
    
    Handles SHA-256 hashing, RSA/ECDSA digital signatures, and secure random generation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._rsa_private_key = None
        self._rsa_public_key = None
        self._ec_private_key = None
        self._ec_public_key = None
    
    @staticmethod
    def generate_sha256_hash(file_path: Path) -> str:
        """
        Generate SHA-256 hash of a file.
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            Hexadecimal SHA-256 hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def generate_sha256_hash_from_bytes(data: bytes) -> str:
        """
        Generate SHA-256 hash from byte data.
        
        Args:
            data: Byte data to hash
            
        Returns:
            Hexadecimal SHA-256 hash string
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def generate_secure_id() -> str:
        """
        Generate cryptographically secure random ID.
        
        Returns:
            Secure random hexadecimal string
        """
        return secrets.token_hex(16)
    
    @staticmethod
    def generate_secure_bytes(length: int) -> bytes:
        """
        Generate cryptographically secure random bytes.
        
        Args:
            length: Number of bytes to generate
            
        Returns:
            Secure random bytes
        """
        return secrets.token_bytes(length)
    
    def generate_rsa_key_pair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair for digital signatures.
        
        Args:
            key_size: RSA key size in bits (default: 2048)
            
        Returns:
            Tuple of (private_key_pem, public_key_pem) as bytes
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self._rsa_private_key = private_key
        self._rsa_public_key = public_key
        
        return private_pem, public_pem
    
    def generate_ec_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate ECDSA key pair for digital signatures.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem) as bytes
        """
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self._ec_private_key = private_key
        self._ec_public_key = public_key
        
        return private_pem, public_pem
    
    def load_rsa_private_key(self, private_key_pem: Union[str, bytes]) -> None:
        """
        Load RSA private key from PEM format.
        
        Args:
            private_key_pem: Private key in PEM format
        """
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode()
        
        self._rsa_private_key = load_pem_private_key(private_key_pem, password=None)
        self._rsa_public_key = self._rsa_private_key.public_key()
    
    def load_rsa_public_key(self, public_key_pem: Union[str, bytes]) -> None:
        """
        Load RSA public key from PEM format.
        
        Args:
            public_key_pem: Public key in PEM format
        """
        if isinstance(public_key_pem, str):
            public_key_pem = public_key_pem.encode()
        
        self._rsa_public_key = load_pem_public_key(public_key_pem)
    
    def load_ec_private_key(self, private_key_pem: Union[str, bytes]) -> None:
        """
        Load ECDSA private key from PEM format.
        
        Args:
            private_key_pem: Private key in PEM format
        """
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode()
        
        self._ec_private_key = load_pem_private_key(private_key_pem, password=None)
        self._ec_public_key = self._ec_private_key.public_key()
    
    def load_ec_public_key(self, public_key_pem: Union[str, bytes]) -> None:
        """
        Load ECDSA public key from PEM format.
        
        Args:
            public_key_pem: Public key in PEM format
        """
        if isinstance(public_key_pem, str):
            public_key_pem = public_key_pem.encode()
        
        self._ec_public_key = load_pem_public_key(public_key_pem)
    
    def sign_data_rsa(self, data: Union[str, bytes]) -> str:
        """
        Generate RSA digital signature for data.
        
        Args:
            data: Data to sign
            
        Returns:
            Base64-encoded digital signature string
            
        Raises:
            ValueError: If RSA private key is not loaded
        """
        if self._rsa_private_key is None:
            raise ValueError("RSA private key not loaded. Call generate_rsa_key_pair() or load_rsa_private_key() first.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        signature = self._rsa_private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature_rsa(self, data: Union[str, bytes], signature: str) -> bool:
        """
        Verify RSA digital signature for data.
        
        Args:
            data: Original data
            signature: Base64-encoded signature to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Raises:
            ValueError: If RSA public key is not loaded
        """
        if self._rsa_public_key is None:
            raise ValueError("RSA public key not loaded. Call generate_rsa_key_pair() or load_rsa_public_key() first.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            signature_bytes = base64.b64decode(signature)
            self._rsa_public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, Exception) as e:
            self.logger.debug(f"RSA signature verification failed: {e}")
            return False
    
    def sign_data_ecdsa(self, data: Union[str, bytes]) -> str:
        """
        Generate ECDSA digital signature for data.
        
        Args:
            data: Data to sign
            
        Returns:
            Base64-encoded digital signature string
            
        Raises:
            ValueError: If ECDSA private key is not loaded
        """
        if self._ec_private_key is None:
            raise ValueError("ECDSA private key not loaded. Call generate_ec_key_pair() or load_ec_private_key() first.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        signature = self._ec_private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature_ecdsa(self, data: Union[str, bytes], signature: str) -> bool:
        """
        Verify ECDSA digital signature for data.
        
        Args:
            data: Original data
            signature: Base64-encoded signature to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Raises:
            ValueError: If ECDSA public key is not loaded
        """
        if self._ec_public_key is None:
            raise ValueError("ECDSA public key not loaded. Call generate_ec_key_pair() or load_ec_public_key() first.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            signature_bytes = base64.b64decode(signature)
            self._ec_public_key.verify(signature_bytes, data, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, Exception) as e:
            self.logger.debug(f"ECDSA signature verification failed: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def sign_data(self, data: str, private_key: Optional[str] = None) -> str:
        """
        Generate digital signature for data using RSA (legacy method).
        
        Args:
            data: Data to sign
            private_key: Private key for signing (ignored, uses loaded key)
            
        Returns:
            Digital signature string
        """
        return self.sign_data_rsa(data)
    
    def verify_signature(self, data: str, signature: str, public_key: Optional[str] = None) -> bool:
        """
        Verify digital signature for data using RSA (legacy method).
        
        Args:
            data: Original data
            signature: Signature to verify
            public_key: Public key for verification (ignored, uses loaded key)
            
        Returns:
            True if signature is valid
        """
        return self.verify_signature_rsa(data, signature)