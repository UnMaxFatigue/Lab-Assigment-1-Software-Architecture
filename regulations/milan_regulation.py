from models import Vehicule
from models import Rental
from models import State
from .regulation import Regulation


class MilanRegulation(Regulation):
    def applyRegulation(self, vehicule: Vehicule,rental: Rental) -> None:
        #TODO: Implement the logic to apply the Milan regulation to the given vehicule
       # pretend helmet sensor
        helmetPresent = True

        if not helmetPresent:
            print("Helmet missing → Cannot unlock")
            vehicule.changeState(State.EMERGENCYLOCK)
