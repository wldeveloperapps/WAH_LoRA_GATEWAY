from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
import time
import os
import uos
import utime
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

def getBatteryPercentage(level):
    try:
        max = 4200
        min = 3400
        batt = int(round(100 - (((max - level) * 100) / (max - min))))
        debug("Step 5 - Battery level: " + str(batt),'v')
        return batt

    except Exception as e:
        print("Step BAT -  Error converting percentage battery level: " + str(e))
        return 0

def sleepWiloc(period):
    try:
        debug("In sleep method: " + str(globalVars.stop_sleep_flag) + " - LoRaSending: " + str(globalVars.flag_sent),'vv')
        if globalVars.stop_sleep_flag == False and globalVars.flag_sent == False:
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
