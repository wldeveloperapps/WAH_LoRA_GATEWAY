from machine import RTC
import pycom
import utime
import machine

rtc = RTC()

def initRTC():
    global rtc
    try:
        dt = pycom.nvs_get('rtc')
        print("Step RTC - Initializing RTC to " + str(int(dt)))
        rtc.init(utime.gmtime(int(dt)))
    except Exception as e1:
        print("Step RTC - Error initializing parametetr: " + str(e1)) 

def forceRTC(dt):
    global rtc
    try:
        # dt = pycom.nvs_get('rtc')
        print("Step RTC - Initializing RTC to " + str(int(dt)))
        rtc.init(utime.gmtime(int(dt)))
    except Exception as e1:
        print("Step RTC - Error initializing parametetr: " + str(e1)) 

def autoRTCInitialize():
    reset_cause = machine.reset_cause()
    if reset_cause is not 3:
        initRTC()
    else:
        print("RTC Reset cause: " + str(reset_cause))

def getRTC():
    global rtc
    try:
        print("Getting RTC: " + str(rtc))
        return rtc
    except Exception as e:
        print("Error")

def updateRTC():
    try:
        pycom.nvs_set('rtc', str(int(utime.time())))
    except Exception as e:
        print("Error updating RTC")