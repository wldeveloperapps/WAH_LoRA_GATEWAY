from machine import Pin, SD
from lib.beacon import DeviceBuzzer, DeviceReport
from errorissuer import checkError
from lib.rtcmgt import forceRTC
# from math import radians, sin, cos, acos
import math
import time
import os
import uos
import utime
import ubinascii
import machine
import globalVars
import struct
import pycom
import gc
from errorissuer import checkError
import sys
from uio import StringIO
# ---------------

try:
    if globalVars.deviceID == 2:
        from pytrack import Pytrack
        from L76GNSS import L76GNSS
        from LIS2HH12 import LIS2HH12
        py = Pytrack()
        acc = LIS2HH12()
    else:
        from pysense import Pysense
        from SI7006A20 import SI7006A20
        from LIS2HH12 import LIS2HH12
        py = Pysense()
        acc = LIS2HH12(py)
        si = SI7006A20(py)

    gc.enable()
    s = StringIO()
    wdt = machine.WDT(timeout=360000)
except BaseException as e:
    checkError("Error initializing tools", e)
    if globalVars.deviceID == 2:
        from pytrack import Pytrack
        from L76GNSS import L76GNSS
        from LIS2HH12 import LIS2HH12
        py = Pytrack()
        acc = LIS2HH12()
    else:
        from pysense import Pysense
        from SI7006A20 import SI7006A20
        from LIS2HH12 import LIS2HH12
        py = Pysense()
        acc = LIS2HH12(py)
        si = SI7006A20(py)

    gc.enable()
    s = StringIO()
    wdt = machine.WDT(timeout=360000)

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
    except BaseException as e:
        checkError("Step BAT -  Error getting battery level", e)
        return 20, "Step BAT -  Error getting battery level"

def getBatteryPercentage():
    try:
        acc_bat = 0
        counter = 0
        for a in range(10):
            val = int(round(py.read_battery_voltage()*1000))   
            if val > 0:
                acc_bat = acc_bat + val
                counter = counter + 1
                time.sleep(0.2)

        
        level = int(round(acc_bat / counter)) 
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

    except BaseException as e:
        checkError("Step BAT -  Error converting percentage battery level", e)
        return 0

def sleepWiloc(period):
    try:
        # debug("In sleep method: " + str(globalVars.stop_sleep_flag) + " - LoRaSending: " + str(globalVars.flag_sent),'vv')
        gc.collect()
        if globalVars.stop_sleep_flag == False and globalVars.flag_sent == False:
            utime.sleep(period)

    except BaseException as e:
        checkError("Step BAT -  Error getting battery level", e)

def sleepProcess():
    global gc
    try:
        debug("Step 8 - Going to sleep",'v')
        feedWatchdog()
        gc.collect()
        globalVars.mac_scanned[:]=[]
        globalVars.scanned_frames[:]=[]
        sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except BaseException as e:
        checkError("Error going to light sleep", e)

def deepSleepWiloc(period):
    try:
        debug("Forcing DeepSleep for " + str(period) + " seconds","v")
        utime.sleep(2)
        py.setup_sleep(period)
        py.go_to_sleep()
        machine.deepsleep(period)
    except BaseException as e:
        checkError("Error going to light sleep",e)

def getResetCause():
    reset_cause = machine.reset_cause()
    debug("Reset cause" + str(reset_cause), "v")

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
    except BaseException as e:
        checkError("Error printing debug", e)

def calculateDistance(latitude_init, longitude_init, latitude_end, longitude_end):
    try:
        debug("Input coordinates of two points:", "vv")
        slat = radians(float(latitude_init))
        slon = radians(float(longitude_init))
        elat = radians(float(latitude_end))
        elon = radians(float(longitude_end))

        dist = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))
        debug("The distance is %.2f meters." % dist, "vv")
        return dist
    except BaseException as e:
        checkError("Error calculating distance", e)
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
        debug("The distance is %s meters" % str(dist), "vv")
        
        return dist
    except BaseException as e:
        checkError("Error haversine method to calculate distance", e)

