import udi_interface
import sys
import time
import urllib3

LOGGER = udi_interface.LOGGER

class GoveeDevice(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, deviceId, ipAddress, sku, send_fn=None):
        super(GoveeDevice, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot

        self.deviceId = deviceId
        self.ipAddress = ipAddress
        self.sku = sku
        self._send = send_fn

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def start(self):
        pass

    def poll(self, polltype):
        if 'longPoll' in polltype:
            LOGGER.debug('longPoll (node)')
        else:
            LOGGER.debug('shortPoll (node)')
            if int(self.getDriver('ST')) == 1:
                self.setDriver('ST',0)
            else:
                self.setDriver('ST',1)

    def setOn(self, command=None):
        """Turn device on"""
        LOGGER.info(f'DON received for {self.address}')
        payload = {"msg": {"cmd": "turn", "data": {"value": 1}}}
        if self._send and self.ipAddress:
            try:
                self._send(self.ipAddress, payload, expect_response=False)
            except Exception as e:
                LOGGER.debug(f"Failed to send ON to {self.ipAddress}: {e}")
        
    def setOff(self, command=None):
        """Turn device off"""
        LOGGER.info(f'DOF received for {self.address}')
        payload = {"msg": {"cmd": "turn", "data": {"value": 0}}}
        if self._send and self.ipAddress:
            try:
                self._send(self.ipAddress, payload, expect_response=False)
            except Exception as e:
                LOGGER.debug(f"Failed to send OFF to {self.ipAddress}: {e}")
        
    def setBrightness(self, command):
        """Set brightness level"""
        value = int(command.get('value'))
        LOGGER.info(f'SET_BRI to {value} for {self.address}')
        payload = {"msg": {"cmd": "brightness", "data": {"value": value}}}
        if self._send and self.ipAddress:
            try:
                self._send(self.ipAddress, payload, expect_response=False)
            except Exception as e:
                LOGGER.debug(f"Failed to send brightness to {self.ipAddress}: {e}")
        
    def setColorTemp(self, command):
        """Set color temperature"""
        value = int(command.get('value'))
        LOGGER.info(f'SET_CLITEMP to {value}K for {self.address}')
        payload = {"msg": {"cmd": "set_color_temp", "data": {"mired": value}}}
        if self._send and self.ipAddress:
            try:
                self._send(self.ipAddress, payload, expect_response=False)
            except Exception as e:
                LOGGER.debug(f"Failed to send color temp to {self.ipAddress}: {e}")
    
    id = 'govee_device'
    
    commands = {
        'DON': setOn,
        'DOF': setOff,
        'SET_BRI': setBrightness,
        'SET_CLITEMP': setColorTemp,
    }
    
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},      # Status (on/off)
        {'driver': 'GV0', 'value': 0, 'uom': 51},    # Brightness (0-100%)
        {'driver': 'GV1', 'value': 2700, 'uom': 26}, # Color Temperature (Kelvin)
        {'driver': 'GV2', 'value': 0, 'uom': 2},     # Active status
    ]