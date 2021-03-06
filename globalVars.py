
#------ Firmware Version -----------
scheduler_version = 1
comms_version = 1
main_version = 1
loc_version = 1

# ------ Device Type ------
# deviceID = 2 # PyTrack
#deviceID = 1 # PySense
deviceID = 0 # Expansion board

#-------- Backhaul --------
backhaul = 2 # 1 LoRaWAN / 2 WIFI
wifi_ssid = "WILOC_AIRE"
wifi_psw = "WiL.10.TeCH"
mqtt_url = "smart-fisherman.cloudmqtt.com"
mqtt_user = "ffetgyj"
mqtt_psw = "mqtt@tr#1234"
mqtt_topic = "/AssetsMgmtTest"

# ------ Configuration parameters --------
MAX_REFRESH_TIME = 60 # Code 20
BLE_SCAN_PERIOD = 6 # Code 21
STANDBY_PERIOD = 1 # Code 22
RSSI_NEAR_THRESHOLD = 'c4' # Code 23
STATISTICS_REPORT_INTERVAL = 600 # Code 24
BUZZER_DURATION = 1 # Code 25
SENT_PERIOD = 120 # Code 26
BUZZER_COUNTER_ALARM = 3 # Code 27
ALARM_LIST_TYPE = 2 # Code 28 ------- 0-None / 1-Whitelist / 2-Blacklist 
LOW_BATTERY_VOLTAGE = 19 # Code 33
# ------ LoRaWAN Configuration -------
LORA_CHANNEL = 1
LORA_NODE_DR = 4
# REGION = 'AS923'
REGION = 'EU868'
MAC_TYPE='LORA'
# MAC_TYPE='BLE'

# ------ Debug -------------
debug_cc = "v"

# ------ Timers -----------
dailyreset="00:00:00"
startDownlink="01:00:00"
endDownlink="03:00:00"
dailyStart="06:00:00"
dailyStandBy="18:00:00"
refDay="23:59:59"
dayOff = [6]

# ------ Flags ------------
stop_sleep_flag = False
flag_sent = False
flag_gps_running = False
flag_blelora = False
flag_rtc_syncro = False

# -------- Lists ------------
devices_whitelist = []
devices_blacklist = []
device_sent = []
mac_scanned = []
scanned_frames = []

#-------- LoRa variables -----

last_lora_sent = 0
lora_sent_devices = []
lora_sent_stats = []
lora_sent_acks = []

# --------- GPS ----------------
gps_enabled = True
gps_timeout = 300
max_distance_allow = 50
latitude = [0,0,0,0]
longitude = [0,0,0,0]
last_lat_tmp=0
last_lon_tmp=0
min_hdop = 1.5
min_pdop = 1.8
min_satellites = 8

# ------- Indicators ---------

indicatorFrequencyOn = 10
indicatorFrequencyOff = 10