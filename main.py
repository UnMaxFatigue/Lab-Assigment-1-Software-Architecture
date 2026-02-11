"""
Main entry point for the SmartMove system.
"""
from datetime import datetime
from models import State, User, Rental
from vehicules import Bike, Scooter
from regulations import LondonRegulation
from controllers import SmartMoveCentralController
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository
from services import AuditLogger, PersistenceManager


def main() -> None:
    """Main function to demonstrate the SmartMove system."""
    
    # Initialize repositories
    vehiculeRepo = VehiculeCSVRepository()
    userRepo = UserCSVRepository()
    rentalRepo = RentalCSVRepository()
    
    # Initialize persistence manager
    persistenceManager = PersistenceManager(vehiculeRepo, userRepo, rentalRepo)
    
    # Initialize audit logger
    auditLogger = AuditLogger("data/audit.log")
    
    # Initialize controller with dependency injection
    controller = SmartMoveCentralController(
        persistenceManager=persistenceManager,
        auditLogger=auditLogger
    )
    controller.regulations = LondonRegulation()
    
    # Create some vehicles
    bike1 = Bike(vehiculeId=1, batteryLevel=80, temperature=20, state=State.AVAILABLE)
    scooter1 = Scooter(vehiculeId=2, batteryLevel=60, temperature=22, state=State.AVAILABLE)
    
    controller.vehicules.append(bike1)
    controller.vehicules.append(scooter1)
    
    # Create a user
    user1 = User("John Doe")
    
    # Create a rental - scheduled to start now
    rental1 = Rental(user1, bike1, scheduledStartTime=datetime.now())
    
    print("SmartMove system initialized successfully!")
    print(f"Available vehicles: {len(controller.vehicules)}")
    print(f"User: {user1.name}")
    print(f"Rental status: {rental1.status.value}")
    print(f"Scheduled start: {rental1.scheduledStartTime}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
