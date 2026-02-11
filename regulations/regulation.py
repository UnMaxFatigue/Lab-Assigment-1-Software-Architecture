from abc import ABC, abstractmethod
from models import Vehicule


class Regulation(ABC):
    @abstractmethod
    def applyRegulation(self, vehicule: Vehicule) -> None:
        pass
