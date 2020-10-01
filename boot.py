# boot.py -- run on boot-up
import pycom
# import utime
# from network import WLAN

pycom.wifi_on_boot(False)

# # configure the WLAN subsystem in station mode (the default is AP)
# wlan = WLAN(mode=WLAN.STA)
# # go for fixed IP settings (IP, Subnet, Gateway, DNS)
# # wlan.ifconfig(config=('192.168.0.107', '255.255.255.0', '192.168.0.1', '192.168.0.1'))
# # wlan.scan()     # scan for available networks
# wlan.connect(ssid='SackDaGo', auth=(WLAN.WPA2, 'sackdago'))
# max_num = 30
# flag_fail = False
# while not wlan.isconnected():
#     if max_num == 0:
#         wlan.deinit()
#         flag_fail = True
#         break;
#     max_num = max_num - 1
#     utime.sleep(1)
#     pass

# if flag_fail == False:
#     print(wlan.ifconfig())

from machine import SD
import os
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
pycom.wdt_on_boot_timeout(360000)
pycom.heartbeat(False)

