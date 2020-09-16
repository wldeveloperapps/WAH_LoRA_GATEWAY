from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
from errorissuer import checkError
# from math import radians, sin, cos, acos
import math
import time
import os
import uos
import utime
import ubinascii
import machine
import globalVars
import gc
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
        if level > max:
            batt = 100
        elif level < min: 
            batt = 0
        else:
            batt = int(round(100 - (((max - level) * 100) / (max - min))))  
        
        debug("Step 5 - Battery level: " + str(batt),'vvv')
        return batt

    except Exception as e:
        print("Step BAT -  Error converting percentage battery level: " + str(e))
        return 0

def sleepWiloc(period):
    try:
        # debug("In sleep method: " + str(globalVars.stop_sleep_flag) + " - LoRaSending: " + str(globalVars.flag_sent),'vv')
        gc.collect()
        if globalVars.stop_sleep_flag == False and globalVars.flag_sent == False:
            utime.sleep(period)
        
    except Exception as e:
        print("Step BAT -  Error getting battery level: " + str(e))

def getResetCause():
    reset_cause = machine.reset_cause()
    checkError("Reset cause: " + str(reset_cause))

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

def calculateDistance(latitude_init, longitude_init, latitude_end, longitude_end):
    try:
        print("Input coordinates of two points:")
        slat = radians(float(latitude_init))
        slon = radians(float(longitude_init))
        elat = radians(float(latitude_end))
        elon = radians(float(longitude_end))

        dist = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))
        print("The distance is %.2f meters." % dist)
        return dist
    except Exception as e:
        print("Error calculating distance: " + str(e))
        return 0

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6372800  # Earth radius in meters
        # lat1, lon1 = coord1
        # lat2, lon2 = coord2
        
        phi1, phi2 = math.radians(lat1), math.radians(lat2) 
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + \
            math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        
        dist = 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))
        print("The distance is %s meters" % str(dist))
        
        return dist
    except Exception as e:
        print("Error haversine method to calculate distance")

def template(dev):
    try:
        print("")
    except Exception as e:
        print("Error")
