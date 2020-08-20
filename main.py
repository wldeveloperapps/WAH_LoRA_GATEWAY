from network import Bluetooth
from lib.beacon import Device
from errorissuer import checkError
from scheduler import Scheduler
import rtcmgt
import machine
import ubinascii
import utime
import pycom
import wilocMain
import tools
import globalVars
import lorawan
import _thread


# -------------------------
scanned_frames = []
mac_scanned = []
statSend = []
pkgSend = []
# -------------------------



def sleepProcess():
    try:
        tools.debug("Step 8 - Going to sleep",'v')
        wilocMain.feedWatchdog()
        globalVars.mac_scanned[:]=[]
        globalVars.scanned_frames[:]=[]
        tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except Exception as e:
        checkError("Error going to light sleep: " + str(e)) 

def bluetooth_scanner():
    try:
        bluetooth = Bluetooth()
        while True:
            try:
                tools.debug('Step 1 - Starting BLE scanner, RSSI: ' + str(int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256) + " - RTC: " + str(int(utime.time())) + " - REFRESH: " + str(globalVars.MAX_REFRESH_TIME) + " - SCAN: " + str(int(globalVars.BLE_SCAN_PERIOD)) + " - SLEEP: " + str(int(globalVars.STANDBY_PERIOD)) + " - DEBUG: " + str(globalVars.debug_cc) ,'v')
                bluetooth = Bluetooth()
                bluetooth.start_scan(int(globalVars.BLE_SCAN_PERIOD))
                while bluetooth.isscanning():
                    adv = bluetooth.get_adv()
                    if adv:
                        if 'WILOC_01' in str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)):
                            data_raw = str(ubinascii.hexlify(adv.data))
                            tools.debug('Name: '+ str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)) +' MAC: '+ str(ubinascii.hexlify(adv.mac))+ ' RSSI: ' + str(adv.rssi) + ' DT: '+ str(int(utime.time())) +' RAW: ' + data_raw,'vvv')
                            if adv.mac not in globalVars.mac_scanned:
                                tools.debug('Step 1 - New device detected: ' + str(ubinascii.hexlify(adv.mac)),'vv')
                                globalVars.mac_scanned.append(adv.mac)
                            if adv.rssi >= (int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256):  
                                wilocMain.checkWhiteList(str(ubinascii.hexlify(adv.mac).decode('utf-8')))
                            globalVars.scanned_frames.append(Device(addr=adv.mac,rssi=adv.rssi, raw=data_raw))

                tools.debug('Step 1 - Stopping BLE scanner ' + str(int(utime.time())) + " - Devices: " + str(len(globalVars.mac_scanned)) + " - Packages: " + str(len(globalVars.scanned_frames)),'v')
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
            except Exception as ee:
                checkError("Bluetooth thread error: " + str(ee))
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except Exception as e:
        checkError("Error scanning Bluetooth " + str(e)) 
        machine.reset()

try:
    rtcmgt.initRTC()
    tools.debug("Step 0 - Starting Main program on " + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8')) + ' - Time: ' + str((int(utime.time()))),'v')
    pycom.nvs_set('laststatsreport', str(0)) # Force a statistics report on every reset
    sched = Scheduler()
    sched.start()
    wilocMain.forceConfigParameters()
    wilocMain.loadConfigParameters()
    wilocMain.loadSDCardData()
    lorawan.join_lora()
    _thread.start_new_thread(bluetooth_scanner,())
    while True:
        try:
            rtcmgt.updateRTC()
            tools.sleepWiloc(int(globalVars.BLE_SCAN_PERIOD))
            if len(globalVars.scanned_frames) > 0:
                dummy_list = wilocMain.rssiFilterDevices(globalVars.RSSI_NEAR_THRESHOLD,globalVars.mac_scanned, globalVars.scanned_frames)
                # print("Step 1")
                if len(dummy_list) > 0:
                    # print("Step 1.1")
                    sentDevices = wilocMain.checkTimeToAddDevices(dummy_list, globalVars.MAX_REFRESH_TIME)
                    # print("Step 1.2")
                    if len(sentDevices) > 0:
                        pkgSend = wilocMain.createPackageToSend(sentDevices, globalVars.scanned_frames)
                        if len(pkgSend) > 0:
                            wilocMain.manage_devices_send(pkgSend)
            # print("Step 2")
            if wilocMain.checkTimeForStatistics(globalVars.STATISTICS_REPORT_INTERVAL) == True:
                pycom.nvs_set('laststatsreport', str(int(utime.time())))
                statSend = wilocMain.createStatisticsReport()
                wilocMain.manage_devices_send(statSend)
            
            # print("Step 3")
            if wilocMain.checkTimeToSend(globalVars.SENT_PERIOD) == True:
                if len(globalVars.lora_sent_devices) > 0:
                    lorawan.sendLoRaWANMessage(globalVars.lora_sent_devices)

            sched.checkNextReset()
            sleepProcess()
        except Exception as eee:
            checkError("Main thread error: " + str(eee))
            sleepProcess()

except Exception as e:
    checkError("Main Error: " + str(e))
    pycom.nvs_set('rtc', str(int(utime.time())))
    utime.sleep(1)
    machine.reset()