

# ------ Device Type ------
deviceID = 2 # PyTrack
# deviceID = 1 # PySense

# ------ Configuration parameters --------
MAX_REFRESH_TIME = 60 # Code 20
BLE_SCAN_PERIOD = 6 # Code 21
STANDBY_PERIOD = 3 # Code 22
RSSI_NEAR_THRESHOLD = 'b0' # Code 23
STATISTICS_REPORT_INTERVAL = 300 # Code 24
BUZZER_DURATION = 1 # Code 25

# ------ LoRaWAN Configuration -------
LORA_CHANNEL = 1
LORA_NODE_DR = 4
# REGION = 'AS923'
REGION = 'EU868'

# ------ Debug -------------
debug_cc = "vv"


# ------ Flags ------------
stop_sleep_flag = False
flag_sent = False

