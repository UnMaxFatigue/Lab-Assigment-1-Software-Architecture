import random
from typing import Optional
from models import Vehicule, GPSLocation
from models import Rental
from vehicules import Moped
from .regulation import Regulation


class MilanRegulation(Regulation):
    def isInJurisdiction(self, location: GPSLocation) -> bool:
        """Check if location is in Milan (approximately 45.3-45.6°N, 9.0-9.4°E)."""
        return (45.3 <= location.latitude <= 45.6 and 
                9.0 <= location.longitude <= 9.4)

    def applyPreTripRegulation(self, vehicule: Vehicule, rental: Rental) -> bool:
        if not isinstance(vehicule, Moped):
            return True

        if not self.checkHelmetSensor():
            print("Helmet missing. Cannot unlock moped.")
            return False

        return True

    def applyInTripRegulation(self, vehicule: Vehicule, rental: Optional[Rental]) -> None:
        pass

    def applyPostTripRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        pass

    def checkHelmetSensor(self) -> bool:
        """Stub for hardware helmet sensor integration."""
        return random.choice([True, False])
