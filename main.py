"""
Main entry point for the SmartMove system.
"""
from datetime import datetime
from models import State, User, Rental
from vehicules import Bike, Scooter
from regulations import LondonRegulation ,RomeRegulation,MilanRegulation
from controllers import SmartMoveCentralController, initializeServer
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository
from services import AuditLogger, PersistenceManager

#from test import testsuit

def initializeControler() -> SmartMoveCentralController:
    
    # Initialize repositories
    vehiculeRepo = VehiculeCSVRepository()
    userRepo = UserCSVRepository()
    rentalRepo = RentalCSVRepository()
    
    # Initialize audit logger
    auditLogger = AuditLogger("data/audit.log")
    
    # Initialize persistence manager
    persistenceManager = PersistenceManager(vehiculeRepo, userRepo, rentalRepo, auditLogger)
    
    # Initialize controller with dependency injection
    controller = SmartMoveCentralController(
        persistenceManager=persistenceManager,
        auditLogger=auditLogger,
        regulations=[LondonRegulation(), RomeRegulation(), MilanRegulation()]
    )
    
    # Load existing data from CSV files
    controller.loadData()

    return controller 

def main() -> None:
    """Main function to demonstrate the SmartMove system."""
    
    

    controller = initializeControler()
    httpServer = initializeServer(controller)

    # Start background telemetry monitoring (lab requirement)
    controller.startBackgroundMonitoring(interval_seconds=10)

    try:
        print("Server started on port 8080")
        httpServer.serve_forever()
    except KeyboardInterrupt:
        print("Interrupt recived. Closing down.")
    finally:
        controller.stopBackgroundMonitoring()
        httpServer.shutdown()
    #testsuit(controller)
    

if __name__ == "__main__":
    main()
