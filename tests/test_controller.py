"""
Unit tests for SmartMoveCentralController
Coverage target: 40%+
"""
import unittest
import os
import tempfile
import time
from datetime import datetime
from models import State, User, Rental, TelemetryData, GPSLocation, RentalStatus
from vehicules import Bike, Scooter, Moped
from regulations import LondonRegulation, MilanRegulation, RomeRegulation
from controllers import SmartMoveCentralController
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository
from services import AuditLogger, PersistenceManager


class TestSmartMoveCentralController(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize repositories with temp paths
        self.vehicule_repo = VehiculeCSVRepository(f"{self.test_dir}/vehicules.csv")
        self.user_repo = UserCSVRepository(f"{self.test_dir}/users.csv")
        self.rental_repo = RentalCSVRepository(f"{self.test_dir}/rentals.csv")
        
        # Initialize audit logger (use dummy logger to avoid disk usage)
        class DummyLogger:
            def __init__(self):
                self.events = []
            def logEvent(self, msg):
                self.events.append(msg)
        self.audit_logger = DummyLogger()
        
        # Initialize persistence manager
        self.persistence_manager = PersistenceManager(
            self.vehicule_repo,
            self.user_repo,
            self.rental_repo,
            self.audit_logger
        )
        
        # Initialize controller
        self.controller = SmartMoveCentralController(
            persistenceManager=self.persistence_manager,
            auditLogger=self.audit_logger,
            regulations=[LondonRegulation(), MilanRegulation(), RomeRegulation()]
        )
        
        # Create test data
        self.test_bike = Bike(1, 80, 25, State.AVAILABLE)
        self.test_scooter = Scooter(2, 70, 30, State.AVAILABLE)
        self.test_moped = Moped(3, 90, 20, State.AVAILABLE)
        self.test_user = User("TestUser")
        
        self.controller.vehicules.append(self.test_bike)
        self.controller.vehicules.append(self.test_scooter)
        self.controller.vehicules.append(self.test_moped)
        self.controller.users.append(self.test_user)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Remove temp files
        for filename in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, filename))
        os.rmdir(self.test_dir)
    
    # Test State Machine
    def test_rent_vehicle_success(self):
        """Test successful vehicle rental."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.assertIsNotNone(rental)
        self.assertEqual(self.test_bike.state, State.RESERVED)
        self.assertTrue(self.test_bike.hasActiveRental)
        self.assertEqual(rental.status, RentalStatus.RESERVED)
    
    def test_rent_vehicle_already_rented(self):
        """Test renting an already rented vehicle fails."""
        self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        rental2 = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.assertIsNone(rental2)
    
    def test_rent_vehicle_unhealthy_telemetry(self):
        """Test renting vehicle with unhealthy telemetry fails."""
        self.test_bike.telemetryData.batteryLevel = 10  # Low but not critical
        self.test_bike.telemetryData.temperature = 55  # High but not overheating
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.assertIsNone(rental)
    
    def test_activate_rental_success(self):
        """Test successful rental activation."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        result, error_msg = self.controller.activateRental(rental)
        self.assertTrue(result)
        self.assertIsNone(error_msg)
        self.assertEqual(rental.status, RentalStatus.ACTIVE)
        self.assertEqual(self.test_bike.state, State.INUSE)
        self.assertIsNotNone(rental.actualStartTime)
    
    def test_activate_rental_wrong_status(self):
        """Test activating rental in wrong status fails."""
        rental = Rental(self.test_user, self.test_bike, datetime.now())
        rental.status = RentalStatus.COMPLETED
        result, error_msg = self.controller.activateRental(rental)
        self.assertFalse(result)
        self.assertIsNotNone(error_msg)
    
    def test_return_vehicle_success(self):
        """Test successful vehicle return."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)[0]
        result = self.controller.returnVehicule(rental)
        self.assertTrue(result)
        self.assertEqual(rental.status, RentalStatus.COMPLETED)
        self.assertEqual(self.test_bike.state, State.AVAILABLE)
        self.assertFalse(self.test_bike.hasActiveRental)
        self.assertIsNotNone(rental.cost)
    
    def test_return_vehicle_emergency(self):
        """Test emergency vehicle return."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)[0]
        result = self.controller.returnVehicule(rental, emergency=True, reason="Test emergency")
        self.assertTrue(result)
        self.assertEqual(rental.status, RentalStatus.CANCELLED)
        self.assertEqual(self.test_bike.state, State.EMERGENCYLOCK)
    
    # Test Telemetry Processing
    def test_telemetry_overheating(self):
        """Test telemetry detects overheating."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)[0]
        
        telemetry = TelemetryData(80, 65)  # Overheating
        self.controller.processTelemetryData(self.test_bike, telemetry)
        
        self.assertEqual(self.test_bike.state, State.EMERGENCYLOCK)
        self.assertEqual(rental.status, RentalStatus.CANCELLED)
    
    def test_telemetry_battery_critical(self):
        """Test telemetry detects critical battery."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)[0]
        
        telemetry = TelemetryData(3, 25)  # Critical battery
        self.controller.processTelemetryData(self.test_bike, telemetry)
        
        self.assertEqual(self.test_bike.state, State.MAINTENANCE)
        self.assertEqual(rental.status, RentalStatus.CANCELLED)
    
    def test_telemetry_theft_detection(self):
        """Test telemetry detects theft (movement without rental)."""
        self.test_bike.lastKnownLocation = GPSLocation(48.8566, 2.3522)  # Paris
        
        telemetry = TelemetryData(80, 25, GPSLocation(48.8600, 2.3550))  # Moved
        self.controller.processTelemetryData(self.test_bike, telemetry)
        
        self.assertEqual(self.test_bike.state, State.EMERGENCYLOCK)
    
    # Test Maintenance
    def test_assign_maintenance(self):
        """Test assigning maintenance to vehicle."""
        result = self.controller.assignMaintenance(self.test_bike)
        self.assertTrue(result)
        self.assertEqual(self.test_bike.state, State.MAINTENANCE)
    
    def test_complete_maintenance_success(self):
        """Test completing maintenance successfully."""
        self.controller.assignMaintenance(self.test_bike)
        result = self.controller.completeMaintenance(self.test_bike)
        self.assertTrue(result)
        self.assertEqual(self.test_bike.state, State.AVAILABLE)
    
    def test_complete_maintenance_low_battery(self):
        """Test completing maintenance fails with low battery."""
        self.controller.assignMaintenance(self.test_bike)
        self.test_bike.telemetryData.batteryLevel = 15
        result = self.controller.completeMaintenance(self.test_bike)
        self.assertFalse(result)
    
    # Test Relocation
    def test_relocate_vehicle(self):
        """Test relocating vehicle."""
        result = self.controller.relocateVehicule(self.test_bike)
        self.assertTrue(result)
        self.assertEqual(self.test_bike.state, State.RELOCATING)
    
    def test_complete_relocation(self):
        """Test completing relocation."""
        self.controller.relocateVehicule(self.test_bike)
        result = self.controller.completeRelocation(self.test_bike)
        self.assertTrue(result)
        self.assertEqual(self.test_bike.state, State.AVAILABLE)
    
    # Test Emergency Unlock
    def test_unlock_vehicle(self):
        """Test unlocking emergency-locked vehicle."""
        self.test_bike.changeState(State.EMERGENCYLOCK)
        result = self.controller.unlockVehicule(self.test_bike, "Test unlock")
        self.assertTrue(result)
        self.assertEqual(self.test_bike.state, State.AVAILABLE)
    
    # Test User Management
    def test_register_user_success(self):
        """Test registering a new user."""
        result = self.controller.registerUser("NewUser")
        self.assertTrue(result)
        user = self.controller.findUserByName("NewUser")
        self.assertIsNotNone(user)
    
    def test_register_user_duplicate(self):
        """Test registering duplicate user fails."""
        self.controller.registerUser("NewUser")
        result = self.controller.registerUser("NewUser")
        self.assertFalse(result)
    
    # Test Vehicle Management
    def test_register_vehicle_success(self):
        """Test registering a new vehicle."""
        result = self.controller.registerVehicle(100, "scooter")
        self.assertTrue(result)
        vehicle = self.controller.getVehicleFromId(100)
        self.assertIsNotNone(vehicle)
        self.assertIsInstance(vehicle, Scooter)
    
    def test_register_vehicle_duplicate(self):
        """Test registering duplicate vehicle fails."""
        result = self.controller.registerVehicle(1, "scooter")
        self.assertFalse(result)
    
    def test_register_vehicle_invalid_type(self):
        """Test registering vehicle with invalid type fails."""
        result = self.controller.registerVehicle(100, "invalid_type")
        self.assertFalse(result)
    
    # Test Search Functions
    def test_find_user_by_name(self):
        """Test finding user by name."""
        user = self.controller.findUserByName("TestUser")
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "TestUser")
    
    def test_get_vehicle_from_id(self):
        """Test getting vehicle by ID."""
        vehicle = self.controller.getVehicleFromId(1)
        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.vehiculeId, 1)
    
    def test_get_user_from_id(self):
        """Test getting user by ID."""
        user = self.controller.getUserFromId(0)
        self.assertIsNotNone(user)
    
    def test_find_active_rental(self):
        """Test finding active rental."""
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)[0]
        found_rental = self.controller.findActiveRental(self.test_bike)
        self.assertIsNotNone(found_rental)
        self.assertEqual(found_rental.vehicule.vehiculeId, 1)
    
    # Test Persistence
    def test_save_and_load_data(self):
        """Test saving and loading data."""
        self.controller.saveData()
        
        new_controller = SmartMoveCentralController(
            persistenceManager=self.persistence_manager,
            auditLogger=self.audit_logger,
            regulations=[]
        )
        new_controller.loadData()
        
        self.assertEqual(len(new_controller.vehicules), 3)
        self.assertEqual(len(new_controller.users), 1)

    def test_handle_overheating_no_lock_without_rental(self):
        self.test_bike.telemetryData.temperature = 65
        result = self.controller._handleOverheatingNoLock(self.test_bike, None)
        self.assertFalse(result)
        self.assertEqual(self.test_bike.state, State.EMERGENCYLOCK)

    def test_handle_battery_critical_no_lock_without_rental(self):
        self.test_bike.telemetryData.batteryLevel = 3
        result = self.controller._handleBatteryCriticalNoLock(self.test_bike, None)
        self.assertFalse(result)
        self.assertEqual(self.test_bike.state, State.MAINTENANCE)

    def test_return_vehicle_no_lock(self):
        rental = self.controller.rentVehicule(self.test_bike, self.test_user, datetime.now())
        self.controller.activateRental(rental)
        result = self.controller._returnVehiculeNoLock(rental, emergency=False)
        self.assertTrue(result)
        self.assertEqual(rental.status, RentalStatus.COMPLETED)
        self.assertEqual(self.test_bike.state, State.AVAILABLE)

    def test_background_monitoring_start_stop(self):
        self.controller.startBackgroundMonitoring(interval_seconds=0.01)
        self.assertTrue(self.controller._monitoring_enabled)
        time.sleep(0.05)
        self.controller.stopBackgroundMonitoring()
        self.assertFalse(self.controller._monitoring_enabled)


