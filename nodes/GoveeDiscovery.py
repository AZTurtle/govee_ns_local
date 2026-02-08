import udi_interface

import socket
import struct
import json
import threading

LOGGER = udi_interface.LOGGER

class GoveeDiscovery:
    def __init__(self, multicastGroup='239.255.255.250', requestPort=4001, receivePort=4002):
        self.multicastGroup = multicastGroup
        self.requestPort = requestPort
        self.receivePort = receivePort
        self.requestSock = None
        self.receiveSock = None
        self.running = False
        self.listenerThread = None
        
    def setupSockets(self):
        """Set up separate sockets for sending and receiving"""
        # Create sending socket
        self.requestSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.requestSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        # Create receiving socket
        self.receiveSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.receiveSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.receiveSock.bind(('', self.receivePort))
        
        mreq = struct.pack('4sL', socket.inet_aton(self.multicastGroup), socket.INADDR_ANY)
        self.receiveSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        self.receiveSock.settimeout(1.0)
        
    def sendDiscovery(self):
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
        self.requestSock.sendto(message, (self.multicastGroup, self.requestPort))
        LOGGER.debug(f"Sent discovery request to {self.multicastGroup}:{self.requestPort}")
        
    def listenForResponses(self, callback=None):
        """Listen for responses from devices on receive port"""
        LOGGER.debug(f"Listening for responses on port {self.receivePort}...")
        while self.running:
            try:
                data, address = self.receiveSock.recvfrom(1024)
                response = json.loads(data.decode('utf-8'))
                LOGGER.debug(f"Received response from {address}: {response}")

                if callback:
                    callback(response, address)
                    
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                LOGGER.debug(f"Error decoding JSON from {address}: {e}")
            except Exception as e:
                LOGGER.debug(f"Error receiving data: {e}")
                
    def startDiscovery(self, callback=None):
        """Start discovery process"""
        self.setupSockets()
        self.running = True
        
        # Start listener thread
        self.listenerThread = threading.Thread(target=self.listenForResponses, args=(callback,))
        self.listenerThread.daemon = True
        self.listenerThread.start()
        
        # Send discovery request
        self.sendDiscovery()
        
    def sendPeriodicDiscovery(self, interval=5):
        """Send discovery requests periodically"""
        while self.running:
            self.sendDiscovery()
            import time
            time.sleep(interval)
        
    def stopDiscovery(self):
        """Stop discovery and clean up"""
        self.running = False
        if self.listenerThread:
            self.listenerThread.join(timeout=2)
        if self.requestSock:
            self.requestSock.close()
        if self.receiveSock:
            self.receiveSock.close()