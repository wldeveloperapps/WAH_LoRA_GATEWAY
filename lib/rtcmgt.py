from machine import RTC
import pycom
import utime
import machine
from errorissuer import checkError
import tools

rtc = RTC()

def initRTC():
    global rtc
    try:
        dt = pycom.nvs_get('rtc_dt')
        print("Step RTC - Initializing RTC to " + str(int(dt)))
        rtc.init(utime.gmtime(int(dt)))
        utime.sleep(2)
    except Exception as e1:
        checkError("Step RTC - Error initializing parametetr", e1) 

def forceRTC(dt, type_dt):
    global rtc
    try:
        # dt = pycom.nvs_get('rtc')
        
        if type_dt == "tuple":
            print("Step RTC - Forcing Tuple RTC to " + str(dt))
            rtc.init(dt)
        elif type_dt == "epoch":
            print("Step RTC - Forcing Epoch RTC to " + str(int(dt)))
            rtc.init(utime.gmtime(int(dt)))

        utime.sleep(3)
        tools.debug("Setting time: " + str(int(utime.time())),"v")
        try:
            pycom.nvs_set('rtc_dt', str(int(utime.time())))
        except OSError as err:
            tools.debug("Error setting RTC: " + str(err), "v")
        
        utime.sleep(5)
        try:
            dt_current = pycom.nvs_get('rtc_dt')
        except OSError as err:
            dt_current = -1
            tools.debug("Error getting RTC: " + str(err), "v")
        
        tools.debug("Current time: " + str(dt_current) + " - RTC: " + str(getDatetime()),"v")
    except Exception as e1:
        checkError("Step RTC - Error initializing parametetr", e1) 

def autoRTCInitialize():
    try:
        reset_cause = machine.reset_cause()
        if reset_cause is not 3:
            initRTC()
        else:
            print("RTC Reset cause: " + str(reset_cause))
    except Exception as e:
        checkError("Error", e)

def getRTC():
    global rtc
    try:
        print("Getting RTC: " + str(rtc))
        return rtc
    except Exception as e:
        checkError("Error", e)

def getDatetime():
    try:
        return rtc.now()
    except Exception as e:
        checkError("Error getting datetime", e)

def updateRTC():
    try:
        tools.debug("Updating RTC to " + str(int(utime.time())),"vv")
        pycom.nvs_set('rtc_dt', str(int(utime.time())))
        utime.sleep(3)
    except Exception as e:
        checkError("Error updating RTC", e)