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
import sys
from uio import StringIO

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
wdt = WDT(timeout=360000)
# ---------------

strError = []
s = StringIO()
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
        tools.debug("Step 2 - Filtering RSSI, Threshold: " + str(thrs) + " - Devices: " + str(len(macs)) + " - Records: " + str(len(frames)), 'v')
        for scanDev in macs:
            ret = calculateRssiAvg(scanDev, frames)
            #if int(ret[0]) >= int(thrs):
            if int(ret[3]) >= globalVars.BUZZER_COUNTER_ALARM:
                tools.debug("Step 2.1 - Adding device to RSSI Filter list " + str(ubinascii.hexlify(scanDev)) + " Distance: Close " + " RSSI: " + str(int(ret[0])) + " Samples: " + str(ret[1]) + " - Up Threshold: " + str(ret[2]) + " - Down Threshold: " + str(ret[3]) + " DT: " + str(int(utime.time())), 'vv')
                rssi_filter_devices.append(DeviceFilter(str(ubinascii.hexlify(scanDev).decode('utf-8')), ret[0], ret[1], int(utime.time()), scanDev))
            elif int(ret[0]) < int(thrs):
                tools.debug("Step 2.1 - Not sending device " + str(ubinascii.hexlify(scanDev)) + " Distance: Far " + " RSSI: " + str(ret[0]) + " Samples: " + str(ret[1]) + " - Up Threshold: " + str(ret[2]) + " - Down Threshold: " + str(ret[3]) + " DT: " + str(int(utime.time())), 'vv')
        return rssi_filter_devices
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Step 2 - Error filtering RSSI: " + str(s.getvalue()))
        return []

def calculateRssiAvg(device, frames):
    try:
        rssi_acc = 0
        rssi_average = 0
        samples = 0
        upthres = 0
        downthres = 0
        for dev in frames:
            if device in dev.addr:
                samples += 1
                rssi_acc += dev.rssi
                if int(dev.rssi) >= (int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256):
                    downthres += 1
                else:
                    upthres += 1
        if samples > 0:
            rssi_average = rssi_acc / samples
        else: 
            rssi_average = -120
 
        # tools.debug("Step 2.2 ------- Device: " + str(ubinascii.hexlify(device).decode('utf-8')) + " - RSSI Avg: " + str(rssi_average) + " - Samples: " + str(samples) + " - Up Threshold: " + str(upthres) + " - Down Threshold: " + str(downthres),'vv')
        return rssi_average, samples, upthres, downthres
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error calculating RSSI Avg: " + str(s.getvalue())) 
        return []

def getBatteryLevel(py):
    try:
        battery = py.read_battery_voltage()
        acc_bat = int(round(battery*1000))
        tools.debug("Battery Level: " + str(acc_bat),'vv')
        return acc_bat
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error getting battery level, " + str(s.getvalue())) 
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
        
        loadLastValidPosition()

    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Step 0 - Error load SD Card information: " + str(s.getvalue())) 
        # strError.append('10')

def forceConfigParameters():
    try:
        pycom.nvs_set('blescanperiod', globalVars.BLE_SCAN_PERIOD)
        pycom.nvs_set('maxrefreshtime', globalVars.MAX_REFRESH_TIME)
        pycom.nvs_set('standbyperiod', globalVars.STANDBY_PERIOD)
        pycom.nvs_set('rssithreshold', str(globalVars.RSSI_NEAR_THRESHOLD))
        pycom.nvs_set('buzzerduration', globalVars.BUZZER_DURATION)
        pycom.nvs_set('statsinterval', globalVars.STATISTICS_REPORT_INTERVAL)
        pycom.nvs_set('lorasentperiod', globalVars.SENT_PERIOD)
        pycom.nvs_set('buzcountalarm', globalVars.BUZZER_COUNTER_ALARM)
        utime.sleep(2)
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error forcing configuration parameters: " + str(s.getvalue())) 

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
            pycom.nvs_set('buzzerduration', str(globalVars.BUZZER_DURATION))
            checkError("BUZZER_DURATION error")
        
        try:
            globalVars.STATISTICS_REPORT_INTERVAL = pycom.nvs_get('statsinterval')
            tools.debug("Step 0.5 - STATISTICS_REPORT_INTERVAL: " + str(globalVars.STATISTICS_REPORT_INTERVAL),'v')
        except Exception:
            pycom.nvs_set('statsinterval', globalVars.STATISTICS_REPORT_INTERVAL)
            checkError("STATISTICS_REPORT_INTERVAL error")

        try:
            globalVars.SENT_PERIOD = pycom.nvs_get('lorasentperiod')
            tools.debug("Step 0.5 - SENT_PERIOD: " + str(globalVars.SENT_PERIOD),'v')
        except Exception:
            pycom.nvs_set('lorasentperiod', globalVars.SENT_PERIOD)
            checkError("SENT_PERIOD error")
    
        try:
            globalVars.BUZZER_COUNTER_ALARM = pycom.nvs_get('buzcountalarm')
            tools.debug("Step 0.5 - BUZZER_COUNTER_ALARM: " + str(globalVars.BUZZER_COUNTER_ALARM),'v')
        except Exception:
            pycom.nvs_set('buzcountalarm', globalVars.BUZZER_COUNTER_ALARM)
            checkError("BUZZER_COUNTER_ALARM error")
        
    except BaseException as e1:
        err = sys.print_exception(e1, s)
        checkError("Step 18 - Error loading config parameters: " + str(s.getvalue())) 

