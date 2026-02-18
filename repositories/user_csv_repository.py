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
        with open(self.filePath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'password_hash']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                row = {
                    'name': user.name,
                    'password_hash': user.password_hash
                }
                writer.writerow(row)
            # Ensure data is written to disk
            csvfile.flush()
    
    def load(self) -> List[User]:
        """Load users from CSV file."""
        users = []
        if not os.path.exists(self.filePath):
            return users
        with open(self.filePath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row['name']
                password_hash = row.get('password_hash', '')
                user = User(name, password_hash)
                users.append(user)
        return users
    
