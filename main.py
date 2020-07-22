from network import Bluetooth
from lib.beacon import Beacon
from lib.rtcmgt import initRTC
from errorissuer import checkError
import machine
import ubinascii
import utime
import pycom
import gc
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
        gc.collect()
        wilocMain.feedWatchdog()
        mac_scanned[:]=[]
        scanned_frames[:]=[]
        pycom.nvs_set('rtc', str(int(utime.time())))
        tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except Exception as e:
        checkError("Error going to light sleep: " + str(e)) 

try:
    initRTC()
    tools.debug("Step 0 - Starting Main program on " + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8')) + ' - Time: ' + str((int(utime.time()))),'v')
    pycom.nvs_set('laststatsreport', str(0)) # Force a statistics report on every reset

    # wilocMain.forceConfigParameters()
    wilocMain.loadConfigParameters()
    wilocMain.loadSDCardData()
    lorawan.join_lora()
    bluetooth = Bluetooth()
    while True:
        tools.debug('Step 1 - Starting BLE scanner ' + str(int(utime.time())),'v')
        gc.collect()
        tools.debug(gc.mem_free(),'v')
        tools.debug("Current thread is: %r" % (_thread.get_ident()),'v')
        bluetooth.start_scan(int(globalVars.BLE_SCAN_PERIOD))
        wilocMain.feedWatchdog()
        while bluetooth.isscanning():
            adv = bluetooth.get_adv()
            if adv:
                if 'WILOC_' in str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)):
                    tools.debug('Name: '+ str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)) +' MAC: '+ str(ubinascii.hexlify(adv.mac))+ ' RSSI: ' + str(adv.rssi) + ' DT: '+ str(int(utime.time())) +' RAW: ' + str(ubinascii.hexlify(adv.data)),'vvv')
                    if adv.mac not in mac_scanned:
                        tools.debug('Step 1 - New device detected: ' + str(ubinascii.hexlify(adv.mac)),'vv')
                        mac_scanned.append(adv.mac)
                    if adv.rssi >= (int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256):  
                        wilocMain.checkWhiteList(str(ubinascii.hexlify(adv.mac).decode('utf-8')))
                    scanned_frames.append(Beacon(adv.mac,adv.rssi,None,None,None,None))
        
        tools.debug('Step 1 - Stopping BLE scanner ' + str(int(utime.time())) + " - Devices: " + str(len(mac_scanned)) + " - Packages: " + str(len(scanned_frames)),'v')
        wilocMain.feedWatchdog()
        if len(scanned_frames) > 0:
            dummy_list = wilocMain.rssiFilterDevices(globalVars.RSSI_NEAR_THRESHOLD,mac_scanned, scanned_frames)
            if len(dummy_list) > 0:
                sentDevices = wilocMain.checkTimeToSend(dummy_list, globalVars.MAX_REFRESH_TIME)
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
        
        if wilocMain.checkTimeForStatistics(globalVars.STATISTICS_REPORT_INTERVAL) == True:
            _thread.start_new_thread(wilocMain.sendStatisticsReport,())
            pycom.nvs_set('laststatsreport', str(int(utime.time())))

        sleepProcess()

except Exception as e:
    checkError("Main Error: " + str(e))
    pycom.nvs_set('rtc', str(int(utime.time())))
    machine.reset()