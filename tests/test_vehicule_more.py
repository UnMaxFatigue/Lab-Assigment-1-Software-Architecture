import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vehicule import Vehicule
from models.state import State
from models.telemetry_data import TelemetryData
from models.gps_location import GPSLocation
from datetime import datetime


def test_change_state_maintenance_to_inuse_blocked():
    v = Vehicule(100, 80, 25, State.MAINTENANCE)
    v.changeState(State.INUSE)
    assert v.state == State.MAINTENANCE


def test_change_state_normal_transitions():
    v = Vehicule(101, 80, 25, State.AVAILABLE)
    v.changeState(State.RESERVED)
    assert v.state == State.RESERVED
    v.changeState(State.INUSE)
    assert v.state == State.INUSE
    v.changeState(State.AVAILABLE)
    assert v.state == State.AVAILABLE


def test_update_telemetry_and_location():
    v = Vehicule(102, 50, 20, State.AVAILABLE)
    loc = GPSLocation(41.9, 12.5)
    t = TelemetryData(30, 25, location=loc)
    v.updateTelemetry(t)
    assert v.telemetryData.batteryLevel == 30
    assert v.telemetryData.location.latitude == 41.9
    assert v.lastKnownLocation is None


def test_has_active_rental_flag():
    v = Vehicule(103, 70, 20, State.AVAILABLE)
    assert v.hasActiveRental is False
    v.hasActiveRental = True
    assert v.hasActiveRental is True
