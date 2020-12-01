from lib.loRaReportsTools import LoRaWANSentListCleanDevices
from lib.buzzerTools import BeepBuzzer, BuzzerListCleanDevices
from lib.rtcmgt import initRTC, forceRTC
from errorissuer import checkError
from lib.beacon import Device
from network import LoRa
from scheduler import Scheduler
import whitelistTools
import blacklisttools
import globalVars
import ubinascii
import binascii
import struct
import socket
import machine
import utime
import pycom
import _thread
import gc
import tools



if globalVars.REGION == 'EU868':
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, device_class=LoRa.CLASS_A, adr=False, tx_power=14, tx_retries=1)
elif globalVars.REGION == 'AS923':
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AS923, device_class=LoRa.CLASS_A, adr=False, tx_power=14, tx_retries=1)

lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

def prepare_channels_as923(lora, channel, data_rate):
    AS923_FREQUENCIES = [
        { "chan": 1, "fq": "923200000" },
        { "chan": 2, "fq": "923400000" },
        { "chan": 3, "fq": "923600000" },
        { "chan": 4, "fq": "923800000" },
        { "chan": 5, "fq": "924000000" },
        { "chan": 6, "fq": "924200000" },
        { "chan": 7, "fq": "924400000" },
        { "chan": 8, "fq": "924600000" },
    ]
    

    if not channel in range(0, 9):
        raise RuntimeError("channels should be in 1-8 for AS923")

    if channel == 0:
        import uos
        channel = (struct.unpack('B',uos.urandom(1))[0] % 7) + 1

    for i in range(0, 8):
        lora.remove_channel(i)

    upstream = (item for item in AS923_FREQUENCIES if item["chan"] == channel).__next__()

    # set default channels frequency
    lora.add_channel(int(upstream.get('chan')), frequency=int(upstream.get('fq')), dr_min=0, dr_max=data_rate)
    return lora

def prepare_channels_eu868(lora, channel, data_rate):
    EU868_FREQUENCIES = [
        { "chan": 1, "fq": "865100000" },
        { "chan": 2, "fq": "865300000" },
        { "chan": 3, "fq": "865500000" },
        { "chan": 4, "fq": "865700000" },
        { "chan": 5, "fq": "865900000" },
        { "chan": 6, "fq": "866100000" },
        { "chan": 7, "fq": "866300000" },
        { "chan": 8, "fq": "866500000" },
        { "chan": 9, "fq": "867100000" },
        { "chan": 10, "fq": "867300000" },
        { "chan": 11, "fq": "867500000" },
        { "chan": 12, "fq": "867700000" },
        { "chan": 13, "fq": "867900000" },
        { "chan": 14, "fq": "868100000" },
        { "chan": 15, "fq": "868300000" },
        { "chan": 16, "fq": "868500000" },
    ]
    

    if not channel in range(0, 17):
        raise RuntimeError("channels should be in 1-8 for AS923")

    if channel == 0:
        import uos
        channel = (struct.unpack('B',uos.urandom(1))[0] % 7) + 1

    for i in range(0, 16):
        lora.remove_channel(i)

    upstream = (item for item in EU868_FREQUENCIES if item["chan"] == channel).__next__()

    # set default channels frequency
    lora.add_channel(int(upstream.get('chan')), frequency=int(upstream.get('fq')), dr_min=0, dr_max=data_rate)
    return lora

def joinLoRaWANModule(lora):
    try:
        # if reset_cause == machine.DEEPSLEEP_RESET and lora.has_joined():
        if lora.has_joined():
            print('Step 0.1 - Skipping LoRaWAN join, previously joined')
        else:
            ddd0 = '0000' + str(ubinascii.hexlify(machine.unique_id()).decode('utf-8'))
            ddd = str(ubinascii.hexlify(lora.mac()).decode('utf-8'))
            print("DEV EUI: " + str(ddd0) + " - LoRa MAC: " + str(ubinascii.hexlify(lora.mac()).decode('utf-8')))
            dev_eui = binascii.unhexlify(ddd)
            app_key = binascii.unhexlify('a926e5bb85271f2d') # not used leave empty loraserver.io
            nwk_key = binascii.unhexlify('a926e5bb85271f2da0440f2f4200afe3')
            lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key, nwk_key), timeout=0, dr=2) # AS923 always joins at DR2
            
            if globalVars.REGION == 'AS923':
                prepare_channels_as923(lora, globalVars.LORA_CHANNEL,  globalVars.LORA_NODE_DR)
            elif globalVars.REGION == 'EU868':
                prepare_channels_eu868(lora, globalVars.LORA_CHANNEL,  globalVars.LORA_NODE_DR)

            print('Step 0.1 - Over the air network activation ... ' + str(globalVars.REGION), end='')
            while not lora.has_joined():
                utime.sleep(2.5)
                print('.', end='')
            print('Joined to ' + str(globalVars.REGION) + '!!')
            globalVars.indicatorFrequencyOn = 100
            lora.nvram_save()
    except BaseException as e:
        checkError("Step 0.1 - Error initializaing LoRaWAN module",e)

