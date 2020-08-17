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
from lib.beacon import Device

sd = SD()
gc.enable()
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

os.mount(sd, '/sd')
wdt = WDT(timeout=300000)
# ---------------

strError = []
# ---------------

# ---------- TODO -------------
#  Sleep schedule by RTC syncronization by GPS
#  Blacklist development
#  Modify buzzer intensity with an ADC output


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
        pycom.nvs_set('lorasentperiod', globalVars.SENT_PERIOD)
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

        try:
            globalVars.SENT_PERIOD = pycom.nvs_get('lorasentperiod')
            # STATISTICS_REPORT_INTERVAL = 60 # Force parameter value
            tools.debug("Step 0.5 - SENT_PERIOD: " + str(globalVars.SENT_PERIOD),'v')
        except Exception:
            pycom.nvs_set('lorasentperiod', globalVars.SENT_PERIOD)
            checkError("SENT_PERIOD error")
        
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

def createPackageToSend(devs, frames):
    global py
    try:
        # CommandID - Latitude - Longitude - GPS/REP - Battery - MACDevice - LatitudeDevice - LongitudeDevice
        # tools.debug("Step 4 - Creating messages to send, Devs: " + str(devs),'v')
        devicesToSend = []
        for dd in devs:
            tools.debug("Creating package to send of device: " + str(dd.addr),'v')
            strToSend = []
            gps_stats = 66
            bat = tools.getBatteryPercentage(int(round(py.read_battery_voltage()*1000)))
            st_bat = struct.pack(">I", bat)
            st_gps_stats = struct.pack(">I", gps_stats)
            strToSend.append(struct.pack(">I", 10)[3]) # Protocol
            # strToSend.append(struct.pack(">I", 0)) # Command ID
            strToSend.append(globalVars.longitude[3]) # Gateway Longitude
            strToSend.append(globalVars.longitude[2]) # Gateway Longitude
            strToSend.append(globalVars.longitude[1]) # Gateway Longitude
            strToSend.append(globalVars.longitude[0]) # Gateway Longitude
            strToSend.append(globalVars.latitude[3]) # Gateway Latitude 
            strToSend.append(globalVars.latitude[2]) # Gateway Latitude 
            strToSend.append(globalVars.latitude[1]) # Gateway Latitude 
            strToSend.append(globalVars.latitude[0]) # Gateway Latitude 

            strToSend.append(st_gps_stats[3]) # Gateway GPS Status & Report type HARDCODE
            strToSend.append(st_bat[3])
            # tools.debug("Getting MAC bytes of : " + str(dd.addr),'vv')
            for bmac in dd.rawMac:
                strToSend.append(bmac)
            # tools.debug("Getting last location of : " + str(dd.addr),'vv')
            last_frame = ""
            last_lat = ""
            last_lon = ""
            for fr in frames:
                # print("FRAMES: " + str(ubinascii.hexlify(fr.addr).decode('utf-8')) + " - DD: " + str(dd.addr) + " - FR: " + str(fr.raw))
                if str(ubinascii.hexlify(fr.addr).decode('utf-8')) == dd.addr:
                    if len(fr.raw) > 36:
                        last_frame = str(fr.raw)[12:36]
            if len(last_frame) > 22:
                last_lat = last_frame[4:12]
                last_lon = last_frame[12:20]
            # print("Last frame: " + str(last_frame) + " - Last lat: " + str(last_lat) + " - Last lon: " + str(last_lon))
            #TODO Convert latitude & longitude to ByteArray
            strToSend.append(int(last_lon[0]+last_lon[1],16)) # End-Device Longitude
            strToSend.append(int(last_lon[2]+last_lon[3],16)) # End-Device Longitude
            strToSend.append(int(last_lon[4]+last_lon[5],16)) # End-Device Longitude
            strToSend.append(int(last_lon[6]+last_lon[7],16)) # End-Device Longitude
            strToSend.append(int(last_lat[0]+last_lat[1],16)) # End-Device Latitude 
            strToSend.append(int(last_lat[2]+last_lat[3],16)) # End-Device Latitude 
            strToSend.append(int(last_lat[4]+last_lat[5],16)) # End-Device Latitude 
            strToSend.append(int(last_lat[6]+last_lat[7],16)) # End-Device Latitude 
            globalVars.device_sent = LoRaWANSentListUpdateDevice(dd)
            devicesToSend.append(Device(addr=dd.addr,raw=strToSend))
        return devicesToSend
    except Exception as e1:
        checkError("Step 5 - Error creating package to send: " + str(e1)) 
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
            tools.debug("Waiting for GPS ",'vv')
            globalVars.latitude, globalVars.longitude = getGPS()
            if globalVars.latitude is None or globalVars.longitude is None:
                globalVars.latitude = struct.pack(">I", 0)
                globalVars.longitude = struct.pack(">I", 0)

        # battery = py.read_battery_voltage()
        # acc_bat = int(round(battery*1000))
        # dev = struct.pack(">I", globalVars.deviceID)
        # bat = struct.pack(">I", acc_bat)
        bat = tools.getBatteryPercentage(int(round(py.read_battery_voltage()*1000)))
        st_bat = struct.pack(">I", bat)
        dt = struct.pack(">I", utime.time())
        whiteLen = struct.pack(">I", len(globalVars.devices_whitelist))
        gps_stats = 67
        st_gps_stats = struct.pack(">I", gps_stats)
        # sentLen = struct.pack(">I", len(globalVars.device_sent))
        strToSendStatistics.append(struct.pack(">I", 11)[3]) # Protocol
        # strToSendStatistics.append(dev[3])
        # strToSendStatistics.append(bat[2])
        # strToSendStatistics.append(bat[3])
        strToSendStatistics.append(globalVars.longitude[3]) # Gateway Longitude
        strToSendStatistics.append(globalVars.longitude[2]) # Gateway Longitude
        strToSendStatistics.append(globalVars.longitude[1]) # Gateway Longitude
        strToSendStatistics.append(globalVars.longitude[0]) # Gateway Longitude
        strToSendStatistics.append(globalVars.latitude[3])  # Gateway Latitude  
        strToSendStatistics.append(globalVars.latitude[2])  # Gateway Latitude 
        strToSendStatistics.append(globalVars.latitude[1])  # Gateway Latitude 
        strToSendStatistics.append(globalVars.latitude[0])  # Gateway Latitude 
        strToSendStatistics.append(st_gps_stats[3]) # Gateway GPS Status & Report type HARDCODE
        strToSendStatistics.append(st_bat[3])
        #TODO Get Accel X, Y, Z 
        accel = acc.acceleration()
        accel_x = round(accel[0]*100)
        accel_y = round(accel[1]*100)
        accel_z = round(accel[2]*100)
        tools.debug("Acceleration X: " + str(accel_x) + " - Y: " + str(accel_y) + " - Z: " + str(accel_z),"v")
        if accel_x > 255: 
            accel_x = 255
        if accel_y > 255: 
            accel_y = 255
        if accel_z > 255: 
            accel_z = 255
        strToSendStatistics.append(struct.pack(">I", accel_x)[3]) # Accel X
        strToSendStatistics.append(struct.pack(">I", accel_y)[3]) # Accel Y
        strToSendStatistics.append(struct.pack(">I", accel_z)[3]) # Accel Z
        strToSendStatistics.append(dt[0])
        strToSendStatistics.append(dt[1])
        strToSendStatistics.append(dt[2])
        strToSendStatistics.append(dt[3])
        strToSendStatistics.append(whiteLen[2])
        strToSendStatistics.append(whiteLen[3])
        # strToSendStatistics.append(sentLen[2])
        # strToSendStatistics.append(sentLen[3])
        tools.debug("Step 7 - Creating statistics report: " + str(strToSendStatistics) + " Battery: " + str(st_bat[3]),'v')
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
            arrToSend = []
            arrToSend.append(Device(addr="stats", raw=statSend))
            lorawan.sendLoRaWANMessage(arrToSend)
            tools.debug("Sending statistics report step 3", 'vv')
           
    except Exception as e:
        checkError("Error sending statistics report: " + str(e))

