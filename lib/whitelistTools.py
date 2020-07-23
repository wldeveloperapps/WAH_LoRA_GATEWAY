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
        

# def WhiteListNewDevice(devString):
#     try:
#         print("##### Whitelist new device ")
#         listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
#         print("##### Creating registers in whitelist: " + str(listDevices))
#         f = open('/sd/whitelist.csv', 'a')
#         strToSave = ""
#         for devDummy in listDevices:
#             # TODO Check if the device already exists in the .csv
#             strToSave = strToSave + str(str(devDummy) + "," + str(int(utime.time()))+ "\r\n")
#             print("##### Including device in whitelist: " + str(strToSave))
#         f.write(strToSave)
#         f.close()
#     except Exception as e:
#         print("##### - Error writing new device in whitelist: " + str(e))
#         return 6, "##### - Error writing new device in whitelist: " + str(e)

def WhiteListNewDevice(devString):
    try:
        print("##### Whitelist new device ")
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        print("##### Creating registers in whitelist: " + str(listDevices))
        f = open('/sd/whitelist.csv', 'r')
        sent_lines = f.readlines()
        f.close()
        
        with open('/sd/whitelist.csv', 'w') as out:
            for dev in listDevices:
                if dev not in sent_lines:
                    sent_lines.append(str(str(dev) + "," + str(int(utime.time()))+ "\r\n"))
        
            if len(sent_lines) > 0:
                globalVars.devices_sent = sent_lines

            for ln in sent_lines:
                out.write(ln)

        tools.debug("New whitelist inserted: " + str(globalVars.devices_sent),'vv')
    except Exception as e:
        print("##### - Error writing new device in whitelist: " + str(e))  

def WhiteListDeleteDevices():
    try:
        print("##### Deleting devices from Whitelist")
        f = open('/sd/whitelist.csv', 'w')
        f.close()
    except Exception as e:
        print("##### - Error cleaning whitelist: " + str(e))
        return 6, "##### - Error cleaning whitelist: " + str(e)

def WhiteListDeleteSpecificDevice(devString):
    try:
        listDevices = [devString[i:i+12] for i in range(0, len(devString), 12)]
        lstToSave = []
        f = open('/sd/whitelist.csv', 'r')
        sent_lines = f.readlines()
        f.close()
   
        with open('/sd/whitelist.csv', 'w') as out:
            for ln in sent_lines:
                if ln.split(',')[0] not in listDevices:
                    out.write(ln)
                    lstToSave.append(ln)
        
        if len(lstToSave) > 0:
            globalVars.devices_whitelist = lstToSave

        tools.debug("New whitelist deleted: " + str(globalVars.devices_whitelist),'vv')
    except Exception as e:
        print("##### - Error cleaning whitelist: " + str(e))
        return 6, "##### - Error cleaning whitelist: " + str(e)        