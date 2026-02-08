#!/usr/bin/env python
import udi_interface
import sys

LOGGER = udi_interface.LOGGER

""" Grab My Controller Node (optional) """
from nodes import Controller

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([Controller])

        polyglot.start()

        control = Controller(polyglot, 'controller', 'controller', 'Govee WLAN Controller')

        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")

        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)