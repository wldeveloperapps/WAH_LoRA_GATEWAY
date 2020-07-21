from machine import Pin, SD
from lib.beacon import DeviceBuzzer
import time
import os
import uos
import ujson
import utime
import pycom 
import ubinascii

p_out = Pin('P10', mode=Pin.OUT)
buzzer_lines = []

def BuzzerTurnOff():
    p_out.hold(False)
    p_out.value(0)
    p_out.hold(True)

def BeepBuzzer(duration):
    # print("Step 4 - Buzzer is sounding")
    p_out.hold(False)
    p_out.value(1)
    time.sleep(duration)
    p_out.value(0)
    p_out.hold(True)
    time.sleep(duration)

def BuzzerListGetDevices():
    try:
        buzzer_devices = []
        f = open('/sd/buzzerlist.csv', 'r')
        strFile = f.read()
        print("Step 0 - Buzzer list Content: " + strFile)
        for dd in strFile.split('\n'):
            if len(dd.split(',')) >= 2:
                buzzer_devices.append(DeviceBuzzer(dd.split(',')[0],int(dd.split(',')[1])))
        f.close()
        #print("Buzzer list already read")
        return 1, buzzer_devices
    except Exception as e:
        print("Step 0 - Error getting new device in buzzerlist: " + str(e))
        return 8, "Step 0 - Error getting device in buzzerlist: " + str(e)
        

def BuzzerListNewDevice(device):
    try:
        print("Step 4 - Creating new register buzzer list: " + str(device.addr) + " ts: " + str(device.timestamp))
        f = open('/sd/buzzerlist.csv', 'a')
        strToSave = str(str(device.addr) + "," + str(int(utime.time()))+ "\r\n")
        f.write(strToSave)
        f.close()

    except Exception as e:
        print("Step 4 - Error writing new device in buzzerlist: " + str(e))
        return 7, "Step 4 - Error writing new device in buzzerlist: " + str(e)
        

def BuzzerListUpdateDevice(device):
    global buzzer_lines
    try:
        print("Step 4 - Updating register buzzer list")         
        strToSave = ''
        
        if len(buzzer_lines) <= 0:
            f = open('/sd/buzzerlist.csv', 'r')
            buzzer_lines = f.readlines()
            f.close()
        
        for idx, value in enumerate(buzzer_lines):
            if device.addr in value:
                strToSave = str(str(device.addr) + "," + str(int(utime.time()))+ "\r\n")
                buzzer_lines[idx] = strToSave
                print("Step 4 - Updating device buzzer list: " + str(strToSave))
        if strToSave == '':
            print("Step 4 - Device to update not found")

        with open('/sd/buzzerlist.csv', 'w') as out:
            for ln in buzzer_lines:
                out.write(ln)

    except Exception as e:
        print("Step 4 - Error updating device in buzzerlist: " + str(e))
        return 7, "Step 4 - Error updating device in buzzerlist: " + str(e)
        

def BuzzerListCleanDevices():
    try:
        dummy = []
        print("Step 6 - Cleaning devices in Buzzer List")
        out = open('/sd/buzzerlist.csv', 'w')
        out.write(dummy)
        out.close()
    except Exception as e:
        print("Step 6 - Error cleaning devices in buzzerlist: " + str(e))
        return 13, "Step 6 - Error cleaning devices in buzzerlist: " + str(e)
        

