#!/usr/bin/env python3
import requests
import time
from threading import Thread, Event
from queue import Queue
from urllib.parse import urljoin

class GameSimulator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.event_queue = Queue()
        self.stop_event = Event()
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "Content-Type": "application/json"
        })
        
    def check_connection(self):
        """Verify we can connect to the server"""
        print("🔍 Checking server connection...")
        try:
            resp = self.session.get(
                urljoin(self.base_url, "/events"), 
                timeout=5,
                stream=True
            )
            if resp.status_code == 200:
                print("✅ Server connection successful")
                resp.close()
                return True
            print(f"⚠️ Server returned status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {str(e)}")
        return False

    def event_listener(self):
        """Listen for game events"""
        url = urljoin(self.base_url, "/events")
        print(f"👂 Connecting to event stream at {url}...")
        
        try:
            with self.session.get(url, stream=True, timeout=5) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line and not self.stop_event.is_set():
                        decoded = line.decode().strip()
                        if decoded.startswith("data:"):
                            self.event_queue.put(decoded[5:].strip())
        except Exception as e:
            self.event_queue.put(f"Event listener error: {str(e)}")

    def create_account(self, userid):
        """Create account with proper headers and empty body"""
        url = urljoin(self.base_url, f"account/{userid}")
        try:
            response = self.session.post(url, data='')
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "details": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def create_character(self, userid, charname):
        """Create character with query params and empty body"""
        url = urljoin(self.base_url, "character")
        try:
            response = self.session.post(
                url,
                params={"userid": userid, "charname": charname},
                data=''
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "details": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def api_call(self, endpoint, method="POST", params=None, data=''):
        """Generic API call with error handling"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                data=data
            )
            if response.status_code in (200, 201):
                return response.json()
            return {"error": f"HTTP {response.status_code}", "details": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def print_response(self, action, response):
        """Print formatted response"""
        if "error" in response:
            print(f"❌ {action} failed: {response['error']}")
            if "details" in response:
                print(f"   Details: {response['details']}")
        else:
            print(f"✅ {action} succeeded")
            if "message" in response:
                print(f"   Message: {response['message']}")
            if "charid" in response:
                print(f"   Character ID: {response['charid']}")

    def run_simulation(self):
        """Run the full simulation"""
        if not self.check_connection():
            return

        # Start event listener
        listener = Thread(target=self.event_listener, daemon=True)
        listener.start()

        try:
            # Create accounts
            print("\n🟡 Creating accounts...")
            p1 = self.create_account("moriartie1")
            self.print_response("Create moriartie1", p1)
            
            p2 = self.create_account("moriartie2")
            self.print_response("Create moriartie2", p2)

            # Create characters
            print("\n🟡 Creating characters...")
            char1 = self.create_character("moriartie1", "warrior1")
            self.print_response("Create warrior1", char1)
            
            char2 = self.create_character("moriartie2", "mage1")
            self.print_response("Create mage1", char2)

            if not char1.get("charid") or not char2.get("charid"):
                print("❌ Need valid character IDs to continue")
                return

            # Login characters
            print("\n🟡 Logging in characters...")
            login1 = self.api_call(f"login/{char1['charid']}", "POST", data='')
            self.print_response(f"Login character {char1['charid']}", login1)
            
            login2 = self.api_call(f"login/{char2['charid']}", "POST", data='')
            self.print_response(f"Login character {char2['charid']}", login2)

            # Gameplay simulation
            print("\n🟢 Starting gameplay actions...")
            
            # Movement
            print("\n🔵 Testing movement...")
            for i in range(1, 4):
                move = self.api_call(
                    f"move/{char1['charid']}",
                    "POST",
                    params={"dx": i, "dy": i},
                    data=''
                )
                self.print_response(f"Move warrior1 {i}", move)
                time.sleep(0.6)

            # Combat
            print("\n🔴 Testing combat...")
            for i in range(3):
                attack = self.api_call(
                    f"attack/{char1['charid']}",
                    "POST",
                    params={"target_id": char2['charid']},
                    data=''
                )
                self.print_response(f"Warrior1 attacks Mage1", attack)
                time.sleep(0.6)

            # Interactions
            print("\n🟢 Testing interactions...")
            for obj_id in [2001, 2002, 2003]:
                interact = self.api_call(
                    f"interact/{char1['charid']}",
                    "POST",
                    params={"object_id": obj_id},
                    data=''
                )
                self.print_response(f"Interact with object {obj_id}", interact)
                time.sleep(0.5)

            # Print captured events
            print("\n📜 Event Log:")
            while not self.event_queue.empty():
                print(self.event_queue.get())

        except KeyboardInterrupt:
            print("\n🛑 Simulation interrupted")
        finally:
            self.stop_event.set()
            listener.join(timeout=1)
            self.session.close()
            print("✅ Simulation complete")

if __name__ == "__main__":
    print("🎮 Starting game simulation")
    simulator = GameSimulator()
    simulator.run_simulation()