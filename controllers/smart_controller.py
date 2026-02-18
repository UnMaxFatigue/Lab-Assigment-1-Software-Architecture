from typing import Optional, List, Callable
from models import Vehicule, Rental, User, GPSLocation, TelemetryData
from regulations import Regulation
from services import PersistenceManager, AuditLogger
from datetime import datetime
from models import RentalStatus, State
from vehicules import Bike, Moped, Scooter
import threading
import time
import random


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
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._monitoring_enabled = False
        self._telemetry_monitor_thread = None
    
    def loadData(self) -> None:
        """Load all data from repositories at startup."""
        with self._lock:
            self.vehicules, self.users, self.rentals = self.persistenceManager.loadAll()
            
            # Fix rental references: associate with actual vehicles and users
            for rental in self.rentals:
                # Find the actual vehicle by ID
                actual_vehicle = None
                for vehicle in self.vehicules:
                    if vehicle.vehiculeId == rental.vehicule.vehiculeId:
                        actual_vehicle = vehicle
                        break
                
                if actual_vehicle:
                    rental.vehicule = actual_vehicle
                else:
                    print(f"[WARNING] Rental references non-existent vehicle ID: {rental.vehicule.vehiculeId}")
                
                # Find the actual user by name
                actual_user = self.findUserByName(rental.user.name)
                if actual_user:
                    rental.user = actual_user
                else:
                    print(f"[WARNING] Rental references non-existent user: {rental.user.name}")
            
            # Synchronize vehicle states with active rentals
            for rental in self.rentals:
                if rental.status == RentalStatus.RESERVED:
                    rental.vehicule.state = State.RESERVED
                    rental.vehicule.hasActiveRental = True
                elif rental.status == RentalStatus.ACTIVE:
                    rental.vehicule.state = State.INUSE
                    rental.vehicule.hasActiveRental = True
            
            if self.auditLogger:
                self.auditLogger.logEvent("DATA_LOADED")
    
    def findUserByName(self, name: str) -> Optional[User]:
        """Find user by username (case-sensitive)."""
        for user in self.users:
            if user.name == name:
                return user
        return None
    
    def saveData(self) -> bool:
        """Save all data to repositories with automatic rollback."""
        with self._lock:
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                # Restore from disk on failure
                self.vehicules, self.users, self.rentals = v, u, r
            return success
    
    def rentVehicule(self, vehicule: Vehicule, user: User, scheduledStartTime: datetime) -> Optional[Rental]:
        """Create a rental reservation for a vehicule."""
        with self._lock:
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
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            
            return rental

    def activateRental(self, rental: Rental) -> tuple[bool, Optional[str]]:
        """Activate a rental and mark vehicule as in use. Returns (success, error_message)."""
        with self._lock:
            # Validate rental is in RESERVED state
            if rental.status != RentalStatus.RESERVED:
                error_msg = f"Rental status is {rental.status.value}, expected RESERVED"
                print(f"Cannot activate rental: {error_msg}")
                if self.auditLogger:
                    self.auditLogger.logEvent("ACTIVATION_REJECTED_STATUS")
                return False, error_msg
            
            # Validate vehicle state
            if rental.vehicule.state not in [State.AVAILABLE, State.RESERVED]:
                error_msg = f"Vehicle is {rental.vehicule.state.value}"
                print(f"Cannot activate rental: {error_msg}")
                if self.auditLogger:
                    self.auditLogger.logEvent("ACTIVATION_REJECTED_STATE")
                return False, error_msg

            # Pre-trip regulation checks (unlock constraints)
            if self.regulations:
                # Filter regulations by jurisdiction based on vehicle location
                applicable_regulations = []
                vehicle_location = rental.vehicule.lastKnownLocation
                
                if vehicle_location:
                    for regulation in self.regulations:
                        if regulation.isInJurisdiction(vehicle_location):
                            applicable_regulations.append(regulation)
                else:
                    # If no location data, apply all regulations (fail-safe)
                    applicable_regulations = self.regulations
                
                for regulation in applicable_regulations:
                    if not regulation.applyPreTripRegulation(rental.vehicule, rental):
                        error_msg = "Pre-trip regulation check failed (helmet missing)"
                        print(f"Cannot activate rental: {error_msg}")
                        # Cancel rental and release vehicle
                        rental.status = RentalStatus.CANCELLED
                        rental.vehicule.changeState(State.AVAILABLE)
                        rental.vehicule.hasActiveRental = False
                        self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                        if self.auditLogger:
                            self.auditLogger.logEvent("ACTIVATION_REJECTED_REGULATION")
                        return False, error_msg
            
            # Validate telemetry before activation
            if not rental.vehicule.telemetryData.isHealthy():
                error_msg = f"Vehicle telemetry is unhealthy (Battery: {rental.vehicule.telemetryData.batteryLevel}%, Temperature: {rental.vehicule.telemetryData.temperature}°C)"
                print(f"Cannot activate rental: {error_msg}")
                # Cancel rental and release vehicle
                rental.status = RentalStatus.CANCELLED
                rental.vehicule.changeState(State.AVAILABLE)
                rental.vehicule.hasActiveRental = False
                self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                if self.auditLogger:
                    self.auditLogger.logEvent("ACTIVATION_REJECTED_TELEMETRY")
                return False, error_msg
            
            # Change rental status to ACTIVE, set actualStartTime
            rental.status = RentalStatus.ACTIVE
            rental.actualStartTime = datetime.now()
            
            # Change vehicule state to INUSE and hasActiveRental to True
            rental.vehicule.changeState(State.INUSE)
            rental.vehicule.hasActiveRental = True
            
            if self.auditLogger:
                self.auditLogger.logEvent("RENTAL_ACTIVATED")
            
            # Save immediately to persist activation
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            
            return True, None
            
            return True

    def cancelRental(self, rental: Rental) -> bool:
        """Cancel a reserved rental (only works if status is RESERVED)."""
        with self._lock:
            # Validate rental is RESERVED
            if rental.status != RentalStatus.RESERVED:
                print(f"Cannot cancel rental: Rental status is {rental.status.value}, expected RESERVED")
                if self.auditLogger:
                    self.auditLogger.logEvent("CANCEL_REJECTED_STATUS")
                return False
            
            try:
                # Mark rental as cancelled
                rental.status = RentalStatus.CANCELLED
                
                # Return vehicle to available state
                rental.vehicule.changeState(State.AVAILABLE)
                rental.vehicule.hasActiveRental = False
                
                if self.auditLogger:
                    self.auditLogger.logEvent(f"RENTAL_CANCELLED: Vehicle {rental.vehicule.vehiculeId}")
                
                # Save with automatic rollback on failure
                success, (v, u, r) = self.persistenceManager.saveAll(
                    self.vehicules, self.users, self.rentals
                )
                
                if not success:
                    # Restore from disk
                    self.vehicules, self.users, self.rentals = v, u, r
                
                return success
                
            except Exception as e:
                print(f"Rental cancellation failed: {e}")
                return False

    def returnVehicule(self, rental: Rental, emergency: bool = False, reason: str = "") -> bool:
        """Return a rented vehicule and complete the rental (normal or emergency)."""
        with self._lock:
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
                        # Filter regulations by jurisdiction
                        vehicle_location = rental.vehicule.lastKnownLocation
                        if vehicle_location:
                            applicable_regulations = [r for r in self.regulations if r.isInJurisdiction(vehicle_location)]
                        else:
                            applicable_regulations = self.regulations
                        
                        for regulation in applicable_regulations:
                            regulation.applyPostTripRegulation(rental.vehicule, rental)
                    
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

    def processTelemetryData(self, vehicule: Vehicule, newTelemetryData: TelemetryData) -> None:
        """
        Process telemetry data received from a vehicule.
        Handles: battery monitoring, temperature alerts, and theft detection.
        """
        with self._lock:
            # Store previous location for theft detection
            previous_location = vehicule.lastKnownLocation
            
            # Update telemetry
            vehicule.updateTelemetry(newTelemetryData)

            is_overheating = vehicule.telemetryData.temperature >= 60
            is_battery_critical = vehicule.telemetryData.batteryLevel <= 5
            active_rental = self._findActiveRentalNoLock(vehicule) if vehicule.hasActiveRental else None

            if is_overheating:
                if active_rental:
                    self.slowDownVehicle(vehicule, "overheating detected")
                    self._returnVehiculeNoLock(active_rental, emergency=True, reason="Overheating detected")
                    return
                if vehicule.state != State.EMERGENCYLOCK:
                    print(f"Vehicle {vehicule.vehiculeId} is overheating, so initiating Emergency Lock.")
                    vehicule.changeState(State.EMERGENCYLOCK)
                    if self.auditLogger:
                        self.auditLogger.logEvent(f"EMERGENCY_LOCK_OVERHEAT: Vehicle {vehicule.vehiculeId}")
                    success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                    if not success:
                        self.vehicules, self.users, self.rentals = v, u, r

            if is_battery_critical:
                if active_rental:
                    self.slowDownVehicle(vehicule, "battery critically low")
                    self._returnVehiculeNoLock(active_rental, emergency=True, reason="Battery critically low")
                    # Force vehicle to MAINTENANCE for recharging (not EMERGENCYLOCK)
                    vehicule.changeState(State.MAINTENANCE)
                    if self.auditLogger:
                        self.auditLogger.logEvent(f"MAINTENANCE_BATTERY_LOW: Vehicle {vehicule.vehiculeId}")
                    success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                    if not success:
                        self.vehicules, self.users, self.rentals = v, u, r
                    return
                if vehicule.state != State.MAINTENANCE:
                    print(f"Vehicle {vehicule.vehiculeId} became battery low, so schedule maintenance.")
                    vehicule.changeState(State.MAINTENANCE)
                    if self.auditLogger:
                        self.auditLogger.logEvent(f"MAINTENANCE_BATTERY_LOW: Vehicle {vehicule.vehiculeId}")
                    success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                    if not success:
                        self.vehicules, self.users, self.rentals = v, u, r
            
            # Update last known location
            if newTelemetryData.location:
                vehicule.lastKnownLocation = newTelemetryData.location

            if self.regulations:
                # Filter regulations by jurisdiction
                vehicle_location = vehicule.lastKnownLocation
                if vehicle_location:
                    applicable_regulations = [r for r in self.regulations if r.isInJurisdiction(vehicle_location)]
                else:
                    applicable_regulations = self.regulations
                
                for regulation in applicable_regulations:
                    regulation.applyInTripRegulation(vehicule, active_rental)
            
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
                        success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
                        if not success:
                            self.vehicules, self.users, self.rentals = v, u, r

            
            if self.auditLogger:
                self.auditLogger.logEvent(f"TELEMETRY_PROCESSED: Vehicle {vehicule.vehiculeId}")
    
    def slowDownVehicle(self, vehicule: Vehicule, reason: str) -> None:
        """Request vehicle to slow down (hardware integration point)."""
        pass
    
    def _findActiveRentalNoLock(self, vehicule: Vehicule) -> Optional[Rental]:
        """Internal method to find active rental without acquiring lock (already locked)."""
        for rental in self.rentals:
            if rental.vehicule.vehiculeId == vehicule.vehiculeId and rental.status == RentalStatus.ACTIVE:
                return rental
        return None
    
    def _returnVehiculeNoLock(self, rental: Rental, emergency: bool = False, reason: str = "") -> bool:
        """Internal method to return vehicle without acquiring lock (already locked)."""
        if rental.status != RentalStatus.ACTIVE:
            return False
        
        try:
            rental.endTime = datetime.now()
            
            if emergency:
                rental.status = RentalStatus.CANCELLED
                rental.vehicule.changeState(State.EMERGENCYLOCK)
                rental.vehicule.hasActiveRental = False
                if self.auditLogger:
                    self.auditLogger.logEvent(f"EMERGENCY_TERMINATION: {reason}")
            else:
                rental.status = RentalStatus.COMPLETED
                rental.calculateRentalCost()
                if self.regulations:
                    # Filter regulations by jurisdiction
                    vehicle_location = rental.vehicule.lastKnownLocation
                    if vehicle_location:
                        applicable_regulations = [r for r in self.regulations if r.isInJurisdiction(vehicle_location)]
                    else:
                        applicable_regulations = self.regulations
                    
                    for regulation in applicable_regulations:
                        regulation.applyPostTripRegulation(rental.vehicule, rental)
                rental.vehicule.changeState(State.AVAILABLE)
                rental.vehicule.hasActiveRental = False
                if self.auditLogger:
                    self.auditLogger.logEvent("VEHICLE_RETURNED")
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success
        except Exception as e:
            print(f"Return/termination failed: {e}")
            return False
    
    def findActiveRental(self, vehicule: Vehicule) -> Optional[Rental]:
        """Find the active rental for a given vehicle."""
        with self._lock:
            return self._findActiveRentalNoLock(vehicule)

    def unlockVehicule(self, vehicule: Vehicule, reason: str = "") -> bool:
        """Manually unlock a vehicle from EMERGENCYLOCK."""
        with self._lock:
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
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success

    def assignMaintenance(self, vehicule: Vehicule) -> bool:
        """Manually mark a vehicle as needing maintenance."""
        with self._lock:
            if vehicule.state not in [State.AVAILABLE, State.EMERGENCYLOCK]:
                print(f"Cannot assign maintenance: Vehicle {vehicule.vehiculeId} is {vehicule.state.value}")
                if self.auditLogger:
                    self.auditLogger.logEvent("MAINTENANCE_ASSIGN_REJECTED_STATE")
                return False

            vehicule.changeState(State.MAINTENANCE)
            if self.auditLogger:
                self.auditLogger.logEvent(f"MAINTENANCE_ASSIGNED: Vehicle {vehicule.vehiculeId}")
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success

    def completeMaintenance(self, vehicule: Vehicule) -> bool:
        """Manually end maintenance and restore availability."""
        with self._lock:
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
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success

    def relocateVehicule(self, vehicule: Vehicule, reason: str = "") -> bool:
        """Mark a vehicle as relocating for operator rebalancing."""
        with self._lock:
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
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success

    def completeRelocation(self, vehicule: Vehicule) -> bool:
        """Finish relocation and return vehicle to availability."""
        with self._lock:
            if vehicule.state != State.RELOCATING:
                print(f"Cannot complete relocation: Vehicle {vehicule.vehiculeId} is {vehicule.state.value}")
                if self.auditLogger:
                    self.auditLogger.logEvent("RELOCATION_COMPLETE_REJECTED_STATE")
                return False

            vehicule.changeState(State.AVAILABLE)
            if self.auditLogger:
                self.auditLogger.logEvent(f"RELOCATION_COMPLETED: Vehicle {vehicule.vehiculeId}")
            
            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if not success:
                self.vehicules, self.users, self.rentals = v, u, r
            return success
    
    def registerUser(self, username: str, password: str = "") -> bool:
        with self._lock:
            # Check if user already exists
            for user in self.users:
                if user.name == username:
                    return False
            
            user = User(username)
            if password:
                user.set_password(password)
            self.users.append(user)

            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if success:
                if self.auditLogger:
                    self.auditLogger.logEvent(f"USER {username} REGISTERED")
                return True
            else:
                self.vehicules, self.users, self.rentals = v, u, r
                return False
    
    def authenticateUser(self, username: str, password: str) -> bool:
        """Authenticate a user with username and password."""
        with self._lock:
            user = self.findUserByName(username)
            if user and user.verify_password(password):
                return True
            return False
    
    def registerVehicle(self, vehicleId: int, vehicleType: str) -> bool:
        with self._lock:
            # Check if vehicle already exists
            for vehicle in self.vehicules:
                if vehicle.vehiculeId == vehicleId:
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

            success, (v, u, r) = self.persistenceManager.saveAll(self.vehicules, self.users, self.rentals)
            if success:
                if self.auditLogger:
                    self.auditLogger.logEvent(f"VEHICLE {vehicle.vehiculeId} REGISTERD")
                return True
            else:
                self.vehicules, self.users, self.rentals = v, u, r
                return False

    def findUserByName(self, username: str) -> Optional[User]:
        with self._lock:
            for user in self.users:
                if user.name == username:
                    return user
            return None
    
    def getUserFromId(self, userId: int) -> Optional[User]:
        """Find user by ID (using index as ID for simplicity)."""
        with self._lock:
            if 0 <= userId < len(self.users):
                return self.users[userId]
            return None
    
    def getVehicleFromId(self, vehicleId: int) -> Optional[Vehicule]:
        with self._lock:
            for vehicle in self.vehicules:
                if vehicle.vehiculeId == vehicleId:
                    return vehicle
            return None

    def getRentalFromNameId(self, username: str, vehicleId: int) -> Optional[Rental]:
        with self._lock:
            for rental in self.rentals:
                if (rental.user.name == username
                    and rental.vehicule.vehiculeId == vehicleId
                    and (rental.status == RentalStatus.ACTIVE or rental.status == RentalStatus.RESERVED)):
                    return rental
            return None
    def startBackgroundMonitoring(self, interval_seconds: int = 10) -> None:
        """
        Start background telemetry monitoring thread (daemon).
        This simulates continuous vehicle telemetry streams as per lab requirements.
        """
        if self._monitoring_enabled:
            print("Background monitoring already running")
            return
        
        self._monitoring_enabled = True
        self._telemetry_monitor_thread = threading.Thread(
            target=self._background_telemetry_monitoring,
            args=(interval_seconds,),
            daemon=True  # Daemon thread terminates with main program
        )
        self._telemetry_monitor_thread.start()
        print(f"Background telemetry monitoring started (interval: {interval_seconds}s)")
    
    def stopBackgroundMonitoring(self) -> None:
        """Stop the background monitoring thread gracefully."""
        if not self._monitoring_enabled:
            return
        
        self._monitoring_enabled = False
        if self._telemetry_monitor_thread:
            self._telemetry_monitor_thread.join(timeout=5)
        print("Background telemetry monitoring stopped")
    
    def _background_telemetry_monitoring(self, interval_seconds: int) -> None:
        """
        Background thread that simulates continuous telemetry updates.
        Periodically generates random telemetry for active vehicles.
        """
        while self._monitoring_enabled:
            try:
                time.sleep(interval_seconds)
                
                # Get snapshot of vehicles (thread-safe)
                with self._lock:
                    vehicles_snapshot = self.vehicules.copy()
                
                # Simulate telemetry for vehicles in use
                for vehicle in vehicles_snapshot:
                    if vehicle.state == State.INUSE and vehicle.hasActiveRental:
                        # Simulate realistic telemetry updates
                        battery_drift = random.randint(-3, -1)  # Battery always decreases during use
                        temp_drift = random.randint(-3, 3)
                        
                        new_battery = max(0, min(100, vehicle.telemetryData.batteryLevel + battery_drift))
                        new_temp = max(15, min(70, vehicle.telemetryData.temperature + temp_drift))
                        
                        # Simulate GPS movement (small random drift)
                        if vehicle.lastKnownLocation:
                            lat_drift = random.uniform(-0.001, 0.001)
                            lon_drift = random.uniform(-0.001, 0.001)
                            new_location = GPSLocation(
                                vehicle.lastKnownLocation.latitude + lat_drift,
                                vehicle.lastKnownLocation.longitude + lon_drift
                            )
                        else:
                            new_location = GPSLocation(51.5074, -0.1278)  # Default: London
                        
                        # Create and process new telemetry
                        new_telemetry = TelemetryData(new_battery, new_temp, new_location)
                        self.processTelemetryData(vehicle, new_telemetry)
                    
                    # Also check AVAILABLE vehicles for maintenance needs (critical battery/overheating)
                    elif vehicle.state == State.AVAILABLE:
                        # Check if battery is critically low or overheating
                        if vehicle.telemetryData.batteryLevel <= 5:
                            # Trigger maintenance for battery critical
                            dummy_telemetry = TelemetryData(
                                vehicle.telemetryData.batteryLevel,
                                vehicle.telemetryData.temperature,
                                vehicle.lastKnownLocation
                            )
                            self.processTelemetryData(vehicle, dummy_telemetry)
                        elif vehicle.telemetryData.temperature >= 60:
                            # Trigger emergency lock for overheating
                            dummy_telemetry = TelemetryData(
                                vehicle.telemetryData.batteryLevel,
                                vehicle.telemetryData.temperature,
                                vehicle.lastKnownLocation
                            )
                            self.processTelemetryData(vehicle, dummy_telemetry)
                        
            except Exception as e:
                print(f"Background monitoring error: {e}")