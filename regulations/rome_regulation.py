from models import Vehicule
from models import Rental
from vehicules import Scooter
from .regulation import Regulation


class RomeRegulation(Regulation):
    def applyRegulation(self, vehicule: Vehicule,rental: Rental) -> None:
        #TODO: Implement the logic to apply the Rome regulation to the given vehicule
    
     # only scooters have zone restriction
        if isinstance(vehicule, Scooter):
           
         if vehicule.lastKnownLocation is not None:
                lat = vehicule.lastKnownLocation.latitude
                print( vehicule.lastKnownLocation.latitude)

                if lat > 40.0:  #test restricted rule
                    print("Restricted zone , 10€ fine")

                    if rental.cost is None:
                        rental.cost = 0

                    rental.cost += 10