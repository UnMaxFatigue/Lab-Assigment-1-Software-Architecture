from typing import Optional
from models import Vehicule, GPSLocation
from models import Rental
from .regulation import Regulation


class LondonRegulation(Regulation):
    def __init__(self, congestion_charge: float = 5.0) -> None:
        self.congestion_charge = congestion_charge
    
    def isInJurisdiction(self, location: GPSLocation) -> bool:
        """Check if location is in London (approximately 51.3-51.7°N, -0.5-0.3°W)."""
        return (51.3 <= location.latitude <= 51.7 and 
                -0.5 <= location.longitude <= 0.3)

    def applyPreTripRegulation(self, vehicule: Vehicule, rental: Rental) -> bool:
        return True

    def applyInTripRegulation(self, vehicule: Vehicule, rental: Optional[Rental]) -> None:
        pass

    def applyPostTripRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        #TODO: Implement the logic to apply the London regulation to the given vehicule
        if rental.cost is None:
            rental.cost = 0

        rental.cost += self.congestion_charge
        print(" Congestion charge added")
