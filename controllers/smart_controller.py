from typing import Optional
from models import Vehicule, Rental, User
from regulations import Regulation
from services import PersistenceManager, AuditLogger


class SmartMoveCentralController:
    vehicules: list[Vehicule]
    users: list[User]
    rentals: list[Rental]
    regulations: Optional[Regulation]
    persistenceManager: PersistenceManager
    auditLogger: Optional[AuditLogger]

    def __init__(
        self,
        persistenceManager: PersistenceManager,
        auditLogger: Optional[AuditLogger] = None
    ) -> None:
        self.vehicules = []
        self.users = []
        self.rentals = []
        self.regulations = None
        self.persistenceManager = persistenceManager
        self.auditLogger = auditLogger
    
    def loadData(self) -> None:
        """Load all data from repositories at startup."""
        self.vehicules, self.users, self.rentals = self.persistenceManager.loadAll()
        if self.auditLogger:
            self.auditLogger.logEvent("DATA_LOADED")
    
    def saveData(self) -> None:
        """Save all data to repositories."""
        self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
        if self.auditLogger:
            self.auditLogger.logEvent("DATA_SAVED")
    
    def findVehicule(self, vehiculeId: int) -> Optional[Vehicule]:
        """Find a vehicule by its ID."""
        for vehicule in self.vehicules:
            if vehicule.vehiculeId == vehiculeId:
                return vehicule
        return None
    
    def rentVehicule(self, vehicule: Vehicule) -> Rental:
        #TODO: Implement the logic to rent a vehicule to the user with the given vehicule 
        # Create rebtak
        # Change vehicule state to IN_USE
        # Log event
        pass

    def activateRental(self, rental: Rental) -> None:
        #TODO: Implement the logic to activate a rental for the user with the given rental
        # Change rental status to ACTIVE, set actualStartTime
        # Change vehicule state to IN_USE and hasActiveRental to True
        # Log event
        pass

    def returnVehicule(self, rental: Rental) -> None:
        #TODO: Implement the logic to return a vehicule from the user with the given the rental
        # Change rental status to COMPLETED, set endTime, calculate cost
        # Change vehicule state to AVAILABLE
        # Log event
        pass

    def processTelemetryData(self, vehicule: Vehicule) -> None:
        #TODO: Implement the logic to process the telemetry data received from the vehicule with the given vehiculeId
        pass

    def applyRegulations(self, vehicule: Vehicule) -> None:
        #TODO: Implement the logic to apply the regulations to the given vehicule
        pass
