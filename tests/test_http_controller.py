import unittest
import threading
import time
import requests
from controllers.http_controller import initializeServer
from controllers import SmartMoveCentralController
from repositories import VehiculeCSVRepository, UserCSVRepository, RentalCSVRepository
from services import PersistenceManager, AuditLogger
from regulations import LondonRegulation
from vehicules import Bike
from models import State

class DummyLogger:
    def __init__(self):
        self.events = []
    def logEvent(self, msg):
        self.events.append(msg)

class TestHttpController(unittest.TestCase):
    def setUp(self):
        self.vehicule_repo = VehiculeCSVRepository("./test_vehicules.csv")
        self.user_repo = UserCSVRepository("./test_users.csv")
        self.rental_repo = RentalCSVRepository("./test_rentals.csv")
        self.audit_logger = DummyLogger()
        self.persistence_manager = PersistenceManager(self.vehicule_repo, self.user_repo, self.rental_repo, self.audit_logger)
        self.controller = SmartMoveCentralController(self.persistence_manager, self.audit_logger, [LondonRegulation()])
        self.controller.vehicules.append(Bike(1, 80, 20, State.AVAILABLE))
        self.server = initializeServer(self.controller, adress="127.0.0.1", port=9090)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        time.sleep(0.1)

    def tearDown(self):
        self.server.shutdown()
        self.server_thread.join(timeout=2)

    def test_get_users_empty(self):
        resp = requests.get("http://127.0.0.1:9090/users", timeout=2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_register_user_login(self):
        resp = requests.post("http://127.0.0.1:9090/registerUser", json={"username": "alice", "password": "pass"}, timeout=2)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

        login_resp = requests.post("http://127.0.0.1:9090/login", json={"username": "alice", "password": "pass"}, timeout=2)
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json().get("username"), "alice")

    def test_reserve_and_activate(self):
        requests.post("http://127.0.0.1:9090/registerUser", json={"username": "bob", "password": "pass"}, timeout=2)
        users = requests.get("http://127.0.0.1:9090/users", timeout=2).json()
        self.assertTrue(len(users) > 0)
        user_id = users[0]["userId"]

        reserve = requests.post("http://127.0.0.1:9090/reserveVehicle", json={"userId": user_id, "vehicleId": 1}, timeout=2)
        self.assertEqual(reserve.status_code, 200)

        activate = requests.post("http://127.0.0.1:9090/activateVehicle", json={"username": "bob", "vehicleId": 1}, timeout=2)
        self.assertIn(activate.status_code, [200, 422])

    def test_register_and_maintenance_endpoints(self):
        r = requests.post("http://127.0.0.1:9090/registerUser", json={"username": "charlie", "password": "pass"}, timeout=2)
        self.assertEqual(r.status_code, 200)

        r = requests.post("http://127.0.0.1:9090/registerVehicle", json={"vehicleId": 2, "vehicleType": "scooter"}, timeout=2)
        self.assertEqual(r.status_code, 200)

        r = requests.post("http://127.0.0.1:9090/assignMaintenance", json={"vehicleId": 2}, timeout=2)
        self.assertEqual(r.status_code, 200)

        r = requests.post("http://127.0.0.1:9090/completeMaintenance", json={"vehicleId": 2}, timeout=2)
        self.assertIn(r.status_code, [200, 422])

if __name__ == '__main__':
    unittest.main()
