from machine import SD
import utime

def LoRaWANSaveStatistics(strError):
    try:
        f = open('/sd/statistics.csv', 'a')
        strToSave = str(str(strError) + "," + str(int(utime.time()))+ "\r\n")
        print("Step 5 - Creating new register LoRaWAN Sent list: " + str(strToSave))
        f.write(strToSave)
        f.close()

    except Exception as e:
        print("Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e))
        return 11, "Step 5 - Error writing new device in LoRaWAN Sent list: " + str(e)
        