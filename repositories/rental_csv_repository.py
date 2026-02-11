from typing import List
from models import Rental


class RentalCSVRepository:
    """CSV implementation of rental repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/rentals.csv") -> None:
        self.filePath = filePath
    
    def save(self, rentals: List[Rental]) -> None:
        #TODO: Implement CSV save logic
        pass
    
    def load(self) -> List[Rental]:
        #TODO: Implement CSV load logic
        pass
