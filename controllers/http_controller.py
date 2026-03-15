from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler 
from controllers import SmartMoveCentralController
from functools import partial
from datetime import datetime
import json

class HttpHandler(BaseHTTPRequestHandler):
    def __init__(self, moveControl: SmartMoveCentralController, *args, **kwargs):
        self.moveControl = moveControl
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == "/users":
            # List all users (userId is the index in the users list)
            users_data = []
            for index, user in enumerate(self.moveControl.users):
                users_data.append({
                    "userId": index,
                    "username": user.name
                })
            self.responseJson(200, json.dumps(users_data))
        
        elif self.path == "/vehicles":
            # List all vehicles
            vehicles_data = []
            for vehicle in self.moveControl.vehicules:
                vehicles_data.append({
                    "vehicleId": vehicle.vehiculeId,
                    "type": vehicle.__class__.__name__.lower(),
                    "state": vehicle.state.name,
                    "batteryLevel": vehicle.telemetryData.batteryLevel,
                    "temperature": vehicle.telemetryData.temperature,
                    "hasActiveRental": vehicle.hasActiveRental
                })
            self.responseJson(200, json.dumps(vehicles_data))
        
        elif self.path == "/vehicles/available":
            # List available vehicles
            vehicles_data = []
            for vehicle in self.moveControl.vehicules:
                if vehicle.state.name == "AVAILABLE" and not vehicle.hasActiveRental:
                    vehicles_data.append({
                        "vehicleId": vehicle.vehiculeId,
                        "type": vehicle.__class__.__name__.lower(),
                        "batteryLevel": vehicle.telemetryData.batteryLevel
                    })
            self.responseJson(200, json.dumps(vehicles_data))
        
        elif self.path.startswith("/user/"):
            # Get user by username (userId is the index in the users list)
            username = self.path.split("/")[-1]
            user = self.moveControl.findUserByName(username)
            if user:
                # Find the index of this user
                user_index = -1
                for index, u in enumerate(self.moveControl.users):
                    if u.name == username:
                        user_index = index
                        break
                if user_index >= 0:
                    user_data = {
                        "userId": user_index,
                        "username": user.name
                    }
                    self.responseJson(200, json.dumps(user_data))
                else:
                    self.send_response(404)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        
        elif self.path.startswith("/rentals/"):
            # Get active rentals for a user
            username = self.path.split("/")[-1]
            user = self.moveControl.findUserByName(username)
            if user:
                from datetime import datetime, timedelta
                rentals_data = []
                now = datetime.now()
                for rental in self.moveControl.rentals:
                    try:
                        if rental.user.name == username:
                            # Show RESERVED and ACTIVE rentals
                            # Also show CANCELLED rentals from last 30 minutes (emergency terminations)
                            is_active = rental.status.name in ["RESERVED", "ACTIVE"]
                            is_recent_cancellation = (
                                rental.status.name == "CANCELLED" and 
                                rental.endTime and 
                                (now - rental.endTime) < timedelta(minutes=30)
                            )
                            
                            if is_active or is_recent_cancellation:
                                rental_data = {
                                    "vehicleId": rental.vehicule.vehiculeId,
                                    "vehicleType": rental.vehicule.__class__.__name__.lower(),
                                    "status": rental.status.name,
                                    "scheduledStartTime": rental.scheduledStartTime.isoformat() if rental.scheduledStartTime else None,
                                    "actualStartTime": rental.actualStartTime.isoformat() if rental.actualStartTime else None,
                                    "endTime": rental.endTime.isoformat() if rental.endTime else None,
                                    "cost": rental.cost if rental.cost else None
                                }
                                
                                # Add vehicle telemetry if available
                                if rental.vehicule and rental.vehicule.telemetryData:
                                    rental_data["vehicleState"] = rental.vehicule.state.name
                                    rental_data["batteryLevel"] = rental.vehicule.telemetryData.batteryLevel
                                    rental_data["temperature"] = rental.vehicule.telemetryData.temperature
                                    if rental.vehicule.lastKnownLocation:
                                        rental_data["latitude"] = rental.vehicule.lastKnownLocation.latitude
                                        rental_data["longitude"] = rental.vehicule.lastKnownLocation.longitude
                                
                                rentals_data.append(rental_data)
                    except Exception as e:
                        # Log error but continue processing other rentals
                        print(f"Error processing rental for vehicle {rental.vehicule.vehiculeId if rental.vehicule else 'N/A'}: {e}")
                        continue
                
                self.responseJson(200, json.dumps(rentals_data))
            else:
                self.send_response(404)
                self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        dispatch = {
            "/login": self._handle_login,
            "/reserveVehicle": self._handle_reserve_vehicle,
            "/activateVehicle": self._handle_activate_vehicle,
            "/cancelRental": self._handle_cancel_rental,
            "/returnVehicle": self._handle_return_vehicle,
            "/assignMaintenance": self._handle_assign_maintenance,
            "/completeMaintenance": self._handle_complete_maintenance,
            "/assignRelocation": self._handle_assign_relocation,
            "/completeRelocation": self._handle_complete_relocation,
            "/requestEmUnlock": self._handle_request_em_unlock,
            "/update": self._handle_update,
            "/registerVehicle": self._handle_register_vehicle,
            "/registerUser": self._handle_register_user,
            "/shutdown": self._handle_shutdown
        }

        handler = dispatch.get(self.path)
        if handler:
            handler()
            return

        self.send_response(404)
        self.end_headers()

    def _handle_login(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return

        username = data.get("username"); password = data.get("password")
        if self.moveControl.authenticateUser(username, password):
            user_index = next((i for i, user in enumerate(self.moveControl.users) if user.name == username), -1)
            if user_index >= 0:
                self._respond_success({"userId": user_index, "username": username})
                return
        self._respond_error(401)

    def _handle_reserve_vehicle(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return

        user = self.moveControl.getUserFromId(data.get("userId"))
        vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
        if user is None or vehicle is None:
            self._respond_error(422); return
        if self.moveControl.rentVehicule(vehicle, user, datetime.now()):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_activate_vehicle(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return

        try:
            rental = self.moveControl.getRentalFromNameId(data.get("username"), int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return

        if rental is None:
            self._respond_error(422, {"error": "Rental not found"}); return
        success, error_msg = self.moveControl.activateRental(rental)
        if success:
            self._respond_success(); return
        self._respond_error(422, {"error": error_msg or "Cannot activate rental"})

    def _handle_cancel_rental(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return

        try:
            rental = self.moveControl.getRentalFromNameId(data.get("username"), int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if rental is None:
            self._respond_error(422); return

        if self.moveControl.cancelRental(rental):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_return_vehicle(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return

        try:
            rental = self.moveControl.getRentalFromNameId(data.get("username"), int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if rental is None:
            self._respond_error(422); return

        if self.moveControl.returnVehicule(rental):
            duration = rental.calculateRentalDuration()
            self._respond_success({"success": True, "cost": rental.cost if rental.cost else 0.0, "duration_minutes": duration if duration else 0.0})
        else:
            self._respond_error(422)

    def _handle_assign_maintenance(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        try:
            vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if vehicle is None:
            self._respond_error(422); return
        if self.moveControl.assignMaintenance(vehicle):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_complete_maintenance(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
        if vehicle is None:
            self._respond_error(422); return
        if self.moveControl.completeMaintenance(vehicle):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_assign_relocation(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        try:
            vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if vehicle is None:
            self._respond_error(422); return
        if self.moveControl.relocateVehicule(vehicle):
            self._respond_success();
        else:
            self._respond_error(422)

    def _handle_complete_relocation(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        try:
            vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if vehicle is None:
            self._respond_error(422); return
        if self.moveControl.completeRelocation(vehicle):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_request_em_unlock(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
        if vehicle is None:
            self._respond_error(422); return
        if self.moveControl.unlockVehicule(vehicle):
            self._respond_success();
        else:
            self._respond_error(422)

    def _handle_update(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        try:
            vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
        except (TypeError, ValueError):
            self._respond_error(400); return
        if vehicle is None:
            self._respond_error(422); return

        from models import TelemetryData, GPSLocation
        batteryLevel = int(data.get("batteryLevel", vehicle.telemetryData.batteryLevel))
        temperature = int(data.get("temperature", vehicle.telemetryData.temperature))
        isFaulted = data.get("isFaulted", False)
        location = None
        if "latitude" in data and "longitude" in data:
            try:
                location = GPSLocation(float(data["latitude"]), float(data["longitude"]))
            except (TypeError, ValueError):
                pass
        newTelemetry = TelemetryData(batteryLevel, temperature, location, isFaulted)
        self.moveControl.processTelemetryData(vehicle, newTelemetry)
        self._respond_success()

    def _handle_register_vehicle(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400); return
        try:
            vehicleId = int(data.get("vehicleId"))
        except (TypeError, ValueError):
            self._respond_error(400); return
        vehicleType = data.get("vehicleType")
        if self.moveControl.registerVehicle(vehicleId, vehicleType):
            self._respond_success()
        else:
            self._respond_error(422)

    def _handle_register_user(self):
        data = self._parse_json_body();
        if data is None:
            self._respond_error(400, {"success": False, "error": "Invalid request"}); return
        username = data.get("username")
        password = data.get("password", "")
        if self.moveControl.registerUser(username, password):
            self._respond_success({"success": True, "username": username})
        else:
            self._respond_error(422, {"success": False, "error": "Username already exists"})

    def _handle_shutdown(self):
        try:
            print("\n[SHUTDOWN] Received shutdown request...")
            print("[SHUTDOWN] Saving data...")
            self.moveControl.saveData()
            print("[SHUTDOWN] Stopping background monitoring...")
            self.moveControl.stopBackgroundMonitoring()
            self._respond_success({"success": True, "message": "Server shutting down gracefully"})
            import threading
            def delayed_shutdown():
                import time
                time.sleep(1)
                print("[SHUTDOWN] Stopping server...")
                self.server.shutdown()
            threading.Thread(target=delayed_shutdown, daemon=True).start()
        except Exception as e:
            print(f"[SHUTDOWN] Error during shutdown: {e}")
            self.responseJson(500, json.dumps({"success": False, "error": str(e)}))

    def responseJson(self, code: int, json_data: str):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json_data.encode("utf-8"))

    def _parse_json_body(self):
        contentLength = int(self.headers.get('Content-Length', 0))
        if contentLength <= 0:
            return None
        content = self.rfile.read(contentLength).decode("utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    def _respond_error(self, code=400, body=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if body is not None:
            self.wfile.write(json.dumps(body).encode("utf-8"))

    def _respond_success(self, body=None):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if body is not None:
            self.wfile.write(json.dumps(body).encode("utf-8"))


def initializeServer(
        moveControl: SmartMoveCentralController,
        adress="",
        port=8080
        ) -> ThreadingHTTPServer:
    """Returns the built-in python HTTP threaded server, except that the move
    controller is injected into the router."""
    
    handlerMoveControler = partial(HttpHandler, moveControl)
    return ThreadingHTTPServer((adress, port), handlerMoveControler)
