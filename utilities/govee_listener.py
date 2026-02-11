import udi_interface
import socket
import struct
import json
import threading

LOGGER = udi_interface.LOGGER


class GoveeListener:
    """Listens for UDP/multicast responses and calls a callback with (response, address).

    Example:
        listener = GoveeListener(multicastGroup, receivePort)
        listener.start(callback=cb)
        ...
        listener.stop()
    """
    def __init__(self, multicastGroup='239.255.255.250', receivePort=4002, timeout=1.0):
        self.multicastGroup = multicastGroup
        self.receivePort = receivePort
        self.timeout = timeout

        self.sock = None
        self.running = False
        self.thread = None

    def _setup_socket(self):
        if self.sock:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.receivePort))
        mreq = struct.pack('4sL', socket.inet_aton(self.multicastGroup), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.settimeout(self.timeout)

    def _listen_loop(self, callback):
        LOGGER.debug(f"GoveeListener listening on port {self.receivePort}")
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                try:
                    payload = json.loads(data.decode('utf-8'))
                except Exception as e:
                    LOGGER.debug(f"Failed to decode JSON from {addr}: {e}")
                    continue
                try:
                    callback(payload, addr)
                except Exception as e:
                    LOGGER.debug(f"Listener callback error: {e}")
            except socket.timeout:
                continue
            except Exception as e:
                LOGGER.debug(f"GoveeListener receive error: {e}")

    def start(self, callback):
        self._setup_socket()
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, args=(callback,))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
