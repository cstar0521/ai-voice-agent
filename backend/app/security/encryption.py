"""
PII Encryption utilities for securing sensitive data.

This module provides field-level encryption for PII (Personally Identifiable Information)
using Fernet symmetric encryption from cryptography library.
"""

import os
import base64
import logging
from typing import Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class PIIEncryption:
    """
    Handles encryption and decryption of PII fields.
    
    Uses Fernet symmetric encryption with a key derived from
    a master password/key stored in environment variables.
    """
    
    # Fields that should be encrypted
    PII_FIELDS = {"phone", "name", "email", "address"}
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption handler.
        
        Args:
            encryption_key: Base64-encoded encryption key (defaults to env var)
        """
        key = encryption_key or os.getenv("ENCRYPTION_KEY")
        
        if not key:
            logger.warning(
                "ENCRYPTION_KEY not set. Generating temporary key. "
                "Set ENCRYPTION_KEY environment variable for production!"
            )
            key = Fernet.generate_key().decode()
        
        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode()
        
        try:
            self.fernet = Fernet(key)
            logger.info("PIIEncryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            raise
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Master password
            salt: Optional salt (generated if not provided)
        
        Returns:
            Tuple of (key, salt) as base64-encoded strings
        """
        if salt is None:
            salt = os.urandom(16)
        elif isinstance(salt, str):
            salt = base64.b64decode(salt)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        salt_b64 = base64.b64encode(salt).decode()
        
        return key.decode(), salt_b64
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            value: Plain text value to encrypt
        
        Returns:
            Encrypted value as base64 string
        """
        if not value:
            return value
        
        try:
            encrypted = self.fernet.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted value.
        
        Args:
            encrypted_value: Encrypted value as base64 string
        
        Returns:
            Decrypted plain text value
        """
        if not encrypted_value:
            return encrypted_value
        
        try:
            decrypted = self.fernet.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_dict(self, data: dict, fields: Optional[set] = None) -> dict:
        """
        Encrypt specified fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            fields: Set of field names to encrypt (defaults to PII_FIELDS)
        
        Returns:
            Dictionary with encrypted fields
        """
        if fields is None:
            fields = self.PII_FIELDS
        
        encrypted_data = data.copy()
        
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
                    encrypted_data[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field}: {str(e)}")
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields: Optional[set] = None) -> dict:
        """
        Decrypt specified fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields: Set of field names to decrypt (defaults to PII_FIELDS)
        
        Returns:
            Dictionary with decrypted fields
        """
        if fields is None:
            fields = self.PII_FIELDS
        
        decrypted_data = data.copy()
        
        for field in fields:
            if field in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                    decrypted_data.pop(f"{field}_encrypted", None)
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {str(e)}")
        
        return decrypted_data
    
    def mask_pii(self, value: str, field_type: str = "phone") -> str:
        """
        Mask PII for logging and display.
        
        Args:
            value: Value to mask
            field_type: Type of field (phone, email, name)
        
        Returns:
            Masked value
        """
        if not value:
            return value
        
        if field_type == "phone":
            # Mask phone: +91XXXXXX3210 -> +91******3210
            if len(value) > 6:
                return value[:3] + "*" * (len(value) - 7) + value[-4:]
            return "*" * len(value)
        
        elif field_type == "email":
            # Mask email: john@example.com -> j***@example.com
            if "@" in value:
                local, domain = value.split("@", 1)
                if len(local) > 2:
                    return local[0] + "*" * (len(local) - 1) + "@" + domain
                return "*" * len(local) + "@" + domain
            return "*" * len(value)
        
        elif field_type == "name":
            # Mask name: John Doe -> J*** D***
            parts = value.split()
            masked_parts = []
            for part in parts:
                if len(part) > 1:
                    masked_parts.append(part[0] + "*" * (len(part) - 1))
                else:
                    masked_parts.append("*")
            return " ".join(masked_parts)
        
        else:
            # Generic masking
            if len(value) > 4:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
            return "*" * len(value)
    
    def mask_dict(self, data: dict, fields: Optional[set] = None) -> dict:
        """
        Mask PII fields in dictionary for logging.
        
        Args:
            data: Dictionary containing data
            fields: Set of field names to mask (defaults to PII_FIELDS)
        
        Returns:
            Dictionary with masked fields
        """
        if fields is None:
            fields = self.PII_FIELDS
        
        masked_data = data.copy()
        
        for field in fields:
            if field in masked_data and masked_data[field]:
                masked_data[field] = self.mask_pii(
                    str(masked_data[field]),
                    field_type=field
                )
        
        return masked_data


class SecureLogger:
    """
    Logger wrapper that automatically masks PII in log messages.
    """
    
    def __init__(self, logger_name: str, encryption: Optional[PIIEncryption] = None):
        """
        Initialize secure logger.
        
        Args:
            logger_name: Name of the logger
            encryption: PIIEncryption instance for masking
        """
        self.logger = logging.getLogger(logger_name)
        self.encryption = encryption or PIIEncryption()
    
    def _mask_message(self, message: str, context: Optional[dict] = None) -> str:
        """
        Mask PII in log message.
        
        Args:
            message: Log message
            context: Optional context dictionary
        
        Returns:
            Masked message
        """
        # If context provided, mask PII fields
        if context:
            masked_context = self.encryption.mask_dict(context)
            return f"{message} | Context: {masked_context}"
        
        return message
    
    def info(self, message: str, context: Optional[dict] = None):
        """Log info message with PII masking."""
        self.logger.info(self._mask_message(message, context))
    
    def warning(self, message: str, context: Optional[dict] = None):
        """Log warning message with PII masking."""
        self.logger.warning(self._mask_message(message, context))
    
    def error(self, message: str, context: Optional[dict] = None):
        """Log error message with PII masking."""
        self.logger.error(self._mask_message(message, context))
    
    def debug(self, message: str, context: Optional[dict] = None):
        """Log debug message with PII masking."""
        self.logger.debug(self._mask_message(message, context))
