from abc import ABC, abstractmethod
from typing import Optional
from models import Vehicule, Rental, GPSLocation


class Regulation(ABC):
    @abstractmethod
    def applyPreTripRegulation(self, vehicule: Vehicule, rental: Rental) -> bool:
        pass

    @abstractmethod
    def applyInTripRegulation(self, vehicule: Vehicule, rental: Optional[Rental]) -> None:
        pass

    @abstractmethod
    def applyPostTripRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        pass
    
    @abstractmethod
    def isInJurisdiction(self, location: GPSLocation) -> bool:
        """Check if a GPS location is within this regulation's jurisdiction."""
        pass
