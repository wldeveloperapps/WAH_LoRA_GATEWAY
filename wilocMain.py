from lib.whitelistTools import WhiteListGetDevices
from lib.blacklistTools import BlackListGetDevices
from lib.loRaReportsTools import LoRaWANListSentDevices, LoRaWANSentListUpdateDevice
from lib.buzzerTools import BeepBuzzer
from lib.beacon import Device, DeviceFilter
from errorissuer import checkError, checkWarning
import ubinascii
import utime
import machine
import os
import tools
import struct
import pycom
import globalVars
import lorawan
import _thread
import rtcmgt

# ---------- TODO -------------
#  Sleep schedule by RTC syncronization by GPS
#  Blacklist development
#  Modify buzzer intensity with an ADC output


def rssiFilterDevices(RSSI_NEAR_THRESHOLD, macs, frames):
    try:
        
        rssi_filter_devices = []
        thrs = int(RSSI_NEAR_THRESHOLD,16) - 256
        tools.debug("Step 2 - Filtering RSSI, Threshold: " + str(thrs) + " - Devices: " + str(len(macs)) + " - Records: " + str(len(frames)), 'vv')
        for scanDev in macs:
            ret = calculateRssiAvg(scanDev, frames)
            #if int(ret[0]) >= int(thrs):
            if int(ret[3]) >= globalVars.BUZZER_COUNTER_ALARM:
                tools.debug("Step 2.1 - Adding device to RSSI Filter list " + str(scanDev) + " Distance: Close " + " RSSI: " + str(int(ret[0])) + " Samples: " + str(ret[1]) + " - Up Threshold: " + str(ret[2]) + " - Down Threshold: " + str(ret[3]) + " DT: " + str(int(utime.time())), 'vv')
                rssi_filter_devices.append(DeviceFilter(scanDev, ret[0], ret[1], int(utime.time()), scanDev))
            elif int(ret[0]) < int(thrs):
                tools.debug("Step 2.1 - Not sending device " + str(scanDev) + " Distance: Far " + " RSSI: " + str(ret[0]) + " Samples: " + str(ret[1]) + " - Up Threshold: " + str(ret[2]) + " - Down Threshold: " + str(ret[3]) + " DT: " + str(int(utime.time())), 'vv')
        return rssi_filter_devices
    except BaseException as e:
        checkError("Step 2 - Error filtering RSSI", e)
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
        checkError("Error calculating RSSI Avg", e) 
        return []

def loadSDCardData():
    try:
        ret = WhiteListGetDevices() 
        if ret[0] == 1:
            globalVars.devices_whitelist = ret[1]
        else:
            tools.debug("Step 0 - Error Getting whitelist: " +str(ret[1]), "vv")

        ret = BlackListGetDevices() 
        if ret[0] == 1:
            globalVars.devices_blacklist = ret[1]
        else:
            tools.debug("Step 0 - Error Getting blacklist: " + str(ret[1]), "vv")

        sent = LoRaWANListSentDevices() 
        if sent[0] == 1:
            # print("Step 0 - Getting LoRaWAN Sent list")
            globalVars.device_sent = sent[1]
        else:
            tools.debug("Step 0 - Error Getting LoRaWAN Sent devices list: " + str(sent[1]), "vv")
        
        loadLastValidPosition()

    except BaseException as e:
        checkError("Step 0 - Error load SD Card information", e)

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
        pycom.nvs_set('alarmlisttype', globalVars.ALARM_LIST_TYPE)
        utime.sleep(2)
    except BaseException as e:
        checkError("Error forcing configuration parameters", e) 

def checkListType(dev, listType):
    try:
        if listType == 1:
            if dev not in globalVars.devices_whitelist:
                tools.debug("Step 1.1 - Device not found in the Whitelist: " + str(dev),'vvv')
                BeepBuzzer(0.1)
            else:
                tools.debug("Step 1.1 - Device found in Whitelist: " + str(dev),'vvv')
        elif listType == 2:
            if dev in globalVars.devices_blacklist:
                tools.debug("Step 1.1 - Device found in the Blacklist: " + str(dev),'vvv')
                BeepBuzzer(0.1)
            else:
                tools.debug("Step 1.1 - Device not found in Blacklist: " + str(dev),'vvv')
    except BaseException as e:
        checkError("Error checking whitelist level", e)

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
                    tools.debug("Step 3 - Waiting for the device " + str(dmDev.addr) + " to send again - Remaining time: " + str(((dmDev.timestamp + int(MAX_REFRESH_TIME)) - ts)),'vv')
            else:
                ret_devices.append(dev)
        
        return ret_devices
    except BaseException as e:
        checkError("Error checking time to send data", e)
        return []

