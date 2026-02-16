from typing import Tuple, List
from models import Vehicule, User, Rental
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository
from .audit_logger import AuditLogger


class PersistenceManager:
    """Manages all data persistence operations across repositories with transaction support."""
    
    vehiculeRepository: VehiculeCSVRepository
    userRepository: UserCSVRepository
    rentalRepository: RentalCSVRepository
    auditLogger: AuditLogger
    
    def __init__(
        self,
        vehiculeRepository: VehiculeCSVRepository,
        userRepository: UserCSVRepository,
        rentalRepository: RentalCSVRepository,
        auditLogger: AuditLogger
    ) -> None:
        self.vehiculeRepository = vehiculeRepository
        self.userRepository = userRepository
        self.rentalRepository = rentalRepository
        self.auditLogger = auditLogger
    
    def loadAll(self) -> Tuple[List[Vehicule], List[User], List[Rental]]:
        """Load all data from repositories."""
        vehicules = self.vehiculeRepository.load()
        users = self.userRepository.load()
        rentals = self.rentalRepository.load()
        self.auditLogger.logEvent("Loaded all data: vehicules, users, rentals")
        return vehicules, users, rentals
    
    def saveAll(self, vehicules: List[Vehicule], users: List[User], rentals: List[Rental]) -> Tuple[bool, Tuple[List[Vehicule], List[User], List[Rental]]]:
        """
        Save all data to repositories with automatic rollback on failure.
        If save fails, automatically reloads from disk to ensure consistency.
        
        Returns: (success: bool, (vehicules, users, rentals))
        - On success: (True, original_data)
        - On failure: (False, data_reloaded_from_disk)
        """
        self.auditLogger.logEvent("SAVE_BEGIN")
        
        try:
            # Attempt to save all data
            self.vehiculeRepository.save(vehicules)
            self.userRepository.save(users)
            self.rentalRepository.save(rentals)
            
            self.auditLogger.logEvent(f"SAVE_SUCCESS: {len(vehicules)} vehicules, {len(users)} users, {len(rentals)} rentals")
            return True, (vehicules, users, rentals)
            
        except Exception as e:
            # Save failed - rollback by reloading from disk
            print(f"Save failed: {e}. Reloading from disk for consistency...")
            self.auditLogger.logEvent(f"SAVE_FAILED: {e}")
            
            try:
                # Reload from repositories (disk = source of truth)
                vehicules_restored = self.vehiculeRepository.load()
                users_restored = self.userRepository.load()
                rentals_restored = self.rentalRepository.load()
                
                self.auditLogger.logEvent("ROLLBACK_SUCCESS")
                print("Data reloaded from disk")
                return False, (vehicules_restored, users_restored, rentals_restored)
                
            except Exception as reload_error:
                # Critical: even reload failed
                print(f"CRITICAL: Reload failed: {reload_error}")
                self.auditLogger.logEvent(f"ROLLBACK_FAILED: {reload_error}")
                return False, (vehicules, users, rentals)
