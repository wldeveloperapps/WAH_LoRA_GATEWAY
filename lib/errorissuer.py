
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

def checkError(message):
    try:
        print("Error control: " +str(message))
        if 'I2C bus error' in str(message):
            machine.reset()
        if 'memory' in str(message):
            machine.reset()     
    except Exception as e:
        print("Error managing error issuer")
        machine.reset()