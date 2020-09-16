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

sent_lines = []

def LoRaWANListSentDevices():
    try:
        sent_devices = []
        f = open('/sd/sentlist.csv', 'r')
        strFile = f.read()
        print("Step 0 - LoRaWAN Sent list Content: " + strFile)
        for dd in strFile.split('\n'):
            if len(dd.split(',')) >= 2:
                sent_devices.append(DeviceReport(dd.split(',')[0],int(dd.split(',')[1])))
        f.close()
        #print("Buzzer list already read")
        return 1, sent_devices
    except Exception as e:
        return 8, "Step 0 - Error getting device in sentlist: " + str(e)
        print("Step 0 - Error getting new device in sentlist: " + str(e))

def LoRaWANSentListCleanDevices():
    try:
        print("Step 6 - Cleaning devices in LoRaWAN Sent List")
        out = open('/sd/sentlist.csv', 'w')
        out.close()
    except Exception as e:
        print("Step 6 - Error cleaning devices in LoRaWAN Sent list: " + str(e))
        return 14, "Step 6 - Error cleaning devices in LoRaWAN Sent list: " + str(e)
        

def LoRaWANSentListNewDevice(device):
    try:
        f = open('/sd/sentlist.csv', 'a')
        strToSave = str(str(device.addr) + "," + str(int(utime.time()))+ "\r\n")
        print("Step 5 - Creating new register LoRaWAN Sent list: " + str(strToSave))
        f.write(strToSave)
        f.close()

    except Exception as e:
        print("Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e))
        return 11, "Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e)
        

def LoRaWANSentListUpdateDevice(device):
    global sent_lines
    try:
        tools.debug("Step 5 - Updating register LoRaWANSent list", "vvv")
        strToSave = ''
        sent_devices = []
        if len(sent_lines) <= 0:
            f = open('/sd/sentlist.csv', 'r')
            sent_lines = f.readlines()
            f.close()
        
        for idx, value in enumerate(sent_lines):
            if device.addr in value:
                strToSave = str(str(device.addr) + "," + str(int(utime.time()))+ "\r\n")
                sent_lines[idx] = strToSave
                # print("Step 5 - Updating device LoRaWAN Sent list: " + str(strToSave))
                
        if strToSave == '':
            print("Step 5 - Device to update not found")
            strToSave = str(str(device.addr) + "," + str(int(utime.time()))+ "\r\n")
            sent_lines.append(strToSave)

        with open('/sd/sentlist.csv', 'w') as out:
            for ln in sent_lines:
                out.write(ln)
                sent_devices.append(DeviceReport(ln.split(',')[0],int(ln.split(',')[1])))
        
                
        return sent_devices            

    except Exception as e:
        print("Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e))
        return 12, "Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e)
        
