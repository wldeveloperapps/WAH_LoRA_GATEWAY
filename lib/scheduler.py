import utime
import machine
import rtcmgt
import tools
import globalVars
from errorissuer import checkError

class Scheduler:
    
    def __init__(self):
        self.dailyreset=globalVars.dailyreset
        self.startDownlink=globalVars.startDownlink
        self.endDownlink=globalVars.endDownlink
        self.dailyStart=globalVars.dailyStart
        self.dailyStandBy=globalVars.dailyStandBy

    
    def checkNextReset(self):
        dt = utime.gmtime()
        tools.debug("Scheduler: " + str(dt[2]) + "-"+ str(dt[1]) + "-" + str(dt[0]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]), 'v')
        if dt[3] == int(globalVars.dailyreset.split(":")[0]) and dt[4] == int(globalVars.dailyreset.split(":")[1]) and dt[5] > int(globalVars.dailyreset.split(":")[2]) and dt[5] < (int(globalVars.dailyreset.split(":")[2])+15):
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

            tools.debug("Scheduler - Daily Start: " + globalVars.dailyStart + "- Daily StandBy: " + globalVars.dailyStandBy, "v")
            if dt[3] == int(globalVars.dailyStandBy.split(":")[0]) and dt[4] == int(globalVars.dailyStandBy.split(":")[1]) and dt[5] > int(globalVars.dailyStandBy.split(":")[2]) and dt[5] < (int(globalVars.dailyStandBy.split(":")[2])+60):
                tools.debug("Scheduler - DutyCycle - Going to sleep for a while...", "v")
                tools.deepSleepWiloc(60)
        except BaseException as e:
            checkError("Error on scheduler", e)

    def start(self):
        try:
            tools.debug("Scheduler - Daily Reset: " + globalVars.dailyreset, "v")
            tools.debug("Scheduler - Start Downlink: " + globalVars.startDownlink, "v")
            tools.debug("Scheduler - End Downlink: " + globalVars.endDownlink, "v")
            tools.debug("Scheduler - Starting scheduler, Time: " + str(utime.gmtime()), "v")
        except BaseException as e:
            checkError("Error on scheduler", e)

    def calculateSleepTime(self):
        try:
            tools.debug("Scheduler - CalculateSleepTime", "v")
        except BaseException as e:
            checkError("Error on scheduler", e)