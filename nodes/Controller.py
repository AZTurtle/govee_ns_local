import udi_interface

from nodes import GoveeDevice
from .GoveeDiscovery import GoveeDiscovery

LOGGER = udi_interface.LOGGER
LOG_HANDLER = udi_interface.LOG_HANDLER
Custom = udi_interface.Custom
ISY = udi_interface.ISY

LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class Controller(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'Template Controller'  # override what was passed in
        self.hb = 0

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
        self.TypedParameters = Custom(polyglot, 'customtypedparams')
        self.TypedData = Custom(polyglot, 'customtypeddata')

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDPARAMS, self.typedParameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDDATA, self.typedDataHandler)
        self.poly.subscribe(self.poly.POLL, self.poll)

        self.discovery = None

        self.poly.ready()

        self.poly.addNode(self)


    def start(self):
        self.poly.updateProfile()

        self.poly.setCustomParamsDoc()

        self.heartbeat(0)

        self.scanForDevices()


    def scanForDevices(self, command=None):
        """Discover Govee devices on the network"""
        if self.discovery:
            self.discovery.stopDiscovery()
            
        self.discovery = GoveeDiscovery()
        self.discovery.startDiscovery(callback=self.processDiscoveredDevice)


    def processDiscoveredDevice(self, response, address):   
        """Callback to handle discovered devices"""
        LOGGER.debug(f"Found device at {address[0]}: {response}")
        
        msg = response.get('msg', {})
        data = msg.get('data', {})

        LOGGER.debug(f"Processing device data: {data}")

        device = GoveeDevice(
            self.poly, 
            self.address, 
            f"child_{data.get('device', 'unknown')}",
            data.get('device', 'unknown'),
            data.get('device', 'unknown'),
            data.get('ip', 'unknown'),
            data.get('sku', 'unknown'),
        )
        self.poly.addNode(device)


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
        else:
            LOGGER.debug('shortPoll (controller)')


    # TODO: On query, request device updates
    def query(self,command=None):
        nodes = self.poly.getNodes()
        for node in nodes:
            nodes[node].reportDrivers()


    def discover(self, *args, **kwargs):
        self.poly.addNode(GoveeDevice(self.poly, self.address, 'templateaddr', 'Template Node Name'))


    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')


    def stop(self):
        LOGGER.debug('NodeServer stopped.')


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

    """
    Optional.
    Since the controller is a node in ISY, it will actual show up as a node.
    Thus it needs to know the drivers and what id it will use. The controller
    should report the node server status and have any commands that are
    needed to control operation of the node server.

    Typically, node servers will use the 'ST' driver to report the node server
    status and it a best pactice to do this unless you have a very good
    reason not to.

    The id must match the nodeDef id="controller" in the nodedefs.xml
    """
    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
    }
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
    ]