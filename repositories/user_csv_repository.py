from typing import List
from models import User


class UserCSVRepository:
    """CSV implementation of user repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/users.csv") -> None:
        self.filePath = filePath
    
    def save(self, users: List[User]) -> None:
        #TODO: Implement CSV save logic
        pass
    
    def load(self) -> List[User]:
        #TODO: Implement CSV load logic
        return []
    
