from controllers import SmartMoveCentralController
from models import TelemetryData, GPSLocation
import time


def testSuite(controller: SmartMoveCentralController) -> None:
    # Create some vehicles
    bike1 = Bike(vehiculeId=1, batteryLevel=80, temperature=20, state=State.AVAILABLE)
    scooter1 = Scooter(vehiculeId=2, batteryLevel=60, temperature=22, state=State.AVAILABLE)
    
    controller.vehicules.append(bike1)
    controller.vehicules.append(scooter1)
    
    # Create a user
    user1 = User("John Doe")
    controller.users.append(user1)
    
    # Create a rental - scheduled to start now
    rental1 = Rental(user1, bike1, scheduledStartTime=datetime.now())
    controller.rentals.append(rental1)
    
    print("=" * 60)
    print("SmartMove System - Complete Functional Test")
    print("=" * 60)
    
    # Test 1: Rent a vehicle
    print("\n[TEST 1] Creating a rental reservation...")
    rental2 = controller.rentVehicule(bike1, user1, datetime.now())
    print(f"Rental created - Status: {rental2.status.value}")
    print(f"  Vehicle ID: {rental2.vehicule.vehiculeId}, State: {rental2.vehicule.state.value}")
    
    # Test 2: Activate the rental
    print("\n[TEST 2] Activating the rental...")
    controller.activateRental(rental2)
    print(f"Rental activated - Status: {rental2.status.value}")
    print(f"  Vehicle State: {rental2.vehicule.state.value}")
    print(f"  Has Active Rental: {rental2.vehicule.hasActiveRental}")
    print(f"  Actual Start Time: {rental2.actualStartTime}")
    
    # Test 3: Process telemetry data
    print("\n[TEST 3] Processing telemetry data...")
    
    newTelemetry = TelemetryData(
        batteryLevel=75, 
        temperature=25, 
        location=GPSLocation(51.5074, -0.1278)  # London
    )
    controller.processTelemetryData(bike1, newTelemetry)
    print(f"Telemetry processed")
    print(f"  Battery Level: {bike1.telemetryData.batteryLevel}%")
    print(f"  Temperature: {bike1.telemetryData.temperature}°C")
    
    # Test 4: Simulate time passing and return the vehicle
    print("\n[TEST 4] Returning the vehicle...")
    time.sleep(1)  # Simulate some rental time
    controller.returnVehicule(rental2)
    print(f"Vehicle returned - Status: {rental2.status.value}")
    print(f"  Vehicle State: {rental2.vehicule.state.value}")
    print(f"  Has Active Rental: {rental2.vehicule.hasActiveRental}")
    print(f"  End Time: {rental2.endTime}")
    print(f"  Duration: {rental2.calculateRentalDuration():.2f} minutes")
    print(f"  Cost: €{rental2.cost:.2f}")
    
    # Test 5: Test regulations with different cities
    print("\n[TEST 5] Testing city regulations...")
    
    # London regulation test
    print("\n  Testing London Regulation:")
    controller.regulations = LondonRegulation()
    rental_london = controller.rentVehicule(scooter1, user1, datetime.now())
    controller.activateRental(rental_london)
    time.sleep(1)
    controller.returnVehicule(rental_london)
    print(f"    Duration: {rental_london.calculateRentalDuration():.2f} min, Cost: €{rental_london.cost:.2f}")
    
    # Rome regulation test
    print("\n  Testing Rome Regulation:")
    controller.regulations = RomeRegulation()
    bike2 = Bike(vehiculeId=3, batteryLevel=90, temperature=25, state=State.AVAILABLE)
    controller.vehicules.append(bike2)
    rental_rome = controller.rentVehicule(bike2, user1, datetime.now())
    controller.activateRental(rental_rome)
    time.sleep(1)
    controller.returnVehicule(rental_rome)
    print(f"    Duration: {rental_rome.calculateRentalDuration():.2f} min, Cost: €{rental_rome.cost:.2f}")
    
    # Test 6: Save and load data
    print("\n[TEST 6] Testing data persistence...")
    controller.saveData()
    print("Data saved to CSV files")
    
    controller2 = SmartMoveCentralController(persistenceManager, auditLogger)
    controller2.loadData()
    print(f"Data loaded - Vehicles: {len(controller2.vehicules)}, Users: {len(controller2.users)}, Rentals: {len(controller2.rentals)}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