class TestModels(unittest.TestCase):
    """Test model classes."""
    
    def test_rental_duration_calculation(self):
        """Test rental duration calculation."""
        user = User("Test")
        bike = Bike(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, bike, datetime.now())
        
        rental.actualStartTime = datetime(2026, 1, 1, 10, 0, 0)
        rental.endTime = datetime(2026, 1, 1, 10, 30, 0)
        
        duration = rental.calculateRentalDuration()
        self.assertEqual(duration, 30.0)
    
    def test_rental_duration_negative(self):
        """Test rental duration handles negative time."""
        user = User("Test")
        bike = Bike(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, bike, datetime.now())
        
        rental.actualStartTime = datetime(2026, 1, 1, 10, 30, 0)
        rental.endTime = datetime(2026, 1, 1, 10, 0, 0)
        
        duration = rental.calculateRentalDuration()
        self.assertEqual(duration, 0.0)
    
    def test_rental_cost_calculation(self):
        """Test rental cost calculation."""
        user = User("Test")
        bike = Bike(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, bike, datetime.now())
        
        rental.actualStartTime = datetime(2026, 1, 1, 10, 0, 0)
        rental.endTime = datetime(2026, 1, 1, 10, 30, 0)
        
        cost = rental.calculateRentalCost()
        self.assertEqual(cost, 15.0)  # 30 minutes * 0.5
    
    def test_gps_location_valid(self):
        """Test valid GPS coordinates."""
        location = GPSLocation(48.8566, 2.3522)
        self.assertEqual(location.latitude, 48.8566)
        self.assertEqual(location.longitude, 2.3522)
    
    def test_gps_location_invalid_latitude(self):
        """Test invalid latitude raises error."""
        with self.assertRaises(ValueError):
            GPSLocation(91.0, 2.3522)
    
    def test_gps_location_invalid_longitude(self):
        """Test invalid longitude raises error."""
        with self.assertRaises(ValueError):
            GPSLocation(48.8566, 181.0)
    
    def test_telemetry_is_healthy(self):
        """Test telemetry health check."""
        telemetry = TelemetryData(80, 25)
        self.assertTrue(telemetry.isHealthy())
        
        telemetry_low_battery = TelemetryData(15, 25)
        self.assertFalse(telemetry_low_battery.isHealthy())
        
        telemetry_hot = TelemetryData(80, 55)
        self.assertFalse(telemetry_hot.isHealthy())


