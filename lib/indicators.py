import utime
import machine
import rtcmgt
import tools
import globalVars
from errorissuer import checkError

class Indicators():
    
    def __init__(self):
        try:
            tools.debug("Indicators Initializing", "v")
            self.p_out_init = machine.Pin('P9', mode=machine.Pin.OUT)
        except BaseException as e:
            checkError("Error on indicators", e)

    def start(self):
        try:
            flag_status = False
            last_valOn = 0
            last_valOff = 0
            while True:
                if last_valOn == globalVars.indicatorFrequencyOn and last_valOff == globalVars.indicatorFrequencyOff:
                    if globalVars.indicatorFrequencyOn != 100 and globalVars.indicatorFrequencyOff != 100:
                        if flag_status == True:
                            self.p_out_init.value(0)
                            utime.sleep(globalVars.indicatorFrequencyOff/10)
                            flag_status = False 
                        else:
                            self.p_out_init.value(1)
                            utime.sleep(globalVars.indicatorFrequencyOn/10)
                            flag_status = True
                    else:    
                        tools.debug("Indicators - Going to sleep directly because lastval=indfrec: " + str(globalVars.indicatorFrequencyOn) + ": " + str(globalVars.indicatorFrequencyOff),"vvv")
                        utime.sleep(5)
                else:
                    tools.debug("Indicators - Updating indicators frequency value: " + str(globalVars.indicatorFrequencyOn) + ": " + str(globalVars.indicatorFrequencyOff),"vvv")
                    last_valOn = globalVars.indicatorFrequencyOn
                    last_valOff = globalVars.indicatorFrequencyOff
                    if globalVars.indicatorFrequencyOn == 100:
                        self.p_out_init.value(1)
                    elif globalVars.indicatorFrequencyOff == 100:
                        self.p_out_init.value(0)


                
        except BaseException as e:
            checkError("Error on indicators", e) 
