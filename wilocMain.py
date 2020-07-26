from lib.whitelistTools import WhiteListGetDevices
from lib.loRaReportsTools import LoRaWANListSentDevices, LoRaWANSentListUpdateDevice
from lib.buzzerTools import BeepBuzzer
from machine import SD, WDT
from lib.rtcmgt import initRTC, autoRTCInitialize
from errorissuer import checkError
import ubinascii
import utime
import machine
import os
import tools
import struct
import pycom
import gc
import globalVars
import lorawan
import _thread

sd = SD()
gc.enable()
if globalVars.deviceID == 2:
    from pytrack import Pytrack
    from L76GNSS import L76GNSS
    py = Pytrack()
else:
    from pysense import Pysense
    from SI7006A20 import SI7006A20
    py = Pysense()
    si = SI7006A20(py)

os.mount(sd, '/sd')
wdt = WDT(timeout=300000)
# ---------------

strError = []
# ---------------


def rssiFilterDevices(RSSI_NEAR_THRESHOLD, macs, frames):
    try:
        from lib.beacon import DeviceFilter
        rssi_filter_devices = []
        thrs = int(RSSI_NEAR_THRESHOLD,16) - 256
        tools.debug("Step 2 - Filtering RSSI of devices, Threshold: " + str(thrs), 'v')
        for scanDev in macs:
            ret = calculateRssiAvg(scanDev, frames)
            if ret[0] >= thrs:
                tools.debug("Step 2 - Adding device to RSSI Filter list " + str(ubinascii.hexlify(scanDev)) + " Distance: Close " + " RSSI: " + str(ret[0]) + " Samples: " + str(ret[1]) + " DT: " + str(int(utime.time())), 'vv')
                rssi_filter_devices.append(DeviceFilter(str(ubinascii.hexlify(scanDev).decode('utf-8')), ret[0], ret[1], int(utime.time()), scanDev))
            elif ret[0] < thrs:
                tools.debug("Step 2 - Not sending device " + str(ubinascii.hexlify(scanDev)) + " Distance: Far " + " RSSI: " + str(ret[0]) + " Samples: " + str(ret[1]) + " DT: " + str(int(utime.time())), 'vv')
        return rssi_filter_devices
    except Exception as e1:
        checkError("Step 2 - Error filtering RSSI: " + str(e1)) 
        return []

def calculateRssiAvg(device, frames):
    try:
        rssi_acc = 0
        rssi_average = 0
        samples = 0
        for dev in frames:
            if device in dev.addr:
                samples += 1
                rssi_acc += dev.rssi
        if samples > 0:
            rssi_average = rssi_acc / samples
        else: 
            rssi_average = -120
        #print("Device: " + str(device) + "RSSI Average: " + str(rssi_average) + " Samples: " + str(samples))
        return rssi_average, samples
    except Exception as e:
        checkError("Error calculating RSSI Avg")
        return []

def getBatteryLevel(py):
    try:
        battery = py.read_battery_voltage()
        acc_bat = int(round(battery*1000))
        tools.debug("Battery Level: " + str(acc_bat),'vv')
        return acc_bat
    except Exception as e:
        checkError("Error getting battery level, " + str(e))
        return 0

def loadSDCardData():
    try:
        ret = WhiteListGetDevices() 
        if ret[0] == 1:
            # print("Step 0 - Getting whitelist")
            globalVars.devices_whitelist = ret[1]
        else:
            checkError("Step 0 - Error Getting whitelist: " + str(ret[1]))
            strError.append(ret[0])

        sent = LoRaWANListSentDevices() 
        if sent[0] == 1:
            # print("Step 0 - Getting LoRaWAN Sent list")
            globalVars.device_sent = sent[1]
        else:
            checkError("Step 0 - Error Getting LoRaWAN Sent devices list: " + str(sent[1]))
            strError.append(sent[0])

    except Exception as e:
        checkError("Step 0 - Error load SD Card information: " + str(e))
        strError.append('10')

def forceConfigParameters():
    try:
        pycom.nvs_set('blescanperiod', globalVars.BLE_SCAN_PERIOD)
        pycom.nvs_set('maxrefreshtime', globalVars.MAX_REFRESH_TIME)
        pycom.nvs_set('standbyperiod', globalVars.STANDBY_PERIOD)
        pycom.nvs_set('rssithreshold', str(globalVars.RSSI_NEAR_THRESHOLD))
        pycom.nvs_set('buzzerduration', globalVars.BUZZER_DURATION)
        pycom.nvs_set('statsinterval', globalVars.STATISTICS_REPORT_INTERVAL)
        utime.sleep(2)
    except Exception as e:
        checkError("Error forcing configuration parameters: " + str(e))

