from abc import ABC, abstractmethod
from typing import Optional
from .state import State
from .telemetry_data import TelemetryData
from .gps_location import GPSLocation

class Vehicule(ABC):
    """Abstract base class for all vehicles with robust state machine."""

    _ALLOWED_TRANSITIONS = {
        State.AVAILABLE: {State.AVAILABLE, State.RESERVED, State.MAINTENANCE, State.EMERGENCYLOCK, State.RELOCATING},
        State.RESERVED: {State.RESERVED, State.INUSE, State.AVAILABLE, State.EMERGENCYLOCK, State.MAINTENANCE},
        State.INUSE: {State.INUSE, State.AVAILABLE, State.MAINTENANCE, State.EMERGENCYLOCK},
        State.MAINTENANCE: {State.MAINTENANCE, State.AVAILABLE, State.EMERGENCYLOCK},
        State.EMERGENCYLOCK: {State.EMERGENCYLOCK, State.AVAILABLE, State.MAINTENANCE},
        State.RELOCATING: {State.RELOCATING, State.AVAILABLE},
    }
    
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
        if newState not in self._ALLOWED_TRANSITIONS.get(self.state, set()):
            print(f"Not possible to change Vehicle {self.vehiculeId} from {self.state} to {newState}")
            return
        
        print(f"Vehicle {self.vehiculeId} is changing state from {self.state} to {newState}")
        self.state = newState
