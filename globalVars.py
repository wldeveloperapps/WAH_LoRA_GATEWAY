

# ------ Device Type ------
deviceID = 2 # PyTrack
# deviceID = 1 # PySense

# ------ Configuration parameters --------
MAX_REFRESH_TIME = 150 # Code 20
BLE_SCAN_PERIOD = 6 # Code 21
STANDBY_PERIOD = 1 # Code 22
RSSI_NEAR_THRESHOLD = 'c4' # Code 23
STATISTICS_REPORT_INTERVAL = 600 # Code 24
BUZZER_DURATION = 1 # Code 25
SENT_PERIOD = 300 # Code 26
BUZZER_COUNTER_ALARM = 3 # Code 27

# ------ LoRaWAN Configuration -------
LORA_CHANNEL = 1
LORA_NODE_DR = 5
# REGION = 'AS923'
REGION = 'EU868'


# ------ Debug -------------
debug_cc = "vv"

# ------ Timers -----------


# ------ Flags ------------
stop_sleep_flag = False
flag_sent = False
flag_blelora = False

# -------- Lists ------------
devices_whitelist = []
device_sent = []
mac_scanned = []
scanned_frames = []

#-------- LoRa variables -----

last_lora_sent = 0
lora_sent_devices = []

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