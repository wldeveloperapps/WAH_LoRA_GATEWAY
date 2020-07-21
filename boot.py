# boot.py -- run on boot-up
import pycom

pycom.wifi_on_boot(False)
pycom.pybytes_on_boot(False)
pycom.wdt_on_boot(True) 
pycom.wdt_on_boot_timeout(300000)
pycom.heartbeat(False)

