import utime
import machine
import rtcmgt
import tools
import globalVars
import random
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
        tools.debug("Scheduler: " + str(dt[6]) + " " + str(dt[2]) + "-"+ str(dt[1]) + "-" + str(dt[0]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]), 'v')
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

            tools.debug("Scheduler - Daily ends at: " + globalVars.dailyStandBy + "- Downlinks begin at: " + globalVars.startDownlink, "v")
            # --------- From End of the day to first Downlink message ---------------
            if dt[3] == int(globalVars.dailyStandBy.split(":")[0]) and dt[4] == int(globalVars.dailyStandBy.split(":")[1]) and dt[5] > int(globalVars.dailyStandBy.split(":")[2]) and dt[5] < (int(globalVars.dailyStandBy.split(":")[2])+60):
                rnd_tmp_1 = calculateSleepTime(globalVars.dailyStandBy,globalVars.startDownlink)
                tools.debug("Scheduler - DutyCycle - Going to sleep because the day ends and until the downlinks begin: " + str(rnd_tmp_1), "v")
                tools.deepSleepWiloc(rnd_tmp_1)
            
            # --------- Backup sleeping process in case the device is still on when passing the maximum downlink time  ---------------
            if dt[3] == int(globalVars.endDownlink.split(":")[0]) and dt[4] == int(globalVars.endDownlink.split(":")[1]) and dt[5] > int(globalVars.endDownlink.split(":")[2]) and dt[5] < (int(globalVars.endDownlink.split(":")[2])+60):
                rnm_tmp = calculateSleepTime(globalVars.dailyStandBy,globalVars.startDownlink)
                tools.debug("Scheduler - DutyCycle - Going to sleep until the day begins: " + str(rnm_tmp), "v")
                tools.deepSleepWiloc(rnm_tmp)
            # ---------- Check if today is the day OFF --------------
            if dt[6] == globalVars.dayOff:
                tools.debug("Scheduler - Going to sleep because is the day OFF", "v")
                tools.deepSleepWiloc(86460)

            
        except BaseException as e:
            checkError("Error on scheduler", e)

    def checkOvernightCycle(self, frameid, framescounter):
        try:
            dt = utime.gmtime()
            if globalVars.flag_rtc_syncro == False:
                tools.debug("Scheduler - RTC is not syncronized, so not possible to check the DutyCycle properly", "v")    
                return
            tools.debug("Scheduler - Overnight start: " + globalVars.startDownlink + "- Overnight end: " + globalVars.endDownlink, "v")
            if frameid == framescounter:
                current_wiloc_dt = str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5])
                slp_tm = calculateSleepTime(current_wiloc_dt,globalVars.dailyStart)
                tools.debug("Scheduler - Going to sleep until day begins: " + str(slp_tm), "v")
                tools.deepSleepWiloc(slp_tm)
            else:
                rnd_secs = random.randint(300,900)
                tools.debug("Scheduler - Going to sleep until next downlink: " + str(rnd_secs), "v")
                tools.deepSleepWiloc(rnd_secs)
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

    def calculateSleepTime(self, start, end):
        try:
            tools.debug("Scheduler - CalculateSleepTime", "v")
            diff_hour = int(end.split(':')[0]) - int(start.split(':')[0])
            diff_min = int(end.split(':')[1]) - int(start.split(':')[1])
            diff_sec = int(end.split(':')[2]) - int(start.split(':')[2])
            total_diff = (diff_hour*3600) + (diff_min*60) + diff_sec
            return total_diff
        except BaseException as e:
            checkError("Error on scheduler", e)

    