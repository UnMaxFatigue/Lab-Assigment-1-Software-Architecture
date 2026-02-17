from typing import Optional, List, Callable
from models import Vehicule, Rental, User, GPSLocation, TelemetryData
from regulations import Regulation
from services import PersistenceManager, AuditLogger
from datetime import datetime
from models import RentalStatus, State
from vehicules import Bike, Moped, Scooter


class SmartMoveCentralController:
    vehicules: List[Vehicule]
    users: List[User]
    rentals: List[Rental]
    regulations: List[Regulation]
    persistenceManager: PersistenceManager
    auditLogger: Optional[AuditLogger]

    def __init__(
        self,
        persistenceManager: PersistenceManager,
        auditLogger: Optional[AuditLogger] = None,
        regulations: List[Regulation] = None

    ) -> None:
        self.vehicules = []
        self.users = []
        self.rentals = []
        self.regulations = regulations
        self.persistenceManager = persistenceManager
        self.auditLogger = auditLogger
    
    def loadData(self) -> None:
        """Load all data from repositories at startup."""
        self.vehicules, self.users, self.rentals = self.persistenceManager.loadAll()
        if self.auditLogger:
            self.auditLogger.logEvent("DATA_LOADED")
    
    def saveData(self) -> bool:
        """Save all data to repositories with automatic rollback."""
        success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
        if not success:
            # Restore from disk on failure
            self.vehicules, self.users, self.rentals = v, u, r
        return success
    
    def rentVehicule(self, vehicule: Vehicule, user: User, scheduledStartTime: datetime) -> Optional[Rental]:
        """Create a rental reservation for a vehicule."""
        # Validate vehicle state
        if vehicule.state != State.AVAILABLE:
            print(f"Cannot rent vehicle {vehicule.vehiculeId}: Vehicle is {vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("RENTAL_REJECTED_STATE")
            return None
        
        # Validate vehicle doesn't have an active rental
        if vehicule.hasActiveRental:
            print(f"Cannot rent vehicle {vehicule.vehiculeId}: Vehicle already has an active rental")
            if self.auditLogger:
                self.auditLogger.logEvent("RENTAL_REJECTED_ACTIVE")
            return None
        
        # Validate telemetry (battery and temperature)
        if not vehicule.telemetryData.isHealthy():
            print(f"Cannot rent vehicle {vehicule.vehiculeId}: Vehicle telemetry is unhealthy")
            print(f"Battery: {vehicule.telemetryData.batteryLevel}%, Temperature: {vehicule.telemetryData.temperature}°C")
            if self.auditLogger:
                self.auditLogger.logEvent("RENTAL_REJECTED_TELEMETRY")
            return None
        
        # Create rental
        rental = Rental(user, vehicule, scheduledStartTime)
        self.rentals.append(rental)
        
        # Mark vehicle as reserved (prevent double booking)
        vehicule.changeState(State.RESERVED)
        vehicule.hasActiveRental = True
        
        if self.auditLogger:
            self.auditLogger.logEvent("VEHICLE_RESERVED")
        
        # Save immediately to persist reservation
        self.saveData()
        
        return rental

    def activateRental(self, rental: Rental) -> bool:
        """Activate a rental and mark vehicule as in use."""
        # Validate rental is in RESERVED state
        if rental.status != RentalStatus.RESERVED:
            print(f"Cannot activate rental: Rental status is {rental.status.value}, expected RESERVED")
            if self.auditLogger:
                self.auditLogger.logEvent("ACTIVATION_REJECTED_STATUS")
            return False
        
        # Validate vehicle state
        if rental.vehicule.state not in [State.AVAILABLE, State.RESERVED]:
            print(f"Cannot activate rental: Vehicle is {rental.vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("ACTIVATION_REJECTED_STATE")
            return False

        # Pre-trip regulation checks (unlock constraints)
        if self.regulations and not self.regulations.applyPreTripRegulation(rental.vehicule, rental):
            print("Cannot activate rental: Pre-trip regulation check failed")
            rental.status = RentalStatus.CANCELLED
            if self.auditLogger:
                self.auditLogger.logEvent("ACTIVATION_REJECTED_REGULATION")
            return False
        
        # Validate telemetry before activation
        if not rental.vehicule.telemetryData.isHealthy():
            print(f"Cannot activate rental: Vehicle telemetry is unhealthy")
            print(f"Battery: {rental.vehicule.telemetryData.batteryLevel}%, Temperature: {rental.vehicule.telemetryData.temperature}°C")
            rental.status = RentalStatus.CANCELLED
            if self.auditLogger:
                self.auditLogger.logEvent("ACTIVATION_REJECTED_TELEMETRY")
            return False
        
        # Change rental status to ACTIVE, set actualStartTime
        rental.status = RentalStatus.ACTIVE
        rental.actualStartTime = datetime.now()
        
        # Change vehicule state to INUSE and hasActiveRental to True
        rental.vehicule.changeState(State.INUSE)
        rental.vehicule.hasActiveRental = True
        
        if self.auditLogger:
            self.auditLogger.logEvent("RENTAL_ACTIVATED")
        
        # Save immediately to persist activation
        self.saveData()
        
        return True

    def returnVehicule(self, rental: Rental, emergency: bool = False, reason: str = "") -> bool:
        """Return a rented vehicule and complete the rental (normal or emergency)."""
        # Validate rental is ACTIVE
        if rental.status != RentalStatus.ACTIVE:
            print(f"Cannot return vehicle: Rental status is {rental.status.value}, expected ACTIVE")
            if self.auditLogger:
                self.auditLogger.logEvent("RETURN_REJECTED_STATUS")
            return False
        
        try:
            # Set end time
            rental.endTime = datetime.now()
            
            if emergency:
                # EMERGENCY TERMINATION
                print(f"EMERGENCY TERMINATION: {reason}")
                rental.status = RentalStatus.CANCELLED
                rental.vehicule.changeState(State.EMERGENCYLOCK)
                rental.vehicule.hasActiveRental = False
                
                if self.auditLogger:
                    self.auditLogger.logEvent(f"EMERGENCY_TERMINATION: {reason}")
            else:
                # NORMAL RETURN
                rental.status = RentalStatus.COMPLETED
                
                # Calculate base cost
                rental.calculateRentalCost()
                
                # Apply city-specific post-trip regulations
                if self.regulations:
                    self.regulations.applyPostTripRegulation(rental.vehicule, rental)
                
                # Change vehicle state to available
                rental.vehicule.changeState(State.AVAILABLE)
                rental.vehicule.hasActiveRental = False
                
                if self.auditLogger:
                    self.auditLogger.logEvent("VEHICLE_RETURNED")
            
            # Save with automatic rollback on failure
            success, (v, u, r) = self.persistenceManager.saveAll(
                self.vehicules, self.users, self.rentals
            )
            
            if not success:
                # Restore from disk
                self.vehicules, self.users, self.rentals = v, u, r
            
            return success
            
        except Exception as e:
            print(f"Return/termination failed: {e}")
            return False

    def processTelemetryData(self, vehicule: Vehicule, newTelemetryData) -> None:
        """
        Process telemetry data received from a vehicule.
        Handles: battery monitoring, temperature alerts, and theft detection.
        """
        # Store previous location for theft detection
        previous_location = vehicule.lastKnownLocation
        
        # Update telemetry
        vehicule.updateTelemetry(newTelemetryData)

        is_overheating = vehicule.telemetryData.temperature >= 60
        is_battery_critical = vehicule.telemetryData.batteryLevel <= 5
        active_rental = self.findActiveRental(vehicule) if vehicule.hasActiveRental else None

        if is_overheating:
            if active_rental:
                self.slowDownVehicle(vehicule, "overheating detected")
                self.returnVehicule(active_rental, emergency=True, reason="Overheating detected")
                return
            if vehicule.state != State.EMERGENCYLOCK:
                print(f"Vehicle {vehicule.vehiculeId} is overheating, so initiating Emergency Lock.")
                vehicule.changeState(State.EMERGENCYLOCK)
                if self.auditLogger:
                    self.auditLogger.logEvent(f"EMERGENCY_LOCK_OVERHEAT: Vehicle {vehicule.vehiculeId}")
                self.saveData()

        if is_battery_critical:
            if active_rental:
                self.slowDownVehicle(vehicule, "battery critically low")
                self.returnVehicule(active_rental, emergency=True, reason="Battery critically low")
                return
            if vehicule.state != State.MAINTENANCE:
                print(f"Vehicle {vehicule.vehiculeId} became battery low, so schedule maintenance.")
                vehicule.changeState(State.MAINTENANCE)
                if self.auditLogger:
                    self.auditLogger.logEvent(f"MAINTENANCE_BATTERY_LOW: Vehicle {vehicule.vehiculeId}")
                self.saveData()
        
        # Update last known location
        if newTelemetryData.location:
            vehicule.lastKnownLocation = newTelemetryData.location

        if self.regulations:
            self.regulations.applyInTripRegulation(vehicule, active_rental)
        
        # THEFT DETECTION: Check if vehicle moved without active rental
        if previous_location and vehicule.lastKnownLocation:
            if not vehicule.hasActiveRental:
                # Check if moved beyond threshold (~100 meters = 0.001 degrees)
                lat_diff = abs(previous_location.latitude - vehicule.lastKnownLocation.latitude)
                lon_diff = abs(previous_location.longitude - vehicule.lastKnownLocation.longitude)
                if lat_diff > 0.001 or lon_diff > 0.001:
                    # THEFT DETECTED
                    print(f"THEFT ALARM: Vehicle {vehicule.vehiculeId} is moving without active rental!")
                    vehicule.changeState(State.EMERGENCYLOCK)
                    if self.auditLogger:
                        self.auditLogger.logEvent(f"THEFT_DETECTED: Vehicle {vehicule.vehiculeId}")
                    self.saveData()

        
        if self.auditLogger:
            self.auditLogger.logEvent(f"TELEMETRY_PROCESSED: Vehicle {vehicule.vehiculeId}")
    
    def slowDownVehicle(self, vehicule: Vehicule, reason: str) -> None:
        """Request vehicle to slow down (hardware integration point)."""
        pass
    
    def findActiveRental(self, vehicule: Vehicule) -> Optional[Rental]:
        """Find the active rental for a given vehicle."""
        for rental in self.rentals:
            if rental.vehicule.vehiculeId == vehicule.vehiculeId and rental.status == RentalStatus.ACTIVE:
                return rental
        return None

    def unlockVehicule(self, vehicule: Vehicule, reason: str = "") -> bool:
        """Manually unlock a vehicle from EMERGENCYLOCK."""
        if vehicule.state != State.EMERGENCYLOCK:
            print(f"Cannot unlock vehicle {vehicule.vehiculeId}: Vehicle is {vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("UNLOCK_REJECTED_STATE")
            return False

        if vehicule.hasActiveRental:
            print(f"Cannot unlock vehicle {vehicule.vehiculeId}: Active rental in progress")
            if self.auditLogger:
                self.auditLogger.logEvent("UNLOCK_REJECTED_ACTIVE")
            return False

        vehicule.changeState(State.AVAILABLE)
        if self.auditLogger:
            msg = f"EMERGENCY_UNLOCK: Vehicle {vehicule.vehiculeId}"
            if reason:
                msg = f"{msg} - {reason}"
            self.auditLogger.logEvent(msg)
        return self.saveData()

    def assignMaintenance(self, vehicle: Vehicule) -> bool: pass

    def completeMaintenance(self, vehicule: Vehicule) -> bool:
        """Manually end maintenance and restore availability."""
        if vehicule.state != State.MAINTENANCE:
            print(f"Cannot complete maintenance: Vehicle {vehicule.vehiculeId} is {vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("MAINTENANCE_COMPLETE_REJECTED_STATE")
            return False

        if vehicule.telemetryData.batteryLevel <= 20:
            print(f"Cannot complete maintenance: Vehicle {vehicule.vehiculeId} battery still low")
            if self.auditLogger:
                self.auditLogger.logEvent("MAINTENANCE_COMPLETE_REJECTED_BATTERY")
            return False

        vehicule.changeState(State.AVAILABLE)
        if self.auditLogger:
            self.auditLogger.logEvent(f"MAINTENANCE_COMPLETED: Vehicle {vehicule.vehiculeId}")
        return self.saveData()

    def relocateVehicule(self, vehicule: Vehicule, reason: str = "") -> bool:
        """Mark a vehicle as relocating for operator rebalancing."""
        if vehicule.state != State.AVAILABLE:
            print(f"Cannot relocate vehicle {vehicule.vehiculeId}: Vehicle is {vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("RELOCATION_REJECTED_STATE")
            return False

        vehicule.changeState(State.RELOCATING)
        if self.auditLogger:
            msg = f"RELOCATION_STARTED: Vehicle {vehicule.vehiculeId}"
            if reason:
                msg = f"{msg} - {reason}"
            self.auditLogger.logEvent(msg)
        return self.saveData()

    def completeRelocation(self, vehicule: Vehicule) -> bool:
        """Finish relocation and return vehicle to availability."""
        if vehicule.state != State.RELOCATING:
            print(f"Cannot complete relocation: Vehicle {vehicule.vehiculeId} is {vehicule.state.value}")
            if self.auditLogger:
                self.auditLogger.logEvent("RELOCATION_COMPLETE_REJECTED_STATE")
            return False

        vehicule.changeState(State.AVAILABLE)
        if self.auditLogger:
            self.auditLogger.logEvent(f"RELOCATION_COMPLETED: Vehicle {vehicule.vehiculeId}")
        return self.saveData()
    
    def registerUser(self, username:str) -> bool:
        
        if self.findUserByName(username) is not None:
            return False
        
        self.users.append(username)

        if self.saveData():
            self.auditLogger.logEvent(f"USER {username} REGISTERD")
            return True
        else:
            return False
    
    def registerVehicle(self, vehicleId:int, vehicleType:str) -> bool:
        
        if self.getVehicleFromId(vehicleId) is not None:
            return False
        
        if vehicleType == "bycicle":
            vehicle = Bike(vehicleId, 80, 20, State.AVAILABLE)
        elif vehicleType == "scooter":
            vehicle = Scooter(vehicleId, 80, 20, State.AVAILABLE)
        elif vehicleType == "moped":
            vehicle = Moped(vehicleId, 80, 20, State.AVAILABLE)
        else:
            return False

        self.vehicules.append(vehicle)

        if self.saveData():
            self.auditLogger(f"VEHICLE {vehicle.vehiculeId} REGISTERD")
            return True
        else:      
            return False

    def findUserByName(self, username:str) -> bool:
        return username in self.users

    def getVehicleFromId(self, vehicleId:int) -> Optional[Vehicule]:
        for vehicle in self.vehicules:
            if vehicle.vehiculeId == vehicleId:
                return vehicle
        return None

    def getRentalFromNameId(self, username:str, vehicleId:int) -> Optional[Rental]:
        for rental in self.rentals:
            if (rental.user.name == username
                and rental.vehicule.vehiculeId == vehicleId
                and (rental.status.ACTIVE or rental.status.RESERVED)):
                return rental
        return None