def getGPS():
    try:
        
        l76 = L76GNSS(py)
        rtc = machine.RTC()
        coord = dict(latitude=None, longitude=None)
        # coord = l76.coordinates_v2(debug=False)
        if globalVars.gps_enabled == True:
            coord = l76.get_location(debug=False, tout=globalVars.gps_timeout)
        print("COORD BACKUP: " + str(coord))    
        if coord['latitude'] is not '' and coord['longitude'] is not '':
        # if coord[0] is not None and coord[1] is not None:
            big_endian_latitude = bytearray(struct.pack(">I", int(coord['latitude']*1000000)))  
            big_endian_longitude = bytearray(struct.pack(">I", int(coord['longitude']*1000000))) 
            # big_endian_latitude = bytearray(struct.pack("f", coord[0]))  
            # big_endian_longitude = bytearray(struct.pack("f", coord[1]))  
            # print([ "0x%02x" % b for b in big_endian_latitude ])
            dt = l76.getUTCDateTimeTuple(debug=True)
            if dt is not None:
                rtc.init(dt)
            tools.debug("BigEndianLatitude: " + str(big_endian_latitude) + " - BigEndianLongitude: " + str(big_endian_longitude) + "Latitude: " + str(coord['latitude']) + " - Longitude: " + str(coord['longitude']) + " - Timestamp: " + str(dt),'v')
            # tools.debug("Latitude: " + str(coord[0]) + " - Longitude: " + str(coord[1]) + " - Timestamp: " + str(dt),'v')
            # l76.enterStandBy(debug=False)
            return big_endian_latitude, big_endian_longitude
        else:
            return None,None
    except Exception as e:
        checkError("Error getting GPS: " + str(e))
        return None,None