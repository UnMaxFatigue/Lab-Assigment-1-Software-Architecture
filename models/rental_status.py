from enum import Enum


class RentalStatus(Enum):
    RESERVED = "RESERVED"        # Future reservation (scheduledStartTime in future)
    ACTIVE = "ACTIVE"            # Rental in progress (actualStartTime set, endTime None)
    COMPLETED = "COMPLETED"      # Rental completed (actualStartTime and endTime set)
    CANCELLED = "CANCELLED"      # Cancelled
