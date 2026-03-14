from typing import TYPE_CHECKING
import hashlib
import os

if TYPE_CHECKING:
    from .vehicule import Vehicule


class User:
    name: str
    password_hash: str
    password_salt: str
    
    def __init__(self, name: str, password_hash: str = "", password_salt: str = "") -> None:
        self.name = name
        self.password_hash = password_hash
        self.password_salt = password_salt
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _pbkdf2_hash(password: str, salt: bytes, iterations: int = 200_000) -> str:
        """Derive a password hash using PBKDF2-HMAC-SHA256."""
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return derived.hex()
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if self.password_salt:
            salt = bytes.fromhex(self.password_salt)
            return self.password_hash == User._pbkdf2_hash(password, salt)
        # Legacy fallback for older users without salt
        return self.password_hash == User.hash_password(password)
    
    def set_password(self, password: str) -> None:
        """Set a new password."""
        salt = os.urandom(16)
        self.password_salt = salt.hex()
        self.password_hash = User._pbkdf2_hash(password, salt)
