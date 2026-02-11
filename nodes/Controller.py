import udi_interface

from .GoveeDevice import GoveeDevice
from utilities import GoveeClient
from utilities.timed_govee_listener import TimedGoveeListener

LOGGER = udi_interface.LOGGER
LOG_HANDLER = udi_interface.LOG_HANDLER
Custom = udi_interface.Custom
ISY = udi_interface.ISY

LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class Controller(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.hb = 0

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
        self.TypedParameters = Custom(polyglot, 'customtypedparams')
        self.TypedData = Custom(polyglot, 'customtypeddata')

        self.client = GoveeClient(reuse_socket=True)
        self.listener = None

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDPARAMS, self.typedParameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDDATA, self.typedDataHandler)
        self.poly.subscribe(self.poly.POLL, self.poll)

        self.discovery = None

        self.poly.addNode(self)

        self.poly.ready()


    def start(self):
        self.poly.updateProfile()

        self.poly.setCustomParamsDoc()

        self.heartbeat(0)

        self.scanForDevices()


    def queryDevices(self, command=None):
        """Query Govee devices on the network (short poll)"""
        timeout = 5
        if self.listener and hasattr(self.listener, 'is_active') and self.listener.is_active:
            self.listener.extend(timeout)
        else:
            self.listener = TimedGoveeListener(timeout=timeout, callback=self.processDevice)
            self.listener.start()
        try:
            self.client.send_multicast({
                "msg": {
                    "cmd": "devStatus",
                    "data": {}
                }
            }, multicast_group='239.255.255.250', port=4001, ttl=2)
        except Exception as e:
            LOGGER.debug(f"Failed to send discovery packet: {e}")


    def scanForDevices(self, command=None):
        """Discover Govee devices on the network (long poll)"""
        timeout = 10
        if self.listener and hasattr(self.listener, 'is_active') and self.listener.is_active:
            self.listener.extend(timeout)
        else:
            self.listener = TimedGoveeListener(timeout=timeout, callback=self.processDevice)
            self.listener.start()
        try:
            self.client.send_multicast({
                "msg": {
                    "cmd": "scan",
                    "data": {"account_topic": "reserve"}
                }
            }, multicast_group='239.255.255.250', port=4001, ttl=2)
        except Exception as e:
            LOGGER.debug(f"Failed to send discovery packet: {e}")


    def processDevice(self, response, address):   
        """Callback to handle discovered devices"""
        LOGGER.debug(f"Found device at {address[0]}: {response}")
        
        msg = response.get('msg', {})
        cmd = msg.get('cmd', '')
        data = msg.get('data', {})

        if(cmd == 'scan'):
            device_id = data.get('device', 'unknown').replace(':', '').lower()
            child_address = device_id[:14]

            if self.poly.getNode(child_address):
                """Update device info if it already exists"""
                node = self.poly.getNode(child_address)
                node.ipAddress = data.get('ip', 'unknown')
                node.sku = data.get('sku', 'unknown')
                LOGGER.info(f"Updated existing device with address: {child_address}")
                return

            LOGGER.info(f"Adding device with address: {child_address}, primary: {self.address}")

            device = GoveeDevice(
                self.poly, 
                self.address,  # primary (controller address)
                child_address,  # valid child address (MAC without colons)
                data.get('device', 'unknown'),  # name
                data.get('device', 'unknown'),
                data.get('ip', 'unknown'),
                data.get('sku', 'unknown'),
                send_fn=self.send_request_to_device,
            )
            self.poly.addNode(device)
        elif(cmd == 'devStatus'):
            nodes = self.poly.getNodes()

            for address, node in nodes.items():
                if hasattr(node, 'ipAddress') and node.ipAddress == address[0]:
                    LOGGER.debug(f"Updating status for device at {address[0]}: {data}")
                    node.setDriver('ST', data.get('onOff', 0))
                    node.setDriver('GV0', data.get('brightness', 0))
                    node.setDriver('GV1', data.get('colorTemInKelvin', 0))
                    return
        else:
            LOGGER.debug(f"Unknown command in response: {cmd}")


    def parameterHandler(self, params):
        self.Parameters.load(params)
        LOGGER.debug('Loading parameters now')


    def typedParameterHandler(self, params):
        self.TypedParameters.load(params)
        LOGGER.debug('Loading typed parameters now')
        LOGGER.debug(params)


    def typedDataHandler(self, params):
        self.TypedData.load(params)
        LOGGER.debug('Loading typed data now')
        LOGGER.debug(params)


    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))


    def poll(self, flag):
        if 'longPoll' in flag:
            LOGGER.debug('longPoll (controller)')
            self.heartbeat()
            self.scanForDevices()
        else:
            LOGGER.debug('shortPoll (controller)')
            self.queryDevices()


    # TODO: On query, request device updates
    def query(self,command=None):
        nodes = self.poly.getNodes()
        for node in nodes:
            nodes[node].reportDrivers()


    def discover(self, *args, **kwargs):
        self.poly.addNode(GoveeDevice(self.poly, self.address, 'templateaddr', 'Template Node Name', '00:00:00:00:00:00', '127.0.0.1', 'template', send_fn=self.send_request_to_device))


    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')
        try:
            self.client.close()
        except Exception:
            pass


    def stop(self):
        LOGGER.debug('NodeServer stopped.')
        try:
            self.client.close()
        except Exception:
            pass
        # Stop listener if running
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

    def send_request_to_device(self, ip, payload, port=None, expect_response=False):
        try:
            return self.client.send_request(ip, payload, port=port, expect_response=expect_response)
        except Exception as e:
            LOGGER.debug(f"Error sending request to {ip}: {e}")
            return None


    def heartbeat(self,init=False):
        LOGGER.debug('heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
    }
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
    ]