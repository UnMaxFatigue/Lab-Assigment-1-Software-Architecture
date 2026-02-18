from typing import TYPE_CHECKING
import hashlib

if TYPE_CHECKING:
    from .vehicule import Vehicule


class User:
    name: str
    password_hash: str
    
    def __init__(self, name: str, password_hash: str = "") -> None:
        self.name = name
        self.password_hash = password_hash
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return self.password_hash == User.hash_password(password)
    
    def set_password(self, password: str) -> None:
        """Set a new password."""
        self.password_hash = User.hash_password(password)
