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
    
  
       if self.telemetryData.temperature >= 60:
        print(f"Vehicle {self.vehiculeId} is overheating, so initiating Emergency Lock.")
        self.changeState(State.EMERGENCY_LOCK)
    
       if self.telemetryData.batteryLevel <= 5:
        print(f"Vehicle {self.vehiculeId} became battery low, so schedule maintenance.")
        self.changeState(State.MAINTENANCE)

    def changeState(self, newState: State) -> None:
        if self.state == State.MAINTENANCE and newState == State.IN_USE:
            print(f"Not possible to change Vehicle {self.vehiculeId} from MAINTENANCE to IN USE")
            return
        
        print(f"Vehicle {self.vehiculeId} is changing state from {self.state} to {newState}")
        self.state = newState