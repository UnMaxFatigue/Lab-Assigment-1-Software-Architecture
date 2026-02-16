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
        #TODO: Implement the logic to calculate the duration of the rental for the user with the given vehiculeId
        if self.actualStartTime is not None and self.endTime is not None:
            duration_seconds = (self.endTime - self.actualStartTime).total_seconds()
            return duration_seconds / 60 
        return None
        pass

    def calculateRentalCost(self) -> float:
        #TODO: Implement the logic to calculate the cost of the rental for the user with the given vehiculeId
        # Assuming 0.5 as the cost for 1 minute
        duration = self.calculateRentalDuration()
        if duration is not None:
            self.cost = duration * 0.5
            return self.cost
        return 0.0
