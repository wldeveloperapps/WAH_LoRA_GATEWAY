from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
import time
import os
import uos
import ujson
import utime
import pycom 
import ubinascii
import tools
import globalVars
import sys
from uio import StringIO
s = StringIO()

def WhiteListGetDevices():
    try:
        devices_whitelist = []
        f = open('/sd/whitelist.csv', 'r')
        strFile = f.read()
        print("Step 0 - Getting Whitelist, content: " + strFile)
        for dd in strFile.replace('"','').split('\n'):
            if len(dd.split(',')) >= 2:
                devices_whitelist.append(dd.split(',')[0])
                # devices_whitelist.append(DeviceBuzzer(dd.split(',')[0],int(dd.split(',')[1])))
        f.close()
        #print("Whitelist already read")
        return 1, devices_whitelist
    except BaseException as e:
        err = sys.print_exception(e, s)
        print("Step 0 - Error reading SD: " + str(s.getvalue()))
        return 0, []
        

def WhiteListNewDevice(devString):
    try:
        print("##### Whitelist new device ")
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        print("##### Creating registers in whitelist: " + str(listDevices))
        f = open('/sd/whitelist.csv', 'r')
        white_lines = f.readlines()
        f.close()
        lstDummy = []
        with open('/sd/whitelist.csv', 'w') as out:
            for dev in listDevices:
                exists = False
                for wht in white_lines:
                    if dev in wht.split(',')[0]:
                        exists = True
                        break
                if exists == False:
                    white_lines.append(str(str(dev) + "," + str(int(utime.time()))+ "\r\n"))

            for ln in white_lines:
                out.write(ln)
                lstDummy.append(ln.split(',')[0])

            globalVars.devices_whitelist = lstDummy
        tools.debug("New whitelist inserted: " + str(globalVars.devices_whitelist),'vv')
    except Exception as e:
        print("##### - Error writing new device in whitelist: " + str(e))  

def WhiteListDeleteDevices():
    try:
        print("##### Deleting devices from Whitelist")
        f = open('/sd/whitelist.csv', 'w')
        f.close()
        globalVars.devices_whitelist = []
    except Exception as e:
        print("##### - Error cleaning whitelist: " + str(e))
        return 6, "##### - Error cleaning whitelist: " + str(e)

def WhiteListDeleteSpecificDevice(devString):
    try:
        # print("In deleted specific device method - Step 1")
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        lstToSave = []
        f = open('/sd/whitelist.csv', 'r')
        sent_lines = f.readlines()
        f.close()
        # print("In deleted specific device method - Step 2")
        with open('/sd/whitelist.csv', 'w') as out:
            for ln in sent_lines:
                if ln.split(',')[0] not in listDevices:
                    out.write(ln)
                    lstToSave.append(ln.split(',')[0])
        
        globalVars.devices_whitelist = lstToSave

        tools.debug("New whitelist deleted: " + str(globalVars.devices_whitelist),'vv')
    except Exception as e:
        print("##### - Error cleaning whitelist: " + str(e))
        return 6, "##### - Error cleaning whitelist: " + str(e)        