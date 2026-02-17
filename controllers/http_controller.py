from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler 
from controllers import SmartMoveCentralController
from functools import partial
from datetime import datetime
import json

class HttpHandler(BaseHTTPRequestHandler):
    def __init__(self, moveControl: SmartMoveCentralController, *args, **kwargs):
        self.moveControl = moveControl
        super().__init__(*args, **kwargs)


    def do_POST(self):
        if self.path == "/reserveVehicle":
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
                            user, 
                            vehicle, 
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
                    reserveCheck = self.moveControl.returnVehicule(rental)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
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
                    reserveCheck = self.moveControl.assignRelocation(vehicle)
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
                    reserveCheck = self.moveControl.processTelemetryData(vehicle)
                    if reserveCheck:
                        self.send_response(200)
                        self.end_headers()
                    else:
                        self.send_response(422)
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
                name = data.get("username")
                
                registerCheck = self.moveControl.registerUser(name)
                if registerCheck:
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_response(422)
                    self.end_headers()

            except (json.JSONDecodeError, ValueError):
                self.send_response(400)
                self.end_headers()

            

        else:
            self.send_response(404)
            self.end_headers()



    def responseJson(self, code:int, json:str):
        self.send_response(code)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        self.wfile.write(json.encode("utf-8"))

def initializeServer(
        moveControl: SmartMoveCentralController,
        adress="",
        port=8080
        ) -> ThreadingHTTPServer:
    """Returns the built-in python HTTP threaded server, except that the move
    controller is injected into the router."""
    
    handlerMoveControler = partial(HttpHandler, moveControl)
    return ThreadingHTTPServer((adress, port), handlerMoveControler)