def systemCommands(data):
    try:
        debug("Manual configuration", "v")
        if data[:2] == "ff":
            debug(" --- Manual reset done successful --- ", "v")
            machine.reset()
        elif data[:2] == "f0":
            debug(" --- Force deep sleep done successful --- ", "v")
            deepSleepWiloc(int(data[2:],16))
        elif data[:2] == "f1":
            debug(" --- Force light indicator --- ", "v")
            globalVars.indicatorFrequencyOn = int(data[2:4],16)
            globalVars.indicatorFrequencyOff = int(data[4:6],16)
        elif data[:2] == "aa":
            try:
                debug(" --- Testing Block --- ", "v")
            except BaseException as e5:
                checkError("Error executing DAC outputs",e5)
        else:
            debug(" --- Manual command not recognise --- ", "v")
    except BaseException as e:
        checkError("Error executing manual commands",e)

def getAccelerometer():
    try:
        return acc.acceleration()
    except BaseException as e:
        checkError("Error gettion accelerometer", e)

def getGPS():
    try:
        l76 = L76GNSS(py)
        coord = dict(latitude=None, longitude=None)
        if globalVars.gps_enabled == True:
            coord = l76.get_location(debug=False, tout=globalVars.gps_timeout)
        if coord['latitude'] is not '' and coord['longitude'] is not '':
            haversine(coord['latitude'], coord['longitude'], globalVars.last_lat_tmp, globalVars.last_lon_tmp)
            big_endian_latitude = bytearray(struct.pack(">I", int(coord['latitude']*1000000)))  
            big_endian_longitude = bytearray(struct.pack(">I", int(coord['longitude']*1000000))) 
            dt = l76.getUTCDateTimeTuple(debug=True)
            if dt is not None:
                forceRTC(dt, "tuple")
                debug("Updating timestamp from GPS - " + str(utime.time()) + " - GMT: " + str(utime.gmtime()), "v")
                globalVars.flag_rtc_syncro = True
            
            debug("HDOP: " + str(coord['HDOP']) + "Latitude: " + str(coord['latitude']) + " - Longitude: " + str(coord['longitude']) + " - Timestamp: " + str(dt),'v')
            if float(str(coord['HDOP'])) > float(globalVars.min_hdop):
                return None,None
            else:
                globalVars.last_lat_tmp =  coord['latitude']
                globalVars.last_lon_tmp =  coord['longitude']
                return big_endian_latitude, big_endian_longitude
        else:
            return None,None
    except BaseException as e:
        checkError("Error getting GPS" , e)
        return None,None

def feedWatchdog():
    global wdt
    try:
        wdt.feed()
    except BaseException as e:
        checkError("Error feeding watchdog", e)

