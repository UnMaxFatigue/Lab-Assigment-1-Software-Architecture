from typing import List
from models import Rental, User, RentalStatus, State
from datetime import datetime
import csv
import os


class RentalCSVRepository:
    """CSV implementation of rental repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/rentals.csv") -> None:
        self.filePath = filePath
    
    def save(self, rentals: List[Rental]) -> None:
        """Save rentals to CSV file."""
        os.makedirs(os.path.dirname(self.filePath), exist_ok=True)
        with open(self.filePath, 'w', newline='') as csvfile:
            fieldnames = ['user_name', 'vehicule_id', 'scheduledStartTime', 'actualStartTime', 'endTime', 'cost', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for rental in rentals:
                row = {
                    'user_name': rental.user.name,
                    'vehicule_id': rental.vehicule.vehiculeId,
                    'scheduledStartTime': rental.scheduledStartTime.isoformat(),
                    'actualStartTime': rental.actualStartTime.isoformat() if rental.actualStartTime else '',
                    'endTime': rental.endTime.isoformat() if rental.endTime else '',
                    'cost': str(rental.cost) if rental.cost is not None else '',
                    'status': rental.status.value
                }
                writer.writerow(row)
    
    def load(self) -> List[Rental]:
        """Load rentals from CSV file."""
        rentals = []
        if not os.path.exists(self.filePath):
            return rentals
        with open(self.filePath, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_name = row['user_name']
                vehicule_id = int(row['vehicule_id'])
                scheduledStartTime = datetime.fromisoformat(row['scheduledStartTime'])
                actualStartTime = datetime.fromisoformat(row['actualStartTime']) if row['actualStartTime'] else None
                endTime = datetime.fromisoformat(row['endTime']) if row['endTime'] else None
                cost = float(row['cost']) if row['cost'] else None
                status = row['status']
                # Create User and dummy Vehicule (since we don't have full data)
                user = User(user_name)
                # For Vehicule, create a dummy Bike with id, assume defaults
                from vehicules import Bike
                vehicule = Bike(vehicule_id, 100, 20, State.AVAILABLE)
                rental = Rental(user, vehicule, scheduledStartTime)
                rental.actualStartTime = actualStartTime
                rental.endTime = endTime
                rental.cost = cost
                rental.status = RentalStatus(status)
                rentals.append(rental)
        return rentals
