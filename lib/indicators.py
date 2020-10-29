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
            while True:
                # tools.debug("Indicators thread running: " + str(globalVars.indicatorFrequency) + " - Led Status: " + str(flag_status), "vvv")                
                if globalVars.indicatorFrequency == 100:
                    self.p_out_init.value(1)
                    utime.sleep(1)
                elif globalVars.indicatorFrequency == 0:
                    self.p_out_init.value(0)
                    utime.sleep(1)
                else:
                    if flag_status == True:
                        self.p_out_init.value(0)
                        flag_status = False 
                    else:
                        self.p_out_init.value(1)
                        flag_status = True 
                    
                    utime.sleep(globalVars.indicatorFrequency/10)
                
        except BaseException as e:
            checkError("Error on indicators", e) 
