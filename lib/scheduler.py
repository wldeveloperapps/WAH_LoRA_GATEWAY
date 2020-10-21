import utime
import machine
import rtcmgt
import tools
import globalVars
from errorissuer import checkError

class Scheduler:
    
    def __init__(self):
        self.dailyreset="00:00:00"
        self.startDownlink="01:00:00"
        self.endDownlink="03:00:00"
        self.dailyStart="06:00:00"
        self.dailyStandBy="16:28:00"
    
    def checkNextReset(self):
        dt = utime.gmtime()
        tools.debug("Scheduler: " + str(dt[2]) + "-"+ str(dt[1]) + "-" + str(dt[0]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]), 'v')
        if dt[3] == int(self.dailyreset.split(":")[0]) and dt[4] == int(self.dailyreset.split(":")[1]) and dt[5] > int(self.dailyreset.split(":")[2]) and dt[5] < (int(self.dailyreset.split(":")[2])+15):
            tools.debug("Scheduler - Reseting module because of daily schedule", "v")
            rtcmgt.updateRTC()
            utime.sleep(2)
            machine.reset()           

    def checkDutyCycle(self):
        try:
            dt = utime.gmtime()
            if globalVars.flag_rtc_syncro == False:
                tools.debug("Scheduler - RTC is not syncronized, so not possible to check the DutyCycle properly", "v")    
                return

            tools.debug("Scheduler - Daily Start: " + self.dailyStart, "v")
            tools.debug("Scheduler - Daily StandBy: " + self.dailyStandBy, "v")
            if dt[3] == int(self.dailyStandBy.split(":")[0]) and dt[4] == int(self.dailyStandBy.split(":")[1]) and dt[5] > int(self.dailyStandBy.split(":")[2]) and dt[5] < (int(self.dailyStandBy.split(":")[2])+60):
                tools.debug("Scheduler - DutyCycle - Going to sleep for a while...", "v")
                tools.deepSleepWiloc(60)
        except BaseException as e:
            checkError("Error on scheduler", e)

    def start(self):
        try:
            tools.debug("Scheduler - Daily Reset: " + self.dailyreset, "v")
            tools.debug("Scheduler - Start Downlink: " + self.startDownlink, "v")
            tools.debug("Scheduler - End Downlink: " + self.endDownlink, "v")
            tools.debug("Scheduler - Starting scheduler, Time: " + str(utime.gmtime()), "v")
        except BaseException as e:
            checkError("Error on scheduler", e)