def initLoRaWANSocket(lora_socket, lora):
    try:
        print("Step 0.2 - LoRa socket setup")
        # lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, globalVars.LORA_NODE_DR)
        lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 1)
        lora.callback(trigger=( LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT | LoRa.TX_FAILED_EVENT  ), handler=lora_cb)
        lora_socket.setblocking(True)
    except BaseException as e:
        checkError("Step 0.2 - Error initializaing LoRaWAN Sockets", e)

def lora_cb(lora):
    global lora_socket
    try:
        events = lora.events()
        if events & LoRa.RX_PACKET_EVENT:
            if lora_socket is not None:
                print("##### LoRa Rx Event Callback")
                lora_socket.settimeout(5)
                port = 0
                try:
                    frame, port = lora_socket.recvfrom(256) # longuest frame is +-220
                except Exception as e2:
                    print("Error downlink: " + str(e2))
                
                checkFrameConfiguration(frame, "LoRaWAN")
        if events & LoRa.TX_PACKET_EVENT:
            print("tx_time_on_air: " + str(lora.stats().tx_time_on_air) + " ms @dr: " + str(lora.stats().sftx))
            # BeepBuzzer(0.5)
        if events & LoRa.TX_FAILED_EVENT:
            print("#### Error TxEvent ####")
    except BaseException as e:
        checkError("Step DL - Error managing downlink", e)

def checkFrameConfiguration(frame, port):
    try:
        if port == "LoRaWAN":
            payload = str(ubinascii.hexlify(frame).decode('utf-8'))
        else:
            payload = str(frame.decode('utf-8'))

        print("##### Receiving message: " + str(payload) + " - Frame: " + str(frame) +  " Port: " + str(port))
        if len(payload) > 1: 
            if str(payload[0:2]) == 'a0': # Add new devices to the Whitelist
                print("##### Message received of new device in whitelist, lenght: " + str(len(str(payload))/2))
                whitelistTools.WhiteListNewDevice(str(payload[2:]))
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'a1': # Add new devices to the BlackList
                print("##### Message received of new device in BlackList, lenght: " + str(len(str(payload))/2))
                blacklisttools.BlackListNewDevice(str(payload[2:]))
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'ad': # Add new devices to the White and Black List
                print("##### Message received for generic device adding, lenght: " + str(len(str(payload))/2))
                if len(payload[2:]) >= 4:
                    list_type = int(payload[2:4],16)
                    delete_list = int(payload[4:6],16)
                    max_message_counter = int(payload[6:8],16)
                    id_message = int(payload[8:10],16)
                    # ----------Set List Type-------------
                    pycom.nvs_set('alarmlisttype', int(payload[2:4],16))
                    globalVars.ALARM_LIST_TYPE = int(payload[2:4],16)
                    # ----------Clean specific lists-------------
                    if id_message == 1 and delete_list == 1:
                        if list_type == 1:
                            whitelistTools.WhiteListDeleteDevices()
                        elif list_type == 2:
                            blacklisttools.BlackListDeleteDevices()
                    # ----------Append devices to lists-------------
                    if list_type == 1:
                            whitelistTools.WhiteListNewDevice(str(payload[10:]))
                    elif list_type == 2:
                            blacklisttools.BlackListNewDevice(str(payload[10:]))
                    # ----------Prepare uplink messages-------------
                    createReceivingReport()
                    # ----------Check Scheduler-------------
                    sched = Scheduler()
                    sched.checkOvernightCycle(int(payload[8:10],16),int(payload[6:8],16))

                BeepBuzzer(2)
            elif str(payload[0:2]) == 'd0': # Delete device from the WhiteList
                whitelistTools.WhiteListDeleteSpecificDevice(str(payload[2:]))
                BeepBuzzer(2)
            elif str(payload[0:2])== 'd1': # Delete device from the BlackList
                blacklisttools.BlackListDeleteSpecificDevice(str(payload[2:]))
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'd2': # Delete entire WhiteList file
                whitelistTools.WhiteListDeleteDevices()
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'd3': # Delete entire BlackList file
                blacklisttools.BlackListDeleteDevices()
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'd4': # Delete entire buzzer file
                BuzzerListCleanDevices()
                BeepBuzzer(2)
                machine.reset()
            elif str(payload[0:2]) == 'd5': # Delete entire sent file
                LoRaWANSentListCleanDevices()
                BeepBuzzer(2)
                machine.reset()
            elif str(payload[0:2]) == 'd6': # Delete entire NVS Memory
                pycom.nvs_erase_all()
                BeepBuzzer(2)
                machine.reset()
            elif str(payload[0:2]) == 'cc': # Change configuration parameters
                UpdateConfigurationParameters(str(payload[2:]))
                BeepBuzzer(2)
                # machine.reset()
            elif str(payload[0:2]) == 'c0': # Syncronize RTC
                forceRTC(int(payload[2:10],16), "epoch")
                pycom.nvs_set('rtc_dt', int(payload[2:10],16))
                utime.sleep(5)
                dt = pycom.nvs_get('rtc_dt')
                globalVars.flag_rtc_syncro = True
                print("Step SYNCRO - Syncronized RTC from Server to " + str(dt))
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'cd': # Change Debug Mode
                dummy = int(payload[2:4],16)
                print("Change debug mode: " + str(dummy))
                if dummy == 0:
                    globalVars.debug_cc = ''
                elif dummy == 1:
                    globalVars.debug_cc = 'v'
                elif dummy == 2:
                    globalVars.debug_cc = 'vv'
                elif dummy == 3:
                    globalVars.debug_cc = 'vvv'
                print("Mode changed to: " + str(globalVars.debug_cc))
                BeepBuzzer(2)
            elif str(payload[0:2]) == 'fa': # Force Alarm
                BeepBuzzer(int(payload[2:4],16))
            elif str(payload[0:2]) == 'f0': # Foce GPS Acquisition
                pycom.nvs_set('laststatsreport', str(0))
            elif str(payload[0:2]) == 'f1': # Foce Reset
                machine.reset()
            elif str(payload[0:2]) == 'f2': # Foce Sleep
                tools.deepSleepWiloc(int(payload[2:8],16))
            elif str(payload[0:2]) == "ff":
                tools.systemCommands(str(payload[2:]))
            else:
                print("##### Message received other code: " + str(payload[0:2]) + " Lenght: " + str(len(payload)/2))
    except BaseException as e4:
        checkError("Step DL - Error managing downlink", e4)

