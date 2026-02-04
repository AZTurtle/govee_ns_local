
import udi_interface
import sys
import time
import urllib3

LOGGER = udi_interface.LOGGER

class GoveeDevice(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(GoveeDevice, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.lpfx = '%s:%s' % (address,name)

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

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

    def poll(self, polltype):
        if 'longPoll' in polltype:
            LOGGER.debug('longPoll (node)')
        else:
            LOGGER.debug('shortPoll (node)')
            if int(self.getDriver('ST')) == 1:
                self.setDriver('ST',0)
            else:
                self.setDriver('ST',1)
            LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))

    def cmd_on(self, command):
        self.setDriver('ST', 1)

    def cmd_off(self, command):
        self.setDriver('ST', 0)

    def cmd_ping(self,command):
        LOGGER.debug("cmd_ping:")
        r = self.http.request('GET',"google.com")
        LOGGER.debug("cmd_ping: r={}".format(r))


    def query(self,command=None):
        self.reportDrivers()

    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]

    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    id = 'templatenodeid'

    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                    'PING': cmd_ping
                }