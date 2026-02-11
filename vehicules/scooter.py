from models import Vehicule, State


class Scooter(Vehicule):  
    def __init__(self, vehiculeId: int, batteryLevel: int, temperature: int, state: State) -> None:
        super().__init__(vehiculeId, batteryLevel, temperature, state)
