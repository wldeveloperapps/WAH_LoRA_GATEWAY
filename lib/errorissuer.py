
# Code 0: Error reading SD Card
# Code 1: Error Sending LoRaWAN Information
# Code 2: Error Initializing LoRaWAN Sockets
# Code 3: Error Initializing LoRaWAN module
# Code 4: Error in main program
# Code 5: Error in flash storage
# Code 6: Error writing new device in whitelist
# Code 7: Error writing new device in buzzerlist
# Code 8: Error getting device in buzzerlist
# Code 9: Error cleaning devices timeout
# Code 10: Error getting SD Card initial data
# Code 11: Error writing new device in LoRaWAN Sent list
# Code 12: Error updating device in LoRaWAN Sent list
# Code 13: Error cleaning Buzzer List
# Code 14: Error cleaning LoRaWAN Sent List
# Code 15: Error cleaning White List
# Code 16: Error managing downlink messages
# Code 17: Error setting configuiration parameters
# Code 18: Error initializing paramerters
# Code 19: Error sending statistics reports
# Code 20: Error getting battery level
# Code 21: Error Filtering RSSI values
import machine
import utime
import sys
from uio import StringIO

def checkWarning(message):
    try:
        print("Warning control: " +str(message))
    except BaseException as e:
        err = sys.print_exception(e, s)
        saveErrorInFlash("Error managing warning issuer: " + str(s.getvalue()))
        utime.sleep(5)
        machine.reset()  

def checkError(type_msg ,message):
    try:
        s = StringIO()
        err = sys.print_exception(message, s)
        msg_complete = str(type_msg) + " - " + str(s.getvalue())
        print("Error control: " +str(msg_complete))
        saveErrorInFlash(str(type_msg)+ str(msg_complete))
        utime.sleep(5)
        if 'I2C bus error' in str(msg_complete):
            machine.reset()
        if 'memory' in str(msg_complete):
            machine.reset()     
    except BaseException as e:
        err = sys.print_exception(e, s)
        saveErrorInFlash("Error managing error issuer: " + str(s.getvalue()))
        utime.sleep(5)
        machine.reset()

def saveErrorInFlash(strError):
    try:
        f = open('/sd/errorIssuer.csv', 'a+')
        strToSave = str(str(strError) + "," + str(int(utime.time()))+ "\r\n")
        print("Saving new error: " + str(strToSave))
        f.write(strToSave)
        f.close()

    except Exception as e:
        print("Error saving error: " + str(e))

