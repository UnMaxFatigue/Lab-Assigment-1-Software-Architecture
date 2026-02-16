from models import Vehicule
from models import Rental
from .regulation import Regulation


class LondonRegulation(Regulation):
    def applyRegulation(self, vehicule: Vehicule, rental: Rental) -> None:
        #TODO: Implement the logic to apply the London regulation to the given vehicule
       congestion_charge = 5

       if rental.cost is None:
            rental.cost = 0

       rental.cost += congestion_charge
       print(" Congestion charge added")
