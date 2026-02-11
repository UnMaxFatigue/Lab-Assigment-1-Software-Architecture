from datetime import datetime
from typing import Optional
from .gps_location import GPSLocation


class TelemetryData:
    """Vehicle telemetry data including health indicators."""
    
    batteryLevel: int  # 0-100 %
    temperature: int  # °C
    timeStamp: datetime
    location: Optional[GPSLocation]
    isFaulted: bool  # Hardware fault flag
    
    def __init__(
        self,
        batteryLevel: int,
        temperature: int,
        location: Optional[GPSLocation] = None,
        isFaulted: bool = False
    ) -> None:
        self.batteryLevel = max(0, min(100, batteryLevel))  # Clamp to 0-100
        self.temperature = temperature
        self.timeStamp = datetime.now()
        self.location = location
        self.isFaulted = isFaulted
    
    def isHealthy(self) -> bool:
        """Quick check if vehicle has no critical issues."""
        return not self.isFaulted and self.batteryLevel > 20 and self.temperature < 50
