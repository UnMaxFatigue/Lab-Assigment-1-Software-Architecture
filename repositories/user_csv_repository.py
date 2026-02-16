from typing import List
from models import User
import csv
import os


class UserCSVRepository:
    """CSV implementation of user repository."""
    
    filePath: str
    
    def __init__(self, filePath: str = "data/users.csv") -> None:
        self.filePath = filePath
    
    def save(self, users: List[User]) -> None:
        """Save users to CSV file."""
        os.makedirs(os.path.dirname(self.filePath), exist_ok=True)
        with open(self.filePath, 'w', newline='') as csvfile:
            fieldnames = ['name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                row = {'name': user.name}
                writer.writerow(row)
    
    def load(self) -> List[User]:
        """Load users from CSV file."""
        users = []
        if not os.path.exists(self.filePath):
            return users
        with open(self.filePath, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row['name']
                user = User(name)
                users.append(user)
        return users
    
