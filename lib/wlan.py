from mqtt import MQTTClient
from network import WLAN
from errorissuer import checkError
import machine
import utime
import globalVars
import tools
import ujson

wlan = WLAN(mode=WLAN.STA)
client = None

def response_callback(topic, msg):
    try:
        tools.debug("Topic: " + str(topic), "v")
        tools.debug("Message: " + str(msg), "v")
    except BaseException as e:
        checkError("Error handeling callback from MQTT Request",e)
    

def wlan_connect(wlan=None):
    try:
        #wlan.connect(ssid='WILOC_AIRE', auth=(WLAN.WPA2, 'WiL.10.TeCH'))
        if wlan is None:
            wlan = WLAN(mode=WLAN.STA)

        wlan.connect(ssid=globalVars.wifi_ssid, auth=(WLAN.WPA2, globalVars.wifi_psw))
        retries = 20;
        while not wlan.isconnected():
            tools.debug("Connecting to Wifi... - Try: " + str(retries), "vv")
            utime.sleep(3)
            if retries == 0:
                tools.debug("Reseting module because it does not connect to Wifi or MQTT", "v")
                machine.reset()
            else:
                retries = retries - 1
        tools.debug("Wifi connected successfully" + str(wlan.ifconfig()), "v")
    except BaseException as e:
        checkError("Error connecting to WLAN",e)

def check_connectivity(error):
    try:
        conn = wlan.isconnected()
        tools.debug("Checking connectivity: " + str(conn) + " - " + str(wlan.ifconfig()), "v")
        if conn == False:
            tools.debug("Restarting WLAN Adapter", "v")
            wlan.deinit()
            utime.sleep(5)
            wlan.init(mode=WLAN.STA)
            wlan_connect(wlan)
        #TODO It does not automatically connect. It gets stack trying.
        err = ["ECONNRESET","EHOSTUNREACH", "ECONNABORTED", "EBADF"]
        
        for match in err:
            if match in str(error):
                mqtt_connect()
                break       
        
    except BaseException as e:
        checkError("Error checking connectivity",e)

def mqtt_connect():
    global client
    try:
        tools.debug("Connecting MQTT", "v")
        client = MQTTClient("gtw001_"+str(int(utime.time())), globalVars.mqtt_url, user=globalVars.mqtt_user, password=globalVars.mqtt_psw, port=1883)
        client.set_callback(response_callback)
        client.connect()
        client.subscribe(topic=globalVars.mqtt_topic)
        return client
    except BaseException as e:
        checkError("Error connecting to MQTT",e)

def mqtt_disconnect():
    global client
    try:
        tools.debug("Disconnecting MQTT", "v")
        client.disconnect()
    except BaseException as e:
        checkError("Error connecting to MQTT",e)

def send_MQTT_message(device):
    global client
    try:
        tools.debug("MQTT Sending message", "v")
        mac_pos = [str(device.addr)[i:i+2] for i in range(0, len(str(device.addr)), 2)]
        dev_addr = ""
        for num, a in enumerate(mac_pos):
            dev_addr = dev_addr + a
            if num < (len(mac_pos) - 1):
                dev_addr = dev_addr + ":"

        msg_to = {"gpsQuality" : 10, "lastEventDate" : int(utime.time())*1000, "latitude":40.34155561314692, "login":"", "longitude": -3.8205912308152103, "numSerie":str(dev_addr).upper()}
        client.publish(topic=globalVars.mqtt_topic, msg=ujson.dumps(msg_to), retain=False, qos=1)
        return 1
    except BaseException as e:
        checkError("Error sending POST - ",e)
        client.disconnect()
        check_connectivity(e)
        return 0

def sendPostMessages():
    global client
    try:
        tools.debug("Step 7 - Starting WLAN Sending messages:  " + str(wlan.ifconfig()) + " - MQTT Client ID: " + str(client.getMQTTClientID), 'v')
        devs_error = []
        stats_error = []
        acks_error = []
        if len(globalVars.lora_sent_devices) > 0: 
            for dev in globalVars.lora_sent_devices:
                try:
                    utime.sleep(0.1)
                    if send_MQTT_message(dev) == 1:
                        tools.debug("Step 7 - Devices, WLAN message succesfully, Device: " + str(dev.addr) + " - Raw: " + str(dev.raw), 'vv')
                    else:
                        tools.debug("ERROR Sending device: " + str(dev.addr), 'v')
                        devs_error.append(dev)
                except BaseException as e1:
                    checkError("Error sending message of device: " + str(dev.addr), e1)
                    devs_error.append(dev)

            globalVars.lora_sent_devices = devs_error
        if len(globalVars.lora_sent_stats) > 0:    
            for dev_stat in globalVars.lora_sent_stats:
                try:
                    utime.sleep(0.1)
                    if send_MQTT_message(dev_stat) == 1:
                        tools.debug("Step 7 - Statistics Threading, WLAN message succesfully, Device: " + str(dev_stat.addr) + " - Raw: " + str(dev_stat.raw), 'vv')
                    else:
                        tools.debug("ERROR Sending Statistics: " + str(dev_stat.addr), 'v')
                        stats_error.append(dev_stat)
                except BaseException as e2:
                    checkError("Error sending message of statistics: " + str(dev_stat.addr), e2)
                    stats_error.append(dev_stat)
            
            globalVars.lora_sent_stats = stats_error
        if len(globalVars.lora_sent_acks) > 0:  
            for dev_acks in globalVars.lora_sent_acks:
                try:
                    utime.sleep(0.1)
                    if send_MQTT_message(dev_acks) == 1:
                        tools.debug("Step 7 - ACKs Threading, WLAN message succesfully, Device: " + str(dev_acks.addr) + " - Raw: " + str(dev_acks.raw), 'vv')
                    else:
                        tools.debug("ERROR Sending ACKS: " + str(dev_acks.addr), 'v')
                        stats_error.append(dev_acks)
                except BaseException as e3:
                    checkError("Error sending message of ACKs: " + str(dev_acks.addr), e3)
                    acks_error.append(dev_acks)
            
            globalVars.lora_sent_acks = acks_error
        
    except BaseException as eee:
        checkError("Error Threading WLAN payload",eee)

def template(dev):
    try:
        tools.debug("", "")
    except BaseException as e:
        checkError("Error going to light sleep",e)



