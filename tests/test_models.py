import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from models.telemetry_data import TelemetryData
from models.rental import Rental
from models.user import User
from models.vehicule import Vehicule
from models.state import State


def test_telemetry_is_healthy():
    t = TelemetryData(50, 25)
    assert t.isHealthy() is True

    t_low = TelemetryData(10, 25)
    assert t_low.isHealthy() is False

    t_hot = TelemetryData(50, 60)
    assert t_hot.isHealthy() is False


def test_rental_duration_and_cost():
    u = User("Alice")
    v = Vehicule(1, 100, 20, State.AVAILABLE)
    r = Rental(u, v, datetime.now())
    r.actualStartTime = datetime.now()
    r.endTime = r.actualStartTime + timedelta(minutes=30)
    duration = r.calculateRentalDuration()
    assert duration == 30
    cost = r.calculateRentalCost()
    assert cost == 15
