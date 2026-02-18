"""
SmartMove CLI Client - Text interface to interact with the server
"""
import requests
import json
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
        
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.current_user = user_data['userId']
                self.current_username = user_data['username']
                print(f"\n[OK] Logged in as {self.current_username}")
                return True
            elif response.status_code == 401:
                print("\n[ERROR] Invalid username or password")
                return False
            else:
                print("\n[ERROR] Error during login")
                return False
        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Cannot connect to server. Is it running?")
            return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
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
        
        try:
            response = requests.post(
                f"{self.base_url}/registerUser",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"\n[OK] Account created successfully!")
                # Now login with the new credentials
                login_response = requests.post(
                    f"{self.base_url}/login",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if login_response.status_code == 200:
                    user_data = login_response.json()
                    self.current_user = user_data['userId']
                    self.current_username = username
                    print(f"[OK] Logged in as {self.current_username}")
                    return True
                else:
                    print("[WARNING] Account created. Please login manually.")
                    return False
            elif response.status_code == 422:
                print(f"\n[ERROR] This username already exists")
                return False
            else:
                print(f"\n[ERROR] Error creating account")
                return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False
    
    def view_available_vehicles(self) -> bool:
        """Display available vehicles. Returns True if vehicles are available."""
        try:
            response = requests.get(f"{self.base_url}/vehicles/available", timeout=5)
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
            response = requests.get(f"{self.base_url}/rentals/{self.current_username}", timeout=5)
            if response.status_code == 200:
                rentals = response.json()
                if not rentals:
                    print("\nNo active rentals")
                    return False
                
                self.print_header("MY ACTIVE RENTALS")
                for rental in rentals:
                    status_icon = "[RESERVED]" if rental['status'] == "RESERVED" else "[ACTIVE]"
                    print(f"\n  {status_icon} Vehicle ID: {rental['vehicleId']}")
                    print(f"  Type: {rental['vehicleType'].upper()}")
                    print(f"  Status: {rental['status']}")
                    if rental.get('scheduledStartTime'):
                        print(f"  Scheduled start: {rental['scheduledStartTime']}")
                    if rental.get('actualStartTime'):
                        print(f"  Started on: {rental['actualStartTime']}")
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
            response = requests.post(
                f"{self.base_url}/reserveVehicle",
                json={
                    "userId": self.current_user,
                    "vehicleId": vehicle_id
                },
                timeout=5
            )
            
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
            response = requests.post(
                f"{self.base_url}/activateVehicle",
                json={
                    "username": self.current_username,
                    "vehicleId": vehicle_id
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print("\n[OK] Rental activated! Have a great ride!")
            elif response.status_code == 422:
                print("\n[ERROR] Cannot activate this rental")
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
            response = requests.post(
                f"{self.base_url}/returnVehicle",
                json={
                    "username": self.current_username,
                    "vehicleId": vehicle_id
                },
                timeout=5
            )
            
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
            response = requests.post(
                f"{self.base_url}/cancelRental",
                json={
                    "username": self.current_username,
                    "vehicleId": vehicle_id
                },
                timeout=5
            )
            
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
                "View my active rentals"
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
            
            input("\nPress Enter to continue...")
    
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
