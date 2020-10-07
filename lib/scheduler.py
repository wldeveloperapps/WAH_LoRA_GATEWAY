import utime
import machine
import rtcmgt
import tools
from errorissuer import checkError

class Scheduler:
    
    def __init__(self):
        self.dailyreset="00:00:00"
        self.startDownlink="00:00:00"
        self.endDownlink="05:00:00"

    def checkNextReset(self):
        dt = utime.gmtime()
        tools.debug("Scheduler: " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]), 'v')
        if dt[3] == int(self.dailyreset.split(":")[0]) and dt[4] == int(self.dailyreset.split(":")[1]) and dt[5] > int(self.dailyreset.split(":")[2]) and dt[5] < (int(self.dailyreset.split(":")[2])+15):
            tools.debug("Reseting module because of daily schedule", "v")
            rtcmgt.updateRTC()
            utime.sleep(2)
            machine.reset()           

    def start(self):
        try:
            tools.debug("Daily Reset: " + self.dailyreset, "v")
            tools.debug("Start Downlink: " + self.startDownlink, "v")
            tools.debug("End Downlink: " + self.endDownlink, "v")
            tools.debug("Starting scheduler, Time: " + str(utime.gmtime()), "v")
        except BaseException as e:
            checkError("Error on scheduler", e)
