from typing import Tuple, List
from models import Vehicule, User, Rental
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository


class PersistenceManager:
    """Manages all data persistence operations across repositories."""
    
    vehiculeRepository: VehiculeCSVRepository
    userRepository: UserCSVRepository
    rentalRepository: RentalCSVRepository
    
    def __init__(
        self,
        vehiculeRepository: VehiculeCSVRepository,
        userRepository: UserCSVRepository,
        rentalRepository: RentalCSVRepository
    ) -> None:
        self.vehiculeRepository = vehiculeRepository
        self.userRepository = userRepository
        self.rentalRepository = rentalRepository
    
    def loadAll(self) -> Tuple[List[Vehicule], List[User], List[Rental]]:
        """Load all data from repositories."""
        vehicules = self.vehiculeRepository.load()
        users = self.userRepository.load()
        rentals = self.rentalRepository.load()
        return vehicules, users, rentals
    
    def saveAll(self, vehicules: List[Vehicule], users: List[User], rentals: List[Rental]) -> None:
        """Save all data to repositories."""
        self.vehiculeRepository.save(vehicules)
        self.userRepository.save(users)
        self.rentalRepository.save(rentals)