def UpdateConfigurationParameters(raw_payload):
    try:
        listCommands = [raw_payload[i:i+6] for i in range(0, len(raw_payload), 6)]
        for payload in listCommands:
            if payload[0:2] == '20':
                print("Step CC - Setting Max Refresh Time to " + str(int(payload[2:6],16)))
                pycom.nvs_set('maxrefreshtime', int(payload[2:6],16))
                globalVars.MAX_REFRESH_TIME = int(payload[2:6],16)
            if payload[0:2] == '21':
                print("Step CC - Setting BLE Scan Period to " + str(int(payload[2:6],16)))
                pycom.nvs_set('blescanperiod', int(payload[2:6],16))
                globalVars.BLE_SCAN_PERIOD = int(payload[2:6],16)
            if payload[0:2] == '22':
                print("Step CC - Setting StandBy Period to " + str(int(payload[2:6],16)))
                pycom.nvs_set('standbyperiod', int(payload[2:6],16))
                globalVars.STANDBY_PERIOD = int(payload[2:6],16)
            if payload[0:2] == '23':
                print("Step CC - Setting RSSI Near Threshold to " + str(int(payload[2:6],16)-256))
                pycom.nvs_set('rssithreshold', str(payload[2:6],16))
                globalVars.RSSI_NEAR_THRESHOLD = str(payload[2:6],16)
            if payload[0:2] == '24':
                print("Step CC - Setting Statistics Report Interval to " + str(int(payload[2:6],16)))
                pycom.nvs_set('statsinterval', int(payload[2:6],16))
                globalVars.STATISTICS_REPORT_INTERVAL = int(payload[2:6],16)
            if payload[0:2] == '25':
                print("Step CC - Setting Buzzer Duration Period to " + str(int(payload[2:6],16)))
                pycom.nvs_set('buzzerduration', int(payload[2:6],16))
                globalVars.BUZZER_DURATION = int(payload[2:6],16)
            if payload[0:2] == '26':
                print("Step CC - Setting LoRaWAN Sent Period to " + str(int(payload[2:6],16)))
                pycom.nvs_set('lorasentperiod', int(payload[2:6],16))
                globalVars.SENT_PERIOD = int(payload[2:6],16)
            if payload[0:2] == '27':
                print("Step CC - Setting BUZZER_COUNTER_ALARM to " + str(int(payload[2:6],16)))
                pycom.nvs_set('buzcountalarm', int(payload[2:6],16))
                globalVars.BUZZER_COUNTER_ALARM = int(payload[2:6],16)
            if payload[0:2] == '28':
                print("Step CC - Setting ALARM LIST TYPE to " + str(int(payload[2:6],16)))
                pycom.nvs_set('alarmlisttype', int(payload[2:6],16))
                globalVars.ALARM_LIST_TYPE = int(payload[2:6],16)
            if payload[0:2] == '29':
                print("Step CC - Setting LORA Region to " + str(int(payload[2:6],16)))
                if str(int(payload[2:6],16)) == "923":
                    print("Step CC - Setting LORA Region to AS923")
                    pycom.nvs_set('loraregion', 'AS923')
                    globalVars.REGION = 'AS923'
                elif str(int(payload[2:6],16)) == "868":
                    print("Step CC - Setting LORA Region to EU868")
                    pycom.nvs_set('loraregion', 'EU868')
                    globalVars.REGION = 'EU868'
                machine.reset()
            if payload[0:2] == '30':
                tools.debug("Step CC - Setting Scheduler timers StartTime , payload: " + str(payload), "v")
                tmp_start = str(int(payload[2:6],16))
                if len(tmp_start) == 3:
                    tmp_start = "0" + tmp_start
                tmp_starthour = tmp_start[:2]
                tmp_startmin = tmp_start[2:]
                globalVars.dailyStart = str(tmp_starthour) + ":" + str(tmp_startmin) + ":00"
                pycom.nvs_set('dailystartdate', globalVars.dailyStart)
                tools.debug("Step CC - Setting scheduler done, Start: " + str(globalVars.dailyStart), "v")
            if payload[0:2] == '31':
                tools.debug("Step CC - Setting Scheduler timers StopTime , payload: " + str(payload), "v")
                tmp_stop = str(int(payload[2:6],16))
                if len(tmp_stop) == 3:
                    tmp_stop = "0" + tmp_stop
                tmp_stophour = tmp_stop[:2]
                tmp_stopmin = tmp_stop[2:]
                globalVars.dailyStandBy = str(tmp_stophour) + ":" + str(tmp_stopmin) + ":00"
                pycom.nvs_set('dailystopdate', globalVars.dailyStandBy)
                tools.debug("Step CC - Setting scheduler done, Stop " + str(globalVars.dailyStandBy), "v")
            if payload[0:2] == '32':
                tools.debug("Step CC - Setting Scheduler timers StartDownlinks, payload: " + str(payload), "v")
                tmp_startdwn = str(int(payload[2:6],16))
                if len(tmp_startdwn) == 3:
                    tmp_startdwn = "0" + tmp_startdwn
                tmp_startdwnhour = tmp_startdwn[:2]
                tmp_startdwnmin = tmp_startdwn[2:]
                globalVars.startDownlink = str(tmp_startdwnhour) + ":" + str(tmp_startdwnmin) + ":00"
                pycom.nvs_set('startdowndate', globalVars.startDownlink)
                tools.debug("Step CC - Setting scheduler done, Startdownlinks: " + str(globalVars.startDownlink), "v")
            if payload[0:2] == '33':
                print("Step CC - Setting LOW_BATTERY_VOLTAGE_ALARM to " + str(int(payload[2:6],16)))
                pycom.nvs_set('lowbattalarm', int(payload[2:6],16))
                globalVars.LOW_BATTERY_VOLTAGE = int(payload[2:6],16)
            if payload[0:2] == '34':
                tools.debug("Step CC - Setting Scheduler timers EndDownlinks, payload: " + str(payload), "v")
                tmp_enddwn = str(int(payload[2:6],16))
                if len(tmp_enddwn) == 3:
                    tmp_enddwn = "0" + tmp_enddwn
                tmp_enddwnhour = tmp_enddwn[:2]
                tmp_enddwnmin = tmp_enddwn[2:]
                globalVars.endDownlink = str(tmp_enddwnhour) + ":" + str(tmp_enddwnmin) + ":00"
                pycom.nvs_set('stopdowndate', globalVars.endDownlink)
                tools.debug("Step CC - Setting scheduler done, Enddownlinks: " + str(globalVars.endDownlink), "v")
            if payload[0:2] == '35': # Configure the days off
                tools.debug("Step CC - Setting Scheduler days off, payload: " + str(payload), "v")
                days_tmp = []
                var_tmp = tools.bitfield(int(payload[4:6],16))
                for i in range(7):
                    if str(var_tmp[i]) == '1':
                        days_tmp.append(6-i)
                globalVars.dayOff = days_tmp
                tools.debug("Step CC - Setting scheduler do: " + str(days_tmp)+" - "+str(var_tmp), "v")

    except BaseException as e:
        checkError("Step CC -  Error setting configuiration parameters", e)
        return 17, "Step CC -  Error setting configuiration parameters: " + str(e)

