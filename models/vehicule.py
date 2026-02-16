from abc import ABC, abstractmethod
from typing import Optional
from .state import State
from .telemetry_data import TelemetryData
from .gps_location import GPSLocation

class Vehicule(ABC):
    """Abstract base class for all vehicles with robust state machine."""
    
    vehiculeId: int
    telemetryData: TelemetryData
    state: State
    lastKnownLocation: Optional[GPSLocation]  # For theft detection
    hasActiveRental: bool  # Tracks if currently rented
    
    def __init__(self, vehiculeId: int, batteryLevel: int, temperature: int, state: State) -> None:
        self.vehiculeId = vehiculeId
        self.telemetryData = TelemetryData(batteryLevel, temperature)
        self.state = state
        self.lastKnownLocation = None
        self.hasActiveRental = False

    def updateTelemetry(self, telemetryData: TelemetryData) -> None:
        self.telemetryData = telemetryData

    def changeState(self, newState: State) -> None:
        if self.state == State.MAINTENANCE and newState == State.INUSE:
            print(f"Not possible to change Vehicle {self.vehiculeId} from MAINTENANCE to IN USE")
            return
        
        print(f"Vehicle {self.vehiculeId} is changing state from {self.state} to {newState}")
        self.state = newState