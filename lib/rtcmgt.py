from machine import RTC
import pycom
import utime
import machine

def initRTC():
    try:
        rtc = RTC()
        dt = pycom.nvs_get('rtc')
        print("Step RTC - Initializing RTC to " + str(int(dt)))
        rtc.init(utime.gmtime(int(dt)))
    except Exception as e1:
        print("Step RTC - Error initializing parametetr: " + str(e1)) 

def forceRTC(dt):
    try:
        rtc = RTC()
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

def checkCalendar(req_day, req_hour, req_minute):
    try:
        print("")
    except Exception as e:
        print("Error")

def updateRTC():
    try:
        pycom.nvs_set('rtc', str(int(utime.time())))
    except Exception as e:
        print("Error updating RTC")