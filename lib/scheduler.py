import utime
import machine
import rtcmgt
from errorissuer import checkError

class Scheduler:
    
    def __init__(self):
        self.dailyreset="00:00:00"
        self.startDownlink="00:00:00"
        self.endDownlink="05:00:00"

    def checkNextReset(self):
        # print("Daily Reset:",self.dailyreset)
        # print("Start Downlink:",self.startDownlink)
        # print("End Downlink:",self.endDownlink)
        dt = utime.gmtime()
        print("Scheduler: " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]))
        if dt[3] == int(self.dailyreset.split(":")[0]) and dt[4] == int(self.dailyreset.split(":")[1]) and dt[5] > int(self.dailyreset.split(":")[2]) and dt[5] < (int(self.dailyreset.split(":")[2])+15):
            checkError("Reseting module because of daily schedule")
            rtcmgt.updateRTC()
            utime.sleep(2)
            machine.reset()           

    def start(self):
        try:
            print("Daily Reset:",self.dailyreset)
            print("Start Downlink:",self.startDownlink)
            print("End Downlink:",self.endDownlink)
            print("Starting scheduler, Time: " + str(utime.gmtime()))
        except Exception as e:
            print("Error on scheduler: " + str(e))
