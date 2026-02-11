from typing import List
from models import Vehicule


class VehiculeCSVRepository:
    """CSV implementation of vehicule repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/vehicules.csv") -> None:
        self.filePath = filePath
    
    def save(self, vehicules: List[Vehicule]) -> None:
        #TODO: Implement CSV save logic
        pass
    
    def load(self) -> List[Vehicule]:
        #TODO: Implement CSV load logic
        pass    
        
