# boot.py -- run on boot-up
import pycom
from lib.indicators import Indicators
import _thread
from machine import SD 
import os

pycom.wifi_on_boot(False)

ind = Indicators()
_thread.start_new_thread(ind.start,())


sd = SD()
os.mount(sd, '/sd')
# check the content
os.listdir('/sd')

# try some standard file operations
f = open('/sd/test.txt', 'w')
f.write('Testing SD card write operations')
f.close()
f = open('/sd/test.txt', 'r')
aaa = f.read()
print("Test SD: " + str(aaa))
f.close()
pycom.pybytes_on_boot(False)
pycom.wdt_on_boot(True) 
pycom.wdt_on_boot_timeout(720000)
pycom.heartbeat(False)