class TestRegulations(unittest.TestCase):
    """Test regulation classes."""
    
    def test_london_regulation_congestion_charge(self):
        """Test London regulation applies congestion charge."""
        user = User("Test")
        bike = Bike(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, bike, datetime.now())
        rental.cost = 10.0
        
        regulation = LondonRegulation()
        regulation.applyPostTripRegulation(bike, rental)
        
        self.assertEqual(rental.cost, 15.0)  # 10 + 5
    
    def test_milan_regulation_helmet_check(self):
        """Test Milan regulation checks helmet for moped."""
        user = User("Test")
        moped = Moped(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, moped, datetime.now())
        
        regulation = MilanRegulation()
        # Random result, just check it returns boolean
        result = regulation.applyPreTripRegulation(moped, rental)
        self.assertIsInstance(result, bool)
    
    def test_milan_regulation_non_moped(self):
        """Test Milan regulation allows non-moped without helmet check."""
        user = User("Test")
        bike = Bike(1, 80, 25, State.AVAILABLE)
        rental = Rental(user, bike, datetime.now())
        
        regulation = MilanRegulation()
        result = regulation.applyPreTripRegulation(bike, rental)
        self.assertTrue(result)
    
    def test_rome_regulation_restricted_zone(self):
        """Test Rome regulation detects restricted zone."""
        user = User("Test")
        scooter = Scooter(1, 80, 25, State.INUSE)
        scooter.lastKnownLocation = GPSLocation(41.8912, 12.4930)  # In restricted zone
        rental = Rental(user, scooter, datetime.now())
        
        regulation = RomeRegulation()
        regulation.applyInTripRegulation(scooter, rental)
        
        self.assertEqual(scooter.state, State.EMERGENCYLOCK)


if __name__ == '__main__':
    unittest.main()
