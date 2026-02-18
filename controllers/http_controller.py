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
                rentals_data = []
                for rental in self.moveControl.rentals:
                    if rental.user.name == username and rental.status.name in ["RESERVED", "ACTIVE"]:
                        rentals_data.append({
                            "vehicleId": rental.vehicule.vehiculeId,
                            "vehicleType": rental.vehicule.__class__.__name__.lower(),
                            "status": rental.status.name,
                            "scheduledStartTime": rental.scheduledStartTime.isoformat() if rental.scheduledStartTime else None,
                            "actualStartTime": rental.actualStartTime.isoformat() if rental.actualStartTime else None
                        })
                self.responseJson(200, json.dumps(rentals_data))
            else:
                self.send_response(404)
                self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/login":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                username = data.get("username")
                password = data.get("password")
                
                if self.moveControl.authenticateUser(username, password):
                    # Find user index
                    user_index = -1
                    for index, user in enumerate(self.moveControl.users):
                        if user.name == username:
                            user_index = index
                            break
                    
                    if user_index >= 0:
                        user_data = {
                            "userId": user_index,
                            "username": username
                        }
                        self.responseJson(200, json.dumps(user_data))
                    else:
                        self.send_response(401)
                        self.end_headers()
                else:
                    self.send_response(401)  # Unauthorized
                    self.end_headers()
            
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
        
        elif self.path == "/reserveVehicle":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                user = self.moveControl.getUserFromId(data.get("userId"))
                vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
                
                if user is None or vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.rentVehicule(
                            vehicle, 
                            user, 
                            datetime.now() 
                            )

                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()

        elif self.path == "/activateVehicle":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                rental = self.moveControl.getRentalFromNameId(
                        data.get("username"),
                        int(data.get("vehicleId"))
                        )
                
                if rental is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.activateRental(rental)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/cancelRental":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                rental = self.moveControl.getRentalFromNameId(
                        data.get("username"),
                        int(data.get("vehicleId"))
                        )
                
                if rental is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    cancelCheck = self.moveControl.cancelRental(rental)
                    if cancelCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/returnVehicle":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                rental = self.moveControl.getRentalFromNameId(
                        data.get("username"),
                        int(data.get("vehicleId"))
                        )
                
                if rental is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    returnCheck = self.moveControl.returnVehicule(rental)
                    if returnCheck:
                        # Return cost information
                        duration = rental.calculateRentalDuration()
                        response_data = {
                            "success": True,
                            "cost": rental.cost if rental.cost else 0.0,
                            "duration_minutes": duration if duration else 0.0
                        }
                        self.responseJson(200, json.dumps(response_data))
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/assignMaintenance":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.assignMaintenance(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/completeMaintenance":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.completeMaintenance(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
        
        elif self.path == "/assignRelocation":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.relocateVehicule(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/completeRelocation":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.completeRelocation(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

        elif self.path == "/requestEmUnlock":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(data.get("vehicleId"))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    reserveCheck = self.moveControl.unlockVehicule(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
                        self.end_headers()

            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()

        elif self.path == "/update":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicle = self.moveControl.getVehicleFromId(int(data.get("vehicleId")))
                
                if vehicle is None:
                    self.send_response(422)
                    self.end_headers()
                else:
                    # Extract telemetry data from request
                    from models import TelemetryData, GPSLocation
                    
                    batteryLevel = int(data.get("batteryLevel", vehicle.telemetryData.batteryLevel))
                    temperature = int(data.get("temperature", vehicle.telemetryData.temperature))
                    isFaulted = data.get("isFaulted", False)
                    
                    location = None
                    if "latitude" in data and "longitude" in data:
                        location = GPSLocation(float(data["latitude"]), float(data["longitude"]))
                    
                    newTelemetry = TelemetryData(batteryLevel, temperature, location, isFaulted)
                    
                    self.moveControl.processTelemetryData(vehicle, newTelemetry)
                    self.send_response(200)
                    self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()


        elif self.path == "/registerVehicle":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                vehicleId = int(data.get("vehicleId"))
                vehicleType = data.get("vehicleType")
                
                registerCheck = self.moveControl.registerVehicle(vehicleId, vehicleType)
                if registerCheck:
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_response(422)
                    self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()
    
        elif self.path == "/registerUser":
            contentLength = int(self.headers.get('Content-Length',0))
            content = self.rfile.read(contentLength).decode("utf-8")
            
            try:
                data = json.loads(content)
                username = data.get("username")
                password = data.get("password", "")
                
                registerCheck = self.moveControl.registerUser(username, password)
                if registerCheck:
                    response_data = {"success": True, "username": username}
                    self.responseJson(200, json.dumps(response_data))
                else:
                    response_data = {"success": False, "error": "Username already exists"}
                    self.responseJson(422, json.dumps(response_data))

            except (json.JSONDecodeError, ValueError):
                response_data = {"success": False, "error": "Invalid request"}
                self.responseJson(400, json.dumps(response_data))

            

        else:
            self.send_response(404)
            self.end_headers()


    def responseJson(self, code: int, json_data: str):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json_data.encode("utf-8"))

def initializeServer(
        moveControl: SmartMoveCentralController,
        adress="",
        port=8080
        ) -> ThreadingHTTPServer:
    """Returns the built-in python HTTP threaded server, except that the move
    controller is injected into the router."""
    
    handlerMoveControler = partial(HttpHandler, moveControl)
    return ThreadingHTTPServer((adress, port), handlerMoveControler)
