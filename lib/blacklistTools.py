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

def BlackListGetDevices():
    try:
        devices_blacklist = []
        f = open('/sd/blacklist.csv', 'r')
        strFile = f.read()
        print("Step 0 - Getting Blacklist,content: " + strFile)
        for dd in strFile.replace('"','').split('\n'):
            if len(dd.split(',')) >= 2:
                devices_blacklist.append(dd.split(',')[0])
        f.close()
        return 1, devices_blacklist
    except Exception as e:
        print("Step 0 - Error reading get blacklist SD: " + str(e))
        if "ENOENT" in str(e):
            with open('/sd/blacklist.csv', 'a') as out:
                out.write('0,0\r\n')
        return 0, []
        

def BlackListNewDevice(devString):
    try:
        print("##### Blacklist new device ")
        if globalVars.MAC_TYPE == "LORA":
            listDevices = [devString[i:i+16] for i in range(0, len(devString), 16)]
        elif globalVars.MAC_TYPE == "BLE":
            listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]

        print("##### Creating registers in blacklist: " + str(listDevices))
        f = open('/sd/blacklist.csv', 'r')
        black_lines = f.readlines()
        f.close()
        lstDummy = []
        with open('/sd/blacklist.csv', 'w') as out:
            for dev in listDevices:
                exists = False
                for wht in black_lines:
                    if dev in wht.split(',')[0]:
                        exists = True
                        break
                if exists == False:
                    black_lines.append(str(str(dev).lower() + "," + str(int(utime.time()))+ "\r\n"))

            for ln in black_lines:
                out.write(ln)
                lstDummy.append(ln.split(',')[0].lower())

            globalVars.devices_blacklist = lstDummy

        tools.debug("New blacklist inserted: " + str(globalVars.devices_blacklist),'vv')
    except Exception as e:
        print("##### - Error writing new device in blacklist: " + str(e))  

def BlackListDeleteDevices():
    try:
        print("##### Deleting devices from Blacklist")
        f = open('/sd/blacklist.csv', 'w')
        f.close()
        globalVars.devices_blacklist = []
    except Exception as e:
        print("##### - Error cleaning blacklist: " + str(e))
        return 6, "##### - Error cleaning blacklist: " + str(e)

def BlackListDeleteSpecificDevice(devString):
    try:
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        lstToSave = []
        f = open('/sd/blacklist.csv', 'r')
        sent_lines = f.readlines()
        f.close()
        with open('/sd/blacklist.csv', 'w') as out:
            for ln in sent_lines:
                if ln.split(',')[0] not in listDevices:
                    out.write(ln)
                    lstToSave.append(ln.split(',')[0])
        
        globalVars.devices_blacklist = lstToSave

        tools.debug("New blacklist deleted: " + str(globalVars.devices_blacklist),'vv')
    except Exception as e:
        print("##### - Error cleaning blacklist: " + str(e))
        return 6, "##### - Error cleaning blacklist: " + str(e)        