def loadConfigParameters():
    try:
        try:
            globalVars.BLE_SCAN_PERIOD = pycom.nvs_get('blescanperiod')
            tools.debug("Step 0.5 - BLE_SCAN_PERIOD: " + str(globalVars.BLE_SCAN_PERIOD),'v')
        except Exception:
            pycom.nvs_set('blescanperiod', globalVars.BLE_SCAN_PERIOD)
            checkError("BLE_SCAN_PERIOD error")

        try:
            globalVars.MAX_REFRESH_TIME = pycom.nvs_get('maxrefreshtime')
            tools.debug("Step 0.5 - MAX_REFRESH_TIME: " + str(globalVars.MAX_REFRESH_TIME),'v')
        except Exception:
            pycom.nvs_set('maxrefreshtime', globalVars.MAX_REFRESH_TIME)
            checkError("MAX_REFRESH_TIME error") 
        try:
            globalVars.STANDBY_PERIOD = pycom.nvs_get('standbyperiod')
            tools.debug("Step 0.5 - STANDBY_PERIOD: " + str(globalVars.STANDBY_PERIOD),'v')
        except Exception:
            pycom.nvs_set('standbyperiod', globalVars.STANDBY_PERIOD)
            checkError("STANDBY_PERIOD error")

        try:
            globalVars.RSSI_NEAR_THRESHOLD = pycom.nvs_get('rssithreshold')
            tools.debug("Step 0.5 - RSSI_NEAR_THRESHOLD: " + str(int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256),'v')
        except Exception:
            pycom.nvs_set('rssithreshold', str(globalVars.RSSI_NEAR_THRESHOLD))
            checkError("RSSI_NEAR_THRESHOLD error")

        try:
            globalVars.BUZZER_DURATION = pycom.nvs_get('buzzerduration')
            tools.debug("Step 0.5 - BUZZER_DURATION: " + str(globalVars.BUZZER_DURATION),'v')
        except Exception:
            pycom.nvs_set('buzzerduration', globalVars.BUZZER_DURATION)
            checkError("BUZZER_DURATION error")
        
        try:
            globalVars.STATISTICS_REPORT_INTERVAL = pycom.nvs_get('statsinterval')
            # STATISTICS_REPORT_INTERVAL = 60 # Force parameter value
            tools.debug("Step 0.5 - STATISTICS_REPORT_INTERVAL: " + str(globalVars.STATISTICS_REPORT_INTERVAL),'v')
        except Exception:
            pycom.nvs_set('statsinterval', globalVars.STATISTICS_REPORT_INTERVAL)
            checkError("STATISTICS_REPORT_INTERVAL error")
        
    except Exception as e1:
        checkError("Step 18 - Error loading config parameters: " + str(e1)) 

def checkWhiteList(dev):
    try:
        if dev not in globalVars.devices_whitelist:
            tools.debug("Step 1.1 - Device not found in the Whitelist: " + str(dev),'vvv')
            if str(globalVars.debug_cc).count('v') <= 3:
                BeepBuzzer(0.1)
        else:
            tools.debug("Step 1.1 - Device found in Whitelist: " + str(dev),'vvv')

    except Exception as e:
        checkError("Error checking whitelist level, " + str(e))

def checkTimeToSend(devs, MAX_REFRESH_TIME):
    try:
        ret_devices = []
        ts = int(utime.time())
        for dev in devs:
            dmDev = tools.isInList(dev, globalVars.device_sent)
            if dmDev is not None:
                if (dmDev.timestamp + int(MAX_REFRESH_TIME)) < ts:
                    ret_devices.append(dev)
                else:
                    tools.debug("Step 3 - Waiting for the device " + str(dmDev.addr) + " to send again - Remaining time: " + str(((dmDev.timestamp + int(MAX_REFRESH_TIME)) - ts)),'v')
            else:
                ret_devices.append(dev)
        
        return ret_devices
    except Exception as e:
        checkError("Error checking time to send data: " + str(e))
        return []

def createPackageToSend(devs):
    global py
    try:
        tools.debug("Step 4 - Creating message to send",'v')
        strToSend = []
        battery = py.read_battery_voltage()
        acc_bat = int(round(battery*1000))
        nearCode = 0
        nearCode = struct.pack(">I", acc_bat)
        strToSend.append(nearCode[2])
        strToSend.append(nearCode[3])
        tools.debug("Step 5 - Battery level: " + str(nearCode),'v')
        for dev in devs:
            for bmac in dev.rawMac:
                strToSend.append(bmac)
            globalVars.device_sent = LoRaWANSentListUpdateDevice(dev)

        return strToSend
    except Exception as e1:
        checkError("Step 5 - Error sending LoRaWAN: " + str(e1)) 
        strError.append('1')
        return []

def feedWatchdog():
    global wdt
    try:
        wdt.feed()
    except Exception as e:
        checkError("Error feeding watchdog")

def ForceBuzzerSound(duration):
    try:
        BeepBuzzer(duration)
    except Exception as e:
        checkError("Error forcing buzzer")