def join_lora():
    global lora
    global lora_socket
    try:
        joinLoRaWANModule(lora)
        initLoRaWANSocket(lora_socket, lora)
        utime.sleep(1)
    except BaseException as e:
        checkError("Error joining LoRa Network",e)

def sendLoRaWANMessage():
    global lora_socket
    try:
        if lora.has_joined():
            sendAckMessageThread(lora_socket)
        else:
            tools.debug("Impossible to send because device is not joined", 'v')
            join_lora()
            if lora.has_joined():
                sendAckMessageThread(lora_socket)
    except BaseException as eee:

        checkError("Error sending LoRaWAN message",eee)

def sendAckMessageThread(lora_sck):
    try:
        tools.debug("Step 7 - Starting Threading LoRaWAN messages ", 'v')
        devs_error = []
        stats_error = []
        acks_error = []
        if len(globalVars.lora_sent_devices) > 0: 
            for dev in globalVars.lora_sent_devices:
                try:
                    utime.sleep(5)
                    lora_sck.send(bytes(dev.raw))
                    tools.debug("Step 7 - Devices Threading, LoRaWAN message succesfully, Device: " + str(dev.addr) + " - Raw: " + str(dev.raw), 'vv')
                except BaseException as e1:
                    checkError("Error sending message of device: " + str(dev.addr), e1)
                    devs_error.append(dev)

            globalVars.lora_sent_devices = devs_error
        if len(globalVars.lora_sent_stats) > 0:    
            for dev_stat in globalVars.lora_sent_stats:
                try:
                    utime.sleep(5)
                    lora_sck.send(bytes(dev_stat.raw))
                    tools.debug("Step 7 - Statistics Threading, LoRaWAN message succesfully, Device: " + str(dev_stat.addr) + " - Raw: " + str(dev_stat.raw), 'vv')
                except BaseException as e2:
                    checkError("Error sending message of statistics: " + str(dev_stat.addr), e2)
                    stats_error.append(dev_stat)
            
            globalVars.lora_sent_stats = stats_error
        if len(globalVars.lora_sent_acks) > 0:  
            for dev_acks in globalVars.lora_sent_acks:
                try:
                    utime.sleep(5)
                    lora_sck.send(bytes(dev_acks.raw))
                    tools.debug("Step 7 - ACKs Threading, LoRaWAN message succesfully, Device: " + str(dev_acks.addr) + " - Raw: " + str(dev_acks.raw), 'vv')
                except BaseException as e3:
                    checkError("Error sending message of ACKs: " + str(dev_acks.addr), e3)
                    acks_error.append(dev_acks)
            
            globalVars.lora_sent_acks = acks_error
        
    except BaseException as eee:
        checkError("Error Threading LoRaWAN payload",eee)

def createReceivingReport():
    try:
        devicesToSend = []
        strToSend = []
        gps_stats = 66
        bat = tools.getBatteryPercentage()
        st_bat = struct.pack(">I", bat)
        st_gps_stats = struct.pack(">I", gps_stats)
        whiteLen = struct.pack(">I", len(globalVars.devices_whitelist))
        blackLen = struct.pack(">I", len(globalVars.devices_blacklist))
        strToSend.append(struct.pack(">I", 173)[3]) # Protocol
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
        strToSend.append(whiteLen[2])
        strToSend.append(whiteLen[3])
        strToSend.append(blackLen[2])
        strToSend.append(blackLen[3])
        tools.debug("Step 8 - Creating ack report: " + str(strToSend),'v')
        globalVars.lora_sent_acks.append(Device(addr="ackresp",raw=strToSend))
        # tools.manage_devices_send(devicesToSend)
    except BaseException as e1:
        checkError("Step 5 - Error creating ack report", e1)
        return [] 