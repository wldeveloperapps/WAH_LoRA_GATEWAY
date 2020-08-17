import utime

class Scheduler:
    
    def __init__(self):
        self.dailyreset=""
        self.startDownlink=""
        self.endDownlink=""

    def getNextReset(self):
        print("Daily Reset:",self.dailyreset)
        print("Start Downlink:",self.startDownlink)
        print("End Downlink:",self.endDownlink)

    def start(self):
        try:
            dt = utime.gmtime()
            print("Starting scheduler, Time: " + str(dt))
            if dt[3] == 00:
                print("Time for reset")
            else:
                print("Waiting for the reset: " + str(dt.split(',')[3]))
        except Exception as e:
            print("Error on scheduler: " + str(e))
