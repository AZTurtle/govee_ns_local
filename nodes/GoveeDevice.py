import udi_interface
import sys
import time
import urllib3

LOGGER = udi_interface.LOGGER

class GoveeDevice(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, macAddress, ipAddress, sku):
        super(GoveeDevice, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.lpfx = '%s:%s' % (address,name)

        self.macAddress = macAddress
        self.ipAddress = ipAddress
        self.sku = sku

        self.poly.subscribe(self.poly.START, self.start, address)

    def start(self):
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.setDriver('ST', 1)
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.setDriver('ST', 0)
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.setDriver('ST', 1)
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.setDriver('ST', 0)
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.http = urllib3.PoolManager()

    def setOn(self, command=None):
        """Turn device on"""
        LOGGER.info(f'DON received for {self.address}')
        # Send command to Govee device here
        self.setDriver('ST', 1)
        
    def setOff(self, command=None):
        """Turn device off"""
        LOGGER.info(f'DOF received for {self.address}')
        # Send command to Govee device here
        self.setDriver('ST', 0)
        
    def setBrightness(self, command):
        """Set brightness level"""
        value = int(command.get('value'))
        LOGGER.info(f'SET_BRI to {value} for {self.address}')
        # Send brightness command to Govee device here
        self.setDriver('GV0', value)
        
    def setColorTemp(self, command):
        """Set color temperature"""
        value = int(command.get('value'))
        LOGGER.info(f'SET_CLITEMP to {value}K for {self.address}')
        # Send color temp command to Govee device here
        self.setDriver('GV1', value)
    
    def query(self, command=None):
        """Query device for current status"""
        LOGGER.info(f'Query received for {self.address}')
        # Poll device for current status here
        self.reportDrivers()
    
    id = 'govee_device'
    
    commands = {
        'DON': setOn,
        'DOF': setOff,
        'SET_BRI': setBrightness,
        'SET_CLITEMP': setColorTemp,
        'QUERY': query,
    }
    
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},      # Status (on/off)
        {'driver': 'GV0', 'value': 0, 'uom': 51},    # Brightness (0-100%)
        {'driver': 'GV1', 'value': 2700, 'uom': 26}, # Color Temperature (Kelvin)
        {'driver': 'GV2', 'value': 0, 'uom': 2},     # Active status
    ]