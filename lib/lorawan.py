from lib.loRaReportsTools import LoRaWANSentListCleanDevices
from lib.whitelistTools import WhiteListNewDevice, WhiteListDeleteDevices, WhiteListDeleteSpecificDevice
from lib.buzzerTools import BeepBuzzer, BuzzerListCleanDevices
from lib.rtcmgt import initRTC, forceRTC
from errorissuer import checkError
from network import LoRa
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
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, device_class=LoRa.CLASS_A, adr=True, tx_power=14, tx_retries=2, power_mode=LoRa.ALWAYS_ON)
elif globalVars.REGION == 'AS923':
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AS923, device_class=LoRa.CLASS_A, adr=True, tx_power=14, tx_retries=2)

lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

strError = []
flag_sent = False

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

            print('Step 0.1 - Over the air network activation ... ', end='')
            while not lora.has_joined():
                utime.sleep(2.5)
                print('.', end='')
            print('Joined!!')
            # lora.callback(trigger=(LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT), handler=lora_cb)
            lora.nvram_save()
    except Exception as e:
        checkError("Step 0.1 - Error initializaing LoRaWAN module: " + str(e))
        strError.append('3')

def initLoRaWANSocket(lora_socket, lora):
    try:
        print("Step 0.2 - LoRa socket setup")
        # lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, globalVars.LORA_NODE_DR)
        lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 1)
        lora.callback(trigger=( LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT | LoRa.TX_FAILED_EVENT  ), handler=lora_cb)
        lora_socket.setblocking(True)

        # return lora_socket
    except Exception as e:
        checkError("Step 0.2 - Error initializaing LoRaWAN Sockets: " + str(e))
        strError.append('2')

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
                payload = str(ubinascii.hexlify(frame).decode('utf-8'))
                print("##### Receiving message" + payload + " Port: " + str(port))
                if len(payload) > 1: 
                    if payload[0:2] == '0a': # Add new devices to the whitelist
                        print("##### Message received of new device in whitelist, lenght: " + str(len(payload)/2));
                        WhiteListNewDevice(payload[2:])
                        BeepBuzzer(2)
                        # machine.reset()
                    elif payload[0:2] == '0d': # Delete device from the whitelist
                        WhiteListDeleteSpecificDevice(payload[2:])
                        BeepBuzzer(2)
                        # machine.reset()
                    elif payload[0:2] == 'fa': # Delete entire whitelist file
                        WhiteListDeleteDevices()
                        BeepBuzzer(2)
                    elif payload[0:2] == 'fb': # Delete entire buzzer file
                        BuzzerListCleanDevices()
                        BeepBuzzer(2)
                        machine.reset()
                    elif payload[0:2] == 'fc': # Delete entire sent file
                        LoRaWANSentListCleanDevices()
                        BeepBuzzer(2)
                        machine.reset()
                    elif payload[0:2] == 'fd': # Delete entire NVS Memory
                        pycom.nvs_erase_all()
                        BeepBuzzer(2)
                        machine.reset()
                    elif payload[0:2] == 'cc': # Change configuration parameters
                        UpdateConfigurationParameters(payload[2:])
                        BeepBuzzer(2)
                        # machine.reset()
                    elif payload[0:2] == 'd0': # Syncronize RTC
                        forceRTC(int(payload[2:10],16))
                        pycom.nvs_set('rtc', int(payload[2:10],16))
                        utime.sleep(5)
                        dt = pycom.nvs_get('rtc')
                        print("Step SYNCRO - Syncronized RTC from Server to " + str(dt))
                        BeepBuzzer(2)
                    elif payload[0:2] == 'dc': # Change Debug Mode
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
                    elif payload[0:2] == 'b0': # Force Alarm
                        BeepBuzzer(int(payload[2:4],16))
                    else:
                        print("##### Message received other code: " + str(payload[0:2]) + " Lenght: " + str(len(payload)/2))

        if events & LoRa.TX_PACKET_EVENT:
            print("tx_time_on_air: " + str(lora.stats().tx_time_on_air) + " ms @dr: " + str(lora.stats().sftx))
            BeepBuzzer(0.5)
        if events & LoRa.TX_FAILED_EVENT:
            print("#### Error TxEvent ####")
    except Exception as e1:
        checkError("Step DL - Error managing downlink: " + str(e1)) 

