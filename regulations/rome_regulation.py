from typing import Optional
from models import Vehicule, GPSLocation
from models import Rental
from models import State
from vehicules import Scooter
from .regulation import Regulation


RESTRICTED_ZONES = [
    (41.8902, 41.8922, 12.4920, 12.4940),
    (41.9020, 41.9040, 12.4950, 12.4970),
    (41.9060, 41.9080, 12.4980, 12.5000),
]


class RomeRegulation(Regulation):
    def isInJurisdiction(self, location: GPSLocation) -> bool:
        """Check if location is in Rome (approximately 41.7-42.0°N, 12.3-12.7°E)."""
        return (41.7 <= location.latitude <= 42.0 and 
                12.3 <= location.longitude <= 12.7)
    
    def applyPreTripRegulation(self, vehicule: Vehicule, rental: Rental) -> bool:
        return True

    def applyInTripRegulation(self, vehicule: Vehicule, rental: Optional[Rental]) -> None:
        # Only scooters have zone restriction
        if not isinstance(vehicule, Scooter):
            return

        location = vehicule.lastKnownLocation
        if location is None:
            return

        for min_lat, max_lat, min_lon, max_lon in RESTRICTED_ZONES:
            if min_lat <= location.latitude <= max_lat and min_lon <= location.longitude <= max_lon:
                print("Restricted zone detected, locking vehicle")
                vehicule.changeState(State.EMERGENCYLOCK)
                return

    def applyPostTripRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        pass