def checkWhiteList(dev):
    try:
        if dev not in globalVars.devices_whitelist:
            tools.debug("Step 1.1 - Device not found in the Whitelist: " + str(dev),'vvv')
            if str(globalVars.debug_cc).count('v') <= 3:
                BeepBuzzer(0.1)
        else:
            tools.debug("Step 1.1 - Device found in Whitelist: " + str(dev),'vvv')
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error checking whitelist level, " + str(s.getvalue()))

def checkTimeToAddDevices(devs, MAX_REFRESH_TIME):
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
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error checking time to send data: " + str(s.getvalue()))
        return []

def createPackageToSend(devs, frames):
    global py
    try:
        # CommandID - Latitude - Longitude - GPS/REP - Battery - MACDevice - LatitudeDevice - LongitudeDevice
        # tools.debug("Step 4 - Creating messages to send, Devs: " + str(devs),'v')
        devicesToSend = []
        for dd in devs:
            
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
            dev_gps_stats = 0
            gps_flag = True
            for fr in frames:
                # print("FRAMES: " + str(ubinascii.hexlify(fr.addr).decode('utf-8')) + " - DD: " + str(dd.addr) + " - FR: " + str(fr.raw))
                if str(ubinascii.hexlify(fr.addr).decode('utf-8')) == dd.addr:
                    if len(fr.raw) > 36:
                        last_frame = str(fr.raw)[12:36]
            if len(last_frame) > 22:
                last_lat = last_frame[12:20]
                last_lon = last_frame[4:12]
                dev_gps_stats = int(last_frame[20:22],16)

            if int(last_lon[0]+last_lon[1],16) == 0 and int(last_lon[2]+last_lon[3],16) == 0 and int(last_lon[4]+last_lon[5],16) == 0 and int(last_lon[6]+last_lon[7],16) == 0:
                gps_flag = False
            if dev_gps_stats < 64:
                gps_flag = False

            if gps_flag == False:
                tools.debug("----- Device with NO GPS -----","vvv")
                strToSend.append(globalVars.longitude[3]) # Gateway Longitude
                strToSend.append(globalVars.longitude[2]) # Gateway Longitude
                strToSend.append(globalVars.longitude[1]) # Gateway Longitude
                strToSend.append(globalVars.longitude[0]) # Gateway Longitude
                strToSend.append(globalVars.latitude[3]) # Gateway Latitude 
                strToSend.append(globalVars.latitude[2]) # Gateway Latitude 
                strToSend.append(globalVars.latitude[1]) # Gateway Latitude 
                strToSend.append(globalVars.latitude[0]) # Gateway Latitude 
            else:
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
            tools.debug("Creating package to send of device: " + str(dd.addr) + " - Batt: " + str(bat) + " - GPS From: " + str('Device' if gps_flag == True else 'Campanolo'),'v')
        return devicesToSend
    except BaseException as e1:
        err = sys.print_exception(e1, s)
        checkError("Step 5 - Error creating package to send: " + str(s.getvalue()))
        # strError.append('1')
        return []

def feedWatchdog():
    global wdt
    try:
        wdt.feed()
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error feeding watchdog: " + str(s.getvalue()))

def ForceBuzzerSound(duration):
    try:
        BeepBuzzer(duration)
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error forcing buzzer: " + str(s.getvalue()))

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
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error checking time for statistics: " + str(s.getvalue()))
        return False

