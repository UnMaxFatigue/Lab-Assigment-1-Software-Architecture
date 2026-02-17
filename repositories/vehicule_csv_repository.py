from typing import List
from models import Vehicule, State, TelemetryData, GPSLocation
import csv
import os


class VehiculeCSVRepository:
    """CSV implementation of vehicule repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/vehicules.csv") -> None:
        self.filePath = filePath
    
    def save(self, vehicules: List[Vehicule]) -> None:
        """Save vehicules to CSV file."""
        os.makedirs(os.path.dirname(self.filePath), exist_ok=True)
        with open(self.filePath, 'w', newline='') as csvfile:
            fieldnames = ['type', 'vehiculeId', 'batteryLevel', 'temperature', 'state', 'hasActiveRental', 'latitude', 'longitude']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for vehicule in vehicules:
                row = {
                    'type': type(vehicule).__name__,
                    'vehiculeId': vehicule.vehiculeId,
                    'batteryLevel': vehicule.telemetryData.batteryLevel,
                    'temperature': vehicule.telemetryData.temperature,
                    'state': vehicule.state.value,
                    'hasActiveRental': vehicule.hasActiveRental,
                    'latitude': vehicule.lastKnownLocation.latitude if vehicule.lastKnownLocation else '',
                    'longitude': vehicule.lastKnownLocation.longitude if vehicule.lastKnownLocation else ''
                }
                writer.writerow(row)
    
    def load(self) -> List[Vehicule]:
        """Load vehicules from CSV file."""
        vehicules = []
        if not os.path.exists(self.filePath):
            return vehicules
        with open(self.filePath, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                vehicule_type = row['type']
                vehiculeId = int(row['vehiculeId'])
                batteryLevel = int(row['batteryLevel'])
                temperature = int(row['temperature'])
                state = State(row['state'])
                hasActiveRental = row['hasActiveRental'].lower() == 'true'
                latitude = float(row['latitude']) if row['latitude'] else None
                longitude = float(row['longitude']) if row['longitude'] else None
                lastKnownLocation = GPSLocation(latitude, longitude) if latitude is not None and longitude is not None else None
                # Import concrete classes
                from vehicules import Bike, Scooter, Moped
                cls = {'Bike': Bike, 'Scooter': Scooter, 'Moped': Moped}.get(vehicule_type, Bike)
                vehicule = cls(vehiculeId, batteryLevel, temperature, state)
                vehicule.hasActiveRental = hasActiveRental
                vehicule.lastKnownLocation = lastKnownLocation
                vehicules.append(vehicule)
        return vehicules    
        
