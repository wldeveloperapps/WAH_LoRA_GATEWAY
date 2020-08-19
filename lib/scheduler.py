import utime
import machine

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
        if dt[3] == 00 and dt[4] == 00 and dt[5] > 00 and dt[5] < 5:
            print("Reseting module because of daily schedule")
            utime.sleep(2)
            machine.reset()           

    def start(self):
        try:
            print("Daily Reset:",self.dailyreset)
            print("Start Downlink:",self.startDownlink)
            print("End Downlink:",self.endDownlink)
            dt = utime.gmtime()
            print("Starting scheduler, Time: " + str(dt))
            if dt[3] == 00:
                print("Time for reset")
            else:
                print("Waiting for the reset: " + str(dt[3]))
        except Exception as e:
            print("Error on scheduler: " + str(e))
