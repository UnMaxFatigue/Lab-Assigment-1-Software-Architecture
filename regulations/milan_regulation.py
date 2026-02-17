import random
from typing import Optional
from models import Vehicule
from models import Rental
from vehicules import Moped
from .regulation import Regulation


class MilanRegulation(Regulation):

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
