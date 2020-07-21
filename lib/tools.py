from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
import time
import os
import uos
import utime
import pycom 
import ubinascii
import machine
import globalVars
# ---------------

try:
    sd = SD()
except Exception as e:
    print("Error initializing SD Card")
    sd = SD()

def isInList(device, dmList):
    for dev in dmList:
        if device.addr in dev.addr:
            return dev

    return None

def StopSDCard():
    sd.deinit()

def UpdateConfigurationParameters(payload):
    try:
        
        if payload[0:2] == '20':
            print("Step CC - Setting Max Refresh Time to " + str(int(payload[2:6],16)))
            pycom.nvs_set('maxrefreshtime', int(payload[2:6],16))
        if payload[0:2] == '21':
            print("Step CC - Setting BLE Scan Period to " + str(int(payload[2:6],16)))
            pycom.nvs_set('blescanperiod', int(payload[2:6],16))
        if payload[0:2] == '22':
            print("Step CC - Setting StandBy Period to " + str(int(payload[2:6],16)))
            pycom.nvs_set('standbyperiod', int(payload[2:6],16))
        if payload[0:2] == '23':
            print("Step CC - Setting RSSI Near Threshold to " + str(int(payload[2:6],16)-256))
            pycom.nvs_set('rssithreshold', str(payload[2:6],16))
        if payload[0:2] == '24':
            print("Step CC - Setting Statistics Report Interval to " + str(int(payload[2:6],16)))
            pycom.nvs_set('statsinterval', int(payload[2:6],16))
        if payload[0:2] == '25':
            print("Step CC - Setting Buzzer Duration Period to " + str(int(payload[2:6],16)))
            pycom.nvs_set('buzzerduration', int(payload[2:6],16))
            
    except Exception as e:
        print("Step CC -  Error setting configuiration parameters: " + str(e))
        return 17, "Step CC -  Error setting configuiration parameters: " + str(e)

def getBatteryLevel():
    try:
        adc = machine.ADC()             
        apin = adc.channel(pin='P16', attn=adc.ATTN_11DB)
        acc_bat = 0
        for a in range(10):
            val = apin()
            val = int(round(int(val) * 1.4))    
            if val > 0:
                acc_bat = acc_bat + val
                time.sleep(0.2)
        acc_bat = int(round(acc_bat / 10)) 
        return acc_bat
    except Exception as e:
        print("Step BAT -  Error getting battery level: " + str(e))
        return 20, "Step BAT -  Error getting battery level: " + str(e)

def sleepWiloc(period):
    try:
        # print("In sleep method: " + str(globalVars.stop_sleep_flag))
        if globalVars.stop_sleep_flag == False:
            utime.sleep(period)
    except Exception as e:
        print("Step BAT -  Error getting battery level: " + str(e))

def int_to_bytes(value, length):
    result = []

    for i in range(0, length):
        result.append(value >> (i * 8) & 0xff)

    result.reverse()

    return result

def debug(payload, type):
    try:
        if str(globalVars.debug_cc).count('v') >=  str(type).count('v'):
            print("Debug 0 - " + str(payload))
                
    except Exception as e:
        print("Error printing debug: " + str(e))

def template(dev):
    try:
        print("")
    except Exception as e:
        print("Error")
