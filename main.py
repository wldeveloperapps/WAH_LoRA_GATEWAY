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
import sys
from uio import StringIO

# -------------------------
scanned_frames = []
mac_scanned = []
statSend = []
pkgSend = []
# -------------------------
ble_thread = False
s = StringIO()

# def uart_task():
#     try:
#         uart = UART(1, baudrate=9600, timeout_chars=2000)
#         while True:
#             data = uart.read(2000)
#             if data != None:
#                 print(data)
#     except BaseException as e:
#         err = sys.print_exception(e, s)
#         checkError("Error thread UART Task: " + str(s.getvalue()))
#     finally:
#         ble_thread = False
#         _thread.start_new_thread(uart_task,())

def bluetooth_scanner():
    global ble_thread
    try:
        while True:
            try:
                tools.debug('Step 1 - Starting BLE scanner, RSSI: ' + str(int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256) + " - RTC: " + str(int(utime.time())) + " - REFRESH: " + str(globalVars.MAX_REFRESH_TIME) + " - SCAN: " + str(int(globalVars.BLE_SCAN_PERIOD)) + " - SLEEP: " + str(int(globalVars.STANDBY_PERIOD)) + " - DEBUG: " + str(globalVars.debug_cc) ,'v')
                ble_thread = True
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
                                wilocMain.checkListType(str(ubinascii.hexlify(adv.mac).decode('utf-8')), globalVars.ALARM_LIST_TYPE)
                            globalVars.scanned_frames.append(Device(addr=adv.mac,rssi=adv.rssi, raw=data_raw))

                tools.debug('Step 1 - Stopping BLE scanner ' + str(int(utime.time())),'v')
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
            except BaseException as ee1:
                err = sys.print_exception(ee1, s)
                checkError("Error scanning Bluetooth: " + str(s.getvalue()))
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except BaseException as e:
        err = sys.print_exception(e, s)
        checkError("Error thread Bluetooth: " + str(s.getvalue()))
        ble_thread = False
    finally:
        ble_thread = False
        _thread.start_new_thread(bluetooth_scanner,())

try:
    rtcmgt.initRTC()
    tools.debug("Step 0 - Starting Main program on " + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8')) + ' - Time: ' + str((int(utime.time()))),'v')
    pycom.nvs_set('laststatsreport', str(0)) # Force a statistics report on every reset
    sched = Scheduler()
    sched.start()
    tools.getResetCause()
    # wilocMain.forceConfigParameters()
    wilocMain.loadConfigParameters()
    wilocMain.loadSDCardData()
    # _thread.start_new_thread(uart_task,())
    
    lorawan.join_lora()
    
    while True:
        try:
            if ble_thread == False:
                _thread.start_new_thread(bluetooth_scanner,())

            rtcmgt.updateRTC()
            tools.sleepWiloc(int(globalVars.BLE_SCAN_PERIOD))
            if len(globalVars.scanned_frames) > 0:
                dummy_list = wilocMain.rssiFilterDevices(globalVars.RSSI_NEAR_THRESHOLD,globalVars.mac_scanned, globalVars.scanned_frames)
                if len(dummy_list) > 0:
                    sentDevices = wilocMain.checkTimeToAddDevices(dummy_list, globalVars.MAX_REFRESH_TIME)
                    if len(sentDevices) > 0:
                        pkgSend = wilocMain.createPackageToSend(sentDevices, globalVars.scanned_frames)
                        if len(pkgSend) > 0:
                            wilocMain.manage_devices_send(pkgSend)
            
            if wilocMain.checkTimeForStatistics(globalVars.STATISTICS_REPORT_INTERVAL) == True:
                pycom.nvs_set('laststatsreport', str(int(utime.time())))
                # _thread.start_new_thread(wilocMain.manage_devices_send,(wilocMain.createStatisticsReport(),))
                _thread.start_new_thread(wilocMain.createStatisticsReport,())
            
            if wilocMain.checkTimeToSend(globalVars.SENT_PERIOD) == True:
                if len(globalVars.lora_sent_devices) > 0:
                    lorawan.sendLoRaWANMessage()
            else:
                sched.checkNextReset()
                wilocMain.sleepProcess()
            
        except BaseException as eee:
            err = sys.print_exception(eee, s)
            checkError("Main Task Error: " + str(s.getvalue()))
            wilocMain.sleepProcess()

except BaseException as e:
    err = sys.print_exception(e, s)
    checkError("Main Thread Error: " + str(s.getvalue()))
finally:
    checkError("Main thread finishing for unexpected error: ")
    pycom.nvs_set('rtc', str(int(utime.time())))
    utime.sleep(10)
    machine.reset()