def checkTimeForStatistics(INTERVAL):
    try:
        tools.debug("Step 6 - Checking time for statistics",'vvv')
        # tools.debug("Test 0",'vvv')
        ts = int(utime.time())
        # tools.debug("Test 1",'vvv')
        try:
            last_report = pycom.nvs_get('laststatsreport')
        except Exception:
            pycom.nvs_set('laststatsreport', str(ts))
            last_report = ts
        # tools.debug("Test 2",'vvv')
        if (int(last_report) + int(INTERVAL)) < ts:
            pycom.nvs_set('rtc', str(int(utime.time())))
            return True
        else:
            tools.debug("Step 6 - No statistics reports yet, WhiteList: " + str(len(globalVars.devices_whitelist)) + " - remaining: " + str(((int(last_report) + int(INTERVAL)) - ts)),'v')
            return False
    except Exception as e:
        checkError("Error checking time for statistics: " + str(e))
        return False

def createStatisticsReport():
    try:
        strToSendStatistics = []
        if globalVars.deviceID == 1:
            temperature = 0
            altitude = 0
            battery = py.read_battery_voltage()
            temperature = si.temperature()
            humidity = si.humidity()
            acc_tmp = int(round(temperature))
            acc_hum = int(round(humidity))
            lat =  struct.pack(">I", acc_tmp)
            lon =  struct.pack(">I", acc_hum)
        elif globalVars.deviceID == 2:
            tools.debug("Waiting for GPS",'vv')
            lat, lon = getGPS()
            if lat is None or lon is None:
                lat = struct.pack(">I", 0)
                lon = struct.pack(">I", 0)

        battery = py.read_battery_voltage()
        acc_bat = int(round(battery*1000))
        dev = struct.pack(">I", globalVars.deviceID)
        bat = struct.pack(">I", acc_bat)
        dt = struct.pack(">I", utime.time())
        whiteLen = struct.pack(">I", len(globalVars.devices_whitelist))
        sentLen = struct.pack(">I", len(globalVars.device_sent))
        strToSendStatistics.append(dev[3])
        strToSendStatistics.append(bat[2])
        strToSendStatistics.append(bat[3])
        strToSendStatistics.append(lat[0])
        strToSendStatistics.append(lat[1])
        strToSendStatistics.append(lat[2])
        strToSendStatistics.append(lat[3])
        strToSendStatistics.append(lon[0])
        strToSendStatistics.append(lon[1])
        strToSendStatistics.append(lon[2])
        strToSendStatistics.append(lon[3])
        strToSendStatistics.append(dt[0])
        strToSendStatistics.append(dt[1])
        strToSendStatistics.append(dt[2])
        strToSendStatistics.append(dt[3])
        strToSendStatistics.append(whiteLen[2])
        strToSendStatistics.append(whiteLen[3])
        strToSendStatistics.append(sentLen[2])
        strToSendStatistics.append(sentLen[3])
        tools.debug("Step 7 - Creating statistics report: " + str(strToSendStatistics) + " Battery: " + str(acc_bat),'v')
        return strToSendStatistics
    except Exception as e:
        checkError("Error creating statistics report: " + str(e)) 
        strError.append('19')
        return []

def sendStatisticsReport():
    try:
        tools.debug("Sending statistics report step 1", 'vv')
        statSend = createStatisticsReport()
        tools.debug("Sending statistics report step 2", 'vv')
        if len(statSend) > 0:
            lorawan.sendLoRaWANMessage(statSend)
            tools.debug("Sending statistics report step 3", 'vv')
           
    except Exception as e:
        checkError("Error sending statistics report: " + str(e))

def getGPS():
    try:
        l76 = L76GNSS(py)
        rtc = machine.RTC()
        coord = (None,None)
        coord = l76.coordinates_v2(debug=False)
        # if coord['latitude'] is not None and coord['longitude'] is not None:
        if coord[0] is not None and coord[1] is not None:
            # big_endian_latitude = bytearray(struct.pack("f", coord['latitude']))  
            # big_endian_longitude = bytearray(struct.pack("f", coord['longitude'])) 
            big_endian_latitude = bytearray(struct.pack("f", coord[0]))  
            big_endian_longitude = bytearray(struct.pack("f", coord[1]))  
            # print([ "0x%02x" % b for b in big_endian_latitude ])
            dt = l76.getUTCDateTimeTuple(debug=True)
            if dt is not None:
                rtc.init(dt)
            # tools.debug("Latitude: " + str(coord['latitude']) + " - Longitude: " + str(coord['longitude']) + " - Timestamp: " + str(dt),'v')
            tools.debug("Latitude: " + str(coord[0]) + " - Longitude: " + str(coord[1]) + " - Timestamp: " + str(dt),'v')
            # l76.enterStandBy(debug=False)
            return big_endian_latitude, big_endian_longitude
        else:
            return None,None
    except Exception as e:
        checkError("Error getting GPS: " + str(e))
        return None,None