def createStatisticsReport():
    try:
        strToSendStatistics = []
        statsToSend = []
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
                loadLastValidPosition()
            else:
                lat_st = str(globalVars.latitude[0]) + "," + str(globalVars.latitude[1]) + "," + str(globalVars.latitude[2]) + "," + str(globalVars.latitude[3])
                lon_st = str(globalVars.longitude[0]) + "," + str(globalVars.longitude[1]) + "," + str(globalVars.longitude[2]) + "," + str(globalVars.longitude[3])
                pycom.nvs_set('last_lat', lat_st)
                pycom.nvs_set('last_lon', lon_st)

        bat = tools.getBatteryPercentage(int(round(py.read_battery_voltage()*1000)))
        st_bat = struct.pack(">I", bat)
        dt = struct.pack(">I", utime.time())
        whiteLen = struct.pack(">I", len(globalVars.devices_whitelist))
        gps_stats = 67
        st_gps_stats = struct.pack(">I", gps_stats)
        # sentLen = struct.pack(">I", len(globalVars.device_sent))
        strToSendStatistics.append(struct.pack(">I", 11)[3]) # Protocol
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
        tools.debug("Step 7 - Creating statistics report: " + str(strToSendStatistics) + " Battery: " + str(st_bat[3]),'v')
        statsToSend.append(Device(addr="stats",raw=strToSendStatistics))
        manage_devices_send(statsToSend)
        return statsToSend
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error creating statistics report: " + str(s.getvalue()))
        # strError.append('19')
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
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error sending statistics report: " + str(s.getvalue()))

def loadLastValidPosition():
    try:
        dummy_lat = pycom.nvs_get('last_lat')
        globalVars.latitude = tuple(map(int, dummy_lat.split(','))) 
        tools.debug("Getting latitude from FLASH: " + str(globalVars.latitude),'v')
    except Exception:
        checkError("Error getting Latitude") 
        globalVars.latitude = struct.pack(">I", 0)
    
    try:
        dummy_lon = pycom.nvs_get('last_lon')
        globalVars.longitude = tuple(map(int, dummy_lon.split(','))) 
        tools.debug("Getting longitude from FLASH: " + str(globalVars.longitude),'v')
    except Exception:
        checkError("Error getting Longitude") 
        globalVars.longitude = struct.pack(">I", 0)

def getGPS():
    try:
        l76 = L76GNSS(py)
        rtc = machine.RTC()
        coord = dict(latitude=None, longitude=None)
        if globalVars.gps_enabled == True:
            coord = l76.get_location(debug=False, tout=globalVars.gps_timeout)
        if coord['latitude'] is not '' and coord['longitude'] is not '':
            tools.haversine(coord['latitude'], coord['longitude'], globalVars.last_lat_tmp, globalVars.last_lon_tmp)
            big_endian_latitude = bytearray(struct.pack(">I", int(coord['latitude']*1000000)))  
            big_endian_longitude = bytearray(struct.pack(">I", int(coord['longitude']*1000000))) 
            dt = l76.getUTCDateTimeTuple(debug=True)
            if dt is not None:
                rtc.init(dt)
            tools.debug("HDOP: " + str(coord['HDOP']) + "Latitude: " + str(coord['latitude']) + " - Longitude: " + str(coord['longitude']) + " - Timestamp: " + str(dt),'v')
            if float(str(coord['HDOP'])) > float(globalVars.min_hdop):
                return None,None
            else:
                globalVars.last_lat_tmp =  coord['latitude']
                globalVars.last_lon_tmp =  coord['longitude']
                return big_endian_latitude, big_endian_longitude
        else:
            return None,None
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error getting GPS: " + str(s.getvalue()))
        return None,None

def checkTimeToSend(interval):
    try:
        ts = int(utime.time())
        if (globalVars.last_lora_sent + int(interval)) < ts: 
            globalVars.last_lora_sent = ts
            return True
        else:
            tools.debug("LoRaWAN Sent - Remaining time: " + str(((globalVars.last_lora_sent + int(interval)) - ts)) + " - Store devices: " + str(len(globalVars.lora_sent_devices)),"v")
            return False
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error checking time to send by LoRa: " + str(s.getvalue()))
        return False

def manage_devices_send(dev_list):
    try:
        for dd1 in dev_list:
            exists = False
            for dd2 in globalVars.lora_sent_devices:
                # print("Dev1: " + str(dd1.addr) + " - Dev2: " + str(dd2.addr))
                if str(dd1.addr) == str(dd2.addr):
                    # print("Device already exist: " + str(dd1.addr))
                    exists = True
            if exists == False:
                globalVars.lora_sent_devices.append(dd1)
                # print("Adding device to sent list: " + str(dd1.addr))

        tools.debug("LoRaWAN Stored records to send: " + str(len(globalVars.lora_sent_devices)),"vvv")
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error managing devices to send: " + str(s.getvalue()))

def sleepProcess():
    global gc
    try:
        tools.debug("Step 8 - Going to sleep",'v')
        feedWatchdog()
        gc.collect()
        globalVars.mac_scanned[:]=[]
        globalVars.scanned_frames[:]=[]
        tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error going to light sleep: " + str(s.getvalue()))