def loadConfigParameters():
    try:
        try:
            globalVars.BLE_SCAN_PERIOD = pycom.nvs_get('blescanperiod')
            debug("Step 0.5 - BLE_SCAN_PERIOD: " + str(globalVars.BLE_SCAN_PERIOD),'v')
        except BaseException as e:
            pycom.nvs_set('blescanperiod', globalVars.BLE_SCAN_PERIOD)
            checkError("BLE_SCAN_PERIOD error", e)

        try:
            globalVars.MAX_REFRESH_TIME = pycom.nvs_get('maxrefreshtime')
            debug("Step 0.5 - MAX_REFRESH_TIME: " + str(globalVars.MAX_REFRESH_TIME),'v')
        except BaseException as e:
            pycom.nvs_set('maxrefreshtime', globalVars.MAX_REFRESH_TIME)
            checkError("MAX_REFRESH_TIME error", e) 
        try:
            globalVars.STANDBY_PERIOD = pycom.nvs_get('standbyperiod')
            debug("Step 0.5 - STANDBY_PERIOD: " + str(globalVars.STANDBY_PERIOD),'v')
        except BaseException as e:
            pycom.nvs_set('standbyperiod', globalVars.STANDBY_PERIOD)
            checkError("STANDBY_PERIOD error", e)

        try:
            globalVars.RSSI_NEAR_THRESHOLD = pycom.nvs_get('rssithreshold')
            debug("Step 0.5 - RSSI_NEAR_THRESHOLD: " + str(int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256),'v')
        except BaseException as e:
            pycom.nvs_set('rssithreshold', str(globalVars.RSSI_NEAR_THRESHOLD))
            checkError("RSSI_NEAR_THRESHOLD error", e)

        try:
            globalVars.BUZZER_DURATION = pycom.nvs_get('buzzerduration')
            debug("Step 0.5 - BUZZER_DURATION: " + str(globalVars.BUZZER_DURATION),'v')
        except BaseException as e:
            pycom.nvs_set('buzzerduration', str(globalVars.BUZZER_DURATION))
            checkError("BUZZER_DURATION error", e)
        
        try:
            globalVars.STATISTICS_REPORT_INTERVAL = pycom.nvs_get('statsinterval')
            debug("Step 0.5 - STATISTICS_REPORT_INTERVAL: " + str(globalVars.STATISTICS_REPORT_INTERVAL),'v')
        except BaseException as e:
            pycom.nvs_set('statsinterval', globalVars.STATISTICS_REPORT_INTERVAL)
            checkError("STATISTICS_REPORT_INTERVAL error", e)

        try:
            globalVars.SENT_PERIOD = pycom.nvs_get('lorasentperiod')
            debug("Step 0.5 - SENT_PERIOD: " + str(globalVars.SENT_PERIOD),'v')
        except BaseException as e:
            pycom.nvs_set('lorasentperiod', globalVars.SENT_PERIOD)
            checkError("SENT_PERIOD error", e)

        try:
            globalVars.BUZZER_COUNTER_ALARM = pycom.nvs_get('buzcountalarm')
            debug("Step 0.5 - BUZZER_COUNTER_ALARM: " + str(globalVars.BUZZER_COUNTER_ALARM),'v')
        except BaseException as e:
            pycom.nvs_set('buzcountalarm', globalVars.BUZZER_COUNTER_ALARM)
            checkError("BUZZER_COUNTER_ALARM error", e)

        try:
            globalVars.ALARM_LIST_TYPE = pycom.nvs_get('alarmlisttype')
            debug("Step 0.5 - ALARM_LIST_TYPE: " + str(globalVars.ALARM_LIST_TYPE),'v')
        except BaseException as e:
            pycom.nvs_set('alarmlisttype', globalVars.ALARM_LIST_TYPE)
            checkError("ALARM_LIST_TYPE error", e)
        
        try:
            globalVars.REGION = pycom.nvs_get('loraregion')
            debug("Step 0.5 - LoRaWAN REGION: " + str(globalVars.REGION),'v')
        except BaseException as e:
            pycom.nvs_set('loraregion', globalVars.REGION)
            checkError("LoRaWAN REGION error", e)

        try:
            globalVars.LOW_BATTERY_VOLTAGE = pycom.nvs_get('lowbattalarm')
            debug("Step 0.5 - LOW_BATTERY_VOLTAGE: " + str(globalVars.LOW_BATTERY_VOLTAGE),'v')
        except BaseException as e:
            pycom.nvs_set('lowbattalarm', globalVars.LOW_BATTERY_VOLTAGE)
            checkError("LoRaWAN LOW_BATTERY_VOLTAGE error", e)
    except BaseException as e1:
        checkError("Step 18 - Error loading config parameters",e1) 

def resetDevice(dev):
    try:
        debug("Resetting device manually", "vv")
        machine.reset()
    except BaseException as e:
        checkError("Error going to light sleep",e)

def template(dev):
    try:
        debug("", "")
    except BaseException as e:
        checkError("Error going to light sleep",e)

def manage_devices_send(dev_list):
    try:
        for dd1 in dev_list:
            exists = False
            # if dd1.addr == "stats":
            #     globalVars.lora_sent_stats.append(dd1)
            # elif dd1.addr == "ackresp":
            #     globalVars.lora_sent_acks.append(dd1)
            # else:
            for dd2 in globalVars.lora_sent_devices:
                if str(dd1.addr) == str(dd2.addr):
                    exists = True
            if exists == False:
                globalVars.lora_sent_devices.append(dd1)

        debug("LoRaWAN Stored records to send, Devices: " 
        + str(len(globalVars.lora_sent_devices)) 
        + " - Stats: " + str(len(globalVars.lora_sent_stats)) 
        + " - ACKs: "+ str(len(globalVars.lora_sent_acks)) ,"vvv")
    except BaseException as e:
        checkError("Error managing devices to send", e)
