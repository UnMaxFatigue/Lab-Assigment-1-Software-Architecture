import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from models.telemetry_data import TelemetryData
from models.vehicule import Vehicule
from models.user import User
from models.state import State
from controllers.smart_controller import SmartMoveCentralController
from models.rental_status import RentalStatus


class DummyPM:
    def loadAll(self):
        return ([], [], [])

    def saveAll(self, v, u, r):
        return (True, (v, u, r))


class DummyLogger:
    def __init__(self):
        self.events = []

    def logEvent(self, msg):
        self.events.append(msg)


def test_rent_activate_return_flow():
    pm = DummyPM()
    al = DummyLogger()
    ctrl = SmartMoveCentralController(pm, al)

    user = User("Bob")
    v = Vehicule(10, 80, 25, State.AVAILABLE)

    # Rent vehicle
    rental = ctrl.rentVehicule(v, user, datetime.now())
    assert rental is not None
    assert v.state == State.RESERVED
    assert v.hasActiveRental is True

    # Activate rental
    ok = ctrl.activateRental(rental)
    assert ok is True
    assert rental.status == RentalStatus.ACTIVE
    assert v.state == State.INUSE

    # Return vehicle normally
    ok2 = ctrl.returnVehicule(rental)
    assert ok2 is True
    assert rental.status == RentalStatus.COMPLETED
    assert v.state == State.AVAILABLE
    assert v.hasActiveRental is False
