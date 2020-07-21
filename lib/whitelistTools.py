from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
import time
import os
import uos
import ujson
import utime
import pycom 
import ubinascii

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
    except Exception as e:
        print("Step 0 - Error reading SD: " + str(e))
        return 0, []
        

def WhiteListNewDevice(devString):
    try:
        print("##### Whitelist new device ")
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        print("##### Creating registers in whitelist: " + str(listDevices))
        f = open('/sd/whitelist.csv', 'a')
        for devDummy in listDevices:
            # TODO Check if the device already exists in the .csv
            strToSave = str(str(devDummy) + "," + str(int(utime.time()))+ "\r\n")
            print("##### Including device in whitelist: " + str(strToSave))
        f.write(strToSave)
        f.close()
    except Exception as e:
        print("##### - Error writing new device in whitelist: " + str(e))
        return 6, "##### - Error writing new device in whitelist: " + str(e)
        

def WhiteListDeleteDevices():
    try:
        print("##### Deleting devices from Whitelist")
        f = open('/sd/whitelist.csv', 'w')
        f.close()
    except Exception as e:
        print("##### - Error cleaning whitelist: " + str(e))
        return 6, "##### - Error cleaning whitelist: " + str(e)
        