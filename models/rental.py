from datetime import datetime
from typing import Optional
from .user import User
from .vehicule import Vehicule
from .rental_status import RentalStatus


class Rental:
    user: User
    vehicule: Vehicule
    scheduledStartTime: datetime  # When the rental is scheduled to start (can be future)
    actualStartTime: Optional[datetime]  # When the rental actually started (after activation)
    endTime: Optional[datetime]  # When the rental ends
    cost: Optional[float]  # Cost (calculated after endTime)
    status: RentalStatus  # Status: RESERVED, ACTIVE, COMPLETED, CANCELLED
    
    def __init__(self, user: User, vehicule: Vehicule, scheduledStartTime: datetime) -> None:
        self.user = user
        self.vehicule = vehicule
        self.scheduledStartTime = scheduledStartTime
        self.actualStartTime = None
        self.endTime = None
        self.cost = None
        self.status = RentalStatus.RESERVED

    def calculateRentalDuration(self) -> Optional[float]:
        if self.actualStartTime is not None and self.endTime is not None:
            duration_seconds = (self.endTime - self.actualStartTime).total_seconds()
            duration_minutes = duration_seconds / 60
            # Prevent negative duration (edge case handling)
            return max(0.0, duration_minutes)
        return None
        

    def calculateRentalCost(self) -> float:
        # Assuming 0.5 as the cost for 1 minute
        duration = self.calculateRentalDuration()
        if duration is not None:
            self.cost = duration * 0.5
            return self.cost
        return 0.0
