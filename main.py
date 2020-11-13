from network import Bluetooth
from lib.beacon import Device
from errorissuer import checkError, checkWarning
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
from machine import UART

# -------------------------
scanned_frames = []
mac_scanned = []
statSend = []
pkgSend = []
# -------------------------
ble_thread = False

def uart_task():
    try:
        uart = UART(0, 115200)                         # init with given baudrate
        while True:
            data = uart.read(1024)
            if data != None:
                # arr_tmp = [str(data.decode('utf-8'))[i:i+2] for i in range(0, len(str(data.decode('utf-8'))), 2)]
                tools.debug("Serial received: "+ str(data.decode('utf-8')), "v")
                lorawan.checkFrameConfiguration(data,"Serial-0")
    except BaseException as e:
        checkError("Error thread UART Task",e)
    finally:
        ble_thread = False
        checkWarning("Finally thread UART Task")
        _thread.start_new_thread(uart_task,())

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
                            data_raw = str(ubinascii.hexlify(adv.data).decode('utf-8'))
                            if globalVars.MAC_TYPE == "LORA":
                                mac_proc = data_raw[34:50] # LoRa MAC
                            elif globalVars.MAC_TYPE == "BLE":
                                mac_proc = str(ubinascii.hexlify(adv.mac).decode('utf-8')) # MAC BLE
                            tools.debug('Name: '+ str(bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)) +' MAC: '+ str(mac_proc)+ ' RSSI: ' + str(adv.rssi) + ' DT: '+ str(int(utime.time())) +' RAW: ' + data_raw,'vvv')
                            if mac_proc not in globalVars.mac_scanned:
                                tools.debug('Step 1 - New device detected: ' + str(mac_proc),'vv')
                                globalVars.mac_scanned.append(mac_proc)
                            if adv.rssi >= (int(globalVars.RSSI_NEAR_THRESHOLD,16) - 256):  
                                wilocMain.checkListType(str(mac_proc), globalVars.ALARM_LIST_TYPE)
                            globalVars.scanned_frames.append(Device(addr=mac_proc,rssi=adv.rssi, raw=data_raw))

                tools.debug('Step 1 - Stopping BLE scanner ' + str(int(utime.time())),'v')
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
            except BaseException as ee1:
                checkError("Error scanning Bluetooth",ee1)
                tools.sleepWiloc(int(globalVars.STANDBY_PERIOD))
    except BaseException as e:
        checkError("Error thread Bluetooth", e)
        ble_thread = False
    finally:
        ble_thread = False
        _thread.start_new_thread(bluetooth_scanner,())

try:
    _thread.start_new_thread(uart_task,())
    rtcmgt.initRTC()
    tools.debug("Step 0 - Starting Main program on " + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8')) + ' - Time: ' + str((int(utime.time()))),'v')
    pycom.nvs_set('laststatsreport', str(0)) # Force a statistics report on every reset
    sched = Scheduler()
    sched.start()
    tools.getResetCause()
    # wilocMain.forceConfigParameters()
    tools.loadConfigParameters()
    wilocMain.loadSDCardData()
    utime.sleep(2)
    lorawan.join_lora()
    
    while True:
        try:
            if ble_thread == False:
                _thread.start_new_thread(bluetooth_scanner,())

            tools.sleepWiloc(int(globalVars.BLE_SCAN_PERIOD))
            if len(globalVars.scanned_frames) > 0:
                dummy_list = wilocMain.rssiFilterDevices(globalVars.RSSI_NEAR_THRESHOLD,globalVars.mac_scanned, globalVars.scanned_frames)
                if len(dummy_list) > 0:
                    sentDevices = wilocMain.checkTimeToAddDevices(dummy_list, globalVars.MAX_REFRESH_TIME)
                    if len(sentDevices) > 0:
                        pkgSend = wilocMain.createPackageToSend(sentDevices, globalVars.scanned_frames)
                        if len(pkgSend) > 0:
                            tools.manage_devices_send(pkgSend)
            
            if wilocMain.checkTimeForStatistics(globalVars.STATISTICS_REPORT_INTERVAL) == True:
                _thread.start_new_thread(wilocMain.createStatisticsReport,())
            
            if wilocMain.checkTimeToSend(globalVars.SENT_PERIOD) == True:
                    lorawan.sendLoRaWANMessage()
            else:
                sched.checkNextReset()
                sched.checkDutyCycle()
                tools.sleepProcess()
            
        except BaseException as eee:
            checkError("Main Task Error",eee)
            tools.sleepProcess()

except BaseException as e:
    checkError("Main Thread Error",e)
finally:
    checkWarning("Main thread finishing for unexpected error")
    rtcmgt.updateRTC()
    utime.sleep(10)
    machine.reset()