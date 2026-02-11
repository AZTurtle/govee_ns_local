import socket
import json
import threading
import udi_interface

LOGGER = udi_interface.LOGGER


class GoveeClient:
    """Simple UDP client for sending requests to a single device IP.

    Usage:
      client = GoveeClient(timeout=2.0, reuse_socket=True)
      client.send_request('192.168.1.50', {'msg': {...}}, port=4003)
      client.close()
    """

    def __init__(self, port: int = 4003, reuse_socket: bool = True, timeout: float = 2.0):
        self.port = port
        self.timeout = timeout
        self.reuse = reuse_socket
        self.sock = None
        self._lock = threading.Lock()

        if self.reuse:
            self._ensure_socket()

    def _ensure_socket(self):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(self.timeout)

    def send_request(self, ip: str, payload: dict, port: int | None = None, expect_response: bool = False):
        """Send a JSON payload (dict) to `ip:port` via UDP.

        If `expect_response` is True, attempts to receive a response from the same socket.
        Returns parsed JSON response or None on timeout/no-response.
        """
        target_port = port or self.port
        message = json.dumps(payload).encode('utf-8')

        if expect_response:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tsock:
                tsock.settimeout(self.timeout)
                try:
                    tsock.sendto(message, (ip, target_port))
                except Exception as e:
                    LOGGER.debug(f"Error sending (expect_response) to {ip}:{target_port}: {e}")
                    raise
                try:
                    data, addr = tsock.recvfrom(4096)
                    return json.loads(data.decode('utf-8'))
                except socket.timeout:
                    return None

        # No response expected: use reusable socket if configured.
        if self.reuse:
            self._ensure_socket()
            with self._lock:
                try:
                    self.sock.sendto(message, (ip, target_port))
                except Exception as e:
                    LOGGER.debug(f"Error sending to {ip}:{target_port}: {e}")
                    raise
            return None
        else:
            # Use a temporary socket for this request (no response expected)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tsock:
                tsock.settimeout(self.timeout)
                tsock.sendto(message, (ip, target_port))
            return None

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_multicast(self, payload: dict, multicast_group: str = '239.255.255.250', port: int = 4001, ttl: int = 2):
        """Send a JSON payload to a multicast group/port.

        This method will set the multicast TTL appropriately. It uses the
        client's reusable socket if `reuse=True`, otherwise creates a
        short-lived socket for the multicast send.
        """
        message = json.dumps(payload).encode('utf-8')

        if self.reuse:
            self._ensure_socket()
            with self._lock:
                try:
                    # set multicast TTL on the socket for this send
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
                except Exception:
                    # not fatal; continue to send
                    pass
                try:
                    self.sock.sendto(message, (multicast_group, port))
                except Exception as e:
                    LOGGER.debug(f"Error sending multicast to {multicast_group}:{port}: {e}")
                    raise
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as msock:
                try:
                    msock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
                except Exception:
                    pass
                msock.sendto(message, (multicast_group, port))


def send_to_device(ip: str, payload: dict, port: int = 4003, timeout: float = 2.0):
    """Convenience function to send a single request and get optional response.

    This creates a short-lived socket (no fd reuse required).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        s.sendto(json.dumps(payload).encode('utf-8'), (ip, port))
        try:
            data, addr = s.recvfrom(4096)
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            return None
