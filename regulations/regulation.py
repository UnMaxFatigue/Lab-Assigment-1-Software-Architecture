from abc import ABC, abstractmethod
from models import Vehicule,Rental


class Regulation(ABC):
    @abstractmethod
    def applyRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        pass
