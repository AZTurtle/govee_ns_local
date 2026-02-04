import socket
import struct
import json
import threading

class GoveeDiscovery:
    def __init__(self, multicast_group='239.255.255.250', send_port=4001, receive_port=4002):
        self.multicast_group = multicast_group
        self.send_port = send_port
        self.receive_port = receive_port
        self.send_sock = None
        self.receive_sock = None
        self.running = False
        self.listener_thread = None
        
    def setup_sockets(self):
        """Set up separate sockets for sending and receiving"""
        # Create sending socket
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        self.receive_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.receive_sock.bind(('', self.receive_port))
        
        mreq = struct.pack('4sL', socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        self.receive_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        self.receive_sock.settimeout(1.0)
        
    def send_discovery(self):
        """Send discovery request to multicast group"""
        discovery_msg = {
            "msg": {
                "cmd": "scan",
                "data": {
                    "account_topic": "reserve"
                }
            }
        }
        
        message = json.dumps(discovery_msg).encode('utf-8')
        self.send_sock.sendto(message, (self.multicast_group, self.send_port))
        print(f"Sent discovery request to {self.multicast_group}:{self.send_port}")
        
    def listen_for_responses(self, callback=None):
        """Listen for responses from devices on receive port"""
        print(f"Listening for responses on port {self.receive_port}...")
        while self.running:
            try:
                data, address = self.receive_sock.recvfrom(1024)
                response = json.loads(data.decode('utf-8'))
                print(f"Received response from {address}: {response}")
                
                if callback:
                    callback(response, address)
                    
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {address}: {e}")
            except Exception as e:
                print(f"Error receiving data: {e}")
                
    def start_discovery(self, callback=None):
        """Start discovery process"""
        self.setup_sockets()
        self.running = True
        
        # Start listener thread
        self.listener_thread = threading.Thread(target=self.listen_for_responses, args=(callback,))
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
        # Send discovery request
        self.send_discovery()
        
    def send_periodic_discovery(self, interval=5):
        """Send discovery requests periodically"""
        while self.running:
            self.send_discovery()
            import time
            time.sleep(interval)
        
    def stop_discovery(self):
        """Stop discovery and clean up"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        if self.send_sock:
            self.send_sock.close()
        if self.receive_sock:
            self.receive_sock.close()