def createPackageToSend(devs, frames):
    try:
        # CommandID - Latitude - Longitude - GPS/REP - Battery - MACDevice - LatitudeDevice - LongitudeDevice
        # tools.debug("Step 4 - Creating messages to send, Devs: " + str(devs),'v')
        devicesToSend = []
        for dd in devs:
            
            strToSend = []
            gps_stats = 66
            bat = tools.getBatteryPercentage()
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
            
            mac_proc = [dd.addr[i:i+2] for i in range(0, len(dd.addr), 2)]
            tools.debug("Getting MAC bytes of : " + str(mac_proc) ,'vvv')
            for bmac in mac_proc:
                strToSend.append(int(bmac,16))
            # tools.debug("Getting last location of : " + str(dd.addr),'vv')
            last_frame = ""
            last_lat = "00000000"
            last_lon = "00000000"
            dev_gps_stats = 0
            gps_flag = True
            for fr in frames:
                # print("FRAMES: " + str(ubinascii.hexlify(fr.addr).decode('utf-8')) + " - DD: " + str(dd.addr) + " - FR: " + str(fr.raw))
                if str(fr.addr) == str(dd.addr):
                    if len(fr.raw) > 36:
                        last_frame = str(fr.raw)[12:36]
            if len(last_frame) > 22:
                last_lat = last_frame[10:18]
                last_lon = last_frame[2:10]
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
            tools.debug("Step 5 - Creating package to send of device: " + str(dd.addr) + " - Batt: " + str(bat) + " - GPS From: " + str('Device' if gps_flag == True else 'Campanolo'),'v')
        return devicesToSend
    except BaseException as e1:
        checkError("Step 5 - Error creating package to send", e1)
        return []

def checkTimeForStatistics(INTERVAL):
    try:
        tools.debug("Step 6 - Checking time for statistics",'vvv')
        ts = int(utime.time())

        try:
            last_report = pycom.nvs_get('laststatsreport')
        except Exception:
            pycom.nvs_set('laststatsreport', str(ts))
            last_report = ts
 
        if (int(last_report) + int(INTERVAL)) < ts and globalVars.flag_gps_running == False:
            globalVars.flag_gps_running = True
            pycom.nvs_set('laststatsreport', str(ts))
            rtcmgt.updateRTC()
            return True
        else:
            tools.debug("STATS - No statistics reports yet, WhiteList: " + str(len(globalVars.devices_whitelist)) + " - BlackList: " + str(len(globalVars.devices_blacklist)) +" - remaining: " + str(((int(last_report) + int(INTERVAL)) - ts)),'v')
            return False
    except BaseException as e:
        checkError("Error checking time for statistics", e)
        return False

def createStatisticsReport():
    try:
        strToSendStatistics = []
        statsToSend = []
        if globalVars.deviceID == 1:
            temperature = 0
            altitude = 0
            temperature = si.temperature()
            humidity = si.humidity()
            acc_tmp = int(round(temperature))
            acc_hum = int(round(humidity))
            lat =  struct.pack(">I", acc_tmp)
            lon =  struct.pack(">I", acc_hum)
        elif globalVars.deviceID == 2:
            tools.debug("GPS - Starting GPS acquisition",'v')
            globalVars.latitude, globalVars.longitude = tools.getGPS()
            if globalVars.latitude is None or globalVars.longitude is None:
                loadLastValidPosition()
            else:
                lat_st = str(globalVars.latitude[0]) + "," + str(globalVars.latitude[1]) + "," + str(globalVars.latitude[2]) + "," + str(globalVars.latitude[3])
                lon_st = str(globalVars.longitude[0]) + "," + str(globalVars.longitude[1]) + "," + str(globalVars.longitude[2]) + "," + str(globalVars.longitude[3])
                pycom.nvs_set('last_lat', lat_st)
                pycom.nvs_set('last_lon', lon_st)

        bat = tools.getBatteryPercentage()
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
        accel = tools.getAccelerometer()
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
        globalVars.flag_gps_running = False
        globalVars.lora_sent_stats.append(Device(addr="stats",raw=strToSendStatistics))
        # return statsToSend
    except BaseException as e:
        checkError("Error creating statistics report", e)
        # strError.append('19')
        return []

def checkLowBattery():
    try:
        
        batt = tools.getBatteryPercentage()
        tools.debug("Step 6 - Checking battery voltage: " + str(batt) + "%", "v")
        if batt < globalVars.LOW_BATTERY_VOLTAGE:
            globalVars.indicatorFrequencyOn = 2
            globalVars.indicatorFrequencyOff = 30
            return True
        else:
            globalVars.indicatorFrequencyOn = 100
            globalVars.indicatorFrequencyOff = 0
            return False

        
    except BaseException as e:
        checkError("Error going to light sleep",e)

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

def checkTimeToSend(interval):
    try:
        ts = int(utime.time())
        if (globalVars.last_lora_sent + int(interval)) < ts: 
            globalVars.last_lora_sent = ts
            rtcmgt.updateRTC()
            checkLowBattery()
            return True
        else:
            tools.debug("LoRaWAN - Remaining time to send: " + str(((globalVars.last_lora_sent + int(interval)) - ts)) 
            + " - Store devices: " + str(len(globalVars.lora_sent_devices)) 
            + " - Stats: " + str(len(globalVars.lora_sent_stats))
            + " - ACKs: " + str(len(globalVars.lora_sent_acks)),"v")
            return False
    except BaseException as e:
        checkError("Error checking time to send by LoRa", e)
        return False