def changeFlagSent(value):
    globalVars.flag_sent = value

def UpdateConfigurationParameters(payload):
    try:
        
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
    except Exception as e:
        print("Step CC -  Error setting configuiration parameters: " + str(e))
        return 17, "Step CC -  Error setting configuiration parameters: " + str(e)

def join_lora():
    global lora
    global lora_socket
    try:
        joinLoRaWANModule(lora)
        initLoRaWANSocket(lora_socket, lora)
        # initLoRaWANSocket()
        utime.sleep(1)
    except Exception as ee:
        checkError("Error joining LoRa Network: " + str(ee))

def sendLoRaWANMessage(devices_payload):
    global lora_socket
    try:
        ts = int(utime.time())
        manage_devices_send(devices_payload)
        if (globalVars.last_lora_sent + int(globalVars.SENT_PERIOD)) < ts: 
            globalVars.last_lora_sent = ts
            if lora.has_joined():
                # for dev in globalVars.lora_sent_devices:
                # _thread.start_new_thread(sendAckMessageThread,(lora_socket,))
                # _thread.start_new_thread(sendAckMessageThread,())
                sendAckMessageThread(lora_socket)
                # sendPayload(lora_socket)
                # _thread.start_new_thread(sendPayload,(lora_socket,dev,))
            else:
                print("Impossible to send because device is not joined")
                join_lora()
                if lora.has_joined():
                    _thread.start_new_thread(sendAckMessageThread,(lora_socket,))
        else:
            tools.debug("LoRaWAN Sent - Remaining time: " + str(((globalVars.last_lora_sent + int(globalVars.SENT_PERIOD)) - ts)),"v")
    except Exception as eee:
        checkError("Error sending LoRaWAN message: " + str(eee))

def sendPayload(sck):
    try:
        print("Sending LoRaWAN payload middleware ")
        _thread.start_new_thread(sendAckMessageThread,(sck,))
    except Exception as eee:
        checkError("Error sending LoRaWAN payload: " + str(eee))

def sendAckMessageThread(lora_sck):
    # global lora_socket
    try:
        print("Threading LoRaWAN messages ")
        for dev in globalVars.lora_sent_devices:
            try:
                # lora_sck.setblocking(False)
                # _thread.start_new_thread(lora_sck.send,(bytes(dev.raw),))
                # lora_sck.setblocking(True)
                lora_sck.send(bytes(dev.raw))
                # if lora_sck is not None:
                #     print("##### LoRa Rx Event Callback")
                #     lora_sck.settimeout(5)
                #     port = 0
                #     try:
                #         frame, port = lora_sck.recvfrom(256) # longuest frame is +-220
                #         payload = str(ubinascii.hexlify(frame).decode('utf-8'))
                #         print("##### Receiving message on thread" + payload + " Port: " + str(port))
                #     except Exception as e2:
                #         print("Error downlink: " + str(e2))
                utime.sleep(2)
                print("Threading LoRaWAN message succesfully, Device: " + str(dev.addr) + " - Raw: " + str(dev.raw))
            except Exception as e1:
                print("Error sending message of device: " + str(dev.addr) + " - Error: " + str(e1))
            utime.sleep(8)
        
        globalVars.lora_sent_devices = []
        # lora_sck.close()
        # _thread.exit()
        
    except Exception as eee:
        checkError("Error Threading LoRaWAN payload: " + str(eee))

def check_downlink_messages(sck):
    try:
        print("Checking downlink messages")
        sck.settimeout(5)
        downlink_message = sck.recv(256) # See if a downlink message arrived
        print(downlink_message)

        if not downlink_message: # If there was no message, get out now
            print("No downlink messages")
            return

        print("Downlink message received!")
    except Exception as e:
        print("Error checking downlink messages: " + str(e))

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

        tools.debug("LoRaWAN Stored records to send: " + str(len(globalVars.lora_sent_devices)),"v")
    except Exception as e:
        print("Error managing devices to send: " + str(e))