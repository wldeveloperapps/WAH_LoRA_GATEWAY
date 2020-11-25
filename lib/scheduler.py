import utime
import machine
import rtcmgt
import tools
import globalVars
from errorissuer import checkError

def singleton(class_):
    class class_w(class_):
        _instance = None
        def __new__(class2, *args, **kwargs):
            if class_w._instance is None:
                class_w._instance = super(class_w, class2).__new__(class2, *args, **kwargs)
                class_w._instance._sealed = False
            return class_w._instance
        def __init__(self, *args, **kwargs):
            if self._sealed:
                return
            super(class_w, self).__init__(*args, **kwargs)
            self._sealed = True
    class_w.__name__ = class_.__name__
    return class_w

@singleton
class Scheduler():
    
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
            dt_dm = str(dt[6]) + " " + str(dt[2]) + "-"+ str(dt[1]) + "-" + str(dt[0]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5])
            tools.debug("Scheduler - Current date: " + str(dt_dm)  + " - Daily ends at: " + globalVars.dailyStandBy + "- Downlinks begin at: " + globalVars.startDownlink, "v")
            # --------- S1 (Sleep Cycle 1) - From End of the day to first Downlink message ---------------
            if dt[3] == int(globalVars.dailyStandBy.split(":")[0]) and dt[4] == int(globalVars.dailyStandBy.split(":")[1]) and dt[5] > int(globalVars.dailyStandBy.split(":")[2]) and dt[5] < (int(globalVars.dailyStandBy.split(":")[2])+60):
                rnd_tmp_1 = tools.calculateSleepTime(globalVars.dailyStandBy,globalVars.startDownlink)
                tools.debug("Scheduler - DutyCycle - Going to sleep because the day ends and until the downlinks begin: " + str(rnd_tmp_1), "v")
                tools.deepSleepWiloc(rnd_tmp_1)
            
            # --------- S2 - Backup sleeping process in case the device is still on when passing the maximum downlink time  ---------------
            if dt[3] == int(globalVars.endDownlink.split(":")[0]) and dt[4] == int(globalVars.endDownlink.split(":")[1]) and dt[5] > int(globalVars.endDownlink.split(":")[2]) and dt[5] < (int(globalVars.endDownlink.split(":")[2])+60):
                rnm_tmp = tools.calculateSleepTime(globalVars.endDownlink,globalVars.dailyStart)
                tools.debug("Scheduler - DutyCycle - Going to sleep until the day begins: " + str(rnm_tmp), "v")
                tools.deepSleepWiloc(rnm_tmp)
            # ---------- Check if today is the day OFF --------------
            if dt[6] in globalVars.dayOff:
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
            current_wiloc_dt = str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5])
            slp_tm_day = tools.calculateSleepTime(current_wiloc_dt,globalVars.dailyStandBy)
            tools.debug("Scheduler - Overnight start: " + globalVars.startDownlink + "- Overnight end: " + globalVars.endDownlink, "v")
            
            if slp_tm_day < 0:
                if frameid == framescounter:
                    #------ Sleep cycle 3 (S3) ---------
                    slp_tm = tools.calculateSleepTime(current_wiloc_dt,globalVars.dailyStart)
                    tools.debug("Overnight Scheduler - Going to sleep until day begins: " + str(slp_tm), "v")
                    tools.deepSleepWiloc(slp_tm)
                else:
                    #------ Sleep cycle 2 (S2) ---------
                    rnd_secs = tools.random()
                    tools.debug("Overnight Scheduler - Going to sleep until next downlink: " + str(rnd_secs), "v")
                    tools.deepSleepWiloc(rnd_secs)
            else:
                tools.debug("Overnight Scheduler - Message received during the day, not going to sleep, current date: " + str(current_wiloc_dt) + " - Remaining day: " + str(slp_tm_day), "v")
                           
        except BaseException as e:
            checkError("Error on scheduler OvernightCycle", e)

    def start(self):
        try:
            tools.debug("Scheduler - Daily Reset: " + globalVars.dailyreset, "v")
            tools.debug("Scheduler - Start Downlink: " + globalVars.startDownlink, "v")
            tools.debug("Scheduler - End Downlink: " + globalVars.endDownlink, "v")
            tools.debug("Scheduler - Starting scheduler, Time: " + str(utime.gmtime()), "v")
        except BaseException as e:
            checkError("Error on scheduler", e)



