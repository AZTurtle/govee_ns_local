import threading
import time
from .govee_listener import GoveeListener

class TimedGoveeListener:
    """
    Wraps GoveeListener with a timeout that can be extended.
    If timeout expires, listener stops itself.
    """
    def __init__(self, multicastGroup='239.255.255.250', receivePort=4002, timeout=5, callback=None):
        self.listener = GoveeListener(multicastGroup, receivePort)
        self.timeout = timeout
        self.callback = callback
        self._timer_thread = None
        self._timer_lock = threading.Lock()
        self._active = False
        self._expire_time = None

    def start(self):
        self.listener.start(self.callback)
        self._active = True
        self.extend(self.timeout)
        self._timer_thread = threading.Thread(target=self._timer_loop)
        self._timer_thread.daemon = True
        self._timer_thread.start()

    def extend(self, seconds):
        with self._timer_lock:
            now = time.time()
            if self._expire_time is None or self._expire_time < now:
                self._expire_time = now + seconds
            else:
                self._expire_time += seconds

    def _timer_loop(self):
        while self._active:
            with self._timer_lock:
                expire = self._expire_time
            if expire is not None and time.time() >= expire:
                self.stop()
                break
            time.sleep(0.5)

    def stop(self):
        self._active = False
        self.listener.stop()
        self._expire_time = None

    @property
    def is_active(self):
        return self._active

