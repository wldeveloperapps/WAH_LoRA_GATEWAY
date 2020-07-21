from network import Bluetooth
import _thread
import machine
import ubinascii
import utime
import pycom
from lib.beacon import Beacon
from lib.rtcmgt import initRTC
import gc
import wilocMain
import tools
import globalVars
import lorawan
from errorissuer import checkError
# -------------------------
MAX_REFRESH_TIME = 300 # Code 20
BLE_SCAN_PERIOD = 7 # Code 21
STANDBY_PERIOD = 2 # Code 22
RSSI_NEAR_THRESHOLD = 'b5' # Code 23
STATISTICS_REPORT_INTERVAL = 1800 # Code 24
BUZZER_DURATION = 1 # Code 25

# -------------------------
scanned_frames = []
mac_scanned = []
statSend = []
pkgSend = []
# -------------------------

def loadConfigParameters():
    global BLE_SCAN_PERIOD
    global MAX_REFRESH_TIME
    global STANDBY_PERIOD
    global RSSI_NEAR_THRESHOLD
    global STATISTICS_REPORT_INTERVAL
    global BUZZER_DURATION
    try:
        try:
            BLE_SCAN_PERIOD = pycom.nvs_get('blescanperiod')
            tools.debug("Step 0.5 - BLE_SCAN_PERIOD: " + str(BLE_SCAN_PERIOD),'v')
        except Exception:
            pycom.nvs_set('blescanperiod', BLE_SCAN_PERIOD)
            checkError("BLE_SCAN_PERIOD error")

        try:
            MAX_REFRESH_TIME = pycom.nvs_get('maxrefreshtime')
            tools.debug("Step 0.5 - MAX_REFRESH_TIME: " + str(MAX_REFRESH_TIME),'v')
        except Exception:
            pycom.nvs_set('maxrefreshtime', MAX_REFRESH_TIME)
            checkError("MAX_REFRESH_TIME error") 
        try:
            STANDBY_PERIOD = pycom.nvs_get('standbyperiod')
            tools.debug("Step 0.5 - STANDBY_PERIOD: " + str(STANDBY_PERIOD),'v')
        except Exception:
            pycom.nvs_set('standbyperiod', STANDBY_PERIOD)
            checkError("STANDBY_PERIOD error")

        try:
            RSSI_NEAR_THRESHOLD = pycom.nvs_get('rssithreshold')
            tools.debug("Step 0.5 - RSSI_NEAR_THRESHOLD: " + str(int(RSSI_NEAR_THRESHOLD,16) - 256),'v')
        except Exception:
            pycom.nvs_set('rssithreshold', str(RSSI_NEAR_THRESHOLD))
            checkError("RSSI_NEAR_THRESHOLD error")

        try:
            BUZZER_DURATION = pycom.nvs_get('buzzerduration')
            tools.debug("Step 0.5 - BUZZER_DURATION: " + str(BUZZER_DURATION),'v')
        except Exception:
            pycom.nvs_set('buzzerduration', BUZZER_DURATION)
            checkError("BUZZER_DURATION error")
        
        try:
            STATISTICS_REPORT_INTERVAL = pycom.nvs_get('statsinterval')
            # STATISTICS_REPORT_INTERVAL = 60 # Force parameter value
            tools.debug("Step 0.5 - STATISTICS_REPORT_INTERVAL: " + str(STATISTICS_REPORT_INTERVAL),'v')
        except Exception:
            pycom.nvs_set('statsinterval', STATISTICS_REPORT_INTERVAL)
            checkError("STATISTICS_REPORT_INTERVAL error")
        
    except Exception as e1:
        checkError("Step 18 - Error loading config parameters: " + str(e1)) 

def sleepProcess():
    global STANDBY_PERIOD
    try:
        tools.debug("Step 8 - Going to sleep",'v')
        gc.collect()
        wilocMain.feedWatchdog()
        mac_scanned[:]=[]
        scanned_frames[:]=[]
        pycom.nvs_set('rtc', str(int(utime.time())))
        tools.sleepWiloc(int(STANDBY_PERIOD))
    except Exception as e:
        checkError("Error going to light sleep: " + str(e)) 

try:
    initRTC()
    tools.debug("Step 0 - Starting Main program on " + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8')) + ' - Time: ' + str((int(utime.time()))),'v')
    pycom.nvs_set('laststatsreport', str(0)) # Force a statistics report on every reset
    # pycom.nvs_set('statsinterval', '60')
    loadConfigParameters()
    wilocMain.loadSDCardData()
    lorawan.join_lora()
    bluetooth = Bluetooth()
    while True:
        tools.debug('Step 1 - Starting BLE scanner ' + str(int(utime.time())),'v')
        bluetooth.start_scan(int(BLE_SCAN_PERIOD))
        wilocMain.feedWatchdog()
        while bluetooth.isscanning():
            adv = bluetooth.get_adv()
            if adv:
                if 'WILOC_' in str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)):
                    tools.debug('Name: '+ str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)) +' MAC: '+ str(ubinascii.hexlify(adv.mac))+ ' RSSI: ' + str(adv.rssi) + ' DT: '+ str(int(utime.time())) +' RAW: ' + str(ubinascii.hexlify(adv.data)),'vvv')
                    if adv.mac not in mac_scanned:
                        tools.debug('Step 1 - New device detected: ' + str(ubinascii.hexlify(adv.mac)),'vv')
                        mac_scanned.append(adv.mac)
                    if adv.rssi >= (int(RSSI_NEAR_THRESHOLD,16) - 256):  
                        wilocMain.checkWhiteList(str(ubinascii.hexlify(adv.mac).decode('utf-8')))
                    scanned_frames.append(Beacon(adv.mac,adv.rssi,None,None,None,None))
        
        tools.debug('Step 1 - Stopping BLE scanner ' + str(int(utime.time())) + " - Devices: " + str(len(mac_scanned)) + " - Packages: " + str(len(scanned_frames)),'v')
        wilocMain.feedWatchdog()
        if len(scanned_frames) > 0:
            dummy_list = wilocMain.rssiFilterDevices(RSSI_NEAR_THRESHOLD,mac_scanned, scanned_frames)
            if len(dummy_list) > 0:
                sentDevices = wilocMain.checkTimeToSend(dummy_list, MAX_REFRESH_TIME)
                if len(sentDevices) > 0:
                    pkgSend = wilocMain.createPackageToSend(sentDevices)
                    if len(pkgSend) > 0:
                        lorawan.sendLoRaWANMessage(pkgSend)
                    else:
                        tools.debug("Step 2 - No package created",'vvv')
                else:
                    tools.debug("Step 2 - No devices to send",'vvv')
            else:
                tools.debug("Step 2 - There are no devices with the right RSSI Threshold",'vvv')
        else:
            tools.debug("Step 2 - There are not devices scanned",'vvv')
        
        if wilocMain.checkTimeForStatistics(STATISTICS_REPORT_INTERVAL) == True:
            statSend = wilocMain.createStatisticsReport()
            if len(statSend) > 0:
                lorawan.sendLoRaWANMessage(statSend)
                pycom.nvs_set('laststatsreport', str(int(utime.time())))

        sleepProcess()

except Exception as e:
    checkError("Main Error: " + str(e))
    pycom.nvs_set('rtc', str(int(utime.time())))
    machine.reset()