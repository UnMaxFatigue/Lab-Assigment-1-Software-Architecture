"""
SmartMove CLI Client - Text interface to interact with the server
"""
import requests
import getpass
from typing import Optional

class SmartMoveClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.current_user = None
        self.current_username = None
    
    def print_header(self, text: str):
        """Display a formatted header"""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60)
    
    def print_menu(self, options: list):
        """Display a menu with options"""
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Back/Quit")

    def _request(self, method: str, path: str, json_data: Optional[dict] = None) -> Optional[requests.Response]:
        """Send an HTTP request and handle common errors."""
        url = f"{self.base_url}{path}"
        try:
            if method == "GET":
                return requests.get(url, timeout=5)
            if method == "POST":
                return requests.post(url, json=json_data, timeout=5)
            print(f"[ERROR] Unsupported HTTP method: {method}")
            return None
        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Cannot connect to server. Is it running?")
            return None
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return None

    def _post(self, path: str, json_data: Optional[dict] = None) -> Optional[requests.Response]:
        """Convenience wrapper for POST requests."""
        return self._request("POST", path, json_data=json_data)

    def _get(self, path: str) -> Optional[requests.Response]:
        """Convenience wrapper for GET requests."""
        return self._request("GET", path)
    
    def get_choice(self, max_option: int) -> int:
        """Get the user's choice"""
        while True:
            try:
                choice = int(input("\nYour choice: "))
                if 0 <= choice <= max_option:
                    return choice
                print(f"Please enter a number between 0 and {max_option}")
            except ValueError:
                print("Please enter a valid number")
    
    def login(self) -> bool:
        """Login or create user"""
        self.print_header("LOGIN")
        print("  1. Login with existing account")
        print("  2. Create a new account")
        print("  0. Back")
        
        choice = self.get_choice(2)
        
        if choice == 0:
            return False
        elif choice == 1:
            return self.login_existing()
        elif choice == 2:
            return self.create_account()
    
    def login_existing(self) -> bool:
        """Login with existing account"""
        username = input("\nEnter your username: ").strip()
        if not username:
            print("[ERROR] Username cannot be empty")
            return False
        
        password = getpass.getpass("Enter your password: ")

        response = self._post("/login", {"username": username, "password": password})
        if not response:
            return False
        if response.status_code == 200:
            user_data = response.json()
            self.current_user = user_data['userId']
            self.current_username = user_data['username']
            print(f"\n[OK] Logged in as {self.current_username}")
            return True
        if response.status_code == 401:
            print("\n[ERROR] Invalid username or password")
            return False
        print("\n[ERROR] Error during login")
        return False
    
    def create_account(self) -> bool:
        """Create a new account"""
        username = input("\nEnter your username: ").strip()
        if not username:
            print("[ERROR] Username cannot be empty")
            return False
        
        password = getpass.getpass("Enter your password: ")
        if not password:
            print("[ERROR] Password cannot be empty")
            return False
        
        password_confirm = getpass.getpass("Confirm your password: ")
        if password != password_confirm:
            print("[ERROR] Passwords do not match")
            return False

        response = self._post("/registerUser", {"username": username, "password": password})
        if not response:
            return False
        if response.status_code == 200:
            print(f"\n[OK] Account created successfully!")
            # Now login with the new credentials
            login_response = self._post("/login", {"username": username, "password": password})
            if login_response and login_response.status_code == 200:
                user_data = login_response.json()
                self.current_user = user_data['userId']
                self.current_username = username
                print(f"[OK] Logged in as {self.current_username}")
                return True
            print("[WARNING] Account created. Please login manually.")
            return False
        if response.status_code == 422:
            print(f"\n[ERROR] This username already exists")
            return False
        print(f"\n[ERROR] Error creating account")
        return False
    
    def view_available_vehicles(self) -> bool:
        """Display available vehicles. Returns True if vehicles are available."""
        try:
            response = self._get("/vehicles/available")
            if not response:
                return False
            if response.status_code == 200:
                vehicles = response.json()
                if not vehicles:
                    print("\nNo vehicles available at the moment")
                    return False
                
                self.print_header("AVAILABLE VEHICLES")
                for vehicle in vehicles:
                    battery_bar = "█" * (vehicle['batteryLevel'] // 10)
                    print(f"\n  ID: {vehicle['vehicleId']}")
                    print(f"  Type: {vehicle['type'].upper()}")
                    print(f"  Battery: [{battery_bar:<10}] {vehicle['batteryLevel']}%")
                return True
            else:
                print("\n[ERROR] Error retrieving vehicles")
                return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False
    
    def view_my_rentals(self) -> bool:
        """Display my active rentals. Returns True if rentals exist."""
        try:
            response = self._get(f"/rentals/{self.current_username}")
            if not response:
                return False
            if response.status_code == 200:
                rentals = response.json()
                if not rentals:
                    print("\nNo active rentals")
                    return False
                
                self.print_header("MY ACTIVE RENTALS")
                for rental in rentals:
                    # Different icons based on status
                    status = rental.get('status', 'UNKNOWN')
                    if status == "RESERVED":
                        status_icon = "[RESERVED]"
                    elif status == "ACTIVE":
                        status_icon = "[ACTIVE]"
                    elif status == "CANCELLED":
                        status_icon = "[CANCELLED]"
                    else:
                        status_icon = f"[{status}]"
                    
                    print(f"\n  {status_icon} Vehicle ID: {rental.get('vehicleId', 'N/A')}")
                    print(f"  Type: {rental.get('vehicleType', 'unknown').upper()}")
                    print(f"  Status: {status}")
                    
                    # Vehicle telemetry (may not always be available)
                    if 'vehicleState' in rental:
                        print(f"  Vehicle State: {rental['vehicleState']}")
                    
                    if 'batteryLevel' in rental:
                        battery_level = rental['batteryLevel']
                        battery_bar = "█" * (battery_level // 10)
                        print(f"  Battery: [{battery_bar:<10}] {battery_level}%")
                    
                    if 'temperature' in rental:
                        print(f"  Temperature: {rental['temperature']}°C")
                    
                    if rental.get('latitude') and rental.get('longitude'):
                        print(f"  Location: {rental['latitude']:.4f}, {rental['longitude']:.4f}")
                    
                    if rental.get('scheduledStartTime'):
                        print(f"  Scheduled start: {rental['scheduledStartTime']}")
                    if rental.get('actualStartTime'):
                        print(f"  Started on: {rental['actualStartTime']}")
                    if rental.get('endTime'):
                        print(f"  Ended on: {rental['endTime']}")
                    if rental.get('cost'):
                        print(f"  Cost: ${rental['cost']:.2f}")
                    
                    # Show warning if cancelled unexpectedly
                    if status == "CANCELLED":
                        vehicle_state = rental.get('vehicleState', '')
                        if vehicle_state == "EMERGENCYLOCK":
                            print(f"  [WARNING] Rental terminated due to emergency (battery/overheating/theft)")
                        elif vehicle_state == "MAINTENANCE":
                            print(f"  [WARNING] Vehicle sent to maintenance")
                return True
            else:
                print("\n[ERROR] Error retrieving rentals")
                return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False
    
    def reserve_vehicle(self):
        """Reserve a vehicle"""
        if not self.view_available_vehicles():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to reserve (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
            response = self._post("/reserveVehicle", {"userId": self.current_user, "vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Vehicle reserved successfully!")
                print("[INFO] Don't forget to activate the rental before leaving")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot reserve this vehicle (already rented or unavailable)")
            else:
                print("\n[ERROR] Error during reservation")
        except ValueError:
            print("\n[ERROR] Invalid ID")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def activate_rental(self):
        """Activate a reserved rental"""
        if not self.view_my_rentals():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to activate (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
            response = self._post("/activateVehicle", {"username": self.current_username, "vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Rental activated! Have a great ride!")
            elif response.status_code == 422:
                error_data = response.json()
                error_msg = error_data.get("error", "Cannot activate this rental")
                print(f"\n[ERROR] {error_msg}")
            else:
                print("\n[ERROR] Error during activation")
        except ValueError:
            print("\n[ERROR] Invalid ID")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def return_vehicle(self):
        """Return a vehicle"""
        if not self.view_my_rentals():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to return (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
            
        try:
            response = self._post("/returnVehicle", {"username": self.current_username, "vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                try:
                    data = response.json()
                    cost = data.get('cost', 0.0)
                    duration = data.get('duration_minutes', 0.0)
                    print("\n[OK] Vehicle returned successfully! Thank you!")
                    print(f"[INFO] Rental duration: {duration:.1f} minutes")
                    print(f"[INFO] Total cost: ${cost:.2f}")
                except Exception as json_err:
                    print("\n[OK] Vehicle returned successfully! Thank you!")
                    print(f"[WARNING] Could not parse cost information: {json_err}")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot return this vehicle (must be ACTIVE, not just RESERVED)")
                print("[INFO] If you want to cancel a reservation, use option 5")
            else:
                print("\n[ERROR] Error during return")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def cancel_rental(self):
        """Cancel a reserved rental"""
        if not self.view_my_rentals():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to cancel reservation (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
            response = self._post("/cancelRental", {"username": self.current_username, "vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Reservation cancelled successfully!")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot cancel this rental (must be RESERVED, not ACTIVE)")
            else:
                print("\n[ERROR] Error during cancellation")
        except ValueError:
            print("\n[ERROR] Invalid ID")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def main_menu(self):
        """Main menu after login"""
        while True:
            self.print_header(f"WELCOME {self.current_username.upper()}")
            options = [
                "View available vehicles",
                "Reserve a vehicle",
                "Activate a rental",
                "Return a vehicle",
                "Cancel a reservation",
                "View my active rentals",
                "Admin Mode (Vehicle Management)"
            ]
            self.print_menu(options)
            
            choice = self.get_choice(len(options))
            
            if choice == 0:
                print("\nSee you soon!")
                self.current_user = None
                self.current_username = None
                break
            elif choice == 1:
                self.view_available_vehicles()
            elif choice == 2:
                self.reserve_vehicle()
            elif choice == 3:
                self.activate_rental()
            elif choice == 4:
                self.return_vehicle()
            elif choice == 5:
                self.cancel_rental()
            elif choice == 6:
                self.view_my_rentals()
            elif choice == 7:
                self.admin_menu()
    
    def view_all_vehicles(self) -> bool:
        """Display all vehicles with their states. Returns True if vehicles exist."""
        try:
            response = self._get("/vehicles")
            if not response:
                return False
            if response.status_code == 200:
                vehicles = response.json()
                if not vehicles:
                    print("\nNo vehicles in the system")
                    return False
                
                self.print_header("ALL VEHICLES")
                for vehicle in vehicles:
                    battery_bar = "█" * (vehicle['batteryLevel'] // 10)
                    status_icon = {
                        'AVAILABLE': '[AVAILABLE]',
                        'RESERVED': '[RESERVED]',
                        'INUSE': '[IN USE]',
                        'MAINTENANCE': '[MAINTENANCE]',
                        'EMERGENCYLOCK': '[LOCKED]',
                        'RELOCATING': '[RELOCATING]'
                    }.get(vehicle['state'], f"[{vehicle['state']}]")
                    
                    print(f"\n  {status_icon} ID: {vehicle['vehicleId']}")
                    print(f"  Type: {vehicle['type'].upper()}")
                    print(f"  State: {vehicle['state']}")
                    print(f"  Battery: [{battery_bar:<10}] {vehicle['batteryLevel']}%")
                    print(f"  Temperature: {vehicle['temperature']}°C")
                    print(f"  Has Active Rental: {'Yes' if vehicle['hasActiveRental'] else 'No'}")
                return True
            else:
                print("\n[ERROR] Error retrieving vehicles")
                return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False
    
    def view_vehicles_by_state(self, states: list, header: str) -> bool:
        """Display vehicles filtered by state(s). Returns True if matching vehicles exist."""
        try:
            response = self._get("/vehicles")
            if not response:
                return False
            if response.status_code == 200:
                vehicles = response.json()
                filtered = [v for v in vehicles if v['state'] in states]
                
                if not filtered:
                    print(f"\nNo vehicles in state(s): {', '.join(states)}")
                    return False
                
                self.print_header(header)
                for vehicle in filtered:
                    battery_bar = "█" * (vehicle['batteryLevel'] // 10)
                    print(f"\n  ID: {vehicle['vehicleId']}")
                    print(f"  Type: {vehicle['type'].upper()}")
                    print(f"  State: {vehicle['state']}")
                    print(f"  Battery: [{battery_bar:<10}] {vehicle['batteryLevel']}%")
                    print(f"  Temperature: {vehicle['temperature']}°C")
                    print(f"  Has Active Rental: {'Yes' if vehicle['hasActiveRental'] else 'No'}")
                return True
            else:
                print("\n[ERROR] Error retrieving vehicles")
                return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False
    
    def assign_maintenance(self):
        """Assign a vehicle to maintenance"""
        if not self.view_vehicles_by_state(['AVAILABLE', 'EMERGENCYLOCK'], "VEHICLES ELIGIBLE FOR MAINTENANCE"):
            return
        
        vehicle_id = input("\nEnter the vehicle ID to assign to maintenance (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
            
        try:
            response = self._post("/assignMaintenance", {"vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Vehicle assigned to maintenance successfully!")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot assign maintenance (vehicle must be AVAILABLE or EMERGENCYLOCK)")
            else:
                print("\n[ERROR] Error assigning maintenance")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def complete_maintenance(self):
        """Complete maintenance on a vehicle"""
        if not self.view_vehicles_by_state(['MAINTENANCE'], "VEHICLES IN MAINTENANCE"):
            return
        
        vehicle_id = input("\nEnter the vehicle ID to complete maintenance (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
            
        try:
            response = self._post("/completeMaintenance", {"vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Maintenance completed! Vehicle is now available.")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot complete maintenance (vehicle must be in MAINTENANCE state with battery > 20%)")
            else:
                print("\n[ERROR] Error completing maintenance")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def unlock_vehicle(self):
        """Unlock a vehicle from EMERGENCYLOCK state"""
        if not self.view_vehicles_by_state(['EMERGENCYLOCK'], "EMERGENCY LOCKED VEHICLES"):
            return
        
        vehicle_id = input("\nEnter the vehicle ID to unlock (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
            
        try:
            response = self._post("/requestEmUnlock", {"vehicleId": vehicle_id})
            if not response:
                return
            if response.status_code == 200:
                print("\n[OK] Vehicle unlocked successfully!")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot unlock vehicle (must be in EMERGENCYLOCK state with no active rental)")
            else:
                print("\n[ERROR] Error unlocking vehicle")
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
    
    def simulate_theft(self):
        """Simulate theft by moving an idle vehicle"""
        if not self.view_all_vehicles():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to simulate theft (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
        
        print("\n[INFO] Simulating theft: moving vehicle without active rental...")
        
        # Simulate vehicle movement by updating GPS with a significant change
        # This will trigger theft detection if vehicle has no active rental
        response = self._post("/update", {"vehicleId": vehicle_id, "latitude": 51.510, "longitude": -0.130})
        if not response:
            return
        if response.status_code == 200:
            print("\n[OK] Telemetry updated!")
            print("[INFO] If vehicle had no active rental, it should now be in EMERGENCYLOCK")
            input("\nPress Enter to view vehicle status...")
            self.view_all_vehicles()
        else:
            print("\n[ERROR] Error updating telemetry")
    
    def simulate_telemetry(self):
        """Simulate various telemetry scenarios"""
        if not self.view_all_vehicles():
            return
        
        vehicle_id = input("\nEnter the vehicle ID (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
        
        print("\n=== TELEMETRY SIMULATION ===")
        print("1. Low battery (4%)")
        print("2. Overheating (65°C)")
        print("3. Custom values")
        print("0. Cancel")
        
        choice = input("\nYour choice: ")
        
        telemetry = {"vehicleId": vehicle_id}
        
        if choice == "1":
            telemetry["batteryLevel"] = 4
            print("\n[INFO] Simulating critical battery (4%)...")
        elif choice == "2":
            telemetry["temperature"] = 65
            print("\n[INFO] Simulating overheating (65°C)...")
        elif choice == "3":
            try:
                battery = input("Battery level (0-100, Enter to skip): ")
                if battery:
                    telemetry["batteryLevel"] = int(battery)
                
                temp = input("Temperature (°C, Enter to skip): ")
                if temp:
                    telemetry["temperature"] = int(temp)
                
                lat = input("Latitude (Enter to skip): ")
                if lat:
                    telemetry["latitude"] = float(lat)
                    lon = input("Longitude: ")
                    telemetry["longitude"] = float(lon)
            except ValueError:
                print("\n[ERROR] Invalid input")
                return
        else:
            return
        
        response = self._post("/update", telemetry)
        if not response:
            return
        if response.status_code == 200:
            print("\n[OK] Telemetry updated!")
            print("[INFO] Check vehicle status for effects...")
            input("\nPress Enter to view vehicle status...")
            self.view_all_vehicles()
        else:
            print("\n[ERROR] Error updating telemetry")
    
    def simulate_charging(self):
        """Simulate charging a vehicle's battery"""
        if not self.view_all_vehicles():
            return
        
        vehicle_id = input("\nEnter the vehicle ID to charge (0 to cancel): ")
        if vehicle_id == "0":
            return
        
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            print("\n[ERROR] Invalid ID - must be a number")
            return
        
        # Ask for target battery level
        battery_input = input("\nTarget battery level (press Enter for 100%): ").strip()
        if battery_input:
            try:
                battery_level = int(battery_input)
                if battery_level < 0 or battery_level > 100:
                    print("\n[ERROR] Battery level must be between 0 and 100")
                    return
            except ValueError:
                print("\n[ERROR] Invalid battery level")
                return
        else:
            battery_level = 100
        
        print(f"\n[INFO] Simulating charge to {battery_level}%...")
        
        response = self._post("/update", {"vehicleId": vehicle_id, "batteryLevel": battery_level})
        if not response:
            return
        if response.status_code == 200:
            print(f"\n[OK] Battery updated to {battery_level}%!")
            
            # Check if vehicle is in maintenance and battery is sufficient
            if battery_level > 20:
                complete = input("\nVehicle charged. Complete maintenance? (y/n): ").lower()
                if complete == 'y':
                    maint_response = self._post("/completeMaintenance", {"vehicleId": vehicle_id})
                    if maint_response and maint_response.status_code == 200:
                        print("\n[OK] Maintenance completed! Vehicle is now available.")
                    elif maint_response and maint_response.status_code == 422:
                        print("\n[INFO] Vehicle is not in maintenance state")
                    else:
                        print("\n[ERROR] Could not complete maintenance")
            
            input("\nPress Enter to view vehicle status...")
            self.view_all_vehicles()
        else:
            print("\n[ERROR] Error updating battery")
    
    def shutdown_server(self):
        """Shutdown the server gracefully"""
        print("\n[WARNING] This will stop the server and close all connections.")
        confirm = input("Are you sure you want to shutdown the server? (yes/no): ").lower()
        
        if confirm != "yes":
            print("\n[INFO] Shutdown cancelled.")
            return
        
        print("\n[INFO] Sending shutdown request to server...")
        response = self._post("/shutdown")
        if response and response.status_code == 200:
            print("\n[OK] Server shutdown initiated successfully!")
            print("[INFO] Data saved, monitoring stopped.")
            print("[INFO] You can now close the CLI.")
            input("\nPress Enter to exit...")
            import sys
            sys.exit(0)
        elif response:
            print("\n[ERROR] Error shutting down server")
        else:
            print("\n[INFO] Server has shut down (connection closed).")
            input("\nPress Enter to exit...")
            import sys
            sys.exit(0)
    
    def admin_menu(self):
        """Admin menu for vehicle management"""
        while True:
            self.print_header("ADMIN MODE - VEHICLE MANAGEMENT")
            options = [
                "View all vehicles",
                "Assign vehicle to maintenance",
                "Complete maintenance (battery charged)",
                "Unlock vehicle (from EMERGENCYLOCK)",
                "Simulate charging (update battery level)",
                "Simulate theft (move idle vehicle)",
                "Simulate telemetry (battery/temp/GPS)",
                "Shutdown server (graceful exit)"
            ]
            self.print_menu(options)
            
            choice = self.get_choice(len(options))
            
            if choice == 0:
                break
            elif choice == 1:
                self.view_all_vehicles()
            elif choice == 2:
                self.assign_maintenance()
            elif choice == 3:
                self.complete_maintenance()
            elif choice == 4:
                self.unlock_vehicle()
            elif choice == 5:
                self.simulate_charging()
            elif choice == 6:
                self.simulate_theft()
            elif choice == 7:
                self.simulate_telemetry()
            elif choice == 8:
                self.shutdown_server()
                return  # Exit admin menu after shutdown
    
    def run(self):
        """Launch the CLI application"""
        print("\n" + "="*60)
        print("          SMARTMOVE - CLI Client")
        print("   Shared Vehicle Rental System")
        print("="*60)
        
        while True:
            if not self.current_user:
                if not self.login():
                    print("\nGoodbye!")
                    break
            
            if self.current_user:
                self.main_menu()


def main():
    """Main entry point"""
    client = SmartMoveClient()
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n\nInterrupt detected. Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")


if __name__ == "__main__":
    main()
