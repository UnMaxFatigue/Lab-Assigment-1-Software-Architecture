import os
from datetime import datetime, timedelta
from models.user import User
from models.vehicule import Vehicule
from models.state import State
from models.telemetry_data import TelemetryData
from models.gps_location import GPSLocation
from models.rental import Rental
from models.rental_status import RentalStatus
from repositories.user_csv_repository import UserCSVRepository
from repositories.vehicule_csv_repository import VehiculeCSVRepository
from repositories.rental_csv_repository import RentalCSVRepository


def test_user_repository_save_load(tmp_path):
    p = tmp_path / "users.csv"
    repo = UserCSVRepository(str(p))
    users = [User("Alice"), User("Bob")]
    repo.save(users)
    loaded = repo.load()
    assert len(loaded) == 2
    assert loaded[0].name == "Alice"
    assert loaded[1].name == "Bob"


def test_vehicule_repository_save_load(tmp_path):
    p = tmp_path / "vehicules.csv"
    repo = VehiculeCSVRepository(str(p))

    # Create two vehicles
    v1 = Vehicule(1, 80, 20, State.AVAILABLE)
    v2 = Vehicule(2, 30, 35, State.MAINTENANCE)
    # set location on v1
    v1.lastKnownLocation = GPSLocation(41.9, 12.5)
    repo.save([v1, v2])

    loaded = repo.load()
    assert len(loaded) == 2
    ids = {lv.vehiculeId for lv in loaded}
    assert 1 in ids and 2 in ids


def test_rental_repository_save_load(tmp_path):
    p = tmp_path / "rentals.csv"
    repo = RentalCSVRepository(str(p))

    user = User("Charlie")
    v = Vehicule(10, 90, 20, State.AVAILABLE)
    scheduled = datetime.now()
    r = Rental(user, v, scheduled)
    r.actualStartTime = scheduled + timedelta(minutes=1)
    r.endTime = r.actualStartTime + timedelta(minutes=10)
    r.cost = 5.0
    r.status = RentalStatus.COMPLETED

    repo.save([r])
    loaded = repo.load()
    assert len(loaded) == 1
    lr = loaded[0]
    assert lr.user.name == "Charlie"
    assert lr.vehicule.vehiculeId == 10
    assert lr.status == RentalStatus.COMPLETED
    assert abs((lr.scheduledStartTime - scheduled).total_seconds()) < 2
